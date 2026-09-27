# ==============================================================================
# Setup Auto-Start for Windows 11 (Silent Background System Tray)
# ==============================================================================

$WshShell = New-Object -ComObject WScript.Shell
$StartupFolder = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Startup)
$ShortcutPath = Join-Path $StartupFolder "Personal_Assistant_Silent.lnk"

$TargetPath = "c:\Users\Aswin\OneDrive\Desktop\Personal Assistant\Launch_Silent.vbs"
$WorkingDir = "c:\Users\Aswin\OneDrive\Desktop\Personal Assistant"

Write-Host "Creating Windows Startup Shortcut at: $ShortcutPath" -ForegroundColor Cyan
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$TargetPath`""
$Shortcut.WorkingDirectory = $WorkingDir
$Shortcut.Description = "Private Local Personal Assistant for Aswin"
$Shortcut.Save()

Write-Host "[SUCCESS] Auto-start configured! Your assistant will now run silently in your System Tray on boot." -ForegroundColor Green
