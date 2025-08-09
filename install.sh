#!/bin/bash

# VibeCodeTask 一键安装脚本
# 支持 macOS, Linux, Windows (WSL)
# 版本: 1.0.0

set -euo pipefail

# 配置变量
readonly SCRIPT_VERSION="1.0.0"
readonly PROJECT_NAME="VibeCodeTask"
readonly INSTALL_DIR="$HOME/.vibecodetask"
readonly BIN_DIR="$HOME/.local/bin"
readonly CONFIG_DIR="$HOME/.config/vibecodetask"
readonly REPO_URL="https://github.com/yourusername/vibecodetask"
readonly RAW_URL="https://raw.githubusercontent.com/yourusername/vibecodetask/main"

# 颜色定义
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly GRAY='\033[0;37m'
readonly NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_debug() { [[ "${DEBUG:-}" == "1" ]] && echo -e "${GRAY}🔍 $1${NC}"; }

# 显示横幅
show_banner() {
    echo -e "${PURPLE}"
    cat << 'EOF'
    ╦  ╦┬┌┐ ┌─┐╔═╗┌─┐┌┬┐┌─┐╔╦╗┌─┐┌─┐┬┌─
    ╚╗╔╝│├┴┐├┤ ║  │ │ ├┤ ║ ├─┤└─┐├┴┐
     ╚╝ ┴└─┘└─┘╚═╝└─┘─┴┘└─┘╩ ┴ ┴└─┘┴ ┴
EOF
    echo -e "${NC}"
    echo -e "${CYAN}Claude Code 自动任务管理系统${NC}"
    echo -e "${GRAY}版本: ${SCRIPT_VERSION}${NC}"
    echo
}

# 检测系统信息
detect_system() {
    local os_name arch
    os_name=$(uname -s)
    arch=$(uname -m)
    
    case "$os_name" in
        "Darwin")
            echo "macos-$arch"
            ;;
        "Linux")
            # 检查是否为 WSL
            if grep -qi "microsoft" /proc/version 2>/dev/null; then
                echo "wsl-$arch"
            else
                echo "linux-$arch"
            fi
            ;;
        "MINGW"*|"CYGWIN"*|"MSYS"*)
            echo "windows-$arch"
            ;;
        *)
            echo "unknown-$arch"
            ;;
    esac
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查网络连接
check_internet() {
    log_info "检查网络连接..."
    
    if command_exists curl; then
        if curl -s --connect-timeout 5 https://www.google.com >/dev/null; then
            return 0
        fi
    elif command_exists wget; then
        if wget -q --spider --timeout=5 https://www.google.com; then
            return 0
        fi
    fi
    
    return 1
}

# 检查必要依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    local missing_deps=()
    local optional_deps=()
    
    # 必要依赖
    if ! command_exists curl && ! command_exists wget; then
        missing_deps+=("curl 或 wget")
    fi
    
    # Claude Code CLI 检查
    if ! command_exists claude; then
        log_error "Claude Code CLI 未安装"
        echo
        echo "请先安装 Claude Code CLI:"
        echo "  访问: https://claude.ai/code"
        echo "  或运行: npm install -g @anthropic-ai/claude-cli"
        echo
        exit 1
    fi
    
    if ! command_exists ccusage; then
        log_warning "ccusage 命令不可用，可能影响额度检查功能"
    fi
    
    # 可选依赖检查
    command_exists git || optional_deps+=("git")
    command_exists node || optional_deps+=("node")
    command_exists python3 || optional_deps+=("python3")
    command_exists jq || optional_deps+=("jq")
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "缺少必要依赖: ${missing_deps[*]}"
        exit 1
    fi
    
    if [[ ${#optional_deps[@]} -gt 0 ]]; then
        log_warning "建议安装可选依赖以获得更好体验: ${optional_deps[*]}"
    fi
    
    log_success "依赖检查通过"
}

# 创建目录结构
create_directories() {
    log_info "创建目录结构..."
    
    local dirs=(
        "$INSTALL_DIR"
        "$BIN_DIR"
        "$CONFIG_DIR"
        "$INSTALL_DIR/logs"
        "$INSTALL_DIR/results"
        "$INSTALL_DIR/templates"
        "$INSTALL_DIR/examples"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_debug "创建目录: $dir"
        fi
    done
    
    log_success "目录结构创建完成"
}

# 下载文件
download_file() {
    local url="$1"
    local output="$2"
    local description="${3:-文件}"
    
    log_debug "下载 $description: $url -> $output"
    
    if command_exists curl; then
        curl -fsSL "$url" -o "$output"
    elif command_exists wget; then
        wget -q "$url" -O "$output"
    else
        log_error "未找到下载工具 (curl 或 wget)"
        return 1
    fi
}

# 下载项目文件
download_project_files() {
    log_info "下载项目文件..."
    
    # 核心文件列表
    local files=(
        "vct.py:Python单文件版本"
        "vct.sh:Shell脚本版本"
        "package.json:Node.js配置文件"
    )
    
    # 下载核心文件
    for file_info in "${files[@]}"; do
        IFS=':' read -r filename description <<< "$file_info"
        
        if download_file "$RAW_URL/$filename" "$INSTALL_DIR/$filename" "$description"; then
            chmod +x "$INSTALL_DIR/$filename" 2>/dev/null || true
            log_success "已下载: $filename"
        else
            log_warning "下载失败: $filename (将使用备用方案)"
        fi
    done
    
    # 下载配置模板
    local templates=(
        "config/tasks.example.json:任务配置模板"
        "config/settings.example.json:系统设置模板"
        "templates/development.yaml:开发任务模板"
        "templates/testing.yaml:测试任务模板"
        "templates/documentation.yaml:文档模板"
    )
    
    for template_info in "${templates[@]}"; do
        IFS=':' read -r filepath description <<< "$template_info"
        local filename=$(basename "$filepath")
        local target_dir=$(dirname "$INSTALL_DIR/$filepath")
        
        mkdir -p "$target_dir"
        
        if download_file "$RAW_URL/$filepath" "$INSTALL_DIR/$filepath" "$description"; then
            log_success "已下载: $filename"
        else
            log_warning "下载失败: $filename"
        fi
    done
    
    # 下载示例文件
    local examples=(
        "examples/simple-task.json:简单任务示例"
        "examples/web-development.json:Web开发示例"
        "examples/learning-plan.json:学习计划示例"
    )
    
    for example_info in "${examples[@]}"; do
        IFS=':' read -r filepath description <<< "$example_info"
        local filename=$(basename "$filepath")
        
        if download_file "$RAW_URL/$filepath" "$INSTALL_DIR/$filepath" "$description"; then
            log_success "已下载: $filename"
        else
            log_warning "下载失败: $filename"
        fi
    done
    
    log_success "项目文件下载完成"
}

# 创建本地备用文件
create_fallback_files() {
    log_info "创建备用文件..."
    
    # 创建简化版 Python 脚本
    cat > "$INSTALL_DIR/vct_simple.py" << 'PYTHON_EOF'
#!/usr/bin/env python3
"""VibeCodeTask 简化版本"""

import subprocess
import sys
import json
import os
from datetime import datetime

def execute_claude_task(task_description):
    """执行 Claude 任务"""
    print(f"🚀 执行任务: {task_description}")
    
    # 优化提示词
    optimized_prompt = f"""
任务: {task_description}

请分步骤完成此任务:
1. 分析需求
2. 制定方案
3. 实现功能
4. 测试验证

每完成一步请输出进度，最后提供执行总结。
"""
    
    try:
        # 执行 Claude 命令
        result = subprocess.run(
            ['claude', optimized_prompt],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ 任务执行成功")
            print("结果预览:")
            print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        else:
            print(f"❌ 任务执行失败: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏱️ 任务执行超时")
    except Exception as e:
        print(f"❌ 执行出错: {e}")

def main():
    if len(sys.argv) < 2:
        print("用法: python3 vct_simple.py <任务描述>")
        print("示例: python3 vct_simple.py '创建一个计算器程序'")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    execute_claude_task(task)

if __name__ == "__main__":
    main()
PYTHON_EOF
    
    chmod +x "$INSTALL_DIR/vct_simple.py"
    
    # 创建简化配置
    cat > "$INSTALL_DIR/simple_tasks.json" << 'JSON_EOF'
{
  "tasks": [
    {
      "id": "example",
      "name": "示例任务",
      "requirements": "这是一个示例任务，请替换为您的实际需求",
      "priority": 1,
      "type": "development"
    }
  ],
  "settings": {
    "maxConcurrent": 1,
    "checkInterval": 300000
  }
}
JSON_EOF
    
    log_success "备用文件创建完成"
}

# 创建启动器脚本
create_launcher() {
    log_info "创建启动器..."
    
    cat > "$BIN_DIR/vct" << 'LAUNCHER_EOF'
#!/bin/bash

# VibeCodeTask 启动器
# 自动选择最佳实现

VCT_DIR="$HOME/.vibecodetask"

# 显示帮助
show_help() {
    echo "VibeCodeTask - Claude Code 自动任务管理系统"
    echo
    echo "使用方法:"
    echo "  vct <任务描述>           - 直接执行任务"
    echo "  vct run [配置文件]       - 运行任务管理器"
    echo "  vct status              - 显示系统状态"
    echo "  vct init                - 初始化配置"
    echo "  vct --help              - 显示帮助"
    echo
    echo "示例:"
    echo "  vct '创建一个 React 应用'"
    echo "  vct run tasks.json"
    echo
}

# 检查 Claude Code
check_claude() {
    if ! command -v claude &> /dev/null; then
        echo "❌ Claude Code CLI 未安装"
        echo "请访问 https://claude.ai/code 获取安装说明"
        exit 1
    fi
}

# 选择实现
select_implementation() {
    # 优先级: Node.js > Python > Shell > 简化版
    if [[ -f "$VCT_DIR/src/index.js" ]] && command -v node &> /dev/null; then
        echo "nodejs"
    elif [[ -f "$VCT_DIR/vct.py" ]] && command -v python3 &> /dev/null; then
        echo "python"
    elif [[ -f "$VCT_DIR/vct.sh" ]]; then
        echo "shell"
    elif [[ -f "$VCT_DIR/vct_simple.py" ]] && command -v python3 &> /dev/null; then
        echo "simple"
    else
        echo "none"
    fi
}

# 执行实现
execute_implementation() {
    local impl="$1"
    shift
    
    case "$impl" in
        "nodejs")
            exec node "$VCT_DIR/src/index.js" "$@"
            ;;
        "python")
            exec python3 "$VCT_DIR/vct.py" "$@"
            ;;
        "shell")
            exec bash "$VCT_DIR/vct.sh" "$@"
            ;;
        "simple")
            if [[ $# -eq 0 || "$1" == "--help" || "$1" == "-h" ]]; then
                show_help
            else
                exec python3 "$VCT_DIR/vct_simple.py" "$@"
            fi
            ;;
        *)
            echo "❌ 未找到可用的 VibeCodeTask 实现"
            echo "请重新运行安装脚本或检查安装是否完整"
            exit 1
            ;;
    esac
}

# 主逻辑
main() {
    # 处理帮助参数
    if [[ $# -eq 0 || "$1" == "--help" || "$1" == "-h" ]]; then
        show_help
        exit 0
    fi
    
    # 检查 Claude Code
    check_claude
    
    # 选择并执行实现
    local impl=$(select_implementation)
    execute_implementation "$impl" "$@"
}

main "$@"
LAUNCHER_EOF
    
    chmod +x "$BIN_DIR/vct"
    log_success "启动器创建完成"
}

# 配置 Shell 环境
configure_shell() {
    log_info "配置 Shell 环境..."
    
    # 检测 Shell 类型
    local shell_config=""
    if [[ -n "${BASH_VERSION:-}" ]]; then
        shell_config="$HOME/.bashrc"
    elif [[ -n "${ZSH_VERSION:-}" ]]; then
        shell_config="$HOME/.zshrc"
    elif [[ "$SHELL" == *"fish"* ]]; then
        shell_config="$HOME/.config/fish/config.fish"
    else
        shell_config="$HOME/.profile"
    fi
    
    log_debug "使用配置文件: $shell_config"
    
    # 添加 PATH
    if [[ ! -d "$BIN_DIR" ]]; then
        mkdir -p "$BIN_DIR"
    fi
    
    # 检查是否已经添加了 PATH
    if ! grep -q "$BIN_DIR" "$shell_config" 2>/dev/null; then
        echo "" >> "$shell_config"
        echo "# VibeCodeTask PATH" >> "$shell_config"
        
        if [[ "$shell_config" == *"fish"* ]]; then
            echo "set -gx PATH $BIN_DIR \$PATH" >> "$shell_config"
        else
            echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$shell_config"
        fi
        
        log_success "已更新 PATH: $shell_config"
    else
        log_debug "PATH 已存在于 $shell_config"
    fi
    
    # 添加便捷别名
    if ! grep -q "alias vct-status" "$shell_config" 2>/dev/null; then
        echo "" >> "$shell_config"
        echo "# VibeCodeTask 别名" >> "$shell_config"
        
        if [[ "$shell_config" == *"fish"* ]]; then
            echo "alias vct-status='vct status'" >> "$shell_config"
            echo "alias vct-init='vct init'" >> "$shell_config"
            echo "alias vct-help='vct --help'" >> "$shell_config"
        else
            echo "alias vct-status='vct status'" >> "$shell_config"
            echo "alias vct-init='vct init'" >> "$shell_config"
            echo "alias vct-help='vct --help'" >> "$shell_config"
        fi
        
        log_success "已添加便捷别名"
    fi
    
    # 设置环境变量
    export PATH="$BIN_DIR:$PATH"
}

# 创建默认配置
create_default_config() {
    log_info "创建默认配置..."
    
    local config_file="$HOME/vct-tasks.json"
    
    if [[ ! -f "$config_file" ]]; then
        cp "$INSTALL_DIR/examples/simple-task.json" "$config_file" 2>/dev/null || {
            cat > "$config_file" << 'CONFIG_EOF'
{
  "tasks": [
    {
      "id": "hello-world",
      "name": "创建 Hello World 程序",
      "priority": 1,
      "type": "development",
      "requirements": "创建一个简单的 Hello World 程序，选择合适的编程语言",
      "schedule": "immediate"
    }
  ],
  "settings": {
    "maxConcurrent": 1,
    "checkInterval": 300000
  }
}
CONFIG_EOF
        }
        
        log_success "默认配置已创建: $config_file"
    else
        log_debug "配置文件已存在: $config_file"
    fi
}

# 测试安装
test_installation() {
    log_info "测试安装..."
    
    # 测试启动器
    if [[ -x "$BIN_DIR/vct" ]]; then
        if "$BIN_DIR/vct" --help >/dev/null 2>&1; then
            log_success "启动器测试通过"
        else
            log_warning "启动器测试失败，但文件存在"
        fi
    else
        log_error "启动器未正确安装"
        return 1
    fi
    
    # 测试 Claude Code
    if command -v claude >/dev/null 2>&1; then
        log_success "Claude Code CLI 可用"
    else
        log_warning "Claude Code CLI 不可用"
    fi
    
    return 0
}

# 显示安装后的说明
show_post_install_info() {
    echo
    log_success "🎉 安装完成！"
    echo
    echo -e "${CYAN}📋 后续步骤:${NC}"
    echo
    echo "1. 重新启动终端或运行以下命令:"
    echo -e "   ${GRAY}source ~/.bashrc${NC}  (bash用户)"
    echo -e "   ${GRAY}source ~/.zshrc${NC}   (zsh用户)"
    echo
    echo "2. 测试安装:"
    echo -e "   ${GRAY}vct --help${NC}"
    echo
    echo "3. 编辑配置文件:"
    echo -e "   ${GRAY}nano ~/vct-tasks.json${NC}"
    echo
    echo "4. 运行示例任务:"
    echo -e "   ${GRAY}vct '创建一个简单的计算器程序'${NC}"
    echo
    echo "5. 查看系统状态:"
    echo -e "   ${GRAY}vct status${NC}"
    echo
    echo -e "${CYAN}📖 更多帮助:${NC}"
    echo -e "   文档: ${GRAY}https://github.com/yourusername/vibecodetask${NC}"
    echo -e "   问题: ${GRAY}https://github.com/yourusername/vibecodetask/issues${NC}"
    echo
    echo -e "${YELLOW}💡 提示:${NC} 确保已安装并配置 Claude Code CLI"
    echo -e "   访问: ${GRAY}https://claude.ai/code${NC}"
    echo
}

# 卸载函数
uninstall() {
    log_info "开始卸载 $PROJECT_NAME..."
    
    # 询问确认
    echo -n "确定要卸载 $PROJECT_NAME 吗? (y/N): "
    read -r confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "取消卸载"
        exit 0
    fi
    
    # 删除安装目录
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        log_success "已删除安装目录: $INSTALL_DIR"
    fi
    
    # 删除启动脚本
    if [[ -f "$BIN_DIR/vct" ]]; then
        rm -f "$BIN_DIR/vct"
        log_success "已删除启动脚本: $BIN_DIR/vct"
    fi
    
    # 删除配置目录
    if [[ -d "$CONFIG_DIR" ]]; then
        rm -rf "$CONFIG_DIR"
        log_success "已删除配置目录: $CONFIG_DIR"
    fi
    
    log_success "🗑️  卸载完成"
    echo
    echo -e "${YELLOW}注意:${NC} 以下文件未被删除，如需完全清理请手动删除:"
    echo "  - 用户配置: ~/vct-tasks.json"
    echo "  - Shell 配置中的 PATH 和别名"
    echo "  - 任务结果和日志文件"
}

# 显示系统信息
show_system_info() {
    local system=$(detect_system)
    
    echo -e "${CYAN}📊 系统信息:${NC}"
    echo "  操作系统: $system"
    echo "  Shell: ${SHELL##*/}"
    echo "  用户: $(whoami)"
    echo "  主目录: $HOME"
    echo
    echo -e "${CYAN}📁 安装路径:${NC}"
    echo "  安装目录: $INSTALL_DIR"
    echo "  可执行文件: $BIN_DIR"
    echo "  配置目录: $CONFIG_DIR"
    echo
    echo -e "${CYAN}🔧 依赖检查:${NC}"
    
    local deps=("curl" "wget" "git" "node" "python3" "claude" "ccusage" "jq")
    for cmd in "${deps[@]}"; do
        if command_exists "$cmd"; then
            echo "  ✅ $cmd: $(command -v "$cmd")"
        else
            echo "  ❌ $cmd: 未安装"
        fi
    done
}

# 主安装函数
install() {
    log_info "开始安装 $PROJECT_NAME..."
    
    # 检查网络连接
    if ! check_internet; then
        log_warning "网络连接不稳定，将使用本地备用方案"
    fi
    
    # 系统检查
    local system=$(detect_system)
    log_info "检测到系统: $system"
    
    # 依赖检查
    check_dependencies
    
    # 创建目录
    create_directories
    
    # 下载文件（如果网络可用）
    if check_internet; then
        download_project_files || log_warning "部分文件下载失败，将创建备用文件"
    else
        log_warning "跳过网络下载，创建本地备用文件"
    fi
    
    # 创建备用文件
    create_fallback_files
    
    # 创建启动器
    create_launcher
    
    # 配置环境
    configure_shell
    
    # 创建配置
    create_default_config
    
    # 测试安装
    if test_installation; then
        log_success "安装测试通过"
    else
        log_warning "安装测试部分失败，但基本功能应该可用"
    fi
    
    # 显示后续说明
    show_post_install_info
}

# 错误处理
trap 'log_error "安装过程中出现错误 (行号: $LINENO)"; exit 1' ERR

# 主函数
main() {
    # 解析命令行参数
    case "${1:-install}" in
        "install"|"")
            show_banner
            install
            ;;
        "uninstall")
            show_banner
            uninstall
            ;;
        "info")
            show_banner
            show_system_info
            ;;
        "--help"|"-h")
            show_banner
            echo "用法: $0 [命令]"
            echo
            echo "命令:"
            echo "  install    - 安装 VibeCodeTask (默认)"
            echo "  uninstall  - 卸载 VibeCodeTask"
            echo "  info       - 显示系统信息"
            echo "  --help     - 显示帮助"
            echo
            echo "环境变量:"
            echo "  DEBUG=1    - 启用调试输出"
            echo
            ;;
        *)
            log_error "未知命令: $1"
            echo "运行 '$0 --help' 查看帮助"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"