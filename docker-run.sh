#!/bin/sh

IMAGE_NAME=f110-rl-image
CONTAINER_NAME=f110-rl-container
REPO_DIRECTORY=/home/formula/Team-1

# load in previous Dockerfile modification details
last_dockerfile_details=$(head -n 1 dockerfile-build.log) || last_dockerfile_details=x
last_dockerfile_details="$(echo -e "${last_dockerfile_details}" | tr -d '[:space:]')"
# get current Dockerfile details
current_file_time=$(stat -c %y Dockerfile)
current_file_size=$(stat --printf="%s" Dockerfile)
current_dockerfile_details=$current_file_time$current_file_size
current_dockerfile_details="$(echo -e "${current_dockerfile_details}" | tr -d '[:space:]')"

#compare details to see if Dockerfile has been changed
if [ $current_dockerfile_details != $last_dockerfile_details ] || ( ! docker image inspect $IMAGE_NAME >/dev/null 2>&1 ); then
    # if Dockerfile has changed, then re-build the image
    failed=false
    docker build -t $IMAGE_NAME . || failed=true
    if [ "$failed" == true ] ; then
        echo "Build failed ---> check Dockerfile"
        return
    fi
    echo "$current_file_time $current_file_size" > dockerfile-build.log
fi

# start up the F1TenthGym/StableBaselines3 container with the current repository mounted
docker run \
    -it \
    --rm \
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
    $IMAGE_NAME -c "cd $REPO_DIRECTORY/f1tenth_gym && pip3 install -e gym/ >/dev/null 2>&1 & clear; bash"