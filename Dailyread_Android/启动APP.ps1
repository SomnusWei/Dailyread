# DailyRead配套管理APP启动脚本 - PowerShell版本
# 使用PowerShell启动，也不会显示命令行窗口
# 注意：可能需要先执行 Set-ExecutionPolicy RemoteSigned 来允许脚本运行

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyScript = Join-Path $scriptPath "dailyread_manager.py"

if (Test-Path $pyScript) {
    Start-Process "pythonw.exe" -ArgumentList "`"$pyScript`"" -WindowStyle Hidden -WorkingDirectory $scriptPath
} else {
    Write-Host "找不到dailyread_manager.py"
    Read-Host "按回车键退出"
}
