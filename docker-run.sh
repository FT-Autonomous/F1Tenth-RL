#!/bin/sh

CONTAINER_NAME=f110

# start background process which waits for container to start, then sets up the Gym
{
    i=0
    while [ "$( docker container inspect -f '{{.State.Running}}' $CONTAINER_NAME)" != "true" ] && [ $i != 10 ]; do
        sleep 0.5
        let i=i+1
    done
    # try to run install command for F1Tenth Gym in container
    docker exec -it $CONTAINER_NAME bash -c "cd /home/formula/Team-1/f1tenth_gym && pip3 install -e gym/"
} >/dev/null 2>&1 & disown

# start up the F1TenthGym/StableBaselines3 container with the current repository mounted
docker run -it \
    --name $CONTAINER_NAME \
    --device /dev/dri/card0 \
    -e DISPLAY \
    -e TERM \
    -e QT_X11_NO_MITSHM=1 \
    -e XAUTHORITY=/tmp/.docker.xauth \
    -v /tmp/.docker.xauth:/tmp/.docker.xauth \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /etc/localtime:/etc/localtime:ro \
    -v $PWD:/home/formula/Team-1 \
    f1tenth_rl