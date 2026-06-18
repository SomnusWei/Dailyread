' DailyRead配套管理APP启动脚本
' 使用此脚本启动不会显示命令行窗口

Set WshShell = CreateObject("WScript.Shell")
strFolder = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strFolder
WshShell.Run "cmd /c pythonw.exe dailyread_manager.py", 0, False
