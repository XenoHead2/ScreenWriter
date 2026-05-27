@echo off
echo Installing required build tools and dependencies...
pip install pyinstaller fpdf pyspellchecker pywebview

echo.
echo Building KindredScript Pro into a single executable...
echo This may take a couple of minutes. Please wait...

pyinstaller --noconfirm --onefile --windowed ^
  --add-data "index.html;." ^
  --add-data "styles.css;." ^
  --add-data "script.js;." ^
  --hidden-import webview ^
  --hidden-import fpdf ^
  --hidden-import spellchecker ^
  --hidden-import editor ^
  --hidden-import tkinter ^
  --hidden-import tkinter.filedialog ^
  desktop.pyw

echo.
echo Build complete! 
echo You can find your final executable inside the newly created "dist" folder.
pause
