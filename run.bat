@echo off
setlocal
if not "%~1"=="" goto command

rem Double-click mode: Python keeps accepting text until the user enters :q.
python "%~dp0main.py"
set "ascii_exit_code=%errorlevel%"
if not "%ascii_exit_code%"=="0" (
    echo.
    echo The program could not continue. Review the error above.
    set /p "ascii_close_prompt=Press Enter to close..."
)
exit /b %ascii_exit_code%

:command
python "%~dp0main.py" %*
exit /b %errorlevel%
