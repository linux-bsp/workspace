#!/usr/bin/env bash
set -euo pipefail

COMMON_SUBMODULES=(
    buildroot
    br2-external
    lpf
)

usage() {
    cat <<'EOF'
Usage: scripts/setup-platform.sh [options] <platform>

Set up a target platform workspace by initializing or updating only the required submodules.

Platforms:
  imx6ull        buildroot, br2-external, lpf, linux/linux-7.0, uboot/uboot-2024.10
  ti            buildroot, br2-external, lpf, linux/ti-linux-kernel-6.18.13, uboot/ti-u-boot-2025.10
  all           all submodules listed in .gitmodules

Options:
  --remote      Update submodules to their configured remote branch instead of the recorded commit
  --depth N     Use shallow clone/update depth N and blob filtering for large source trees
  --jobs N      Parallel submodule jobs, default: 4
  --no-common   Skip common submodules and update only platform-specific source trees
  --dry-run     Print the git commands without running them
  --list        List supported platforms and their submodules
  -h, --help    Show this help

Examples:
  scripts/setup-platform.sh imx6ull
  scripts/setup-platform.sh --remote imx6ull
  scripts/setup-platform.sh --depth 1 imx6ull
  scripts/setup-platform.sh --dry-run imx6ull
EOF
}

print_command() {
    printf '+'
    printf ' %q' "$@"
    printf '\n'
}

run() {
    if [[ "$DRY_RUN" == 1 ]]; then
        print_command "$@"
    else
        "$@"
    fi
}

platform_specific_submodules() {
    local platform="$1"

    case "$platform" in
        imx6ull|imx6ullevk)
            printf '%s\n' \
                linux/linux-7.0 \
                uboot/uboot-2024.10
            ;;
        ti|ti-evm)
            printf '%s\n' \
                linux/ti-linux-kernel-6.18.13 \
                uboot/ti-u-boot-2025.10
            ;;
        all)
            git config --file .gitmodules --get-regexp '^submodule\..*\.path$' | awk '{print $2}'
            ;;
        *)
            printf 'Unsupported platform: %s\n\n' "$platform" >&2
            usage >&2
            exit 2
            ;;
    esac
}

list_platforms() {
    cat <<'EOF'
imx6ull:
  buildroot
  br2-external
  lpf
  linux/linux-7.0
  uboot/uboot-2024.10

ti:
  buildroot
  br2-external
  lpf
  linux/ti-linux-kernel-6.18.13
  uboot/ti-u-boot-2025.10

all:
  every path listed in .gitmodules
EOF
}

validate_platform() {
    case "$1" in
        imx6ull|imx6ullevk|ti|ti-evm|all)
            ;;
        *)
            printf 'Unsupported platform: %s

' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
}

append_unique() {
    local item="$1"
    local existing

    for existing in "${SUBMODULES[@]}"; do
        if [[ "$existing" == "$item" ]]; then
            return
        fi
    done

    SUBMODULES+=("$item")
}

is_positive_integer() {
    [[ "$1" =~ ^[1-9][0-9]*$ ]]
}

REMOTE=0
DRY_RUN=0
INCLUDE_COMMON=1
JOBS=4
DEPTH=""
PLATFORM=""
SUBMODULES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --remote)
            REMOTE=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --no-common)
            INCLUDE_COMMON=0
            shift
            ;;
        --jobs)
            if [[ $# -lt 2 ]] || ! is_positive_integer "$2"; then
                printf '%s\n' '--jobs requires a positive integer' >&2
                exit 2
            fi
            JOBS="$2"
            shift 2
            ;;
        --depth)
            if [[ $# -lt 2 ]] || ! is_positive_integer "$2"; then
                printf '%s\n' '--depth requires a positive integer' >&2
                exit 2
            fi
            DEPTH="$2"
            shift 2
            ;;
        --list)
            list_platforms
            exit 0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            printf 'Unknown option: %s\n\n' "$1" >&2
            usage >&2
            exit 2
            ;;
        *)
            if [[ -n "$PLATFORM" ]]; then
                printf '%s\n\n' 'Only one platform can be specified' >&2
                usage >&2
                exit 2
            fi
            PLATFORM="$1"
            shift
            ;;
    esac
done

if [[ $# -gt 0 ]]; then
    if [[ -n "$PLATFORM" || $# -gt 1 ]]; then
        printf '%s\n\n' 'Only one platform can be specified' >&2
        usage >&2
        exit 2
    fi
    PLATFORM="$1"
fi

if [[ -z "$PLATFORM" ]]; then
    usage >&2
    exit 2
fi

validate_platform "$PLATFORM"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR/.." rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [[ "$PLATFORM" != all && "$INCLUDE_COMMON" == 1 ]]; then
    for module in "${COMMON_SUBMODULES[@]}"; do
        append_unique "$module"
    done
fi

while IFS= read -r module; do
    [[ -n "$module" ]] && append_unique "$module"
done < <(platform_specific_submodules "$PLATFORM")

if [[ "${#SUBMODULES[@]}" -eq 0 ]]; then
    printf '%s\n' 'No submodules selected' >&2
    exit 1
fi

printf 'Selected platform: %s\n' "$PLATFORM"
printf 'Selected submodules:\n'
printf '  %s\n' "${SUBMODULES[@]}"

update_args=(submodule update --init --recursive "--jobs=$JOBS")

if [[ "$REMOTE" == 1 ]]; then
    update_args+=(--remote)
fi

if [[ -n "$DEPTH" ]]; then
    update_args+=(--depth "$DEPTH" --filter=blob:none)
fi

run git submodule sync --recursive -- "${SUBMODULES[@]}"
run git "${update_args[@]}" -- "${SUBMODULES[@]}"
