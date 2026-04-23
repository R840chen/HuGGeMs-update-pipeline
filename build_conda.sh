#!/bin/bash
# HuGGeMs Conda 包构建脚本
# 用法: bash build_conda.sh [OPTIONS]

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_step() {
    echo -e "${BLUE}==>${NC} $1"
}

echo_success() {
    echo -e "${GREEN}✓${NC} $1"
}

echo_error() {
    echo -e "${RED}✗${NC} $1"
}

# 检查依赖
check_dependencies() {
    echo_step "检查构建依赖..."

    local missing_deps=()

    for cmd in conda python git; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=($cmd)
        fi
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo_error "缺少依赖: ${missing_deps[*]}"
        echo "请先安装这些工具"
        exit 1
    fi

    echo_success "所有依赖已安装"
}

# 清理之前的构建
clean_build() {
    echo_step "清理之前的构建..."
    rm -rf build/ dist/ *.egg-info/ huggems.egg-info/
    rm -rf conda.recipe/*.egg-info/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    echo_success "清理完成"
}

# 构建 Python 包
build_python_package() {
    echo_step "构建 Python 包..."

    # 使用 pip 构建 wheel
    pip install --upgrade build twine
    python -m build

    echo_success "Python 包构建完成"
}

# 构建 conda 包
build_conda_package() {
    echo_step "构建 Conda 包..."

    # 检查是否安装了 conda-build
    if ! command -v conda-build &> /dev/null; then
        echo_step "安装 conda-build..."
        conda install -y conda-build conda-verify
    fi

    # 构建包
    conda-build conda.recipe/ --no-anaconda-upload

    echo_success "Conda 包构建完成"
}

# 显示使用帮助
show_help() {
    echo "用法: $0 [OPTIONS]"
    echo ""
    echo "选项:"
    echo "  --clean         清理之前的构建"
    echo "  --python        只构建 Python 包 (pip wheel)"
    echo "  --conda         构建 Conda 包"
    echo "  --all           构建所有包 (默认)"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --all        # 构建所有包"
    echo "  $0 --python     # 只构建 pip wheel"
    echo "  $0 --conda      # 只构建 conda 包"
}

# 主函数
main() {
    local build_python=false
    local build_conda=false
    local do_clean=false

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean)
                do_clean=true
                shift
                ;;
            --python)
                build_python=true
                shift
                ;;
            --conda)
                build_conda=true
                shift
                ;;
            --all)
                build_python=true
                build_conda=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                echo_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 默认构建所有
    if [ "$build_python" = false ] && [ "$build_conda" = false ]; then
        build_python=true
        build_conda=true
    fi

    # 清理
    if [ "$do_clean" = true ]; then
        clean_build
    fi

    # 检查依赖
    check_dependencies

    # 构建
    if [ "$build_python" = true ]; then
        build_python_package
    fi

    if [ "$build_conda" = true ]; then
        build_conda_package
    fi

    echo ""
    echo_success "所有构建完成!"
    echo ""
    echo "下一步:"
    echo "  1. 安装测试: pip install -e ."
    echo "  2. 验证安装: huggems --help"
    echo "  3. 如需发布到 conda-forge, 创建 PR 到 huggingreds-feedstock"
}

# 运行
main "$@"
