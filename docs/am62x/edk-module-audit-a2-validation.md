# A2 AM625 实板验收：PDI 私有契约与 hwmon

2026-11-25；23:32:59–23:33:03、23:33:36–23:33:37+08:00。
[EDK A2 开发记录](../../edk/docs/edk-module-audit-a2-validation.md)。
证据 `output/edk-module-audit-a2-20261125-2330/`。

设备 MAC 1c:63:49:22:c4:f7、HWID 1010001000110000，A 槽、boot
`542e6381-e300-41b7-ae2b-41dddbbd0583`，正式版本 0.0.1/full ID
`683e05eaa30726d7d54eced37f55f0c446f3ddcb7b366d75a9fcca935fa9bfed`。
正式 configuration PDI_HWMON=n，变更仅测试、文档及关闭的 SDK 注释，
沿用上一成功发布，无正式 OTA 内容变化。
`board-formal-v6.sh`、fwctl version/ota-status/ota-check/health-check；
八制品与实际包匹配，旧 SDK PDM 被动枚举两设备，六源 sequence=172、last_status=0、failures=0。

`board-hwmon-v6.sh`：原交叉工具链独立 hwmon-on SDK，tmpfs 文件夹具，
不是物理传感器；核对真实 loader 和候选 libpdi SHA256
`faf2331da87cb160c064f16a95863d265745cc6d0d88e27e333022c44cea914f`，
libbsl `3b257199b65fe0989ace91ada808085de5d8c6b3522d4cd1970f2f7f6dbef584`，
探针 `0a2306ce5f344a08e31e88a4429c269d9fd79c66d44bac86093f66e7050785db`。
实际断言负温 -12000、普通垃圾 -EINVAL、溢出或溢出带垃圾 -ERANGE、
31 字节过长 -EINVAL、缺失 -ENOENT、目录 -EINVAL，所有失败哨兵不变。
主机校验 31 字节，板上精确校验全部文件摘要（首轮缺 wc，重验成功）。
使用后清理临时目录，正式八制品与健康再次复核。
关闭 SDK 的专头/符号在独立交叉前缀明确裁剪。
没有对其他真实服务器做任何写入/控制。

EDK 主机回归 259/259，定向 4/4，各对象/拒绝反例通过。
EDK master 先推，再核对工作区 gitlink/master，详见证据目录 git-verification.log。

EDK 子仓远端已验证：`06226c3ec6df6d536f4b15d797726c2be4848cca`。
