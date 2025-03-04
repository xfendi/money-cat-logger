@echo off
setlocal
color 3

set "PYTHON_FILE_PATH=X:\logger\python\version.py"
set "OUTPUT_DIR=X:\logger\builds"
set "WORK_DIR=X:\logger\temp"
set "ICON_PATH=X:\logger\icons\edge.ico"
set "SPEC_DIR=X:\logger\specs"

:: Tworzenie folderów, jeśli nie istnieją
for %%F in ("%OUTPUT_DIR%" "%WORK_DIR%" "%SPEC_DIR%") do (
    if not exist "%%F" mkdir "%%F"
)

:: Przechodzimy do katalogu z plikiem Python
cd /d "%PYTHON_FILE_PATH%\.."

:: Uruchamiamy PyInstaller
pyinstaller --onefile --noconsole --icon="%ICON_PATH%" --distpath="%OUTPUT_DIR%" --workpath="%WORK_DIR%" --specpath="%SPEC_DIR%" "%PYTHON_FILE_PATH%"

:: Usuwamy pliki tymczasowe i .spec
rmdir /s /q "%WORK_DIR%"
rmdir /s /q "%SPEC_DIR%"

echo [SUCCESS] Build completed and temporary files removed!
