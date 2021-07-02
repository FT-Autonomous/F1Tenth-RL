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
Sample python script to show the process of choosing a Stable Baselines model,
training it with a chosen policy, and then evaluating the trained model on the
environment while visualising it
"""
#if getting the module not found error run;
#pip install --user -e gym/
#in the f1tenth_gym folder

import gym
import time
import numpy as np
import torch
import os
import argparse
from datetime import datetime
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback
from code.wrappers import F110_Wrapped, RandomMap, RandomF1TenthMap, ThrottleMaxSpeedReward
from code.manus_callbacks import SaveOnBestTrainingRewardCallback
from code.schedulers import linear_schedule

TRAIN_DIRECTORY = "./train"
TRAIN_STEPS = 1.5 * np.power(10, 5)    # for reference, it takes about one sec per 500 steps
SAVE_CHECK_FREQUENCY = int(TRAIN_STEPS / 10)
MIN_EVAL_EPISODES = 100
NUM_PROCESS = 4
MAP_PATH = "./f1tenth_racetracks/Austin/Austin_map"
MAP_EXTENSION = ".png"

def main():

    #       #
    # TRAIN #
    #       #

    # prepare the environment
    def wrap_env():
        # starts F110 gym
        env = gym.make("f110_gym:f110-v0",
                       map=MAP_PATH,
                       map_ext=MAP_EXTENSION,
                       num_agents=1)
        # wrap basic gym with RL functions
        env = F110_Wrapped(env)
        #env = RandomMap(env, 3000)
        env = RandomF1TenthMap(env, 3000)
        #env = ThrottleMaxSpeedReward(env,0,1,2.5,2.5)
        env = ThrottleMaxSpeedReward(env, 0, int(0.75 * TRAIN_STEPS), 2.5) #this is what eoin used in the code on weights and biases
        return env

    # vectorise environment (parallelise)
    envs = make_vec_env(wrap_env,
                        n_envs=NUM_PROCESS,
                        seed=np.random.randint(pow(2, 31) - 1),
                        vec_env_cls=SubprocVecEnv)

    # choose RL model and policy here
    """eval_env = gym.make("f110_gym:f110-v0",map=MAP_PATH,map_ext=MAP_EXTENSION,num_agents=1)
    eval_env = F110_Wrapped(eval_env)
    eval_env = RandomF1TenthMap(eval_env, 500)
    eval_env.seed(np.random.randint(pow(2, 31) - 1))"""
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu") #RuntimeError: CUDA error: out of memory whenever I use gpu
    model = PPO("MlpPolicy", envs,  learning_rate=linear_schedule(0.0003), gamma=0.99, gae_lambda=0.95, verbose=1, device='cpu')
    eval_callback = EvalCallback(envs, best_model_save_path='./train_test/',
                             log_path='./train_test/', eval_freq=5000,
                             deterministic=True, render=False)

    # train model and record time taken
    start_time = time.time()
    model.learn(total_timesteps=TRAIN_STEPS, callback=eval_callback)
    print(f"Training time {time.time() - start_time:.2f}s")
    print("Training cycle complete.")

    # save model with unique timestamp
    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    model.save(f"./train/ppo-f110-{timestamp}")

    #          #
    # EVALUATE #
    #          #

    # create evaluation environment (same as train environment in this case)
    eval_env = gym.make("f110_gym:f110-v0",
                        map=MAP_PATH,
                        map_ext=MAP_EXTENSION,
                        num_agents=1)

    # wrap evaluation environment
    eval_env = F110_Wrapped(eval_env)
    eval_env = RandomF1TenthMap(eval_env, 500)
    eval_env.seed(np.random.randint(pow(2, 31) - 1))
    model = model.load("./train_test/best_model")

    # simulate a few episodes and render them, ctrl-c to cancel an episode
    episode = 0
    while episode < MIN_EVAL_EPISODES:
        try:
            episode += 1
            obs = eval_env.reset()
            done = False
            while not done:
                action, _ = model.predict(obs)
                obs, reward, done, _ = eval_env.step(action)
                eval_env.render()
        except KeyboardInterrupt:
            pass

# necessary for Python multi-processing
if __name__ == "__main__":
    main()