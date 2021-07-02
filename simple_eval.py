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

MIN_EVAL_EPISODES = 100
MAP_PATH = "./f1tenth_racetracks/Silverstone/Silverstone_map"
MAP_EXTENSION = ".png"

eval_env = gym.make("f110_gym:f110-v0",
                        map=MAP_PATH,
                        map_ext=MAP_EXTENSION,
                        num_agents=1)

# wrap evaluation environment
eval_env = F110_Wrapped(eval_env)
#eval_env = ThrottleMaxSpeedReward(eval_env,0,1,2.5,2.5)
#eval_env = RandomF1TenthMap(eval_env, 1)
eval_env.seed(np.random.randint(pow(2, 31) - 1))
model = PPO.load("./train_test/best_model")

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
            if done:
                print("Lap done")
            print("R:", reward)
            eval_env.render()
    except KeyboardInterrupt:
        pass