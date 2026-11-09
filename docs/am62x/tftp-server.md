# Development TFTP server

The development host serves AM625 firmware at
`tftp://192.168.10.246/release.itb` on the 192.168.10.0/24 development LAN.
The host address is on `eno1`; the board network preset uses 192.168.10.211.

The Debian host packages are `tftpd-hpa` and `tftp-hpa`. The
`tftpd-hpa.service` unit is enabled for boot and the publish directory is
`/srv/tftp/am625`. This directory is owned by the development user so firmware
can be refreshed without sudo. The daemon runs as `tftp` and published files
are mode 0644. Upload/create mode is not enabled.

The host's `/etc/default/tftpd-hpa` contains:

```sh
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="/srv/tftp/am625"
TFTP_ADDRESS="192.168.10.246:69"
TFTP_OPTIONS="--secure --verbose --blocksize 1468 --port-range 40000:40032"
```

Debian 13's packaged unit has `ProtectHome=yes`. A firmware directory under
`/home/guohao/` is therefore inaccessible to this service even if the daemon
starts as root. Keep the publish directory under `/srv`; changing home-directory
permissions does not fix that service namespace restriction.

## Publish a new build

The server publishes a copy, so refresh it after rebuilding firmware. From
the SadBoard workspace root, copy component images first and the manifest last:

```sh
firmware_dir="$PWD/output/am625-debug-systemd/images/release"
install -m 0644 "$firmware_dir/kernel.itb" \
    "$firmware_dir/rootfs.itb" /srv/tftp/am625/
install -m 0644 "$firmware_dir/release.itb" /srv/tftp/am625/
```

No service restart is needed after publishing. Complete publication before
starting an update so the manifest and component files are from the same build.
If using the default in-tree Buildroot output, set `firmware_dir` to
`$PWD/buildroot/output/images/release` instead. The current release manifest
contains kernel and rootfs; copying a bootloader package is not part of this flow.

## Board update

Use the explicit URL to override any different update-server setting already
present in `/etc/device-manager/firmware.conf`:

```sh
fwctl update all tftp://192.168.10.246/release.itb
```

The release manifest selects kernel and rootfs; remote bootloader updates stay
disabled by the product configuration. `fwctl` validates component hashes and
writes the inactive deployment. It does not reboot automatically. The host
setup does not execute any board update.

## Service checks

```sh
systemctl status tftpd-hpa --no-pager
systemctl is-enabled tftpd-hpa
ss -lun 'sport = :69'
sudo journalctl -u tftpd-hpa -n 50 --no-pager
```

The server binds UDP 69 on 192.168.10.246 and uses UDP 40000-40032 for transfer
sessions. If adding a host firewall, permit those ports for the development
network. Do not disable the firewall globally.

Initial setup was verified by downloading `release.itb`, `kernel.itb` and
`rootfs.itb` using the host's TFTP client over 192.168.10.246 and comparing all
three files byte-for-byte with the Buildroot output. Board-to-host reachability
and the actual board upgrade remain target-side checks.
