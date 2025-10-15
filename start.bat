@echo off
setlocal enabledelayedexpansion
REM Exit immediately if any command fails

REM === Configurations ===
set "VENV_DIR=.venv"
set "REQUIREMENTS_FILE=requirements.txt"
set "ENTRANCE_FILE=main.py"

echo === Checking Python Environment ===

REM Check if Python exists
@where python >nul 2>nul
@if errorlevel 1 (
    echo Python not found. Please install Python 3.11 or higher.
    exit /b 1
)

REM Check Python version
@for /f "tokens=1,2 delims=." %%a in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do (
    set MAJOR=%%a
    set MINOR=%%b
)

@if %MAJOR% LSS 3 (
    echo Python version must be > 3.11. Current version: %MAJOR%.%MINOR%
    exit /b 1
)
@if %MAJOR%==3 if %MINOR% LEQ 11 (
    echo Python version must be > 3.11. Current version: %MAJOR%.%MINOR%
    exit /b 1
)

echo Python version OK: %MAJOR%.%MINOR%
echo.

echo === Checking Virtual Environment ===

REM Create virtual environment if not exists
@if not exist "%VENV_DIR%" (
    echo Creating virtual environment: %VENV_DIR%
    @python -m venv "%VENV_DIR%"
) else (
    echo Virtual environment already exists: %VENV_DIR%
)

REM Activate virtual environment
set "ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate.bat"
@if not exist "%ACTIVATE_SCRIPT%" (
    echo Cannot find virtual environment activation script: %ACTIVATE_SCRIPT%
    exit /b 1
)

@call "%ACTIVATE_SCRIPT%"
echo Virtual environment activated
echo.

echo === Installing Dependencies ===

@if exist "%REQUIREMENTS_FILE%" (
    echo Installing dependencies, please wait...
    @pip install -r "%REQUIREMENTS_FILE%" >nul 2>&1
    echo Dependencies installed
) else (
    echo Requirements file not found: %REQUIREMENTS_FILE%. Skipping installation.
)
echo.

echo === Running Program ===

@if exist "%ENTRANCE_FILE%" (
    echo Running %ENTRANCE_FILE% ...
    @python "%ENTRANCE_FILE%"
) else (
    echo Entrance file not found: %ENTRANCE_FILE%
    exit /b 1
)
