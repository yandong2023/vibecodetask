# VibeCodeTask Windows PowerShell 安装脚本
# 支持 Windows 10/11 和 Windows PowerShell/PowerShell Core
# 版本: 1.0.0

param(
    [Parameter(Position = 0)]
    [ValidateSet("install", "uninstall", "info", "help")]
    [string]$Action = "install",
    
    [switch]$Force,
    [switch]$Debug
)

# 错误处理
$ErrorActionPreference = "Stop"

# 配置变量
$SCRIPT_VERSION = "1.0.0"
$PROJECT_NAME = "VibeCodeTask"
$INSTALL_DIR = Join-Path $env:USERPROFILE ".vibecodetask"
$BIN_DIR = Join-Path $env:USERPROFILE ".local\bin"
$CONFIG_DIR = Join-Path $env:USERPROFILE ".config\vibecodetask"
$REPO_URL = "https://github.com/yourusername/vibecodetask"
$RAW_URL = "https://raw.githubusercontent.com/yourusername/vibecodetask/main"

# 颜色函数
function Write-ColorOutput {
    param(
        [Parameter(ValueFromPipeline = $true)]
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    
    if ($Host.UI.RawUI.ForegroundColor) {
        Write-Host $Message -ForegroundColor $ForegroundColor
    } else {
        Write-Host $Message
    }
}

function Write-Info { param($Message) Write-ColorOutput "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-ColorOutput "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-ColorOutput "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-ColorOutput "❌ $Message" -ForegroundColor Red }
function Write-Debug { param($Message) if ($Debug) { Write-ColorOutput "🔍 $Message" -ForegroundColor Gray } }

# 显示横幅
function Show-Banner {
    Write-ColorOutput @"
    ╦  ╦┬┌┐ ┌─┐╔═╗┌─┐┌┬┐┌─┐╔╦╗┌─┐┌─┐┬┌─
    ╚╗╔╝│├┴┐├┤ ║  │ │ ├┤ ║ ├─┤└─┐├┴┐
     ╚╝ ┴└─┘└─┘╚═╝└─┘─┴┘└─┘╩ ┴ ┴└─┘┴ ┴
"@ -ForegroundColor Magenta
    
    Write-ColorOutput "Claude Code 自动任务管理系统" -ForegroundColor Cyan
    Write-ColorOutput "版本: $SCRIPT_VERSION" -ForegroundColor Gray
    Write-Host ""
}

# 检测系统信息
function Get-SystemInfo {
    return @{
        OS = "$([System.Environment]::OSVersion.Platform) $([System.Environment]::OSVersion.Version)"
        Architecture = [System.Environment]::Is64BitOperatingSystem ? "x64" : "x86"
        PowerShellVersion = $PSVersionTable.PSVersion.ToString()
        User = $env:USERNAME
        ComputerName = $env:COMPUTERNAME
    }
}

# 检查命令是否存在
function Test-Command {
    param([string]$CommandName)
    
    try {
        Get-Command $CommandName -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# 检查网络连接
function Test-InternetConnection {
    Write-Info "检查网络连接..."
    
    try {
        $response = Invoke-WebRequest -Uri "https://www.google.com" -TimeoutSec 5 -Method Head
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

# 检查依赖
function Test-Dependencies {
    Write-Info "检查系统依赖..."
    
    $missingDeps = @()
    $optionalDeps = @()
    
    # 检查 Claude Code CLI
    if (-not (Test-Command "claude")) {
        Write-Error "Claude Code CLI 未安装"
        Write-Host ""
        Write-Host "请先安装 Claude Code CLI:"
        Write-Host "  访问: https://claude.ai/code"
        Write-Host "  或运行: npm install -g @anthropic-ai/claude-cli"
        Write-Host ""
        exit 1
    }
    
    if (-not (Test-Command "ccusage")) {
        Write-Warning "ccusage 命令不可用，可能影响额度检查功能"
    }
    
    # 检查可选依赖
    if (-not (Test-Command "git")) { $optionalDeps += "git" }
    if (-not (Test-Command "node")) { $optionalDeps += "node" }
    if (-not (Test-Command "python")) { $optionalDeps += "python" }
    
    if ($optionalDeps.Count -gt 0) {
        Write-Warning "建议安装可选依赖以获得更好体验: $($optionalDeps -join ', ')"
    }
    
    Write-Success "依赖检查通过"
}

# 创建目录结构
function New-DirectoryStructure {
    Write-Info "创建目录结构..."
    
    $dirs = @(
        $INSTALL_DIR,
        $BIN_DIR,
        $CONFIG_DIR,
        (Join-Path $INSTALL_DIR "logs"),
        (Join-Path $INSTALL_DIR "results"),
        (Join-Path $INSTALL_DIR "templates"),
        (Join-Path $INSTALL_DIR "examples")
    )
    
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Debug "创建目录: $dir"
        }
    }
    
    Write-Success "目录结构创建完成"
}

# 下载文件
function Get-FileFromUrl {
    param(
        [string]$Url,
        [string]$OutputPath,
        [string]$Description = "文件"
    )
    
    Write-Debug "下载 $Description`: $Url -> $OutputPath"
    
    try {
        Invoke-WebRequest -Uri $Url -OutFile $OutputPath -TimeoutSec 30
        return $true
    } catch {
        Write-Warning "下载失败: $Description"
        return $false
    }
}

# 下载项目文件
function Get-ProjectFiles {
    Write-Info "下载项目文件..."
    
    # 核心文件
    $files = @(
        @{ Name = "vct.py"; Description = "Python单文件版本" },
        @{ Name = "package.json"; Description = "Node.js配置文件" }
    )
    
    foreach ($file in $files) {
        $url = "$RAW_URL/$($file.Name)"
        $output = Join-Path $INSTALL_DIR $file.Name
        
        if (Get-FileFromUrl $url $output $file.Description) {
            Write-Success "已下载: $($file.Name)"
        }
    }
    
    # 配置模板
    $templates = @(
        @{ Path = "config/tasks.example.json"; Description = "任务配置模板" },
        @{ Path = "config/settings.example.json"; Description = "系统设置模板" },
        @{ Path = "templates/development.yaml"; Description = "开发任务模板" },
        @{ Path = "templates/testing.yaml"; Description = "测试任务模板" },
        @{ Path = "templates/documentation.yaml"; Description = "文档模板" }
    )
    
    foreach ($template in $templates) {
        $url = "$RAW_URL/$($template.Path)"
        $output = Join-Path $INSTALL_DIR $template.Path
        $dir = Split-Path $output -Parent
        
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        
        if (Get-FileFromUrl $url $output $template.Description) {
            Write-Success "已下载: $(Split-Path $template.Path -Leaf)"
        }
    }
    
    # 示例文件
    $examples = @(
        @{ Path = "examples/simple-task.json"; Description = "简单任务示例" },
        @{ Path = "examples/web-development.json"; Description = "Web开发示例" },
        @{ Path = "examples/learning-plan.json"; Description = "学习计划示例" }
    )
    
    foreach ($example in $examples) {
        $url = "$RAW_URL/$($example.Path)"
        $output = Join-Path $INSTALL_DIR $example.Path
        
        if (Get-FileFromUrl $url $output $example.Description) {
            Write-Success "已下载: $(Split-Path $example.Path -Leaf)"
        }
    }
    
    Write-Success "项目文件下载完成"
}

# 创建备用文件
function New-FallbackFiles {
    Write-Info "创建备用文件..."
    
    # 创建简化版 PowerShell 脚本
    $psScript = @'
# VibeCodeTask PowerShell 版本
param(
    [Parameter(Position = 0)]
    [string]$TaskDescription,
    [string]$ConfigFile = "vct-tasks.json"
)

function Execute-ClaudeTask {
    param([string]$Task)
    
    Write-Host "🚀 执行任务: $Task" -ForegroundColor Green
    
    $optimizedPrompt = @"
任务: $Task

请分步骤完成此任务:
1. 分析需求
2. 制定方案
3. 实现功能
4. 测试验证

每完成一步请输出进度，最后提供执行总结。
"@
    
    try {
        $result = & claude $optimizedPrompt
        Write-Host "✅ 任务执行成功" -ForegroundColor Green
        Write-Host "结果预览:" -ForegroundColor Cyan
        $preview = $result | Out-String
        if ($preview.Length -gt 500) {
            Write-Host ($preview.Substring(0, 500) + "...")
        } else {
            Write-Host $preview
        }
    } catch {
        Write-Host "❌ 任务执行失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Show-Help {
    Write-Host "VibeCodeTask PowerShell 版本" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "用法:"
    Write-Host "  .\vct.ps1 <任务描述>                    - 执行任务"
    Write-Host "  .\vct.ps1 -ConfigFile tasks.json       - 指定配置文件"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\vct.ps1 '创建一个计算器程序'"
    Write-Host ""
}

# 主逻辑
if (-not $TaskDescription) {
    Show-Help
} else {
    Execute-ClaudeTask $TaskDescription
}
'@
    
    $psScript | Out-File -FilePath (Join-Path $INSTALL_DIR "vct.ps1") -Encoding UTF8
    
    # 创建简化配置
    $simpleConfig = @{
        tasks = @(
            @{
                id = "example"
                name = "示例任务"
                requirements = "这是一个示例任务，请替换为您的实际需求"
                priority = 1
                type = "development"
            }
        )
        settings = @{
            maxConcurrent = 1
            checkInterval = 300000
        }
    } | ConvertTo-Json -Depth 10
    
    $simpleConfig | Out-File -FilePath (Join-Path $INSTALL_DIR "simple_tasks.json") -Encoding UTF8
    
    Write-Success "备用文件创建完成"
}

# 创建启动器
function New-Launcher {
    Write-Info "创建启动器..."
    
    # 创建批处理文件
    $batchContent = @"
@echo off
setlocal enabledelayedexpansion

set "VCT_DIR=%USERPROFILE%\.vibecodetask"

REM 显示帮助
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help
if "%1"=="" goto :show_help

REM 检查 Claude Code
where claude >nul 2>&1
if errorlevel 1 (
    echo ❌ Claude Code CLI 未安装
    echo 请访问 https://claude.ai/code 获取安装说明
    exit /b 1
)

REM 选择实现
if exist "%VCT_DIR%\vct.ps1" (
    powershell -ExecutionPolicy Bypass -File "%VCT_DIR%\vct.ps1" %*
) else if exist "%VCT_DIR%\vct.py" (
    python "%VCT_DIR%\vct.py" %*
) else (
    echo ❌ 未找到可用的 VibeCodeTask 实现
    echo 请重新运行安装脚本
    exit /b 1
)

goto :eof

:show_help
echo VibeCodeTask - Claude Code 自动任务管理系统
echo.
echo 使用方法:
echo   vct ^<任务描述^>           - 直接执行任务
echo   vct --help              - 显示帮助
echo.
echo 示例:
echo   vct "创建一个 React 应用"
echo.
"@
    
    $batchContent | Out-File -FilePath (Join-Path $BIN_DIR "vct.bat") -Encoding ASCII
    
    Write-Success "启动器创建完成"
}

# 配置环境变量
function Set-EnvironmentPath {
    Write-Info "配置环境变量..."
    
    # 获取当前用户的 PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    
    # 检查是否已经包含 BIN_DIR
    if ($currentPath -notlike "*$BIN_DIR*") {
        $newPath = "$BIN_DIR;$currentPath"
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        Write-Success "已更新用户 PATH 环境变量"
        
        # 更新当前会话的 PATH
        $env:PATH = "$BIN_DIR;$env:PATH"
    } else {
        Write-Debug "PATH 环境变量已包含 $BIN_DIR"
    }
}

# 创建默认配置
function New-DefaultConfig {
    Write-Info "创建默认配置..."
    
    $configFile = Join-Path $env:USERPROFILE "vct-tasks.json"
    
    if (-not (Test-Path $configFile)) {
        $examplePath = Join-Path $INSTALL_DIR "examples\simple-task.json"
        
        if (Test-Path $examplePath) {
            Copy-Item $examplePath $configFile
        } else {
            # 创建基本配置
            $defaultConfig = @{
                tasks = @(
                    @{
                        id = "hello-world"
                        name = "创建 Hello World 程序"
                        priority = 1
                        type = "development"
                        requirements = "创建一个简单的 Hello World 程序，选择合适的编程语言"
                        schedule = "immediate"
                    }
                )
                settings = @{
                    maxConcurrent = 1
                    checkInterval = 300000
                }
            } | ConvertTo-Json -Depth 10
            
            $defaultConfig | Out-File -FilePath $configFile -Encoding UTF8
        }
        
        Write-Success "默认配置已创建: $configFile"
    } else {
        Write-Debug "配置文件已存在: $configFile"
    }
}

# 测试安装
function Test-Installation {
    Write-Info "测试安装..."
    
    # 测试启动器
    $launcherPath = Join-Path $BIN_DIR "vct.bat"
    if (Test-Path $launcherPath) {
        Write-Success "启动器安装成功"
    } else {
        Write-Warning "启动器未正确安装"
        return $false
    }
    
    # 测试 Claude Code
    if (Test-Command "claude") {
        Write-Success "Claude Code CLI 可用"
    } else {
        Write-Warning "Claude Code CLI 不可用"
    }
    
    return $true
}

# 显示安装后信息
function Show-PostInstallInfo {
    Write-Host ""
    Write-Success "🎉 安装完成！"
    Write-Host ""
    
    Write-ColorOutput "📋 后续步骤:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. 重新启动 PowerShell 或命令提示符"
    Write-Host ""
    Write-Host "2. 测试安装:"
    Write-ColorOutput "   vct --help" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. 编辑配置文件:"
    Write-ColorOutput "   notepad $env:USERPROFILE\vct-tasks.json" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. 运行示例任务:"
    Write-ColorOutput '   vct "创建一个简单的计算器程序"' -ForegroundColor Gray
    Write-Host ""
    Write-Host "5. 获取更多帮助:"
    Write-ColorOutput "   访问: https://github.com/yourusername/vibecodetask" -ForegroundColor Gray
    Write-Host ""
    Write-ColorOutput "💡 提示:" -ForegroundColor Yellow
    Write-Host "确保已安装并配置 Claude Code CLI"
    Write-ColorOutput "访问: https://claude.ai/code" -ForegroundColor Gray
    Write-Host ""
}

# 卸载函数
function Uninstall-VibeCodeTask {
    Write-Info "开始卸载 $PROJECT_NAME..."
    
    # 询问确认
    $confirm = Read-Host "确定要卸载 $PROJECT_NAME 吗? (y/N)"
    
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Info "取消卸载"
        return
    }
    
    # 删除安装目录
    if (Test-Path $INSTALL_DIR) {
        Remove-Item $INSTALL_DIR -Recurse -Force
        Write-Success "已删除安装目录: $INSTALL_DIR"
    }
    
    # 删除启动脚本
    $launcherPath = Join-Path $BIN_DIR "vct.bat"
    if (Test-Path $launcherPath) {
        Remove-Item $launcherPath -Force
        Write-Success "已删除启动脚本: $launcherPath"
    }
    
    # 删除配置目录
    if (Test-Path $CONFIG_DIR) {
        Remove-Item $CONFIG_DIR -Recurse -Force
        Write-Success "已删除配置目录: $CONFIG_DIR"
    }
    
    Write-Success "🗑️  卸载完成"
    Write-Host ""
    Write-ColorOutput "注意:" -ForegroundColor Yellow
    Write-Host "以下文件未被删除，如需完全清理请手动删除:"
    Write-Host "  - 用户配置: $env:USERPROFILE\vct-tasks.json"
    Write-Host "  - 环境变量中的 PATH 设置"
    Write-Host "  - 任务结果和日志文件"
}

# 显示系统信息
function Show-SystemInfo {
    $sysInfo = Get-SystemInfo
    
    Write-ColorOutput "📊 系统信息:" -ForegroundColor Cyan
    Write-Host "  操作系统: $($sysInfo.OS)"
    Write-Host "  架构: $($sysInfo.Architecture)"
    Write-Host "  PowerShell: $($sysInfo.PowerShellVersion)"
    Write-Host "  用户: $($sysInfo.User)"
    Write-Host "  计算机: $($sysInfo.ComputerName)"
    Write-Host ""
    
    Write-ColorOutput "📁 安装路径:" -ForegroundColor Cyan
    Write-Host "  安装目录: $INSTALL_DIR"
    Write-Host "  可执行文件: $BIN_DIR"
    Write-Host "  配置目录: $CONFIG_DIR"
    Write-Host ""
    
    Write-ColorOutput "🔧 依赖检查:" -ForegroundColor Cyan
    $commands = @("git", "node", "python", "claude", "ccusage")
    foreach ($cmd in $commands) {
        if (Test-Command $cmd) {
            $path = (Get-Command $cmd -ErrorAction SilentlyContinue).Source
            Write-Host "  ✅ $cmd`: $path"
        } else {
            Write-Host "  ❌ $cmd`: 未安装"
        }
    }
}

# 主安装函数
function Install-VibeCodeTask {
    Write-Info "开始安装 $PROJECT_NAME..."
    
    # 检查网络连接
    $hasInternet = Test-InternetConnection
    if (-not $hasInternet) {
        Write-Warning "网络连接不稳定，将使用本地备用方案"
    }
    
    # 系统检查
    $sysInfo = Get-SystemInfo
    Write-Info "检测到系统: $($sysInfo.OS)"
    
    # 依赖检查
    Test-Dependencies
    
    # 创建目录
    New-DirectoryStructure
    
    # 下载文件（如果网络可用）
    if ($hasInternet) {
        try {
            Get-ProjectFiles
        } catch {
            Write-Warning "部分文件下载失败，将创建备用文件"
        }
    } else {
        Write-Warning "跳过网络下载，创建本地备用文件"
    }
    
    # 创建备用文件
    New-FallbackFiles
    
    # 创建启动器
    New-Launcher
    
    # 配置环境
    Set-EnvironmentPath
    
    # 创建配置
    New-DefaultConfig
    
    # 测试安装
    if (Test-Installation) {
        Write-Success "安装测试通过"
    } else {
        Write-Warning "安装测试部分失败，但基本功能应该可用"
    }
    
    # 显示后续说明
    Show-PostInstallInfo
}

# 显示帮助
function Show-Help {
    Show-Banner
    Write-Host "用法: .\install.ps1 [命令] [选项]"
    Write-Host ""
    Write-Host "命令:"
    Write-Host "  install    - 安装 VibeCodeTask (默认)"
    Write-Host "  uninstall  - 卸载 VibeCodeTask"  
    Write-Host "  info       - 显示系统信息"
    Write-Host "  help       - 显示帮助"
    Write-Host ""
    Write-Host "选项:"
    Write-Host "  -Force     - 强制覆盖现有安装"
    Write-Host "  -Debug     - 启用调试输出"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\install.ps1"
    Write-Host "  .\install.ps1 install -Force"
    Write-Host "  .\install.ps1 uninstall"
    Write-Host ""
}

# 主函数
function Main {
    switch ($Action.ToLower()) {
        "install" {
            Show-Banner
            Install-VibeCodeTask
        }
        "uninstall" {
            Show-Banner
            Uninstall-VibeCodeTask
        }
        "info" {
            Show-Banner
            Show-SystemInfo
        }
        "help" {
            Show-Help
        }
        default {
            Write-Error "未知命令: $Action"
            Show-Help
            exit 1
        }
    }
}

# 执行主函数
try {
    Main
} catch {
    Write-Error "安装过程中出现错误: $($_.Exception.Message)"
    Write-Debug $_.Exception.StackTrace
    exit 1
}