# 创建备份脚本
param()

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Level, [string]$Message)
    Write-Host "[$Level] $Message"
}

try {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $filename = "openclaw-backup-$timestamp.zip"
    $backupDir = "..\backup"
    $backupPath = "$backupDir\$filename"

    # 确保备份目录存在
    if (!(Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    }

    Write-Log "INFO" "创建备份: $filename"

    # 获取实例数量
    $instancesDir = "..\instances"
    $instanceCount = 0
    if (Test-Path $instancesDir) {
        $instanceCount = (Get-ChildItem -Path $instancesDir -Directory).Count
    }

    # 创建临时压缩
    $tempZip = "$env:TEMP\$filename"

    # 压缩 instances 目录
    if (Test-Path $instancesDir) {
        Compress-Archive -Path "$instancesDir\*" -DestinationPath $tempZip -Force
        Write-Log "INFO" "备份实例数据"
    }

    # 压缩数据库
    $dbPath = "..\backend\data\openclaw.db"
    if (Test-Path $dbPath) {
        Compress-Archive -Path $dbPath -DestinationPath $tempZip -Update
        Write-Log "INFO" "备份数据库"
    }

    # 移动到备份目录
    Move-Item -Path $tempZip -Destination $backupPath -Force

    $fileSize = (Get-Item $backupPath).Length

    Write-Log "SUCCESS" "备份完成: $backupPath"

    @{
        success = $true
        filename = $filename
        path = $backupPath
        size = $fileSize
        instanceCount = $instanceCount
        createdAt = Get-Date -Format "o"
    } | ConvertTo-Json

} catch {
    Write-Log "ERROR" $_.Exception.Message
    @{
        success = $false
        error = $_.Exception.Message
    } | ConvertTo-Json
    exit 1
}
