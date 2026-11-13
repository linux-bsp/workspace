# Repository Guidelines

## Project Scope and Current State

SadBoard is an advanced embedded Linux debugging course for engineers with about three years of BSP experience. Develop this workspace on `SadBoard`; use real AM625 hardware for validation; do not substitute QEMU. The baseline uses systemd, SSH, independent U-Boot `tftp_kernel`/`nfs_root` switches, TFTP/NFS debugging and local SD A/B firmware.

The six curriculum batches are complete: 106 independent cases (35 basic, 24 advanced, 8 A64 and 39 kernel cases), with 104 target commands and two host UART boot-fault controllers. The Obsidian handbook has 251 notes; 14 kernel chapters arrange 101 studies reusing 82 cases. Five engineering review routes reuse canonical cases without adding scenario IDs. Random fault orchestration and general automatic grading remain outside the implementation. Read `docs/advanced-course-completion.md` for completed scope and hardware boundaries; keep dated evidence in `docs/am625-debug-validation.md`. Read the latest dated validation for published build IDs; historical batch IDs remain tied to their recorded evidence.

## Project Structure and Module Organization

- `obsidian-sadboard/`: independent Chinese handbook submodule on `master`. Its only root note is `README.md`. Chapters 01–06 cover hardware, OS, compilation/build systems, assembly, kernel subsystems, and system debugging/optimization. Indexes and preparation live under `06-系统调试与优化/00-实验准备与通用方法/`; unit `11-综合工程复盘/` contains the five review routes.
- `sadboard-external/`: laboratory code, AM625 debug configuration, kernel fragments, native build hooks and deployment helpers; submodule branch `main`, external identifier `SADBOARD`.
- `bsp-base-external/`: shared board support and general netboot functionality; preserve external identifier `LINUX_BSP`.
- `edk/`: integrated management software on `master`. Firmware CLI, OTA daemon and initramfs entry belong to `user/apps/fwctl/`; logging/SOL to `user/apps/logctl/`; time to `user/apps/timectl/`; host `dmserver`/`dmcli` to `user/apps/device-manager/`. Shared OSA, HWID, transfer and protocol libraries live under `user/lib/`. Read `edk/AGENTS.md` before editing it; management architecture belongs in `edk/docs/`.
- `buildroot/`, `linux/`, `uboot/`, `libbmc/`: existing source submodules; libbmc remains separate from EDK.
- `README.md`: project entry and documentation index; keep new guide links reachable.
- `docs/`: workspace instructions and board references, including `workspace-toolchain.md` and the validation archive. i.MX6ULL references do not establish a supported SadBoard profile. Generated builds and raw evidence belong in ignored `output/`.

## Build, Test, and Development Commands

For a fresh checkout, initialize submodules and use native Buildroot:

```sh
git submodule update --init --recursive
cd buildroot
BR2_EXTERNAL="../bsp-base-external ../sadboard-external" make sadboard_am625_debug_defconfig
make all
```

Without `O=`, output goes to `buildroot/output/`. The existing validated tree is workspace `output/am625-debug-systemd/`. Run incremental commands from the workspace root:

```sh
make -C output/am625-debug-systemd sadboard-labs-rebuild
make -C output/am625-debug-systemd all
bash sadboard-external/scripts/verify-debug.sh output/am625-debug-systemd/images
```

For EDK changes, use its native Buildroot configure/build path:

```sh
make -C output/am625-debug-systemd edk-reconfigure BR2_PACKAGE_EDK_DEFCONFIG=ti_am62x_defconfig BR2_PACKAGE_EDK_WEB=y
```

Use separate output trees for toolchain changes. Maintain portable defconfigs through native menuconfig/savedefconfig. Shared `../dl/` is a download cache; `../toolchain/` holds manually extracted SDKs, not a shared `BR2_HOST_DIR`. Existing output trees contain absolute paths and require reconfiguration after relocation.

Run relevant laboratory regressions with `python3 sadboard-external/tests/test-labs.py`; storage-policy changes also require `sadboard-external/tests/test-results.py`, and deployment changes have `sadboard-external/tests/test-sync-artifacts.py`. EDK owns its native CMake/CTest harness; firmware CLI/engine regressions also have `edk/user/apps/fwctl/tests/test_firmware.py`. Supply native dependency include/library paths when needed; Buildroot `host/include` and `host/lib` are distinct from the AArch64 target sysroot. Keep native test binaries in temporary build directories.

Production builds, device software and Device Manager use native C, shell and Buildroot/CMake. Python is limited to host tests, documentation maintenance and serial validation controllers. Upstream host dependencies such as U-Boot binman remain managed by Buildroot. Documentation-only changes require relevant file/link and diff checks, without a firmware rebuild or board reboot.

## Handbook Organization and Writing

Write teaching material in Chinese for the experienced BSP audience. Explain phenomena, object/state models, hardware/OS prerequisites, conditional source paths, competing hypotheses, evidence, repair and regression. Distinguish source-derived paths from captured stacks and measured results from proposed exercises.

- Keep one complete canonical note per case: `<ID>-<specific-problem>/<ID>：<actual-title>.md`. Preserve IDs and commands. Each navigation note uses its directory's exact basename, such as `01-应用崩溃/01-应用崩溃.md`.
- Obsidian uses the filename as the title. Omit YAML properties and body H1 headings; number sections locally as `## 1.`, `### 1.1`, `#### 1.1.1`. Update heading links together with renames.
- Shared tool parameters live in `附录C-工具手册/<tool>.md`; link cases to tools and tools back to concrete cases. Appendix A covers practice/builds, B Bootlin and C tools. Preserve Bootlin attribution and CC BY-SA 3.0 notices.
- Give each independent command its own fenced block with purpose and execution context. Related `setenv`/GDB settings may share a block. Preserve existing commands, captured evidence, continuations and pipelines during reorganization.
- Maintain the vault directly. Preserve personal `.obsidian/` settings and ignored experiment reports; keep ABI knowledge with OS foundations and compilation/Buildroot/Yocto with chapter 03. Mark host exercises separately from cross-compilation and AM625 execution.
- Kernel reading links follow repository `master`; actual addresses/disassembly require the recorded firmware's matching source and symbols. Keep hardware calculations and physical measurements distinct; electrical claims need primary specifications. A53 observations do not establish AMP/RPMsg, CPU-hotplug or other-storage validation.

Each kernel chapter has a framework/principles note and 5–10 progressive studies covering source paths, evidence, diagnosis and repair. Assembly stays under chapter 04, grouped by architecture and AM625 experiments; reading other architectures is separate from board validation.

Check handbook changes from the workspace root:

```sh
python3 obsidian-sadboard/scripts/check-obsidian.py --workspace .
```

A standalone vault can run `python3 scripts/check-obsidian.py`. The checker covers headings, links, case coverage, navigation, tool backlinks and available workspace source paths.

## Coding and Laboratory Contracts

Follow each source module's style; otherwise use four-space indentation. No workspace-wide formatter is configured. Keep shared mechanisms separate from scenario policy. Buildroot must recompile local laboratory binaries with `TARGET_CC` regardless of synchronized file timestamps; verify AArch64 ELF properties, debug sections and source manifests. Preserve BusyBox and Linux configurations; check required tool options as well as binary availability.

Kernel experiments now implement real driver-core, workqueue/waitqueue/kref/kthread, spin/mutex/lockdep, RCU/SRCU, generic IRQ and runtime PM mechanisms. `study.h` shares bounded event/status transport; concrete mechanisms remain in their owning modules. Software IRQ descriptors, resource-free platform devices and private RAM/loop/DM backends establish their stated software contracts, while physical IRQ routing, power rails, real power-loss/FTL behavior and long-duration stress require separate evidence.

- Preserve the inherited laboratory flock, owned-resource markers, bounded waits and private trace instances. Do not alter global tracing or take over an already loaded module. Verify outcome, raw event order, callback trace, zero trace loss and cleanup together. Reset only resources belonging to that run.
- Keep the short hardirq event recorder protected by `raw_spinlock`; blocking work stays outside it. Require live `debug_locks=1` before/after studies and the documented `panic_on_warn=0` prerequisite. An invalid wait context or disabled detector invalidates evidence; correct the cause rather than bypassing checks.
- Lock-debug configuration changes affect internal module ABI. Rebuild all out-of-tree modules, including EDK/PDM, with the matching kernel; identical `uname -r` is insufficient.
- Reference/lifetime faults quarantine actual memory until readers/callbacks finish. Storage faults use only owned tmpfs, loop and DM devices; restore mappings and reclaim mounts/loops, including cancellation paths. Runtime PM snapshots and final reference/policy cleanup are separate observations; `suspended` alone is not a physical power measurement.
- Preserve work counts and checksums when comparing repairs. Separate on-CPU samples, waiting, queueing and completion. Use documented `perf report/script --no-inline` paths on the minimal target; folded dynamic periods are weights, not sample-record counts. Label flamegraph weights correctly.

## Hardware Validation and Evidence

Use `sadboard list B-CR` to filter a unit, `run` to reproduce and `verify` to exercise the reference repair. `evaluate crash /absolute/candidate` checks the ten-input B-CR01 learner contract only. Manage evidence with `status/check/reset`; interrupted or incomplete runs cannot pass as complete experiments. No scenario starts automatically at boot.

Use `sadboard results`: NFS roots default to `/srv/sadboard` (host `/srv/nfs/sadboard-am625/srv/sadboard`), local roots to `/data/sadboard`. Check free space; preserve SD evidence during NFS synchronization. Completed NFS runs and `sadboard share` provide host read access without following symlinks. Device logs, OTA state and boot confirmation stay on persistent data storage; never format it automatically.

All board validation uses AM625 hardware, with WDT active. Network faults belong to owned namespaces. Keep management eth0, IRQ/RPS, CPU online state and remote firmware intact. Before opening UART, check its current owner; preserve a user's tio session and use SSH for independent work. USB/IP/tio instructions live in the preparation chapter. Prior serial access does not authorize killing a new owner.

Panic/Oops/lockup exercises require a confirmed matching firmware, an extra reboot and an unsealed startup. Pause confirmation with SIGSTOP/SIGCONT; stopping its service invokes OnFailure. Before all-CPU lockup, prove actual hardware reset with `sadboard-external/scripts/sadboard-board.py watchdog-probe` for the running content ID. RAM boot faults never save bad bootargs or write firmware partitions; the USB UART cannot forward BREAK, so retain the independent timed rescue child.

Verify failed and healthy SPL/U-Boot/kernel logs, reset evidence, recovery health and server receipts. Early startup archive IDs and Linux `boot_id` are separate namespaces; correlate recovery boot, buffer/generation and timestamps. Retain raw logs, lengths, CRC/loss fields and pstore exports. Report build, staged-binary, installed-image and physical validation separately. Human timestamps use UTC+8; monotonic CSV timestamps and reproducible build timestamps have different meanings.

## Firmware Release and Commit Workflow

Keep firmware at `0.0.1` from `edk/VERSION` unless the user explicitly requests a version change. Distinguish builds with full content IDs; display eight hex characters in human logs, retaining full hashes for comparison, machine interfaces and audit. `fwctl status` reports stored A/B deployment IDs even in netboot; its `hash` is the kernel/rootfs release ID, not a bootloader or individual-partition checksum. See `edk/docs/device-manager/fwctl.md`.

For device software changes:

1. Build the complete native image; preserve matching sources, configurations, vmlinux, modules and symbols under `images/debug/` and the ignored validation archive.
2. Publish the new v0.0.1 content ID and validate kernel/rootfs OTA in local A/B mode. Check the actually booted full ID and `/run/fwctl-boot-confirmed`; an inactive slot containing the new ID is insufficient.
3. Wait for fwctld's real success report and server confirmation before restoring netboot. Local `mark-good` can precede the reporting poll; network mode disables production OTA/slot confirmation.
4. While running local root, synchronize matched netboot/rootfs artifacts using `sadboard-external/scripts/sync-artifacts.sh`. Restore the saved network switches, reboot and verify NFS readiness, executable/module hashes, WDT, services and SOL/archive completion.
5. Commit and immediately push changed submodules before committing/pushing workspace pointers. Pure documentation follows its checks and uses existing validation evidence.

A `BSPNET1` ID identifies a reference build, not the integrity of a subsequently mutable NFS tree. Parse `FWOTA2`/`BSPNET1` by their contracts; do not substitute saved SD metadata for a running network image. Never flash factory images, alter the partition layout or bypass production bootloader-update restrictions for an exercise. Report separately whether U-Boot was built, its environment tested, or its binary installed. Keep source/configuration and experimental images matched throughout validation.

Use focused `docs:`, `chore:`, `feat:` or `fix:` commits. Preserve unrelated work, review untracked files, and run `git diff --check`, `git diff --cached --check` and `git status --short`. PRs describe behavior, configuration, validation and limits. Verify actual branches with Git; ancestor tags from `git describe` do not define the branch or firmware version. Existing submodule licenses apply; the laboratory project's code license remains undecided.
