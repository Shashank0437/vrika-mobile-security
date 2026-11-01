@echo off

if [%1]==[] goto usage
SET conf=%1
goto :run
:usage
SET conf="0.0.0.0:8000 [::]:8000"
:run
echo Running Vrika on %conf%
call poetry run waitress-serve --listen=%conf% --threads=10 --channel-timeout=3600 vrika_mobile_security.Vrika.wsgi:application
set "VRIKA_EXIT_CODE=%ERRORLEVEL%"
call poetry run python manage.py cleanup_android
exit /b %VRIKA_EXIT_CODE%
