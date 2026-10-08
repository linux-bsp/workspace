/************************************************************************
 * PDI BMC PMCP backend
 ************************************************************************/

#include "../pdi_bmc_priv.h"

#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#ifndef MSG_NOSIGNAL
#define MSG_NOSIGNAL 0
#endif

#define PDI_BMC_PMCP_MAGIC 0x504d4350U /* "PMCP" */
#define PDI_BMC_PMCP_VERSION 1U
#define PDI_BMC_PMCP_FRAME_HEADER_LEN 32U
#define PDI_BMC_PMCP_DEFAULT_PORT "62300"
#define PDI_BMC_PMCP_DEFAULT_TIMEOUT_MS 5000U
#define PDI_BMC_PMCP_FRAME_PAYLOAD_MAX 4096U
#define PDI_BMC_PMCP_MESSAGE_MAX (1024U * 1024U)

#define PDI_BMC_PMCP_FLAG_RESPONSE 0x0001U

#define PDI_BMC_PMCP_TYPE_HELLO 1U
#define PDI_BMC_PMCP_TYPE_GET_INFO 2U
#define PDI_BMC_PMCP_TYPE_GET_POWER_STATE 3U
#define PDI_BMC_PMCP_TYPE_POWER_CONTROL 4U
#define PDI_BMC_PMCP_TYPE_GET_SENSORS 5U

struct pdi_bmc_pmcp_ctx {
	int fd;
	uint32_t timeout_ms;
	uint32_t next_seq;
	uint32_t frame_payload_max;
	uint32_t message_max;
};

struct pdi_bmc_pmcp_frame_header {
	uint32_t magic;
	uint8_t version;
	uint8_t header_len;
	uint16_t flags;
	uint16_t type;
	uint16_t reserved;
	uint32_t seq;
	uint32_t offset;
	uint32_t total_len;
	uint32_t data_len;
	uint32_t crc32;
};

typedef char pdi_bmc_pmcp_frame_header_size_check[
	sizeof(struct pdi_bmc_pmcp_frame_header) ==
	PDI_BMC_PMCP_FRAME_HEADER_LEN ? 1 : -1];

struct pdi_bmc_pmcp_hello_request {
	char username[PDI_BMC_MAX_USERNAME_LEN];
	char password[PDI_BMC_MAX_PASSWORD_LEN];
};

struct pdi_bmc_pmcp_hello_response {
	uint32_t status;
	uint32_t max_frame_payload;
	uint32_t max_message_len;
	char controller_id[PDI_BMC_MAX_ID_LEN];
	char protocol_version[PDI_BMC_MAX_TEXT_LEN];
};

struct pdi_bmc_pmcp_info_response {
	uint32_t status;
	uint32_t power_state;
	char system_id[PDI_BMC_MAX_ID_LEN];
	char system_model[PDI_BMC_MAX_TEXT_LEN];
	char system_manufacturer[PDI_BMC_MAX_TEXT_LEN];
	char bios_version[PDI_BMC_MAX_TEXT_LEN];
	char serial_number[PDI_BMC_MAX_TEXT_LEN];
	char manager_id[PDI_BMC_MAX_ID_LEN];
	char model[PDI_BMC_MAX_TEXT_LEN];
	char firmware_version[PDI_BMC_MAX_TEXT_LEN];
	char health[PDI_BMC_MAX_TEXT_LEN];
	char state[PDI_BMC_MAX_TEXT_LEN];
};

struct pdi_bmc_pmcp_power_state_response {
	uint32_t status;
	uint32_t power_state;
};

struct pdi_bmc_pmcp_power_control_request {
	uint32_t action;
};

struct pdi_bmc_pmcp_status_response {
	uint32_t status;
};

struct pdi_bmc_pmcp_sensors_request {
	uint32_t type;
	uint32_t scope;
};

struct pdi_bmc_pmcp_sensors_response_header {
	uint32_t status;
	uint32_t count;
};

struct pdi_bmc_pmcp_sensor_record {
	uint32_t type;
	uint32_t scope;
	char id[PDI_BMC_MAX_ID_LEN];
	char name[PDI_BMC_MAX_TEXT_LEN];
	char source[PDI_BMC_MAX_SOURCE_LEN];
	char units[PDI_BMC_MAX_UNIT_LEN];
	uint64_t reading_milli;
	char health[PDI_BMC_MAX_TEXT_LEN];
	char state[PDI_BMC_MAX_TEXT_LEN];
};

static uint32_t pmcp_timeout_ms(const struct pdi_bmc_pmcp_ctx *ctx)
{
	if (ctx && ctx->timeout_ms)
		return ctx->timeout_ms;
	return PDI_BMC_PMCP_DEFAULT_TIMEOUT_MS;
}

static uint64_t pmcp_bswap64(uint64_t val)
{
	return ((val & 0x00000000000000ffULL) << 56) |
	       ((val & 0x000000000000ff00ULL) << 40) |
	       ((val & 0x0000000000ff0000ULL) << 24) |
	       ((val & 0x00000000ff000000ULL) << 8) |
	       ((val & 0x000000ff00000000ULL) >> 8) |
	       ((val & 0x0000ff0000000000ULL) >> 24) |
	       ((val & 0x00ff000000000000ULL) >> 40) |
	       ((val & 0xff00000000000000ULL) >> 56);
}

static uint64_t pmcp_htonll(uint64_t val)
{
	const uint16_t one = 1;

	if (*(const uint8_t *)&one)
		return pmcp_bswap64(val);
	return val;
}

static uint64_t pmcp_ntohll(uint64_t val)
{
	return pmcp_htonll(val);
}

static uint32_t pmcp_get_u32(uint32_t val)
{
	return ntohl(val);
}

static int32_t pmcp_get_i32(uint32_t val)
{
	return (int32_t)ntohl(val);
}

static uint64_t pmcp_get_u64(uint64_t val)
{
	return pmcp_ntohll(val);
}

static uint32_t pmcp_crc32(const void *data, size_t len)
{
	const uint8_t *bytes = data;
	uint32_t crc = 0xffffffffU;

	for (size_t i = 0; i < len; i++) {
		crc ^= bytes[i];
		for (int bit = 0; bit < 8; bit++) {
			if (crc & 1U)
				crc = (crc >> 1) ^ 0xedb88320U;
			else
				crc >>= 1;
		}
	}

	return ~crc;
}

static int pmcp_wait_fd(int fd, bool write_ready, uint32_t timeout_ms)
{
	fd_set rfds;
	fd_set wfds;
	struct timeval tv;
	int ret;

	if (fd < 0 || fd >= FD_SETSIZE)
		return -EINVAL;

	for (;;) {
		FD_ZERO(&rfds);
		FD_ZERO(&wfds);
		if (write_ready)
			FD_SET(fd, &wfds);
		else
			FD_SET(fd, &rfds);

		tv.tv_sec = timeout_ms / 1000U;
		tv.tv_usec = (suseconds_t)((timeout_ms % 1000U) * 1000U);
		ret = select(fd + 1, write_ready ? NULL : &rfds,
			     write_ready ? &wfds : NULL, NULL, &tv);
		if (ret > 0)
			return 0;
		if (ret == 0)
			return -ETIMEDOUT;
		if (errno != EINTR)
			return -errno;
	}
}

static int pmcp_read_full(struct pdi_bmc_pmcp_ctx *ctx, void *buf, size_t len)
{
	uint8_t *ptr = buf;
	size_t done = 0;

	if (!ctx || ctx->fd < 0 || (!buf && len))
		return -EINVAL;

	while (done < len) {
		ssize_t ret = recv(ctx->fd, ptr + done, len - done, 0);

		if (ret > 0) {
			done += (size_t)ret;
			continue;
		}
		if (ret == 0)
			return -ECONNRESET;
		if (errno == EINTR)
			continue;
		if (errno == EAGAIN || errno == EWOULDBLOCK) {
			ret = pmcp_wait_fd(ctx->fd, false, pmcp_timeout_ms(ctx));
			if (ret < 0)
				return ret;
			continue;
		}
		return -errno;
	}

	return 0;
}

static int pmcp_write_full(struct pdi_bmc_pmcp_ctx *ctx, const void *buf,
				   size_t len)
{
	const uint8_t *ptr = buf;
	size_t done = 0;

	if (!ctx || ctx->fd < 0 || (!buf && len))
		return -EINVAL;

	while (done < len) {
		ssize_t ret = send(ctx->fd, ptr + done, len - done, MSG_NOSIGNAL);

		if (ret > 0) {
			done += (size_t)ret;
			continue;
		}
		if (ret == 0)
			return -EIO;
		if (errno == EINTR)
			continue;
		if (errno == EAGAIN || errno == EWOULDBLOCK) {
			ret = pmcp_wait_fd(ctx->fd, true, pmcp_timeout_ms(ctx));
			if (ret < 0)
				return ret;
			continue;
		}
		return -errno;
	}

	return 0;
}

static int pmcp_set_nonblock(int fd)
{
	int flags;

	flags = fcntl(fd, F_GETFL, 0);
	if (flags < 0)
		return -errno;
	if (fcntl(fd, F_SETFL, flags | O_NONBLOCK) < 0)
		return -errno;

	return 0;
}

static int pmcp_connect_wait(int fd, uint32_t timeout_ms)
{
	int error = 0;
	socklen_t error_len = sizeof(error);
	int ret;

	ret = pmcp_wait_fd(fd, true, timeout_ms ? timeout_ms :
				       PDI_BMC_PMCP_DEFAULT_TIMEOUT_MS);
	if (ret < 0)
		return ret;

	if (getsockopt(fd, SOL_SOCKET, SO_ERROR, &error, &error_len) < 0)
		return -errno;
	if (error)
		return -error;

	return 0;
}

static int pmcp_parse_endpoint(const char *endpoint, char *host,
			       size_t host_len, char *port, size_t port_len)
{
	const char *value;
	const char *first_colon;
	const char *last_colon;
	size_t len;
	int ret;

	if (!endpoint || !endpoint[0] || !host || !host_len || !port || !port_len)
		return -EINVAL;

	value = endpoint;
	if (strncmp(value, "pmcp://", 7) == 0)
		value += 7;
	else if (strncmp(value, "tcp://", 6) == 0)
		value += 6;

	if (!value[0] || strchr(value, '/'))
		return -EINVAL;

	if (value[0] == '[') {
		const char *end = strchr(value, ']');

		if (!end || end == value + 1)
			return -EINVAL;
		len = (size_t)(end - value - 1);
		if (len >= host_len)
			return -ENAMETOOLONG;
		memcpy(host, value + 1, len);
		host[len] = '\0';
		if (end[1] == ':') {
			if (!end[2])
				return -EINVAL;
			return pdi_bmc_copy_string(port, port_len, end + 2);
		}
		if (end[1])
			return -EINVAL;
		return pdi_bmc_copy_string(port, port_len,
					       PDI_BMC_PMCP_DEFAULT_PORT);
	}

	first_colon = strchr(value, ':');
	last_colon = strrchr(value, ':');
	if (first_colon && first_colon == last_colon) {
		if (first_colon == value || !first_colon[1])
			return -EINVAL;
		len = (size_t)(first_colon - value);
		if (len >= host_len)
			return -ENAMETOOLONG;
		memcpy(host, value, len);
		host[len] = '\0';
		return pdi_bmc_copy_string(port, port_len, first_colon + 1);
	}

	ret = pdi_bmc_copy_string(host, host_len, value);
	if (ret < 0)
		return ret;

	return pdi_bmc_copy_string(port, port_len, PDI_BMC_PMCP_DEFAULT_PORT);
}

static int pmcp_connect_endpoint(const char *endpoint, uint32_t timeout_ms)
{
	struct addrinfo hints;
	struct addrinfo *result = NULL;
	struct addrinfo *ai;
	char host[PDI_BMC_MAX_ENDPOINT_LEN];
	char port[16];
	int last_ret = -ENODEV;
	int fd = -1;
	int ret;

	ret = pmcp_parse_endpoint(endpoint, host, sizeof(host), port,
				  sizeof(port));
	if (ret < 0)
		return ret;

	memset(&hints, 0, sizeof(hints));
	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_protocol = IPPROTO_TCP;

	ret = getaddrinfo(host, port, &hints, &result);
	if (ret)
		return ret == EAI_NONAME ? -ENOENT : -EIO;

	for (ai = result; ai; ai = ai->ai_next) {
		fd = socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
		if (fd < 0) {
			last_ret = -errno;
			continue;
		}

		ret = pmcp_set_nonblock(fd);
		if (ret < 0) {
			last_ret = ret;
			close(fd);
			fd = -1;
			continue;
		}

		ret = connect(fd, ai->ai_addr, ai->ai_addrlen);
		if (ret == 0) {
			freeaddrinfo(result);
			return fd;
		}
		if (errno == EINPROGRESS) {
			ret = pmcp_connect_wait(fd, timeout_ms);
			if (ret == 0) {
				freeaddrinfo(result);
				return fd;
			}
			last_ret = ret;
		} else {
			last_ret = -errno;
		}

		close(fd);
		fd = -1;
	}

	freeaddrinfo(result);
	return last_ret;
}

static uint32_t pmcp_next_seq(struct pdi_bmc_pmcp_ctx *ctx)
{
	ctx->next_seq++;
	if (!ctx->next_seq)
		ctx->next_seq++;
	return ctx->next_seq;
}

static int pmcp_send_message(struct pdi_bmc_pmcp_ctx *ctx, uint16_t type,
			     const void *payload, size_t payload_len,
			     uint32_t *seq_out)
{
	const uint8_t *bytes = payload;
	uint32_t seq;
	size_t offset = 0;
	int ret;

	if (!ctx || (!payload && payload_len) || !seq_out)
		return -EINVAL;
	if (payload_len > ctx->message_max || payload_len > UINT32_MAX)
		return -EMSGSIZE;

	seq = pmcp_next_seq(ctx);
	for (;;) {
		struct pdi_bmc_pmcp_frame_header header;
		size_t remaining = payload_len - offset;
		size_t chunk = remaining;
		uint32_t crc;

		if (chunk > ctx->frame_payload_max)
			chunk = ctx->frame_payload_max;

		crc = pmcp_crc32(chunk ? bytes + offset : NULL, chunk);
		memset(&header, 0, sizeof(header));
		header.magic = htonl(PDI_BMC_PMCP_MAGIC);
		header.version = PDI_BMC_PMCP_VERSION;
		header.header_len = PDI_BMC_PMCP_FRAME_HEADER_LEN;
		header.flags = htons(0);
		header.type = htons(type);
		header.seq = htonl(seq);
		header.offset = htonl((uint32_t)offset);
		header.total_len = htonl((uint32_t)payload_len);
		header.data_len = htonl((uint32_t)chunk);
		header.crc32 = htonl(crc);

		ret = pmcp_write_full(ctx, &header, sizeof(header));
		if (ret < 0)
			return ret;
		ret = pmcp_write_full(ctx, chunk ? bytes + offset : NULL, chunk);
		if (ret < 0)
			return ret;

		if (!payload_len || offset + chunk >= payload_len)
			break;
		offset += chunk;
	}

	*seq_out = seq;
	return 0;
}

static int pmcp_recv_message(struct pdi_bmc_pmcp_ctx *ctx, uint16_t type,
			     uint32_t seq, uint8_t **payload_out,
			     size_t *payload_len_out)
{
	uint8_t *payload = NULL;
	size_t total_len = 0;
	size_t received = 0;
	bool started = false;
	int ret;

	if (!ctx || !payload_out || !payload_len_out)
		return -EINVAL;
	*payload_out = NULL;
	*payload_len_out = 0;

	for (;;) {
		struct pdi_bmc_pmcp_frame_header header;
		uint32_t magic;
		uint16_t flags;
		uint16_t frame_type;
		uint32_t frame_seq;
		uint32_t offset;
		uint32_t frame_total;
		uint32_t data_len;
		uint32_t crc;

		ret = pmcp_read_full(ctx, &header, sizeof(header));
		if (ret < 0)
			goto err;

		magic = pmcp_get_u32(header.magic);
		flags = ntohs(header.flags);
		frame_type = ntohs(header.type);
		frame_seq = pmcp_get_u32(header.seq);
		offset = pmcp_get_u32(header.offset);
		frame_total = pmcp_get_u32(header.total_len);
		data_len = pmcp_get_u32(header.data_len);
		crc = pmcp_get_u32(header.crc32);

		if (magic != PDI_BMC_PMCP_MAGIC ||
		    header.version != PDI_BMC_PMCP_VERSION ||
		    header.header_len != PDI_BMC_PMCP_FRAME_HEADER_LEN ||
		    !(flags & PDI_BMC_PMCP_FLAG_RESPONSE) ||
		    frame_type != type || frame_seq != seq) {
			ret = -EPROTO;
			goto err;
		}
		if (frame_total > ctx->message_max ||
		    data_len > ctx->frame_payload_max ||
		    offset > frame_total || data_len > frame_total - offset) {
			ret = -EMSGSIZE;
			goto err;
		}
		if (offset != received) {
			ret = -EPROTO;
			goto err;
		}

		if (!started) {
			total_len = frame_total;
			if (total_len) {
				payload = malloc(total_len);
				if (!payload) {
					ret = -ENOMEM;
					goto err;
				}
			}
			started = true;
		} else if (frame_total != total_len) {
			ret = -EPROTO;
			goto err;
		}

		ret = pmcp_read_full(ctx, data_len ? payload + offset : NULL,
				     data_len);
		if (ret < 0)
			goto err;
		if (pmcp_crc32(data_len ? payload + offset : NULL, data_len) != crc) {
			ret = -EILSEQ;
			goto err;
		}

		received += data_len;
		if (received == total_len) {
			*payload_out = payload;
			*payload_len_out = total_len;
			return 0;
		}
	}

err:
	free(payload);
	return ret;
}

static int pmcp_transaction(struct pdi_bmc_pmcp_ctx *ctx, uint16_t type,
			    const void *request, size_t request_len,
			    uint8_t **response, size_t *response_len)
{
	uint32_t seq;
	int ret;

	ret = pmcp_send_message(ctx, type, request, request_len, &seq);
	if (ret < 0)
		return ret;

	return pmcp_recv_message(ctx, type, seq, response, response_len);
}

static void pmcp_copy_text(char *dst, size_t dst_len, const char *src,
			   size_t src_len)
{
	size_t len = 0;

	if (!dst || !dst_len)
		return;
	dst[0] = '\0';
	if (!src)
		return;

	while (len < src_len && src[len])
		len++;
	if (len >= dst_len)
		len = dst_len - 1U;
	memcpy(dst, src, len);
	dst[len] = '\0';
}

static int pmcp_status_to_errno(int32_t status)
{
	if (!status)
		return 0;
	return status < 0 ? status : -status;
}

static int pmcp_decode_status(const void *payload, size_t payload_len)
{
	const struct pdi_bmc_pmcp_status_response *response = payload;

	if (!payload || payload_len < sizeof(response->status))
		return -EPROTO;
	return pmcp_status_to_errno(pmcp_get_i32(response->status));
}

static enum pdi_bmc_power_state pmcp_power_state_from_wire(uint32_t value)
{
	switch (value) {
	case PDI_BMC_POWER_ON:
	case PDI_BMC_POWER_OFF:
	case PDI_BMC_POWER_POWERING_ON:
	case PDI_BMC_POWER_POWERING_OFF:
		return (enum pdi_bmc_power_state)value;
	case PDI_BMC_POWER_UNKNOWN:
	default:
		return PDI_BMC_POWER_UNKNOWN;
	}
}

static enum pdi_bmc_sensor_type pmcp_sensor_type_from_wire(uint32_t value)
{
	switch (value) {
	case PDI_BMC_SENSOR_TYPE_TEMPERATURE:
	case PDI_BMC_SENSOR_TYPE_POWER:
	case PDI_BMC_SENSOR_TYPE_FAN:
	case PDI_BMC_SENSOR_TYPE_VOLTAGE:
	case PDI_BMC_SENSOR_TYPE_CURRENT:
	case PDI_BMC_SENSOR_TYPE_UTILIZATION:
		return (enum pdi_bmc_sensor_type)value;
	case PDI_BMC_SENSOR_TYPE_ANY:
	default:
		return PDI_BMC_SENSOR_TYPE_ANY;
	}
}

static enum pdi_bmc_sensor_scope pmcp_sensor_scope_from_wire(uint32_t value)
{
	switch (value) {
	case PDI_BMC_SENSOR_SCOPE_SYSTEM:
	case PDI_BMC_SENSOR_SCOPE_CHASSIS:
	case PDI_BMC_SENSOR_SCOPE_CPU:
	case PDI_BMC_SENSOR_SCOPE_GPU:
	case PDI_BMC_SENSOR_SCOPE_MEMORY:
	case PDI_BMC_SENSOR_SCOPE_DRIVE:
	case PDI_BMC_SENSOR_SCOPE_FAN:
	case PDI_BMC_SENSOR_SCOPE_PSU:
	case PDI_BMC_SENSOR_SCOPE_PCIE:
		return (enum pdi_bmc_sensor_scope)value;
	case PDI_BMC_SENSOR_SCOPE_ANY:
	default:
		return PDI_BMC_SENSOR_SCOPE_ANY;
	}
}

static int pmcp_decode_hello(struct pdi_bmc_pmcp_ctx *ctx,
			     const uint8_t *payload, size_t payload_len)
{
	const struct pdi_bmc_pmcp_hello_response *response =
		(const struct pdi_bmc_pmcp_hello_response *)payload;
	uint32_t peer_frame_payload;
	uint32_t peer_message_max;
	int ret;

	ret = pmcp_decode_status(payload, payload_len);
	if (ret < 0)
		return ret;
	if (payload_len < sizeof(*response))
		return 0;

	peer_frame_payload = pmcp_get_u32(response->max_frame_payload);
	peer_message_max = pmcp_get_u32(response->max_message_len);
	if (peer_frame_payload && peer_frame_payload < ctx->frame_payload_max)
		ctx->frame_payload_max = peer_frame_payload;
	if (peer_message_max && peer_message_max < ctx->message_max)
		ctx->message_max = peer_message_max;

	return 0;
}

static int32_t pmcp_get_info(struct pdi_bmc_pmcp_ctx *ctx,
			     struct pdi_bmc_info *info)
{
	const struct pdi_bmc_pmcp_info_response *response;
	uint8_t *payload = NULL;
	size_t payload_len = 0;
	int ret;

	if (!ctx || !info)
		return -EINVAL;

	ret = pmcp_transaction(ctx, PDI_BMC_PMCP_TYPE_GET_INFO, NULL, 0,
			       &payload, &payload_len);
	if (ret < 0)
		return ret;

	ret = pmcp_decode_status(payload, payload_len);
	if (ret < 0)
		goto out;
	if (payload_len < sizeof(*response)) {
		ret = -EPROTO;
		goto out;
	}

	response = (const struct pdi_bmc_pmcp_info_response *)payload;
	memset(info, 0, sizeof(*info));
	info->protocol = PDI_BMC_PROTOCOL_PMCP;
	info->power_state = pmcp_power_state_from_wire(
		pmcp_get_u32(response->power_state));
	pmcp_copy_text(info->system_id, sizeof(info->system_id),
		       response->system_id, sizeof(response->system_id));
	pmcp_copy_text(info->system_model, sizeof(info->system_model),
		       response->system_model, sizeof(response->system_model));
	pmcp_copy_text(info->system_manufacturer,
		       sizeof(info->system_manufacturer),
		       response->system_manufacturer,
		       sizeof(response->system_manufacturer));
	pmcp_copy_text(info->bios_version, sizeof(info->bios_version),
		       response->bios_version, sizeof(response->bios_version));
	pmcp_copy_text(info->serial_number, sizeof(info->serial_number),
		       response->serial_number, sizeof(response->serial_number));
	pmcp_copy_text(info->manager_id, sizeof(info->manager_id),
		       response->manager_id, sizeof(response->manager_id));
	pmcp_copy_text(info->model, sizeof(info->model), response->model,
		       sizeof(response->model));
	pmcp_copy_text(info->firmware_version, sizeof(info->firmware_version),
		       response->firmware_version,
		       sizeof(response->firmware_version));
	pmcp_copy_text(info->health, sizeof(info->health), response->health,
		       sizeof(response->health));
	pmcp_copy_text(info->state, sizeof(info->state), response->state,
		       sizeof(response->state));
	ret = 0;

out:
	free(payload);
	return ret;
}

static int32_t pmcp_get_power_state(struct pdi_bmc_pmcp_ctx *ctx,
				    enum pdi_bmc_power_state *state)
{
	const struct pdi_bmc_pmcp_power_state_response *response;
	uint8_t *payload = NULL;
	size_t payload_len = 0;
	int ret;

	if (!ctx || !state)
		return -EINVAL;

	ret = pmcp_transaction(ctx, PDI_BMC_PMCP_TYPE_GET_POWER_STATE, NULL, 0,
			       &payload, &payload_len);
	if (ret < 0)
		return ret;

	ret = pmcp_decode_status(payload, payload_len);
	if (ret < 0)
		goto out;
	if (payload_len < sizeof(*response)) {
		ret = -EPROTO;
		goto out;
	}

	response = (const struct pdi_bmc_pmcp_power_state_response *)payload;
	*state = pmcp_power_state_from_wire(pmcp_get_u32(response->power_state));
	ret = 0;

out:
	free(payload);
	return ret;
}

static int32_t pmcp_power_control(struct pdi_bmc_pmcp_ctx *ctx,
				  enum pdi_bmc_power_action action)
{
	struct pdi_bmc_pmcp_power_control_request request;
	uint8_t *payload = NULL;
	size_t payload_len = 0;
	int ret;

	if (!ctx)
		return -EINVAL;
	if (action < PDI_BMC_POWER_ACTION_ON ||
	    action > PDI_BMC_POWER_ACTION_FORCE_RESTART)
		return -EINVAL;

	request.action = htonl((uint32_t)action);
	ret = pmcp_transaction(ctx, PDI_BMC_PMCP_TYPE_POWER_CONTROL,
			       &request, sizeof(request), &payload, &payload_len);
	if (ret < 0)
		return ret;

	ret = pmcp_decode_status(payload, payload_len);
	free(payload);
	return ret;
}

static int32_t pmcp_get_sensors(struct pdi_bmc_pmcp_ctx *ctx,
				 const struct pdi_bmc_sensor_filter *filter,
				 struct pdi_bmc_sensor *sensors, uint32_t *count)
{
	struct pdi_bmc_pmcp_sensors_request request;
	struct pdi_bmc_sensor_accumulator acc;
	const struct pdi_bmc_pmcp_sensors_response_header *header;
	const uint8_t *records;
	uint8_t *payload = NULL;
	size_t payload_len = 0;
	uint32_t record_count;
	int ret;

	if (!ctx || !count)
		return -EINVAL;

	request.type = htonl((uint32_t)(filter ? filter->type :
					 PDI_BMC_SENSOR_TYPE_ANY));
	request.scope = htonl((uint32_t)(filter ? filter->scope :
					  PDI_BMC_SENSOR_SCOPE_ANY));

	ret = pmcp_transaction(ctx, PDI_BMC_PMCP_TYPE_GET_SENSORS,
			       &request, sizeof(request), &payload, &payload_len);
	if (ret < 0)
		return ret;

	ret = pmcp_decode_status(payload, payload_len);
	if (ret < 0) {
		*count = 0;
		goto out;
	}
	if (payload_len < sizeof(*header)) {
		ret = -EPROTO;
		goto out;
	}

	header = (const struct pdi_bmc_pmcp_sensors_response_header *)payload;
	record_count = pmcp_get_u32(header->count);
	if ((payload_len - sizeof(*header)) /
		    sizeof(struct pdi_bmc_pmcp_sensor_record) < record_count) {
		ret = -EPROTO;
		goto out;
	}

	ret = pdi_bmc_sensor_accumulator_init(&acc, filter, sensors, count);
	if (ret < 0)
		goto out;

	records = payload + sizeof(*header);
	for (uint32_t i = 0; i < record_count; i++) {
		const struct pdi_bmc_pmcp_sensor_record *record =
			(const struct pdi_bmc_pmcp_sensor_record *)
			(records + (size_t)i * sizeof(*record));
		struct pdi_bmc_sensor sensor;
		int64_t reading_milli;

		memset(&sensor, 0, sizeof(sensor));
		sensor.type = pmcp_sensor_type_from_wire(
			pmcp_get_u32(record->type));
		sensor.scope = pmcp_sensor_scope_from_wire(
			pmcp_get_u32(record->scope));
		reading_milli = (int64_t)pmcp_get_u64(record->reading_milli);
		sensor.reading = (double)reading_milli / 1000.0;
		pmcp_copy_text(sensor.id, sizeof(sensor.id), record->id,
			       sizeof(record->id));
		pmcp_copy_text(sensor.name, sizeof(sensor.name), record->name,
			       sizeof(record->name));
		pmcp_copy_text(sensor.source, sizeof(sensor.source), record->source,
			       sizeof(record->source));
		pmcp_copy_text(sensor.units, sizeof(sensor.units), record->units,
			       sizeof(record->units));
		pmcp_copy_text(sensor.health, sizeof(sensor.health), record->health,
			       sizeof(record->health));
		pmcp_copy_text(sensor.state, sizeof(sensor.state), record->state,
			       sizeof(record->state));

		ret = pdi_bmc_sensor_accumulator_add(&acc, &sensor);
		if (ret < 0)
			goto out;
	}

	ret = pdi_bmc_sensor_accumulator_finish(&acc);

out:
	free(payload);
	return ret;
}

static int pmcp_open(const struct pdi_bmc_open_params *params,
		     void **backend_ctx)
{
	struct pdi_bmc_pmcp_hello_request request;
	struct pdi_bmc_pmcp_ctx *ctx;
	uint8_t *payload = NULL;
	size_t payload_len = 0;
	int fd;
	int ret;

	if (!params || !params->endpoint || !params->endpoint[0] || !backend_ctx)
		return -EINVAL;

	ctx = calloc(1, sizeof(*ctx));
	if (!ctx)
		return -ENOMEM;
	ctx->fd = -1;
	ctx->timeout_ms = params->timeout_ms;
	ctx->frame_payload_max = PDI_BMC_PMCP_FRAME_PAYLOAD_MAX;
	ctx->message_max = PDI_BMC_PMCP_MESSAGE_MAX;

	fd = pmcp_connect_endpoint(params->endpoint, pmcp_timeout_ms(ctx));
	if (fd < 0) {
		ret = fd;
		goto err_free;
	}
	ctx->fd = fd;

	memset(&request, 0, sizeof(request));
	ret = pdi_bmc_copy_string(request.username, sizeof(request.username),
				  params->username);
	if (ret < 0)
		goto err_close;
	ret = pdi_bmc_copy_string(request.password, sizeof(request.password),
				  params->password);
	if (ret < 0)
		goto err_close;

	ret = pmcp_transaction(ctx, PDI_BMC_PMCP_TYPE_HELLO, &request,
			       sizeof(request), &payload, &payload_len);
	if (ret < 0)
		goto err_close;
	ret = pmcp_decode_hello(ctx, payload, payload_len);
	if (ret < 0)
		goto err_close;

	free(payload);
	*backend_ctx = ctx;
	return 0;

err_close:
	free(payload);
	if (ctx->fd >= 0)
		close(ctx->fd);
err_free:
	free(ctx);
	return ret;
}

static void pmcp_close(void *backend_ctx)
{
	struct pdi_bmc_pmcp_ctx *ctx = backend_ctx;

	if (!ctx)
		return;
	if (ctx->fd >= 0)
		close(ctx->fd);
	free(ctx);
}

static int32_t pmcp_request(void *backend_ctx,
			    const struct pdi_bmc_backend_request *request)
{
	struct pdi_bmc_pmcp_ctx *ctx = backend_ctx;

	if (!ctx || !request)
		return -EINVAL;

	switch (request->type) {
	case PDI_BMC_BACKEND_REQ_GET_INFO:
		return pmcp_get_info(ctx, request->args.info);
	case PDI_BMC_BACKEND_REQ_GET_POWER_STATE:
		return pmcp_get_power_state(ctx, request->args.state);
	case PDI_BMC_BACKEND_REQ_POWER_CONTROL:
		return pmcp_power_control(ctx, request->args.action);
	case PDI_BMC_BACKEND_REQ_GET_SENSORS:
		return pmcp_get_sensors(ctx, request->args.sensors.filter,
					request->args.sensors.sensors,
					request->args.sensors.count);
	default:
		return -EINVAL;
	}
}

const struct pdi_bmc_backend_ops pdi_bmc_pmcp_ops = {
	.name = "pmcp",
	.protocol = PDI_BMC_PROTOCOL_PMCP,
	.open = pmcp_open,
	.close = pmcp_close,
	.request = pmcp_request,
};
