@echo off
title MECOM HMI Installer
color 0B
echo ==========================================
echo  MECOM HMI System Installer
echo ==========================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Python...

set PYTHON_CMD=

where python >NUL 2>NUL
if %errorlevel% EQU 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
    set PYTHON_CMD=python
    goto :PYTHON_OK
)

where py >NUL 2>NUL
if %errorlevel% EQU 0 (
    for /f "tokens=2" %%i in ('py --version 2^>^&1') do set PYVER=%%i
    set PYTHON_CMD=py
    goto :PYTHON_OK
)

:: Check common install paths
for %%p in (
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles(x86)%\Python313\python.exe"
    "%ProgramFiles(x86)%\Python312\python.exe"
    "%ProgramFiles(x86)%\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
) do (
    if exist %%p (
        set PYTHON_CMD=%%p
        %%~p --version >NUL 2>&1
        goto :PYTHON_OK
    )
)

echo   Python not found.
echo   Options:
echo     1. Install from python.org (check "Add Python to PATH")
echo     2. Or try: py -m pip install -r requirements.txt
echo.
echo   After installing, re-run this installer.
echo.
pause
exit /b 1

:PYTHON_OK
echo   Found Python %PYVER% (%PYTHON_CMD%)

echo [2/4] Installing libraries...
%PYTHON_CMD% -m pip install --upgrade pip -q
%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% EQU 0 (
    echo   Libraries installed OK
) else (
    echo   Install failed. Try: %PYTHON_CMD% -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo [3/4] COM port setup...
set /p comport="  Enter COM port (default=COM6): "
if "%comport%"=="" set comport=COM6
echo.
echo   Port set to %comport%

echo [4/4] Creating shortcuts...

:: Create start_hmi.bat
> start_hmi.bat (
echo @echo off
echo title MECOM HMI System
echo color 0A
echo.
echo cd /d "%%~dp0"
echo echo [Modbus Worker] starting...
echo start /b python modbus_worker.py
echo echo [API Server] starting...
echo start /b python api_server.py
echo timeout /t 3 /nobreak ^> NUL
echo echo.
echo echo Opening dashboard at http://localhost:8501
echo streamlit run app.py
echo pause
)
echo   Created start_hmi.bat

:: Desktop shortcut via PowerShell
powershell -Command ^
  $WSH = New-Object -ComObject WScript.Shell; ^
  $lnk = $WSH.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\MECOM HMI.lnk'); ^
  $lnk.TargetPath = '%~dp0start_hmi.bat'; ^
  $lnk.WorkingDirectory = '%~dp0'; ^
  $lnk.Save() >NUL 2>&1
echo   Desktop shortcut created

echo.
echo ==========================================
echo  Installation Complete!
echo ==========================================
echo.
echo  Double-click "MECOM HMI" on your desktop
echo  URL: http://localhost:8501
echo.
pause
