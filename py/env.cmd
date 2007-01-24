@echo off
for /F "usebackq delims=" %%i in (`python "%~dp0\env.py"`) do %%i
