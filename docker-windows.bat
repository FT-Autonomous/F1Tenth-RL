@echo off

set IMAGE_NAME=f110-rl-image
set CONTAINER_NAME=f110-rl-container
set REPO_DIRECTORY=/home/formula/Team-1

set "ADAPTER=Wireless LAN ADAPTER WiFi"
set "ADDRESS_TAG=IPv4 Address"

@REM load in previous Dockerfile modification details
set /p last_dockerfile_details=<dockerfile.log || echo Creating log file...
set last_dockerfile_details=%last_dockerfile_details: =%
@REM get current Dockerfile details
for %%X in (Dockerfile) do set current_file_size=%%~zX & set current_file_time=%%~tX
set current_dockerfile_details=%current_file_time%%current_file_size%
set current_dockerfile_details=%current_dockerfile_details: =%
@REM compare details to see if Dockerfile has been changed
set "needs_build="
if not "%current_dockerfile_details%" == "%last_dockerfile_details%" ( set "needs_build=y" )
docker image inspect %IMAGE_NAME% 1>NUL 2>NUL || set "needs_build=y"
@REM if Dockerfile has changed, then re-build the image
if defined needs_build (
    docker build -t %IMAGE_NAME% . || (echo Build failed && pause && exit)
    echo %current_file_time% %current_file_size% > dockerfile.log 
)

setlocal enabledelayedexpansion

@REM get IP address for screen forwarding
set adapterfound=false
for /f "usebackq tokens=1-2 delims=:" %%f in (`ipconfig /all`) do (
    set "item=%%f"
    if /i "!item!"=="!ADAPTER!" (
        set adapterfound=true
    ) else if not "!item!"=="!item:%ADDRESS_TAG%=!" if "!adapterfound!"=="true" (
	    for /f "tokens=1-2 delims=(" %%h in ("%%g") do (
	        set "address=%%h"
	        set address=!address: =!
	    )
        set adapterfound=false
    )
)

@REM run Docker container with the Team-1 repository mounted inside
docker run ^
    -it ^
    --rm ^
    --name %CONTAINER_NAME% ^
    -v "%cd%":%REPO_DIRECTORY% ^
    %IMAGE_NAME% -c "cd %REPO_DIRECTORY%/f1tenth_gym && pip3 install -e gym/ >/dev/null 2>&1 & export DISPLAY=%address%:0.0; clear; bash"

echo Docker container closed
pause