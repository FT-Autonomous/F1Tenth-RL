# F1Tenth Team 1

This repository contains all our code as well as the F1Tenth Gym repository, as a submodule. You can find the [documentation](https://f1tenth-gym.readthedocs.io/en/latest/) of the environment here.

## Quickstart

#### 1. Cloning the repository

```bash
$ git clone --recurse-submodules https://github.com/FT-Autonomous/Team-1.git
$ cd Team-1
```

**N.B.** Don't forget to include the ```--recurse-submodules``` argument when cloning our repo, or else the F1Tenth Gym won't be cloned!

#### 2. Running the Docker container

You can build and run the environment in Docker, alongside **Stable Baselines 3** (our choice of RL library), by running these commands for your OS:

- ##### Windows

  ```bash
  $ docker-windows.bat
  ```
  Then open **XLaunch**, the same software used in David's [Docker Setup Guide](https://github.com/FT-Autonomous/Autonomous_Crash_Course/tree/main/docker-setup)

- ##### Linux

  ```bash
  $ source docker-linux.sh
  ```
To build the GPU version of the Stable Baselines 3 container, append ```--gpu``` to the end of the above commands

| Version       | Size          |
| ------------- |:-------------:|
| CPU           | 3.41 **GB**   |
| GPU           | 6.86 **GB**   |

#### 3. Testing the installation

Then you can run a quick way-point follow example once inside the container by:

```bash
$ cd /home/formula/Team-1/f1tenth_gym/examples
$ python3 waypoint_follow.py
```

To test the Stable Baselines 3 installation inside the Docker container, create a python script (e.g. foo.py) with the following code and run it with the terminal command ```python foo.py```

```python
import stable_baselines3
print(stable_baselines3.__version__)
```

#### 4. Writing code

- Open the folder containing this repository on your **host** machine, **not** in the Docker container, with your editor of choice and code away (VS Code is recommended)
- To then run these files you will have to do this via the Docker container, which should be open in a seperate terminal from the earlier steps
- In summary: code on your host machine, run the code in your Docker container
