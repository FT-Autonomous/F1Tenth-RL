@echo off

set IMAGE_NAME=f110
set CONTAINER_NAME=f110
set REPO_DIRECTORY=/home/formula/Team-1

set "ADAPTER=Wireless LAN ADAPTER WiFi"
set "ADDRESS_TAG=IPv4 Address"

docker build -t %IMAGE_NAME% .

setlocal enabledelayedexpansion

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

docker run ^
    -it ^
    --rm ^
    --name %CONTAINER_NAME% ^
    -v "%cd%":%REPO_DIRECTORY% ^
    %IMAGE_NAME% -c "cd %REPO_DIRECTORY%/f1tenth_gym && pip3 install -e gym/ >/dev/null 2>&1 & export DISPLAY=%address%:0.0; clear; bash"

echo Docker container closed
pause