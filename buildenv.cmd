@ECHO OFF
:: This file is generated by buildenv tool -- see https://buildenv.readthedocs.io/
:: Please do not edit, changes will be lost

:: Check if python is installed
setlocal
python --version > NUL 2> NUL
set _BUILDENV_RC=%ERRORLEVEL%
if %_BUILDENV_RC% NEQ 0 (
    echo|set /p=">> ERROR: python is not installed" & echo.
    goto end
)

:: Wrap to buildenv script
python buildenv-loader.py --from-loader=cmd %*
set _BUILDENV_RC=%ERRORLEVEL%

:: Check for specific RC
if %_BUILDENV_RC% EQU 100 goto shell
if %_BUILDENV_RC% GTR 100 goto run
goto end

:shell
:: Spawn shell if required
cmd /k .buildenv\shell.cmd
set _BUILDENV_RC=%ERRORLEVEL%
goto end

:run
:: Execute command if required
set _BUILDENV_CMD=.buildenv\command.%_BUILDENV_RC%.cmd
cmd /c %_BUILDENV_CMD%
set _BUILDENV_RC=%ERRORLEVEL%
del %_BUILDENV_CMD%
goto end

:end
exit /b %_BUILDENV_RC%

