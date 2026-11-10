[[首页]] · [[工具索引]] · [[案例索引]]

## 解决的问题

核对 ELF 架构、装载段、调试节、解释器和动态依赖。

## 工作原理与准备

它直接读取 ELF 结构，不需要在主机执行目标程序。程序段影响装载，节表用于链接/分析；解释器与 DT_NEEDED 是完整依赖链的起点。

## 参数与结果解释

| 参数/字段 | 含义与判断方法 |
| --- | --- |
| `-h` | ELF 头：机器架构、类别、字节序、类型。 |
| `-l` | 程序头与解释器，核对 PT_LOAD。 |
| `-S` | 节表，确认 .debug_info 等。 |
| `-d` | 动态表与 NEEDED/RUNPATH 等。 |
| `-W` | 宽格式输出，减少换行。 |

## 操作步骤

主机端：核对本次实际调试 ELF 的架构和装载信息。

```sh
output/am625-debug-systemd/host/bin/aarch64-buildroot-linux-gnu-readelf -h -l -W output/am625-debug-systemd/images/debug/labs/crash-bug
```

主机端：核对调试节是否保留。

```sh
output/am625-debug-systemd/host/bin/aarch64-buildroot-linux-gnu-readelf -S -W output/am625-debug-systemd/images/debug/labs/crash-bug
```

主机端：检查程序的动态依赖，不通过执行 ELF 来猜测。

```sh
output/am625-debug-systemd/host/bin/aarch64-buildroot-linux-gnu-readelf -d -W output/am625-debug-systemd/images/debug/labs/crash-bug
```

## 判断边界

能列出 NEEDED 不代表 initramfs 已复制传递依赖与 lib64 别名。分析缺库时同时检查解释器、符号链接和库的实际位置。

## 使用场景

下面链接直达具体案例的定位章节。基础流程沿用实机验收，扩展工具观测不自动记作已执行。

| 案例 | 本工具的观测目标 |
| --- | --- |
| [[01-应用崩溃/B-CR01-缺失记录未判空导致空指针崩溃/B-CR01：缺失记录导致应用崩溃#定位方法\|B-CR01：缺失记录导致应用崩溃]] | 核对 ELF、解释器、调试节和动态依赖 |
| [[02-文件描述符/B-FD01-循环打开文件未关闭导致FD耗尽/B-FD01：文件描述符泄漏与耗尽#定位方法\|B-FD01：文件描述符泄漏与耗尽]] | 核对 ELF、解释器、调试节和动态依赖 |
| [[04-CPU性能与火焰图/B-CPU01-重复线性查找导致CPU热点/B-CPU01：CPU热点与火焰图#定位方法\|B-CPU01：CPU热点与火焰图]] | 核对 ELF、解释器、调试节和动态依赖 |
| [[07-内核启动与恢复/B-BOOT02-initramfs动态加载器缺库导致PID1退出/B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出#定位方法\|B-BOOT02：initramfs 动态加载器缺库导致 PID 1 退出]] | 核对 ELF、解释器、调试节和动态依赖 |
| [[07-内核启动与恢复/B-BOOT03-根设备或文件系统参数错误导致VFS启动失败/B-BOOT03：根设备或文件系统参数错误导致 VFS 启动失败#定位方法\|B-BOOT03：根设备或文件系统参数错误导致 VFS 启动失败]] | 核对 ELF、解释器、调试节和动态依赖 |
