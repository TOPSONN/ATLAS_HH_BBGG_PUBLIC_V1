# Synthetic in-memory CIM objects only. Never dot-source the inventory script.
[CmdletBinding()]param([Parameter(Mandatory)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot '../g1_windows_inventory.ps1'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'SOURCE_PARSE_ERROR'}
$allowed=@('Get-G1Endpoint','Get-G1Inventory','Test-G1UInt32','Get-G1IdentityMap','Convert-G1Associations','Add-Observation')
$functions=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -in $allowed},$true))
if($functions.Count -ne $allowed.Count){throw 'OFFLINE_FUNCTION_ALLOWLIST'}
foreach($f in $functions){. ([scriptblock]::Create($f.Extent.Text))}
function Endpoint([string]$Class,[string]$Id,[string]$Namespace='root/cimv2',[bool]$Key=$true){
    $c=[Microsoft.Management.Infrastructure.CimInstance]::new($Class,$Namespace)
    $flag=if($Key){[Microsoft.Management.Infrastructure.CimFlags]::Key}else{[Microsoft.Management.Infrastructure.CimFlags]::None}
    $c.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create('DeviceID',$Id,[Microsoft.Management.Infrastructure.CimType]::String,$flag))
    return $c
}
function Edge($A,$B,[bool]$Volume=$false,[UInt64]$Start=0,[UInt64]$End=99){
    $class=if($Volume){'Win32_LogicalDiskToPartition'}else{'Win32_DiskDriveToDiskPartition'}
    $c=[Microsoft.Management.Infrastructure.CimInstance]::new($class,'root/cimv2')
    foreach($pair in @(@('Antecedent',$A),@('Dependent',$B))){
        $c.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create($pair[0],$pair[1],[Microsoft.Management.Infrastructure.CimType]::Reference,[Microsoft.Management.Infrastructure.CimFlags]::Key))
    }
    if($Volume){
        foreach($pair in @(@('StartingAddress',$Start),@('EndingAddress',$End))){
            $c.CimInstanceProperties.Add([Microsoft.Management.Infrastructure.CimProperty]::Create($pair[0],$pair[1],[Microsoft.Management.Infrastructure.CimType]::UInt64,[Microsoft.Management.Infrastructure.CimFlags]::None))
        }
    }
    return $c
}
function Setup([int]$Count=1){
    $script:rows=[Collections.Generic.List[object]]::new()
    $script:clock=[Diagnostics.Stopwatch]::StartNew();$script:AbortQueries=$false;$script:RemainingPayloadBytes=196608
    $script:parts=@(for($i=0;$i -lt $Count;$i++){[pscustomobject]@{DeviceID="PART$i";DiskIndex=0}})
    $script:rows.Add(@{key='disk_drives';status='REPORTED_UNATTESTED';data=@([pscustomobject]@{DeviceID='DISK0';Index=0})})
    $script:rows.Add(@{key='partitions';status='REPORTED_UNATTESTED';data=$script:parts})
    $script:rows.Add(@{key='logical_disks';status='REPORTED_UNATTESTED';data=@([pscustomobject]@{DeviceID='V:';DriveType=3})})
}
$results=[Collections.Generic.List[object]]::new()
function Assert([bool]$Condition,[string]$Name){if(-not $Condition){throw "OFFLINE_ASSERT:$Name"};$results.Add(@{case=$Name;status='PASS'})}
function Reject([scriptblock]$Call,[string]$Name){
    $failed=$false
    try{$null=& $Call}catch{if($_.Exception.Message -notmatch 'ASSOCIATION_|QUERY_ROW_BOUND'){throw};$failed=$true}
    Assert $failed $Name
}
Setup
$d=Endpoint 'Win32_DiskDrive' 'DISK0';$p=Endpoint 'Win32_DiskPartition' 'PART0';$v=Endpoint 'Win32_LogicalDisk' 'V:'
$e=Edge $d $p
$flat=@(Convert-G1Associations @($e) 'disk_partition_links')
Assert ($flat.Count -eq 1 -and $flat[0].antecedent.device_id -ceq 'DISK0') 'one_edge_exact'
$script:rows.Add(@{key='disk_partition_links';status='REPORTED_UNATTESTED';data=$flat})
$volume=@(Convert-G1Associations @((Edge $p $v $true 12 ([UInt64]::MaxValue))) 'partition_volume_links')
Assert ($volume[0].starting_address -ceq '12' -and $volume[0].ending_address -ceq '18446744073709551615') 'uint64_lossless_extents'
Reject {Convert-G1Associations @($e,$e) 'disk_partition_links'} 'duplicate_rejected'
Reject {Convert-G1Associations @((Edge $p $v $true 9 2)) 'partition_volume_links'} 'reversed_extent_rejected'
Reject {Convert-G1Associations @((Edge $p (Endpoint 'Win32_LogicalDisk' 'MISSING') $true)) 'partition_volume_links'} 'dangling_endpoint_rejected'
Reject {Get-G1Endpoint (Endpoint 'Win32_LogicalDisk' 'X') 'Win32_DiskDrive'} 'wrong_class_rejected'
Reject {Get-G1Endpoint (Endpoint 'Win32_DiskDrive' 'X' 'root/other') 'Win32_DiskDrive'} 'wrong_namespace_rejected'
Reject {Get-G1Endpoint (Endpoint 'Win32_DiskDrive' 'X' 'root/cimv2' $false) 'Win32_DiskDrive'} 'missing_key_flag_rejected'
Reject {Get-G1Endpoint 'nested_reference_string' 'Win32_DiskDrive'} 'string_reference_rejected'
Reject {Get-G1Endpoint (Endpoint 'Win32_DiskDrive' '') 'Win32_DiskDrive'} 'empty_key_rejected'
Reject {Get-G1Endpoint (Endpoint 'Win32_DiskDrive' "X`n") 'Win32_DiskDrive'} 'control_key_rejected'
Reject {Convert-G1Associations @() 'disk_partition_links'} 'missing_partition_edge_rejected'
Reject {Convert-G1Associations @() 'partition_volume_links'} 'missing_fixed_volume_edge_rejected'
$script:parts[0].DiskIndex=1
Reject {Convert-G1Associations @($e) 'disk_partition_links'} 'disk_index_contradiction_rejected'
Setup 128
$many=@(for($i=0;$i -lt 128;$i++){Edge $d (Endpoint 'Win32_DiskPartition' "PART$i")})
$bounded=@(Convert-G1Associations $many 'disk_partition_links')
$encoded=ConvertTo-Json -InputObject $bounded -Depth 8 -Compress -WarningAction Stop
Assert ($bounded.Count -eq 128 -and [Text.Encoding]::UTF8.GetByteCount($encoded) -le 65536) '128_edges_preserved_within_original_cap'
$script:rows.Add(@{key='disk_partition_links';status='REPORTED_UNATTESTED';data=$bounded})
$volumes=@(for($i=0;$i -lt 128;$i++){Edge (Endpoint 'Win32_DiskPartition' "PART$i") $v $true 0 99})
$vflat=@(Convert-G1Associations $volumes 'partition_volume_links')
$vbytes=[Text.Encoding]::UTF8.GetByteCount((ConvertTo-Json -InputObject $vflat -Depth 8 -Compress -WarningAction Stop))
Assert ($vflat.Count -eq 128 -and $vbytes -le 65536) '128_volume_edges_and_all_extents_preserved'
Reject {Convert-G1Associations @($many+$e) 'disk_partition_links'} '129_edges_reject_entire_set'
Setup 0
Assert (@(Convert-G1Associations @() 'disk_partition_links').Count -eq 0) 'empty_partition_inventory_zero_edges'
Setup
Add-Observation 'fixture_row_bound' 'INERT' {1..129}
Assert ($rows[-1].error_message -ceq 'QUERY_ROW_BOUND' -and -not $rows[-1].ContainsKey('data')) 'row_bound_no_partial_data'
Add-Observation 'fixture_byte_bound' 'INERT' {,@{x=('x'*65537)}}
Assert ($rows[-1].error_message -ceq 'QUERY_BYTE_BOUND') 'per_query_byte_bound'
Assert ($rows[-1].bound_diagnostics.serialized_bytes -gt 65536) 'rejected_byte_minimum_recorded'
$script:RemainingPayloadBytes=1
Add-Observation 'fixture_aggregate_bound' 'INERT' {,@{x='x'}}
Assert ($rows[-1].error_message -ceq 'AGGREGATE_BYTE_BOUND') 'aggregate_byte_bound'
$script:RemainingPayloadBytes=196608
Add-Observation 'fixture_depth' 'INERT' {$n=@{x='leaf'};1..12 | ForEach-Object {$n=@{x=$n}};$n}
Assert ($rows[-1].error_code -ceq 'SERIALIZATION_WARNING' -and -not $rows[-1].ContainsKey('data')) 'depth_warning_rejected'
Add-Observation 'fixture_partial_provider' 'INERT' {$e;throw 'ASSOCIATION_INERT_PROVIDER_FAILURE'}
Assert ($rows[-1].error_code -ceq 'ASSOCIATION_INVALID' -and -not $rows[-1].ContainsKey('data')) 'provider_failure_no_partial_edges'
Setup
Add-Observation 'disk_partition_links' 'INERT' {Convert-G1Associations @($e) 'disk_partition_links'}
Assert ($rows[-1].provider_enumeration_complete -eq $true -and $rows[-1].enumerated_edge_count -eq 1) 'success_enumeration_contract'
Setup
$long=('X'*1024);$script:parts=@(for($i=0;$i -lt 100;$i++){[pscustomobject]@{DeviceID=($long.Substring(0,1020)+$i.ToString('D4'));DiskIndex=0}})
$script:rows[1].data=$script:parts
$oversize=@(foreach($part in $script:parts){Edge $d (Endpoint 'Win32_DiskPartition' $part.DeviceID)})
Add-Observation 'disk_partition_links' 'INERT' {Convert-G1Associations $oversize 'disk_partition_links'}
Assert ($rows[-1].error_message -ceq 'QUERY_BYTE_BOUND' -and -not $rows[-1].ContainsKey('data') -and $rows[-1].bound_diagnostics.observed_rows -eq 100) 'complete_but_oversize_edges_rejected_without_truncation'
$report=@{schema='G1_ASSOCIATION_INERT_OFFLINE_V1';status='PASS';cases=$results.ToArray();
    powershell_version=$PSVersionTable.PSVersion.ToString();new_host_queries=0;wsl_launches=0;
    inventory_top_level_executed=$false;synthetic_edges=$flat;synthetic_volume_edges=$volume;max_128_encoded_bytes=[Text.Encoding]::UTF8.GetByteCount($encoded);max_128_volume_encoded_bytes=$vbytes}
$raw=[Text.UTF8Encoding]::new($false).GetBytes((ConvertTo-Json -InputObject $report -Depth 12 -Compress -WarningAction Stop))
$f=[IO.File]::Open($Output,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
try{$f.Write($raw);$f.Flush($true)}finally{$f.Dispose()}
[pscustomobject]@{status='PASS_INERT_OFFLINE';cases=$results.Count;new_host_queries=0;wsl_launches=0}|ConvertTo-Json -Compress
