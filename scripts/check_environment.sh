#!/usr/bin/env bash
# Read-only Step 0 report for Linux, macOS, and Git Bash for Windows.
set -u
export GIT_OPTIONAL_LOCKS=0
repository_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)" || exit 1
needs_attention=0

report() {
    printf '%s=%s\n' "$1" "$2"
}

tool_version() {
    local key="$1" command_name="$2" version_output
    shift 2
    if ! command -v "$command_name" >/dev/null 2>&1; then
        report "$key" NOT_INSTALLED
        return
    fi
    report "$key" INSTALLED
    if version_output=$("$command_name" "$@" 2>&1); then
        report "${key}_VERSION" "${version_output%%$'\n'*}"
    else
        report "${key}_VERSION" UNAVAILABLE
    fi
}

protect_remote_url() {
    # Never print embedded URL credentials or query parameters.
    printf '%s\n' "$1" | sed -E 's#([[:alpha:]][[:alnum:]+.-]*://)[^/[:space:]]*@#\1[REDACTED]@#; /^[[:alpha:]][[:alnum:]+.-]*:\/\//s/[?#].*$//'
}

report PROJECT ATLAS_HH_BBGG_PUBLIC_V1
report STEP STEP_0_THREE_PC_GITHUB
tool_version GIT git --version
if ! command -v git >/dev/null 2>&1; then
    needs_attention=1
fi

if command -v gh >/dev/null 2>&1; then
    tool_version GH gh --version
    if gh auth status --active --hostname github.com >/dev/null 2>&1; then
        report GH_AUTH AUTHENTICATED
    else
        report GH_AUTH NOT_AUTHENTICATED_OR_UNREACHABLE
        needs_attention=1
    fi
else
    report GH NOT_INSTALLED
    report GH_AUTH NOT_CHECKED_GH_MISSING
    needs_attention=1
fi

compiler_name=''
for candidate in g++ clang++ c++ cl; do
    if command -v "$candidate" >/dev/null 2>&1; then
        compiler_name="$candidate"
        break
    fi
done
if [[ -n "$compiler_name" ]]; then
    report CXX "INSTALLED:$compiler_name"
else
    report CXX NOT_INSTALLED
fi
tool_version CMAKE cmake --version
if command -v root-config >/dev/null 2>&1; then
    tool_version ROOT root-config --version
elif command -v root >/dev/null 2>&1; then
    report ROOT INSTALLED:root
    report ROOT_VERSION NOT_CHECKED_ROOT_CONFIG_MISSING
else
    report ROOT NOT_INSTALLED
fi

top_level=''
physical_top_level=''
if command -v git >/dev/null 2>&1; then
    top_level=$(git -C "$repository_directory" rev-parse --show-toplevel 2>/dev/null) || top_level=''
    if [[ -n "$top_level" ]]; then
        physical_top_level=$(cd -- "$top_level" 2>/dev/null && pwd -P) || physical_top_level=''
    fi
fi

if [[ -n "$physical_top_level" && "$physical_top_level" == "$repository_directory" ]]; then
    report REPOSITORY GIT_REPOSITORY
    if branch=$(git -C "$repository_directory" symbolic-ref --quiet --short HEAD 2>/dev/null); then
        report BRANCH "$branch"
    else
        report BRANCH DETACHED_HEAD
        needs_attention=1
    fi
    if commit=$(git -C "$repository_directory" rev-parse --verify HEAD 2>/dev/null); then
        report COMMIT "$commit"
    else
        report COMMIT NOT_CREATED
        needs_attention=1
    fi
    if remote=$(git -C "$repository_directory" remote get-url origin 2>/dev/null); then
        report ORIGIN "$(protect_remote_url "$remote")"
    else
        report ORIGIN NOT_CONFIGURED
        needs_attention=1
    fi
    if upstream=$(git -C "$repository_directory" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null); then
        report UPSTREAM "$upstream"
    else
        report UPSTREAM NOT_CONFIGURED
        needs_attention=1
    fi
    if status=$(git -C "$repository_directory" status --porcelain=v1 --untracked-files=all 2>/dev/null); then
        if [[ -z "$status" ]]; then
            report WORKING_TREE CLEAN
        else
            report WORKING_TREE DIRTY
            needs_attention=1
        fi
    else
        report WORKING_TREE ERROR
        needs_attention=1
    fi
else
    report REPOSITORY NOT_INITIALIZED_OR_UNAVAILABLE
    report BRANCH NOT_AVAILABLE
    report ORIGIN NOT_AVAILABLE
    report UPSTREAM NOT_AVAILABLE
    report WORKING_TREE NOT_AVAILABLE
    needs_attention=1
fi

if (( needs_attention )); then
    report STEP_0_LOCAL_READINESS NEEDS_ATTENTION
    exit 1
fi
report STEP_0_LOCAL_READINESS READY_FOR_REMOTE_VALIDATION
exit 0
