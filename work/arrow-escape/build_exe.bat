@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Installing game dependencies...
py -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [2/3] Installing packaging tools...
py -m pip install -r requirements-build.txt
if errorlevel 1 goto :error

echo [3/3] Building ArrowEscape.exe...
py -m PyInstaller --noconfirm --clean ArrowEscape.spec
if errorlevel 1 goto :error

echo.
echo Build completed: dist\ArrowEscape.exe
pause
exit /b 0

:error
echo.
echo Build failed. Check the messages above.
pause
exit /b 1
