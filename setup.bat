@echo off
chcp 65001 >nul
echo ========================================
echo   剪贴板历史工具 — 环境安装
echo ========================================
echo.
echo [1/2] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
python --version
echo.
echo [2/2] 安装依赖包...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo [警告] 清华镜像安装失败，尝试默认源...
    pip install -r requirements.txt
)
echo.
echo ========================================
echo   安装完成！双击 app.py 即可启动程序
echo ========================================
pause
