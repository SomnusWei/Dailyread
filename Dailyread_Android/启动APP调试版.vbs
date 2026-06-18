' DailyRead配套管理APP启动脚本 - 调试版
' 此版本会显示错误信息，用于诊断问题
Option Explicit

Dim WshShell, strScriptFolder, strCommand, objFSO, strPythonPath, strScriptPath
Dim result

Set WshShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' 获取脚本所在目录
strScriptFolder = objFSO.GetParentFolderName(WScript.ScriptFullName)
WScript.Echo "脚本目录: " & strScriptFolder

' 切换到脚本所在目录
WshShell.CurrentDirectory = strScriptFolder
WScript.Echo "当前目录: " & WshShell.CurrentDirectory

' 检查Python是否存在
On Error Resume Next
result = WshShell.Run("pythonw.exe --version", 1, True)
If Err.Number = 0 And result = 0 Then
    WScript.Echo "找到pythonw.exe"
Else
    WScript.Echo "未找到pythonw.exe，尝试python.exe"
    result = WshShell.Run("python.exe --version", 1, True)
    If Err.Number = 0 And result = 0 Then
        WScript.Echo "找到python.exe"
        strPythonPath = "python.exe"
    Else
        WScript.Echo "错误: 未找到Python！请确保Python已安装并添加到PATH中。"
        WScript.Quit 1
    End If
End If
On Error Goto 0

' 构建脚本完整路径
strScriptPath = objFSO.BuildPath(strScriptFolder, "dailyread_manager.py")
WScript.Echo "脚本路径: " & strScriptPath

If Not objFSO.FileExists(strScriptPath) Then
    WScript.Echo "错误: 找不到dailyread_manager.py"
    WScript.Quit 2
End If

WScript.Echo "正在启动APP..."

' 运行
strCommand = "pythonw.exe " & Chr(34) & strScriptPath & Chr(34)
On Error Resume Next
WshShell.Run strCommand, 0, False
If Err.Number <> 0 Then
    WScript.Echo "启动失败: " & Err.Description
    Err.Clear
    ' 备用方法
    WScript.Echo "尝试备用方法..."
    strCommand = "cmd /c pythonw.exe " & Chr(34) & strScriptPath & Chr(34)
    WshShell.Run strCommand, 0, False
End If
On Error Goto 0

WScript.Echo "启动命令已发出！"
