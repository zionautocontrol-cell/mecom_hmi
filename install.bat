@echo off
title MECOM HMI Installer
color 0B
echo ==========================================
echo  MECOM HMI System Installer
echo ==========================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Python...

:: 1) python 명령어 테스트 (Windows Store 방지: --version 없이 직접 호출)
python -c "import sys; print(f'Python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}')" > "%TEMP%\pyver.txt" 2>&1
if %errorlevel% EQU 0 (
    set /p PYVER=<"%TEMP%\pyver.txt"
    set PYTHON_CMD=python
    goto :PYTHON_OK
)

:: 2) py launcher
py -3 -c "import sys; print(f'Python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}')" > "%TEMP%\pyver.txt" 2>&1
if %errorlevel% EQU 0 (
    set /p PYVER=<"%TEMP%\pyver.txt"
    set PYTHON_CMD=py -3
    goto :PYTHON_OK
)

:: 3) Common install paths
for %%p in (
    "C:\Program Files\Python313\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Program Files (x86)\Python313\python.exe"
    "C:\Program Files (x86)\Python312\python.exe"
    "C:\Program Files (x86)\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
) do (
    if exist %%p (
        "%%~p" -c "import sys; print(f'Python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}')" > "%TEMP%\pyver.txt" 2>&1
        if exist "%TEMP%\pyver.txt" (
            set /p PYVER=<"%TEMP%\pyver.txt"
        )
        set PYTHON_CMD=%%~p
        goto :PYTHON_OK
    )
)

:: Not found → auto-install
echo   Python not found. Downloading Python 3.12.4...
echo.

set PY_INSTALLER=%TEMP%\python-3.12.4-amd64.exe
echo   Downloading (may take a moment)...
powershell -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%TEMP%\python-3.12.4-amd64.exe' -UseBasicParsing; exit 0 } catch { exit 1 }"
if %errorlevel% NEQ 0 (
    echo   Download failed.
    echo   Please install Python 3.12 manually from python.org
    pause
    exit /b 1
)

echo   Installing Python...
start /w "" "%PY_INSTALLER%" /quiet PrependPath=1 Include_test=0
del "%PY_INSTALLER%" 2>NUL

:: Python이 설치된 경로 찾기
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set PYTHON_CMD=%LocalAppData%\Programs\Python\Python312\python.exe
if exist "%ProgramFiles%\Python312\python.exe" set PYTHON_CMD=%ProgramFiles%\Python312\python.exe
if exist "%ProgramFiles(x86)%\Python312\python.exe" set PYTHON_CMD=%ProgramFiles(x86)%\Python312\python.exe

:: Found it?
if defined PYTHON_CMD (
    "%PYTHON_CMD%" -c "import sys; print(f'Python {sys.version_info[0]}.{sys.version_info[1]}')" > "%TEMP%\pyver.txt" 2>&1
    if %errorlevel% EQU 0 (
        set /p PYVER=<"%TEMP%\pyver.txt"
        goto :PYTHON_OK
    )
)

echo   Installation failed. Try installing Python 3.12 manually from python.org
pause
exit /b 1

:PYTHON_OK
del "%TEMP%\pyver.txt" 2>NUL
echo   Found %PYVER% (%PYTHON_CMD%)

:: ---------------------------------------------------------------
echo [2/4] Installing libraries...
echo.

call %PYTHON_CMD% -m pip install --upgrade pip -q
call %PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% EQU 0 (
    echo.
    echo   Libraries installed OK
    goto :CONTINUE
)

echo.
echo   pip install FAILED.
echo   Possible causes:
echo     1. No internet connection
echo     2. Python is a Windows Store stub (install from python.org)
echo.
echo   You can retry manually after closing this window:
echo     cd /d "%~dp0"
echo     %PYTHON_CMD% -m pip install -r requirements.txt
echo.
pause
exit /b 1

:CONTINUE

:: ---------------------------------------------------------------
echo [3/4] COM port setup...
set /p comport="  Enter COM port (default=COM6): "
if "%comport%"=="" set comport=COM6
echo.
echo   Port set to %comport%
powershell -Command "(Get-Content config.py) -replace 'MODBUS_PORT = \"COM\d+\"', 'MODBUS_PORT = \"%comport%\"' | Set-Content config.py -Encoding UTF8"
echo   Updated config.py

:: ---------------------------------------------------------------
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
if %errorlevel% EQU 0 (
    echo   Desktop shortcut created
) else (
    echo   Warning: Could not create desktop shortcut (run as admin?)
)

:: ---------------------------------------------------------------
echo.
echo ==========================================
echo  Installation Complete!
echo ==========================================
echo.
echo  Double-click "MECOM HMI" on your desktop
echo  URL: http://localhost:8501
echo.
pause
