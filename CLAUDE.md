# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an embedded Linux BSP (Board Support Package) development workspace that aggregates multiple Git submodules for building complete embedded Linux systems. The workspace uses Buildroot as the primary build system and manages Linux kernel, U-Boot, and custom LPF (Linux Peripheral Framework) code.

## Submodule Architecture

The repository uses Git submodules organized by function:

- `buildroot/` - Buildroot source tree (the build orchestrator)
- `br2-external/` - Board-specific Buildroot external layer with defconfigs, overlays, and package integration
- `linux/linux-7.0/` - Linux kernel 7.0 for NXP i.MX6ULL
- `linux/ti-linux-kernel-6.18.13/` - TI-specific Linux kernel for TI platforms
- `uboot/uboot-2024.10/` - U-Boot 2024.10 for NXP i.MX6ULL
- `uboot/ti-u-boot-2025.10/` - U-Boot 2025.10 for TI platforms
- `lpf/` - Linux Peripheral Framework (custom peripheral driver framework)
- `docs/` - Board documentation (datasheets, schematics, reference manuals)
- `dl/` - Buildroot download cache (not tracked in git)

Each submodule is configured to track its remote `master` branch. The workspace records specific commits, but can update to latest remote commits using `--remote` flags.

## Platform-Specific Setup

Use `scripts/setup-platform.sh` to initialize only the submodules needed for a target platform:

```bash
# Initialize i.MX6ULL workspace (common + linux-7.0 + uboot-2024.10)
./scripts/setup-platform.sh imx6ull

# Initialize TI platform workspace (common + ti-linux-kernel + ti-u-boot)
./scripts/setup-platform.sh ti

# Update to latest remote commits instead of recorded commits
./scripts/setup-platform.sh --remote imx6ull

# Use shallow clone for large submodules to reduce download size
./scripts/setup-platform.sh --depth 1 imx6ull

# List supported platforms
./scripts/setup-platform.sh --list
```

## Build Commands

### Building for NXP i.MX6ULL EVK

```bash
cd buildroot
make BR2_EXTERNAL=../br2-external imx6ullevk_defconfig
make
```

The output images (kernel, u-boot, rootfs) will be in `buildroot/output/images/`.

For the debug/study variant with additional tools:

```bash
cd buildroot
make BR2_EXTERNAL=../br2-external imx6ullevk_debug_study_defconfig
make
```

### Buildroot Configuration

```bash
cd buildroot
make menuconfig          # Modify full Buildroot configuration
make linux-menuconfig    # Modify Linux kernel configuration
make uboot-menuconfig    # Modify U-Boot configuration
make savedefconfig       # Save minimal defconfig (must manually copy to br2-external/configs/)
```

After modifying configurations, save the defconfig back to `br2-external/configs/` manually:

```bash
# From buildroot directory
make savedefconfig
cp defconfig ../br2-external/configs/imx6ullevk_defconfig
```

### Rebuilding Specific Components

```bash
cd buildroot
make linux-rebuild       # Rebuild Linux kernel
make uboot-rebuild       # Rebuild U-Boot
make lpf-rebuild         # Rebuild LPF package
make clean               # Clean everything
```

### LPF Development

The LPF (Linux Peripheral Framework) submodule has its own build system combining Kconfig, CMake, and Linux Kbuild:

```bash
cd lpf
make list                                    # List available defconfigs
make ubuntu_x86_modules_defconfig            # Configure for x86 development
make all                                     # Build userspace libs and kernel modules
make modules                                 # Build only kernel modules
make tests                                   # Build and run tests
```

LPF modules must be loaded in order: `osal.ko`, `lpf_configs.ko`, then `lpf_core.ko`.

## Submodule Operations

### Update submodules to recorded commits

```bash
git submodule update --init --recursive                    # All submodules
git submodule update --init -- linux/linux-7.0             # Specific submodule
```

### Update submodules to latest remote commits

```bash
git submodule update --init --remote --recursive           # All submodules
git submodule update --init --remote -- linux/linux-7.0    # Specific submodule

# After updating, commit the new submodule pointers
git add linux/linux-7.0
git commit -m "chore: update linux-7.0 submodule"
```

### Check submodule status

```bash
git submodule status        # Check all submodule states
git status --short          # Check workspace dirty state
```

In `git submodule status` output:
- `-` prefix: submodule not initialized
- `+` prefix: submodule commit differs from recorded commit
- `U` prefix: submodule has conflicts

### Working inside submodules

Submodules are full Git repositories. Enter them and use normal Git commands:

```bash
cd linux/linux-7.0
git status
git log --oneline -10
git checkout -b my-feature
# Make changes, commit, push
cd ../..

# Update workspace to track the new commit
git add linux/linux-7.0
git commit -m "chore: update linux-7.0 to include my-feature"
```

## Key Integration Points

### br2-external Structure

The `br2-external` layer follows Buildroot external tree conventions:

- `configs/` - Board defconfigs (e.g., `imx6ullevk_defconfig`)
- `board/<vendor>/<board>/` - Board-specific files, overlays, post-image scripts
- `package/lpf/` - LPF package integration for Buildroot
- `external.mk` - External tree makefile
- `external.desc` - External tree metadata

### Local Source Overrides

The Buildroot defconfigs use local source overrides pointing to workspace submodules instead of downloading tarballs:

- Linux: `BR2_LINUX_KERNEL_CUSTOM_LOCAL=y` → `../linux/linux-7.0`
- U-Boot: `BR2_TARGET_UBOOT_CUSTOM_LOCAL=y` → `../uboot/uboot-2024.10`
- LPF: `BR2_PACKAGE_LPF_OVERRIDE_SRCDIR=../lpf`

This allows rapid iteration: changes in submodules are picked up on the next `make` without re-downloading.

## Common Workflows

### Starting fresh on a new platform

```bash
git clone git@github.com:linux-bsp/workspace.git
cd workspace
./scripts/setup-platform.sh imx6ull
cd buildroot
make BR2_EXTERNAL=../br2-external imx6ullevk_defconfig
make -j$(nproc)
```

### Developing a Linux kernel change

```bash
cd linux/linux-7.0
git checkout -b fix-gpio-driver
# Edit kernel code
cd ../../buildroot
make linux-rebuild        # Test the change
# If successful, commit in the submodule
cd ../linux/linux-7.0
git add .
git commit -m "fix: correct GPIO initialization"
git push origin fix-gpio-driver
```

### Adding support for a new board

1. Add board defconfig to `br2-external/configs/`
2. Create board directory under `br2-external/board/<vendor>/<board>/`
3. Add necessary overlays, post-image scripts, kernel fragments
4. If using different kernel/u-boot versions, add new submodules under `linux/` or `uboot/`
5. Update `scripts/setup-platform.sh` to recognize the new platform
6. Document board-specific build and boot steps in the board directory

## Build Output

After a successful Buildroot build, find images in:

```
buildroot/output/images/
├── imx6ull-evk.dtb        # Device tree blob
├── rootfs.tar             # Root filesystem archive
├── sdcard.img             # Complete SD card image
├── u-boot.imx             # U-Boot with i.MX header
└── zImage                 # Linux kernel image
```

Flash `sdcard.img` to an SD card or use individual images for network boot or other deployment methods.

## Important Notes

- Never commit changes directly inside `buildroot/output/` - these are build artifacts
- Submodule commits must be tracked: after updating a submodule, commit the pointer in the workspace repository
- The `dl/` directory caches downloads and can grow large - it's excluded from git
- Buildroot builds are out-of-tree by default; clean by removing `buildroot/output/`
- LPF uses separate build directories under `lpf/_build/` for libraries and modules
