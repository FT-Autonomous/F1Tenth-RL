# MIT License

# Copyright (c) 2020 FT Autonomous Team One

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# choose which SB3 image to use, CPU or GPU
ARG PARENT_IMAGE=stablebaselines/rl-baselines3-zoo-cpu

# base the rest of the container off the chosen Stable Baselines 3 image
FROM $PARENT_IMAGE

RUN DEBIAN_FRONTEND="noninteractive" apt-get update --fix-missing && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y \
    python3-dev python3-pip

RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y \
    nano \
    git \
    unzip \
    build-essential \
    autoconf \
    libtool \
    cmake \
    vim

RUN pip3 install --upgrade pip

RUN pip3 install \
    numpy \
    scipy \
    numba \
    Pillow \
    gym \
    pyyaml \
    pyglet \
    shapely \
    wandb \
    pylint

RUN conda install -y autopep8


# add a user (kinda just a hack to make the terminal look better)
RUN useradd -m formula -u 1000 -g 0

# set home directory
ENV HOME /home/formula

# open container in home folder
WORKDIR /home/formula/Team-1

# opens terminal when container starts (also overrides SB3 Xvfb setup)
ENTRYPOINT ["/bin/bash"]
