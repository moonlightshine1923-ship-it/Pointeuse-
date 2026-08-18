@echo off
setlocal
cd /d "%~dp0"
title Serveur Pointeuse

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 goto :NO_PYTHON
  set "PYTHON=python"
)

start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000/admin"
%PYTHON% app.py

echo.
echo Le serveur est arrete.
pause
exit /b

:NO_PYTHON
echo Python 3 est introuvable.
echo Installez-le depuis https://www.python.org/downloads/windows/
echo et cochez l'option Add Python to PATH.
pause
exit /b 1
