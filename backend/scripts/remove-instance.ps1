# 删除实例脚本
param(
    [Parameter(Mandatory=$true)]
    [string]$InstanceId,

    [switch]$KeepData
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Level, [string]$Message)
    Write-Host "[$Level] $Message"
}

try {
    # 停止并删除容器
    $containerName = "openclaw-$InstanceId"

    Write-Log "INFO" "停止容器: $containerName"
    docker stop $containerName 2>$null

    Write-Log "INFO" "删除容器: $containerName"
    docker rm $containerName 2>$null

    # 删除数据目录（如果不保留）
    if (!$KeepData) {
        $instancePath = "..\instances\$InstanceId"
        if (Test-Path $instancePath) {
            Remove-Item -Path $instancePath -Recurse -Force
            Write-Log "INFO" "删除数据目录: $instancePath"
        }
    }

    Write-Log "SUCCESS" "实例 $InstanceId 删除成功"

    @{
        success = $true
        instanceId = $InstanceId
        keepData = $KeepData.IsPresent
    } | ConvertTo-Json

} catch {
    Write-Log "ERROR" $_.Exception.Message
    @{
        success = $false
        error = $_.Exception.Message
    } | ConvertTo-Json
    exit 1
}
