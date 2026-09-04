@echo off
chcp 65001 >nul
where python >nul 2>nul
if errorlevel 1 (
    echo 没有找到 Python。
    echo 本项目需要 Python 3.11 或更高版本。
    echo 安装完成后重新双击“开始体验.bat”。
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)
python harness.py start
if errorlevel 1 (
    echo.
    echo 启动失败。请查看上方说明。
    pause
)
