# Read-only G1 acquisition. Run as the current NON-administrator only.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$ExpectedScriptSha256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$ExpectedWslExeSha256
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$actual=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
if($actual -cne $ExpectedScriptSha256){throw 'REVIEWED_SCRIPT_HASH_MISMATCH'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=[Security.Principal.WindowsPrincipal]::new($identity)
if($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'ADMINISTRATOR_CONTEXT_NOT_AUTHORIZED'}
$dir=Get-Item -LiteralPath $OutputDirectory
if(-not $dir.PSIsContainer -or ($dir.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'PRIVATE_DIRECTORY_REQUIRED'}
$acl=Get-Acl -LiteralPath $dir.FullName
$sid=$identity.User.Value
if(-not $acl.AreAccessRulesProtected){throw 'PRIVATE_DIRECTORY_INHERITANCE_NOT_DISABLED'}
if($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -cne $sid){throw 'PRIVATE_DIRECTORY_OWNER_MISMATCH'}
$rules=@($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]))
if($rules.Count -ne 1 -or $rules[0].IdentityReference.Value -cne $sid -or
   $rules[0].AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow -or
   $rules[0].InheritanceFlags -ne [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit' -or
   $rules[0].PropagationFlags -ne [Security.AccessControl.PropagationFlags]::None -or
   ($rules[0].FileSystemRights -band [Security.AccessControl.FileSystemRights]::FullControl) -ne [Security.AccessControl.FileSystemRights]::FullControl){throw 'PRIVATE_DIRECTORY_CURRENT_USER_ONLY_ACL_REQUIRED'}
$start=[DateTimeOffset]::UtcNow
$clock=[Diagnostics.Stopwatch]::StartNew()
$rows=[Collections.Generic.List[object]]::new()
$script:AbortQueries=$false
$script:RemainingPayloadBytes=196608
function Add-Observation([string]$Key,[string]$Interface,[scriptblock]$Query){
    $t=[DateTimeOffset]::UtcNow.ToString('o')
    if($script:AbortQueries){$rows.Add(@{key=$Key;interface=$Interface;time=$t;status='UNKNOWN';error_code='STOPPED_AFTER_CLEANUP_UNKNOWN'});return}
    if($clock.Elapsed.TotalSeconds -gt 45){$rows.Add(@{key=$Key;interface=$Interface;time=$t;status='UNKNOWN';error_code='ACQUISITION_DEADLINE'});return}
    try{
        $data=@(& $Query)
        if($data.Count -gt 128){throw 'QUERY_ROW_BOUND'}
        $encoded=ConvertTo-Json -InputObject $data -Depth 8 -Compress
        $count=[Text.Encoding]::UTF8.GetByteCount($encoded)
        if($count -gt 65536 -or $count -gt $script:RemainingPayloadBytes){throw 'QUERY_OR_AGGREGATE_BYTE_BOUND'}
        $script:RemainingPayloadBytes-=$count
        if($Key -in @('wsl_version','running_distros') -and $data[0].exit_code -ne 0){
            $code=if(($data[0].stdout+$data[0].stderr) -match 'Wsl/E_ACCESSDENIED'){'ACCESS_DENIED'}else{'NATIVE_QUERY_NONZERO'}
            $rows.Add(@{key=$Key;interface=$Interface;time=$t;status='UNKNOWN';error_code=$code;data=$data})
        }else{$rows.Add(@{key=$Key;interface=$Interface;time=$t;status='REPORTED_UNATTESTED';data=$data})}
    }catch{
        $reason=if($_.Exception.Message -match 'CLEANUP_UNKNOWN'){'CLEANUP_UNKNOWN'}elseif($_.Exception.Message -match 'access|denied|拒絕'){ 'ACCESS_DENIED' }elseif($_.Exception.Message -match 'BOUND'){ 'OUTPUT_BOUND' }elseif($_.Exception.Message -match 'TIMEOUT'){'QUERY_TIMEOUT'}else{'QUERY_FAILED'}
        if($reason -eq 'CLEANUP_UNKNOWN'){$script:AbortQueries=$true}
        # Bounded detailed diagnostics remain ONLY in the private capture.
        $message=$_.Exception.Message
        $rows.Add(@{key=$Key;interface=$Interface;time=$t;status='UNKNOWN';error_code=$reason;error_type=$_.Exception.GetType().FullName;hresult=$_.Exception.HResult;error_message=$message.Substring(0,[Math]::Min(2048,$message.Length))})
    }
}
function Native-WslQuery([string[]]$Arguments){
    # These two inventory argv are the complete allowlist. Never launch a distro.
    $joined=$Arguments -join ' '
    if($joined -notin @('--version','--list --running --quiet')){throw 'FORBIDDEN_WSL_ARGV'}
    $win=[Environment]::GetFolderPath([Environment+SpecialFolder]::Windows)
    $exe=Join-Path $win 'System32\wsl.exe'
    $check=Get-Item -LiteralPath $exe
    while($null -ne $check){
        if($check.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'EXECUTABLE_REPARSE_PATH_REJECTED'}
        $check=if($check -is [IO.DirectoryInfo]){$check.Parent}else{$check.Directory}
    }
    $pin=[IO.File]::Open($exe,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try{
    $exeHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($pin)).ToLowerInvariant()
    if($exeHash -cne $ExpectedWslExeSha256){throw 'REVIEWED_WSL_EXECUTABLE_HASH_MISMATCH'}
    $signature=Get-AuthenticodeSignature -LiteralPath $exe
    if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '^CN=Microsoft (Windows|Corporation)(,|$)'){throw 'UNVERIFIED_MICROSOFT_WSL_EXECUTABLE'}
    $info=[Diagnostics.ProcessStartInfo]::new($exe)
    $info.UseShellExecute=$false;$info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
    foreach($arg in $Arguments){$info.ArgumentList.Add($arg)}
    $proc=[Diagnostics.Process]::new();$proc.StartInfo=$info
    $buffers=@([byte[]]::new(32769),[byte[]]::new(32769))
    $offsets=@(0,0);$done=@($false,$false);$tasks=@($null,$null)
    $timer=[Diagnostics.Stopwatch]::StartNew();$reason=$null
    $started=$false
    try{
        if(-not $proc.Start()){throw 'NATIVE_QUERY_NOT_STARTED'}
        $started=$true
        $streams=@($proc.StandardOutput.BaseStream,$proc.StandardError.BaseStream)
        for($i=0;$i -lt 2;$i++){$tasks[$i]=$streams[$i].ReadAsync($buffers[$i],0,32769)}
        while(-not ($done[0] -and $done[1] -and $proc.HasExited)){
            for($i=0;$i -lt 2;$i++){
                if(-not $done[$i] -and $tasks[$i].IsCompleted){
                    $n=$tasks[$i].GetAwaiter().GetResult();$offsets[$i]+=$n
                    if($offsets[$i] -gt 32768){$reason='OUTPUT_BOUND';break}
                    if($n -eq 0){$done[$i]=$true}else{$tasks[$i]=$streams[$i].ReadAsync($buffers[$i],$offsets[$i],32769-$offsets[$i])}
                }
            }
            if($reason){break}
            if($timer.Elapsed.TotalSeconds -gt 4){$reason='QUERY_TIMEOUT';break}
            [Threading.Thread]::Sleep(10)
        }
        if($reason){throw $reason}
        $decoded=@()
        for($i=0;$i -lt 2;$i++){
            $raw=$buffers[$i][0..([Math]::Max(0,$offsets[$i]-1))]
            if($offsets[$i] -eq 0){$decoded+='';continue}
            $zero=@($raw | Where-Object {$_ -eq 0}).Count
            $encoding=if($zero -gt $raw.Count/5){[Text.Encoding]::Unicode}else{[Text.UTF8Encoding]::new($false,$true)}
            $decoded+=$encoding.GetString($raw).Trim([char]0xfeff)
        }
        return @{argv=$Arguments;exit_code=$proc.ExitCode;stdout=$decoded[0];stderr=$decoded[1];executable_sha256=$exeHash;signature='Valid';cleanup='OWNED_QUERY_EXITED';wall_seconds=$timer.Elapsed.TotalSeconds}
    }finally{
        # A failed decode/read must also clean up only this owned query PID.
        $cleanupUnknown=$false
        if($started){
            try{if(-not $proc.HasExited){$proc.Kill()};if(-not $proc.WaitForExit(1000)){$cleanupUnknown=$true}}catch{$cleanupUnknown=$true}
        }
        $proc.Dispose()
        if($cleanupUnknown){throw 'NATIVE_QUERY_CLEANUP_UNKNOWN'}
    }
    }finally{$pin.Dispose()}
}
Add-Observation 'runtime' 'LOCAL_DOTNET_CURRENT_PROCESS' {
    [pscustomobject]@{windows_version=[Environment]::OSVersion.VersionString;powershell_version=$PSVersionTable.PSVersion.ToString();administrator=$false;process_64bit=[Environment]::Is64BitProcess;system_drive=$env:SystemDrive}
}
Add-Observation 'wsl_version' 'SIGNED_SYSTEM32_WSL_VERSION_QUERY' {Native-WslQuery -Arguments @('--version')}
Add-Observation 'running_distros' 'SIGNED_SYSTEM32_WSL_RUNNING_LIST_QUERY' {Native-WslQuery -Arguments @('--list','--running','--quiet')}
Add-Observation 'os_memory' 'LOCAL_CIM_ROOT_CIMV2_WIN32_OPERATINGSYSTEM' {
    Get-CimInstance -ClassName Win32_OperatingSystem -Property Caption,Version,BuildNumber,TotalVisibleMemorySize,FreePhysicalMemory -OperationTimeoutSec 2 | Select-Object -First 129 Caption,Version,BuildNumber,TotalVisibleMemorySize,FreePhysicalMemory
}
Add-Observation 'hypervisor' 'LOCAL_CIM_ROOT_CIMV2_WIN32_COMPUTERSYSTEM' {
    Get-CimInstance -ClassName Win32_ComputerSystem -Property HypervisorPresent,TotalPhysicalMemory,Manufacturer,Model -OperationTimeoutSec 2 | Select-Object -First 129 HypervisorPresent,TotalPhysicalMemory,Manufacturer,Model
}
Add-Observation 'features' 'LOCAL_CIM_ROOT_CIMV2_WIN32_OPTIONALFEATURE' {
    foreach($name in @('VirtualMachinePlatform','Microsoft-Windows-Subsystem-Linux','HypervisorPlatform','Microsoft-Hyper-V-All')){
        Get-CimInstance -ClassName Win32_OptionalFeature -Property Name,InstallState -Filter "Name='$name'" -OperationTimeoutSec 2 | Select-Object -First 129 Name,InstallState
    }
}
Add-Observation 'disk_drives' 'LOCAL_CIM_ROOT_CIMV2_WIN32_DISKDRIVE' {
    Get-CimInstance -ClassName Win32_DiskDrive -Property Index,Model,SerialNumber,PNPDeviceID,Size,InterfaceType,MediaType -OperationTimeoutSec 2 | Select-Object -First 129 Index,Model,SerialNumber,PNPDeviceID,Size,InterfaceType,MediaType
}
Add-Observation 'partitions' 'LOCAL_CIM_ROOT_CIMV2_WIN32_DISKPARTITION' {
    Get-CimInstance -ClassName Win32_DiskPartition -Property DiskIndex,Index,DeviceID,Size,StartingOffset,BootPartition,PrimaryPartition,Type -OperationTimeoutSec 2 | Select-Object -First 129 DiskIndex,Index,DeviceID,Size,StartingOffset,BootPartition,PrimaryPartition,Type
}
Add-Observation 'logical_disks' 'LOCAL_CIM_ROOT_CIMV2_WIN32_LOGICALDISK' {
    Get-CimInstance -ClassName Win32_LogicalDisk -Property DeviceID,DriveType,FileSystem,Size,FreeSpace -OperationTimeoutSec 2 | Select-Object -First 129 DeviceID,DriveType,FileSystem,Size,FreeSpace
}
Add-Observation 'disk_partition_links' 'LOCAL_CIM_ROOT_CIMV2_WIN32_DISKDRIVETODISKPARTITION' {
    Get-CimInstance -ClassName Win32_DiskDriveToDiskPartition -Property Antecedent,Dependent -OperationTimeoutSec 2 | Select-Object -First 129 Antecedent,Dependent
}
Add-Observation 'partition_volume_links' 'LOCAL_CIM_ROOT_CIMV2_WIN32_LOGICALDISKTOPARTITION' {
    Get-CimInstance -ClassName Win32_LogicalDiskToPartition -Property Antecedent,Dependent -OperationTimeoutSec 2 | Select-Object -First 129 Antecedent,Dependent
}
Add-Observation 'storage_disks' 'LOCAL_CIM_STORAGE_MSFT_DISK' {
    Get-CimInstance -Namespace root/Microsoft/Windows/Storage -ClassName MSFT_Disk -Property Number,UniqueId,UniqueIdFormat,SerialNumber,FriendlyName,Path,Location,Size,PartitionStyle,IsBoot,IsSystem,IsOffline,IsReadOnly,BusType,LogicalSectorSize,PhysicalSectorSize -OperationTimeoutSec 2 | Select-Object -First 129 Number,UniqueId,UniqueIdFormat,SerialNumber,FriendlyName,Path,Location,Size,PartitionStyle,IsBoot,IsSystem,IsOffline,IsReadOnly,BusType,LogicalSectorSize,PhysicalSectorSize
}
Add-Observation 'registered_distro_backing' 'CURRENT_USER_LXSS_REGISTRY_READ_ONLY' {
    $key='HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
    if(Test-Path -LiteralPath $key){Get-ChildItem -LiteralPath $key | Select-Object -First 129 | ForEach-Object {Get-ItemProperty -LiteralPath $_.PSPath -Name DistributionName,BasePath,Version | Select-Object DistributionName,BasePath,Version}}
}
$capture=@{schema='PHASE7I_G1_HOST_CAPTURE_V1';capture_id=[Guid]::NewGuid().ToString();started_utc=$start.ToString('o');ended_utc=[DateTimeOffset]::UtcNow.ToString('o');collector_sha256=$actual;administrator=$false;process_id=$PID;observations=$rows.ToArray();trust='REPORTED_UNATTESTED';host_guest_mapping_complete=$false;protected_storage_complete=$false;distro_launches=0;privileged_actions=0;limits='BOUNDED_RETAINED_OUTPUT_AND_ROW_ENUMERATION; PROVIDER_ALLOCATION_NOT_HARD_BOUNDED; 45S_BETWEEN_QUERY_SOFT_DEADLINE; NOT_FULL_RESOURCE_ENVELOPE'}
$bytes=[Text.UTF8Encoding]::new($false).GetBytes((ConvertTo-Json -InputObject $capture -Depth 12 -Compress))
if($bytes.Length -gt 262144){throw 'CAPTURE_BYTE_BOUND'}
$path=Join-Path $dir.FullName ('host_'+$capture.capture_id+'.json')
$file=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
try{
    $fileAcl=[IO.FileSystemAclExtensions]::GetAccessControl($file)
    $fileRules=@($fileAcl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]))
    if($fileAcl.GetOwner([Security.Principal.SecurityIdentifier]).Value -cne $sid -or
       $fileRules.Count -ne 1 -or $fileRules[0].IdentityReference.Value -cne $sid -or
       $fileRules[0].AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow -or
       ($fileRules[0].FileSystemRights -band [Security.AccessControl.FileSystemRights]::FullControl) -ne [Security.AccessControl.FileSystemRights]::FullControl){throw 'PRIVATE_CAPTURE_FILE_ACL_REQUIRED_BEFORE_RAW_WRITE'}
    $file.Write($bytes,0,$bytes.Length);$file.Flush($true)
}finally{$file.Dispose()}
$readback=[IO.File]::ReadAllBytes($path)
if(-not [Linq.Enumerable]::SequenceEqual([byte[]]$bytes,[byte[]]$readback)){throw 'CAPTURE_REOPEN_MISMATCH'}
[pscustomobject]@{status='CAPTURED_UNATTESTED_READ_ONLY';local_receipt=$path;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();observations=$rows.Count;unknown=@($rows | Where-Object {$_.status -eq 'UNKNOWN'}).Count;distro_launches=0;administrator=$false} | ConvertTo-Json -Compress
