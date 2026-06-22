# workspace

嵌入式 Linux BSP 开发工作区聚合仓库。这个仓库使用 Git 子模块统一管理 Buildroot、Buildroot 外部层、Linux、U-Boot、LPF 和板级文档。

## 子模块常用命令

### 按平台初始化工作区

使用 `scripts/setup-platform.sh` 只初始化或更新目标平台需要的子模块：

```bash
./scripts/setup-platform.sh imx6ull
```

`imx6ull` 会更新 `buildroot`、`br2-external`、`lpf`、`linux/linux-7.0` 和 `uboot/uboot-2024.10`，不会拉取 `linux/ti-linux-kernel-6.18.13` 或 `uboot/ti-u-boot-2025.10`。

如需更新到 `.gitmodules` 中配置的远端 `master` 最新提交：

```bash
./scripts/setup-platform.sh --remote imx6ull
```

查看支持的平台和子模块映射：

```bash
./scripts/setup-platform.sh --list
```

### 克隆与初始化

```bash
git clone git@github.com:linux-bsp/workspace.git
cd workspace
git submodule update --init --recursive
```

如果网络较慢，可以单独初始化较大的子模块，并使用浅克隆和部分克隆减少下载量：

```bash
git submodule update --init --depth 1 --filter=blob:none -- linux/linux-7.0
git submodule update --init --depth 1 --filter=blob:none -- linux/ti-linux-kernel-6.18.13
git submodule update --init --depth 1 --filter=blob:none -- uboot/uboot-2024.10
git submodule update --init --depth 1 --filter=blob:none -- uboot/ti-u-boot-2025.10
```

### 查看状态

```bash
git submodule status
git status --short
```

`git submodule status` 输出中，路径前面的符号含义：

- `-` 子模块还没有初始化
- `+` 子模块工作区提交和主仓库记录的提交不一致
- `U` 子模块存在冲突

### 更新到主仓库记录的提交

```bash
git submodule update --init --recursive
```

只更新某一个子模块：

```bash
git submodule update --init -- linux/linux-7.0
```

### 跟踪 master 分支

本仓库的子模块配置为跟踪各自远端的 `master` 分支。配置命令如下：

```bash
git submodule set-branch --branch master -- buildroot
git submodule set-branch --branch master -- br2-external
git submodule set-branch --branch master -- linux/linux-7.0
git submodule set-branch --branch master -- linux/ti-linux-kernel-6.18.13
git submodule set-branch --branch master -- uboot/uboot-2024.10
git submodule set-branch --branch master -- uboot/ti-u-boot-2025.10
git submodule set-branch --branch master -- lpf
```

这些命令会在 `.gitmodules` 中写入 `branch = master`。注意：主仓库仍然记录每个子模块的具体提交；`branch = master` 只决定 `git submodule update --remote` 从哪个远端分支取最新提交。

### 拉取子模块远端最新提交

将所有子模块更新到各自远端 `master` 分支的最新提交：

```bash
git submodule update --init --remote --recursive
```

只更新某一个子模块到远端 `master` 最新提交：

```bash
git submodule update --init --remote -- linux/linux-7.0
```

更新后需要在主仓库提交新的子模块指针：

```bash
git status
git add .gitmodules buildroot br2-external linux/linux-7.0 linux/ti-linux-kernel-6.18.13 uboot/uboot-2024.10 uboot/ti-u-boot-2025.10 lpf
git commit -m "chore: update submodules"
```

### 同步 URL 配置

如果修改了 `.gitmodules` 或远端地址，先同步本地 Git 配置：

```bash
git submodule sync --recursive
git submodule update --init --recursive
```

只同步某一个子模块：

```bash
git submodule sync -- linux/linux-7.0
git submodule update --init -- linux/linux-7.0
```

### 添加子模块

```bash
git submodule add git@github.com:linux-bsp/example.git example
git add .gitmodules example
git commit -m "chore: add example submodule"
```

添加较大的仓库时可以使用浅克隆：

```bash
git submodule add --depth 1 git@github.com:linux-bsp/example.git example
```

### 删除子模块

```bash
git submodule deinit -f -- example
git rm -f -- example
rm -rf .git/modules/example
git commit -m "chore: remove example submodule"
```

### 进入子模块操作

子模块本身也是 Git 仓库，可以进入目录后正常执行 Git 命令：

```bash
cd linux/linux-7.0
git status
git branch
git log --oneline -5
cd ..
```

也可以在主仓库批量执行命令：

```bash
git submodule foreach 'git status --short'
git submodule foreach 'git log --oneline -1'
```

### 中断或下载失败后重试

如果中断导致子模块留下半截目录，先清理对应路径后重试：

```bash
rm -rf linux/linux-7.0 .git/modules/linux-7.0
git submodule update --init --depth 1 --filter=blob:none -- linux/linux-7.0
```

如果子模块名称和路径都带有目录层级，例如 `linux/ti-linux-kernel-6.18.13`，`.git/modules` 下的清理路径也需要保留同样的层级：

```bash
rm -rf linux/ti-linux-kernel-6.18.13 .git/modules/linux/ti-linux-kernel-6.18.13
git submodule update --init --depth 1 --filter=blob:none -- linux/ti-linux-kernel-6.18.13
```

如果只是工作区缺失，但 `.gitmodules` 和索引中已经有记录，直接重新初始化：

```bash
git submodule update --init -- linux/linux-7.0
```

## 目录说明

- `buildroot/` Buildroot 源码树
- `br2-external/` 面向板级集成的 Buildroot 外部层
- `linux/` Linux 内核源码树目录，按版本放置，例如 `linux/linux-7.0/` 和 `linux/ti-linux-kernel-6.18.13/`
- `uboot/` U-Boot 源码树目录，按版本放置，例如 `uboot/uboot-2024.10/` 和 `uboot/ti-u-boot-2025.10/`
- `lpf/` 项目自定义代码
- `docs/<board>/` 按板卡归档参考手册、数据手册、原理图和相关 PDF，例如 `docs/imx6ull/`
