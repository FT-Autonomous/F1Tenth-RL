#!/bin/sh

IMAGE_NAME=f110-rl-image
CONTAINER_NAME=f110-rl-container
REPO_DIRECTORY=/home/formula/Team-1
PARENT_IMAGE=stablebaselines/rl-baselines3-zoo-cpu
GPU_FLAG=
DETACHED_FLAG="-i"

# choose which image to build from, CPU or GPU
if [[ " $@ " =~ " --gpu " ]]; then
    PARENT_IMAGE=stablebaselines/rl-baselines3-zoo
    GPU_FLAG="--gpus all"
fi

# choose whether to run container in background or not (for cloud server)
# default is interactive
if [[ " $@ " =~ " -d " ]]; then
    DETACHED_FLAG="-d"
fi

# load in previous Dockerfile modification details
last_dockerfile_details=$(head -n 1 dockerfile-build.log) || last_dockerfile_details=x
last_dockerfile_details="$(echo -e "${last_dockerfile_details}" | tr -d '[:space:]')"
# get current Dockerfile details
current_file_time=$(stat -c %y Dockerfile)
current_file_size=$(stat --printf="%s" Dockerfile)
current_dockerfile_details=$current_file_time$current_file_size$PARENT_IMAGE
current_dockerfile_details="$(echo -e "${current_dockerfile_details}" | tr -d '[:space:]')"

# compare details to see if Dockerfile has been changed
if [ $current_dockerfile_details != $last_dockerfile_details ] || ( ! docker image inspect $IMAGE_NAME >/dev/null 2>&1 ); then
    # if Dockerfile has changed, then re-build the image
    failed=false
    docker build --build-arg PARENT_IMAGE=$PARENT_IMAGE -t $IMAGE_NAME . || failed=true
    if [ "$failed" == true ] ; then
        echo "Build failed ---> check Dockerfile"
        return
    fi
    # update build log
    echo "$current_file_time $current_file_size $PARENT_IMAGE" > dockerfile-build.log
    # remove old Docker images
    docker rmi $(docker images -f "dangling=true" -q) >/dev/null 2>&1
fi

# update temporary Docker authentication file
rm /tmp/.docker.xauth >/dev/null 2>&1; \
touch /tmp/.docker.xauth && \
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f /tmp/.docker.xauth nmerge -

# start up the F1TenthGym/StableBaselines3 container with the current repository mounted
docker run \
    -t \
    $DETACHED_FLAG \
    --rm \
    --name $CONTAINER_NAME \
    --device /dev/dri/card0 \
    $GPU_FLAG \
    -e DISPLAY \
    -e TERM \
    -e QT_X11_NO_MITSHM=1 \
    -e XAUTHORITY=/tmp/.docker.xauth \
    -v /tmp/.docker.xauth:/tmp/.docker.xauth \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /etc/localtime:/etc/localtime:ro \
    -v $PWD:$REPO_DIRECTORY \
    $IMAGE_NAME -c "cd $REPO_DIRECTORY/f1tenth_gym && pip3 install -e gym/ >/dev/null 2>&1 & clear; export LC_ALL=C.UTF-8 LANG=C.UTF-8; bash"

# clean up leftover directories from container
rm -rf .cache/ .config/