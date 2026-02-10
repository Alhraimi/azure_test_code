@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Building Windows Executable...
pyinstaller --noconfirm --onefile --windowed --name "InspirationApp" app.py

echo.
echo Build complete!
echo Your .exe file is located in the "dist" folder.
pause
