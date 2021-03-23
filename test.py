import gym
import numpy as np

from wrappers import F110_Wrapped

# create environment
env = gym.make('f110_gym:f110-v0', map='./f1tenth_gym/examples/example_map', map_ext='.png', num_agents=1)

# wrap the environment to match SB3 requirements
env = F110_Wrapped(env)