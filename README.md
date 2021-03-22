# F1Tenth Team 1

This repository contains all our code as well as the F1Tenth Gym repository, as a submodule. You can find the [documentation](https://f1tenth-gym.readthedocs.io/en/latest/) of the environment here.

## Quickstart
#### 1. Installing the Docker image

You can install the environment in Docker, alongside **Stable Baselines 3** (our choice of RL library), by running the following in a terminal:

```bash
$ git clone --recurse-submodules https://github.com/FT-Autonomous/Team-1.git
$ cd Team-1
$ docker build -t f1tenth_rl .
```

**N.B.** don't forget the period at the end of the docker build command.

#### 2. Running the Docker container

The next steps are similar to the Crash Course [Docker Setup Guide](https://github.com/FT-Autonomous/Autonomous_Crash_Course/tree/main/docker-setup). With the Docker image built as above, you can run the container and enter into it by running this in the terminal:

- ##### Windows

  ```bash
  $ docker run -it f1tenth_rl
  ```

  Then open **XLaunch**, as per David's guide

- ##### Linux

  ```bash
  $ source docker-run.sh
  ```

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
