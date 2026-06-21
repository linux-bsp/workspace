# imx6ull

IMX6ULL 开发工作区聚合仓库。这个仓库使用 Git 子模块统一管理板级文档和主要源码树。

## 克隆与初始化

```bash
git clone git@github.com:wanguo99/imx6ull.git
cd imx6ull
git submodule update --init --recursive
```

## 更新子模块

如果修改了 `.gitmodules`，请先同步子模块 URL 配置：

```bash
git submodule sync --recursive
```

将所有子模块更新到主仓库当前记录的提交：

```bash
git submodule update --init --recursive
```

将所有子模块更新到各自跟踪远端分支的最新提交：

```bash
git submodule update --init --remote --recursive
```

如果执行了远端更新，请在仓库根目录检查并提交新的子模块指针：

```bash
git status
git add .
git commit -m "chore: update submodules"
```

## 目录说明

- `buildroot/` Buildroot 源码树
- `buildroot-external-tree/` 面向板级集成的 Buildroot 外部层
- `linux-6.12/` Linux 内核源码树
- `u-boot-v2024.10/` U-Boot 源码树
- `lpf/` 项目自定义代码
- `docs/` 板卡参考手册、数据手册和原理图 PDF
