@echo off
echo Installing required build tools and dependencies...
pip install pyinstaller fpdf pyspellchecker pywebview

echo.
echo Building ReelScript 1.0 into a single executable...
echo This may take a couple of minutes. Please wait...

pyinstaller --noconfirm --onefile --windowed ^
  --icon "movie-icon.ico" ^
  --add-data "movie-icon.ico;." ^
  --add-data "movie-icon.png;." ^
  --add-data "index.html;." ^
  --add-data "styles.css;." ^
  --add-data "script.js;." ^
  --hidden-import webview ^
  --hidden-import fpdf ^
  --hidden-import spellchecker ^
  --hidden-import editor ^
  --hidden-import tkinter ^
  --hidden-import tkinter.filedialog ^
  reelscript.pyw

echo.
echo Build complete! 
echo You can find your final executable inside the newly created "dist" folder.
pause
