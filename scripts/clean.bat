@echo off 
echo =======================Vrika Clean Script for Windows=======================
echo Running this script will delete the Scan database, all files uploaded and generated.
SET vrika_home="%userprofile%\.Vrika"
SET mypath=%~dp0
echo %mypath:~0,-1%
IF "%~1"=="y" (
echo Deleting all uploads
rmdir "vrika_mobile_security\uploads" /q /s >nul 2>&1
echo Deleting all downloads
rmdir "vrika_mobile_security\downloads" /q /s >nul 2>&1
echo Deleting Static Analyzer migrations
rmdir "vrika_mobile_security\StaticAnalyzer\migrations" /q /s >nul 2>&1
echo Deleting Dynamic Analyzer migrations
rmdir "vrika_mobile_security\DynamicAnalyzer\migrations" /q /s >nul 2>&1
echo Deleting Vrika migrations
rmdir "vrika_mobile_security\Vrika\migrations" /q /s >nul 2>&1
echo Deleting temp and log files
del /f "vrika_mobile_security\debug.log" >nul 2>&1
del /f "classes*" >nul 2>&1
echo Deleting Scan database
del /f "vrika_mobile_security\db.sqlite3" >nul 2>&1
echo Deleting Secret file
del /f "vrika_mobile_security\secret" >nul 2>&1
echo Deleting Previous setup files
rmdir "%UserProfile%\Vrika" /q /s >nul 2>&1
del /f "vrika_mobile_security\setup_done.txt" >nul 2>&1
echo Deleting Vrika data directory: %vrika_home%
del /f "%vrika_home%" /q /s >nul 2>&1
rmdir "%vrika_home%" /S /Q >nul 2>&1
echo Done
) ELSE ( 
echo Please run script from vrika_mobile_security.Vrika directory
echo 'scripts/clean.bat y
)
