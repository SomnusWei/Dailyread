' DailyRead配套管理APP启动脚本 - 简单版
' 最稳定的启动方式
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d """ & Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\")) & """ && pythonw.exe dailyread_manager.py", 0, False
