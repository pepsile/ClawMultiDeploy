# 添加实例脚本（由后端调用）
param(
    [Parameter(Mandatory=$true)]
    [string]$InstanceId,

    [Parameter(Mandatory=$true)]
    [string]$InstanceName,

    [Parameter(Mandatory=$true)]
    [int]$Port
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Level, [string]$Message)
    Write-Host "[$Level] $Message"
}

try {
    # 创建目录结构
    $basePath = "..\instances\$InstanceId"
    $dataPath = "$basePath\data"
    $logsPath = "$basePath\logs"

    if (!(Test-Path $dataPath)) {
        New-Item -ItemType Directory -Path $dataPath -Force | Out-Null
        Write-Log "INFO" "创建数据目录: $dataPath"
    }

    if (!(Test-Path $logsPath)) {
        New-Item -ItemType Directory -Path $logsPath -Force | Out-Null
        Write-Log "INFO" "创建日志目录: $logsPath"
    }

    # 创建默认配置文件
    $configPath = "$dataPath\openclaw.json"
    $defaultConfig = @{
        gateway = @{
            mode = "local"
            token = ""
            port = 18789
        }
        agents = @{
            defaults = @{
                model = "gpt-4"
                sandbox = @{
                    mode = "non-main"
                    scope = "agent"
                }
            }
        }
        channels = @()
        tools = @{
            defaults = @("*")
        }
    } | ConvertTo-Json -Depth 10

    $defaultConfig | Out-File -FilePath $configPath -Encoding UTF8
    Write-Log "INFO" "创建配置文件: $configPath"

    # 输出成功信息
    Write-Log "SUCCESS" "实例 $InstanceId 创建成功"

    # 返回 JSON 格式的结果
    @{
        success = $true
        instanceId = $InstanceId
        port = $Port
        dataPath = $dataPath
        logsPath = $logsPath
    } | ConvertTo-Json

} catch {
    Write-Log "ERROR" $_.Exception.Message
    @{
        success = $false
        error = $_.Exception.Message
    } | ConvertTo-Json
    exit 1
}
