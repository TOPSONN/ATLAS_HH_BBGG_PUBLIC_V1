# Reversible workspace output ACL preparation only; no host/service change.
[CmdletBinding()]param()
$ErrorActionPreference='Stop'
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
if(([Security.Principal.WindowsPrincipal]::new($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'NONADMIN_REQUIRED'}
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../../.local/readiness_progress_v1'))
$parent=Split-Path $root -Parent
if(-not (Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Path $parent | Out-Null}
if(Test-Path -LiteralPath $root){throw 'FRESH_OUTPUT_DIRECTORY_REQUIRED'}
New-Item -ItemType Directory -Path $root | Out-Null
$acl=[Security.AccessControl.DirectorySecurity]::new();$acl.SetOwner($id.User);$acl.SetAccessRuleProtection($true,$false)
$rule=[Security.AccessControl.FileSystemAccessRule]::new($id.User,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
$acl.AddAccessRule($rule);Set-Acl -LiteralPath $root -AclObject $acl
$observed=Get-Acl -LiteralPath $root;$rules=@($observed.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]))
if(-not $observed.AreAccessRulesProtected -or $rules.Count -ne 1 -or $rules[0].IdentityReference.Value -cne $id.User.Value){throw 'PRIVATE_ACL_READBACK'}
[pscustomobject]@{status='PRIVATE_ENGINEERING_OUTPUT_READY';resource_envelope_verified=$false}|ConvertTo-Json -Compress
