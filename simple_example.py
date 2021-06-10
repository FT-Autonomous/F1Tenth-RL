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

import gym
import time
import numpy as np

from datetime import datetime

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env

from code.wrappers import F110_Wrapped, RandomMap


TRAIN_STEPS = pow(10, 5)  # for reference, it takes about one sec per 500 steps
MIN_EVAL_EPISODES = 5
NUM_PROCESS = 4
MAP_PATH = "./f1tenth_gym/examples/example_map"
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
        env = RandomMap(env, 3000)
        return env

    # vectorise environment (parallelise)
    envs = make_vec_env(wrap_env,
                        n_envs=NUM_PROCESS,
                        seed=np.random.randint(pow(2, 32) - 1),
                        vec_env_cls=SubprocVecEnv)

    # choose RL model and policy here
    model = PPO("MlpPolicy", envs, verbose=1)

    # train model and record time taken
    start_time = time.time()
    model.learn(total_timesteps=TRAIN_STEPS)
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
                        map="./f1tenth_gym/examples/example_map",
                        map_ext=".png",
                        num_agents=1)

    # wrap evaluation environment
    eval_env = F110_Wrapped(eval_env)
    eval_env = RandomMap(eval_env, 1000)
    eval_env.seed(np.random.randint(pow(2, 32) - 1))

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


# necessary for Python multi-processing
if __name__ == "__main__":
    main()
