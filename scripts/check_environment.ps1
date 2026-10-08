# Read-only Step 0 report. Compatible with Windows PowerShell 5.1 and PowerShell 7.
[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$repositoryDirectory = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$needsAttention = $false

function Write-Report {
    param([string]$Key, [string]$Value)
    Write-Output ($Key + '=' + $Value)
}

function Invoke-ReadOnlyCommand {
    param([string]$Command, [string[]]$CommandArguments)
    # Capture native stderr without publishing auth details or treating it as
    # a terminating PowerShell error. Check each native exit code explicitly.
    $ErrorActionPreference = 'Continue'
    if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
        $PSNativeCommandUseErrorActionPreference = $false
    }
    $commandOutput = @(& $Command @CommandArguments 2>&1)
    $commandExitCode = $LASTEXITCODE
    [pscustomobject]@{
        ExitCode = $commandExitCode
        Lines = @($commandOutput | ForEach-Object { [string]$_ })
    }
}

function Write-ToolVersion {
    param([string]$Key, [string]$Command, [string[]]$CommandArguments)
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        Write-Report $Key 'NOT_INSTALLED'
        return
    }
    $versionResult = Invoke-ReadOnlyCommand $Command $CommandArguments
    Write-Report $Key 'INSTALLED'
    if ($versionResult.ExitCode -eq 0 -and $versionResult.Lines.Count -gt 0) {
        Write-Report ($Key + '_VERSION') $versionResult.Lines[0].Trim()
    } else {
        Write-Report ($Key + '_VERSION') 'UNAVAILABLE'
    }
}

function Protect-RemoteUrl {
    param([string]$Value)
    # Never print embedded URL credentials or query parameters.
    $safeValue = [regex]::Replace($Value, '(?i)([a-z][a-z0-9+.-]*://)[^/\s]*@', '$1[REDACTED]@')
    if ($safeValue -match '^[a-z][a-z0-9+.-]*://') {
        $safeValue = [regex]::Replace($safeValue, '[?#].*$', '')
    }
    return $safeValue
}

Write-Report 'PROJECT' 'ATLAS_HH_BBGG_PUBLIC_V1'
Write-Report 'STEP' 'STEP_0_THREE_PC_GITHUB'
$gitAvailable = [bool](Get-Command git -ErrorAction SilentlyContinue)
Write-ToolVersion 'GIT' 'git' @('--version')
if (-not $gitAvailable) { $needsAttention = $true }

if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-ToolVersion 'GH' 'gh' @('--version')
    $authResult = Invoke-ReadOnlyCommand 'gh' @('auth', 'status', '--active', '--hostname', 'github.com')
    if ($authResult.ExitCode -eq 0) {
        Write-Report 'GH_AUTH' 'AUTHENTICATED'
    } else {
        Write-Report 'GH_AUTH' 'NOT_AUTHENTICATED_OR_UNREACHABLE'
        $needsAttention = $true
    }
} else {
    Write-Report 'GH' 'NOT_INSTALLED'
    Write-Report 'GH_AUTH' 'NOT_CHECKED_GH_MISSING'
    $needsAttention = $true
}

$compilerName = $null
foreach ($candidate in @('g++', 'clang++', 'c++', 'cl')) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $compilerName = $candidate
        break
    }
}
if ($compilerName) {
    Write-Report 'CXX' ('INSTALLED:' + $compilerName)
} else {
    Write-Report 'CXX' 'NOT_INSTALLED'
}
Write-ToolVersion 'CMAKE' 'cmake' @('--version')
if (Get-Command root-config -ErrorAction SilentlyContinue) {
    Write-ToolVersion 'ROOT' 'root-config' @('--version')
} elseif (Get-Command root -ErrorAction SilentlyContinue) {
    Write-Report 'ROOT' 'INSTALLED:root'
    Write-Report 'ROOT_VERSION' 'NOT_CHECKED_ROOT_CONFIG_MISSING'
} else {
    Write-Report 'ROOT' 'NOT_INSTALLED'
}

$previousOptionalLocks = [Environment]::GetEnvironmentVariable('GIT_OPTIONAL_LOCKS', 'Process')
try {
    $env:GIT_OPTIONAL_LOCKS = '0'
    $isThisRepository = $false
    if ($gitAvailable) {
        $topLevel = Invoke-ReadOnlyCommand 'git' @('-C', $repositoryDirectory, 'rev-parse', '--show-toplevel')
        if ($topLevel.ExitCode -eq 0 -and $topLevel.Lines.Count -gt 0) {
            $resolvedTopLevel = [IO.Path]::GetFullPath($topLevel.Lines[0])
            $isThisRepository = [string]::Equals($resolvedTopLevel, $repositoryDirectory, [StringComparison]::OrdinalIgnoreCase)
        }
    }

    if ($isThisRepository) {
        Write-Report 'REPOSITORY' 'GIT_REPOSITORY'
        $branch = Invoke-ReadOnlyCommand 'git' @('-C', $repositoryDirectory, 'symbolic-ref', '--quiet', '--short', 'HEAD')
        if ($branch.ExitCode -eq 0) {
            Write-Report 'BRANCH' $branch.Lines[0]
        } else {
            Write-Report 'BRANCH' 'DETACHED_HEAD'
            $needsAttention = $true
        }
        $commit = Invoke-ReadOnlyCommand 'git' @('-C', $repositoryDirectory, 'rev-parse', '--verify', 'HEAD')
        if ($commit.ExitCode -eq 0) {
            Write-Report 'COMMIT' $commit.Lines[0]
        } else {
            Write-Report 'COMMIT' 'NOT_CREATED'
            $needsAttention = $true
        }
        $remote = Invoke-ReadOnlyCommand 'git' @('-C', $repositoryDirectory, 'remote', 'get-url', 'origin')
        if ($remote.ExitCode -eq 0) {
            Write-Report 'ORIGIN' (Protect-RemoteUrl $remote.Lines[0])
        } else {
            Write-Report 'ORIGIN' 'NOT_CONFIGURED'
            $needsAttention = $true
        }
        $upstream = Invoke-ReadOnlyCommand 'git' @('-C', $repositoryDirectory, 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{upstream}')
        if ($upstream.ExitCode -eq 0) {
            Write-Report 'UPSTREAM' $upstream.Lines[0]
        } else {
            Write-Report 'UPSTREAM' 'NOT_CONFIGURED'
            $needsAttention = $true
        }
        $status = Invoke-ReadOnlyCommand 'git' @('-C', $repositoryDirectory, 'status', '--porcelain=v1', '--untracked-files=all')
        if ($status.ExitCode -ne 0) {
            Write-Report 'WORKING_TREE' 'ERROR'
            $needsAttention = $true
        } elseif ($status.Lines.Count -eq 0) {
            Write-Report 'WORKING_TREE' 'CLEAN'
        } else {
            Write-Report 'WORKING_TREE' 'DIRTY'
            $needsAttention = $true
        }
    } else {
        Write-Report 'REPOSITORY' 'NOT_INITIALIZED_OR_UNAVAILABLE'
        Write-Report 'BRANCH' 'NOT_AVAILABLE'
        Write-Report 'ORIGIN' 'NOT_AVAILABLE'
        Write-Report 'UPSTREAM' 'NOT_AVAILABLE'
        Write-Report 'WORKING_TREE' 'NOT_AVAILABLE'
        $needsAttention = $true
    }
} finally {
    [Environment]::SetEnvironmentVariable('GIT_OPTIONAL_LOCKS', $previousOptionalLocks, 'Process')
}

if ($needsAttention) {
    Write-Report 'STEP_0_LOCAL_READINESS' 'NEEDS_ATTENTION'
    exit 1
}
Write-Report 'STEP_0_LOCAL_READINESS' 'READY_FOR_REMOTE_VALIDATION'
exit 0
