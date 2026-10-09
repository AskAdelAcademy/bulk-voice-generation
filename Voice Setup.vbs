' Double-click launcher. No terminal window, key arguments, or downloads.
Option Explicit
Dim shell, files, folder, runtime, program, candidates, candidate
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
program = folder & "\scripts\voice_setup.py"
runtime = ""
For Each candidate In Array(shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Launcher\pyw.exe", shell.ExpandEnvironmentStrings("%WINDIR%") & "\pyw.exe", shell.ExpandEnvironmentStrings("%USERPROFILE%") & "\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe")
    If files.FileExists(candidate) Then
        runtime = candidate
        Exit For
    End If
Next
If runtime = "" Then
    MsgBox "Ask Codex: Open the Bulk Voice Generation setup window for me. Codex can find an available Python installation. No terminal commands are needed from you.", vbInformation, "Voice Setup"
Else
    shell.Run Chr(34) & runtime & Chr(34) & " " & Chr(34) & program & Chr(34), 0, False
End If
