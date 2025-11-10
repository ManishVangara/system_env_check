@echo off
REM Build executables for Windows

echo ========================================
echo Building System Check Client for Windows
echo ========================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Activate virtual environment if it exists
if exist "%PROJECT_ROOT%\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "%PROJECT_ROOT%\venv\Scripts\activate.bat"
)

REM Install/update dependencies
echo Installing build dependencies...
pip install -r "%PROJECT_ROOT%\client_requirements.txt"
echo.

REM Build for Windows
echo Building for Windows...
python "%SCRIPT_DIR%\build_client.py"
echo.

echo ========================================
echo Build completed!
echo ========================================
echo.
echo Built executable is in: %PROJECT_ROOT%\executables\
echo.

pause
