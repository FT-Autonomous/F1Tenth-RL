# MIT License

# Copyright (c) 2021 Eoin Gogarty, Charlie Maguire and Manus McAuliffe (Formula Trintiy Autonomous)

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

"""
Stable Baselines 3 evaluating script for F1Tenth Gym with wrapped environment
"""

import os
import gym
import time
import glob
import argparse
import numpy as np

from datetime import datetime

from stable_baselines3 import PPO

from code.wrappers import F110_Wrapped, RandomMap


TRAIN_DIRECTORY = "./train"
MIN_EVAL_EPISODES = 5
MAP_PATH = "./f1tenth_gym/examples/example_map"
MAP_EXTENSION = ".png"
MAP_CHANGE_INTERVAL = 3000


def main(args):

    #          #
    # EVALUATE #
    #          #

    # prepare the environment
    def wrap_env():
        # starts F110 gym
        env = gym.make("f110_gym:f110-v0",
                       map=MAP_PATH,
                       map_ext=MAP_EXTENSION,
                       num_agents=1)
        # wrap basic gym with RL functions
        env = F110_Wrapped(env)
        env = RandomMap(env, MAP_CHANGE_INTERVAL)
        return env

    # create evaluation environment (same as train environment)
    eval_env = wrap_env()

    # set random seed
    eval_env.seed(np.random.randint(pow(2, 32) - 1))

    # load or create model
    model, _ = load_model(args.load,
                          TRAIN_DIRECTORY,
                          eval_env,
                          evaluating=True)

    # simulate a few episodes and render them, ctrl-c to cancel an episode
    episode = 0
    while episode < MIN_EVAL_EPISODES:
        try:
            episode += 1
            obs = eval_env.reset()
            done = False
            while not done:
                # use trained model to predict some action, using observations
                action, _ = model.predict(obs)
                obs, _, done, _ = eval_env.step(action)
                eval_env.render()
            # this section just asks the user if they want to run more episodes
            if episode == (MIN_EVAL_EPISODES - 1):
                choice = input("Another episode? (Y/N) ")
                if choice.replace(" ", "").lower() in ["y", "yes"]:
                    episode -= 1
                else:
                    episode = MIN_EVAL_EPISODES
        except KeyboardInterrupt:
            pass


def load_model(load_arg, train_directory, envs, tensorboard_path=None, evaluating=False):
    '''
    Slighly convoluted function that either creates a new model as specified below
    in the "create new model" section, or loads in the latest trained
    model (or user specified model) to continue training
    '''
    
    # create new model
    if (load_arg is None) and (not evaluating):
        print("Creating new model...")
        reset_num_timesteps = True
        model = PPO("MlpPolicy",
                    envs,
                    verbose=1,
                    tensorboard_log=tensorboard_path)
    # load model
    else:
        reset_num_timesteps = False
        # get trained model list
        trained_models = glob.glob(f"{train_directory}/*")
        # latest model
        if (load_arg == "latest") or (load_arg is None):
            model_path = max(trained_models, key=os.path.getctime)
        else:
            trained_models_sorted = sorted(trained_models,
                                           key=os.path.getctime,
                                           reverse=True)
            # match user input to model names
            model_path = [m for m in trained_models_sorted if load_arg in m]
            model_path = model_path[0]
        # get plain model name for printing
        model_name = model_path.replace(".zip", '')
        model_name = model_name.replace(f"{train_directory}/", '')
        print(f"Loading model ({train_directory}) {model_name}")
        # load model from path
        model = PPO.load(model_path)
        # set and reset environment
        model.set_env(envs)
        envs.reset()
    # return new/loaded model
    return model, reset_num_timesteps


# necessary for Python multi-processing (not needed in evaluating)
if __name__ == "__main__":
    # parse runtime arguments to script
    parser = argparse.ArgumentParser()
    parser.add_argument("-l",
                        "--load",
                        help="load previous model",
                        nargs="?",
                        const="latest")
    args = parser.parse_args()
    # call main training function
    main(args)
