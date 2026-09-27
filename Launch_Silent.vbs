Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\Aswin\OneDrive\Desktop\Personal Assistant"
WshShell.Run "python main.py", 0, False
Set WshShell = Nothing
