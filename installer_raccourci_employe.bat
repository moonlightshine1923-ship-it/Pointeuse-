@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Installation du raccourci Pointeuse

echo ============================================================
echo   INSTALLATION DE LA POINTEUSE SUR LE PC DE L'EMPLOYE
echo ============================================================
echo.
echo Le serveur de la pointeuse doit deja etre demarre.
echo Exemple d'adresse : 192.168.1.20:8000
echo.
set /p "SERVER=Adresse affichee par le serveur : "
if "%SERVER%"=="" goto :ERROR

set "URL=%SERVER%"
echo %URL% | findstr /b /i "http:// https://" >nul
if errorlevel 1 set "URL=http://%URL%"

echo Creation du raccourci vers %URL% ...
set "POINTEUSE_URL=%URL%"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$url=$env:POINTEUSE_URL;" ^
  "$desktop=[Environment]::GetFolderPath('Desktop');" ^
  "$shortcut=Join-Path $desktop 'Pointeuse.lnk';" ^
  "$edge=@($env:ProgramFiles+'\Microsoft\Edge\Application\msedge.exe',${env:ProgramFiles(x86)}+'\Microsoft\Edge\Application\msedge.exe') | Where-Object {Test-Path $_} | Select-Object -First 1;" ^
  "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut($shortcut);" ^
  "if($edge){$s.TargetPath=$edge;$s.Arguments='--app=' + [char]34 + $url + [char]34;$s.IconLocation=$edge+',0'}else{$s.TargetPath=$env:WINDIR+'\explorer.exe';$s.Arguments=$url};" ^
  "$s.Description='Pointeuse des employes';$s.Save();Write-Host 'Raccourci cree :' $shortcut"

if errorlevel 1 goto :ERROR

echo.
echo Le raccourci "Pointeuse" a ete cree sur le Bureau.
echo La page va maintenant s'ouvrir. Le responsable doit attribuer
 echo ce PC a l'employe avec le code administrateur.
start "" "%URL%"
echo.
pause
exit /b 0

:ERROR
echo.
echo Installation impossible. Verifiez l'adresse saisie et recommencez.
pause
exit /b 1
