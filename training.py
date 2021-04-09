"""
Stable Baselines 3 training script for F1Tenth Gym with vectorised environments
"""

import os
import gym
import time
import glob
import wandb
import argparse
import numpy as np

from datetime import datetime

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env

from code.wrappers import F110_Wrapped, RandomMap
from code.callbacks import SaveOnBestTrainingRewardCallback


TRAIN_DIRECTORY = "./train"
TRAIN_STEPS = pow(10, 5)  # for reference, it takes about one sec per 500 steps
NUM_PROCESS = 4
MAP_PATH = "./f1tenth_gym/examples/example_map"
MAP_EXTENSION = ".png"
MAP_CHANGE_INTERVAL = 3000
TENSORBOARD_PATH = "./ppo_tensorboard"
SAVE_CHECK_FREQUENCY = int(TRAIN_STEPS / 10)


def main(args):

    #       #
    # TRAIN #
    #       #

    # initialise weights and biases
    if args.wandb:
        wandb.init(sync_tensorboard=True)

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

    # create log directory for monitor wrapper (in make_vec_env)
    log_dir = "tmp/"
    os.makedirs(log_dir, exist_ok=True)

    # vectorise environment (parallelise)
    envs = make_vec_env(wrap_env,
                        n_envs=NUM_PROCESS,
                        seed=np.random.randint(pow(2, 32) - 1),
                        monitor_dir=log_dir,
                        vec_env_cls=SubprocVecEnv)

    # load or create model
    model, reset_num_timesteps = load_model(args.load,
                                            TRAIN_DIRECTORY,
                                            envs,
                                            TENSORBOARD_PATH)

    # create the model saving callback
    saving_callback = SaveOnBestTrainingRewardCallback(check_freq=SAVE_CHECK_FREQUENCY,
                                                       log_dir=log_dir,
                                                       save_dir=TRAIN_DIRECTORY,
                                                       use_wandb=args.wandb,
                                                       always_save=args.save)

    # train model and record time taken
    start_time = time.time()
    model.learn(total_timesteps=TRAIN_STEPS,
                reset_num_timesteps=reset_num_timesteps,
                callback=saving_callback)
    print(f"Training time {time.time() - start_time:.2f}s")
    print("Training cycle complete.")

    # save model with unique timestamp
    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    model.save(f"{TRAIN_DIRECTORY}/ppo-{timestamp}-final")
    if args.wandb:
        wandb.save(f"{TRAIN_DIRECTORY}/ppo-{timestamp}-final")


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


# necessary for Python multi-processing
if __name__ == "__main__":
    # parse runtime arguments to script
    parser = argparse.ArgumentParser()
    parser.add_argument("-l",
                        "--load",
                        help="load previous model",
                        nargs="?",
                        const="latest")
    parser.add_argument("-w",
                        "--wandb",
                        help="use Weights and Biases API",
                        action="store_true")
    parser.add_argument("-s",
                        "--save",
                        help="always save at step interval",
                        action="store_true")
    args = parser.parse_args()
    # call main training function
    main(args)
