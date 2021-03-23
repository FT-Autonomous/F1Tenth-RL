import gym
import numpy as np

from gym import spaces

class F110_Wrapped(gym.Wrapper):
  """
  This is a wrapper for the F1Tenth Gym environment intended
  for only one car, but should be expanded to handle multi-agent scenarios
  """

  def __init__(self, env):
    super().__init__(env)

    # action space, steer and speed
    self.action_space = spaces.Box(low=np.array([-1.0, -1.0]), high=np.array([1.0, 1.0]), dtype=np.float)
    
    # observations, just take the lidar scans
    self.observation_space = spaces.Box(low=0.0, high=30.0, shape=(1080,), dtype=np.float)
    
    # save steering/speed allowed ranges for normalising actions (for RL algorithms)
    self.s_min = self.env.params['s_min']
    self.s_max = self.env.params['s_max']
    self.v_min = self.env.params['v_min']
    self.v_max = self.env.params['v_max']
    self.range_s = self.s_max - self.s_min
    self.range_v = self.v_max - self.v_min

  def step(self, action):
    # convert normalised actions back to actual actions
    action_convert = self.convert_actions(action)
    observation, _, done, info = self.env.step(np.array([action_convert]))
    
    ### REWARD ###

    # TODO -> do some reward engineering here and mess around with this
    # currently setting the speed of the car to be a positive reward
    vel_magnitude = np.linalg.norm([observation['linear_vels_x'][0], observation['linear_vels_y'][0]])
    reward = vel_magnitude
    # but if the car crashes, then assign a large negative reward
    if observation['collisions'][0]:
      reward = -450
    
    # the reward below could be a possible sparse reward
    # reward = self.env.lap_counts[0]

    return observation['scans'][0], reward, bool(done), info

  def reset(self):
    # should start off in slightly different positions to help with training
    rand_x = np.random.uniform(-1.0, 1.0)
    rand_y = np.random.uniform(-1.0, 1.0)
    rand_t = np.random.uniform(65.0, 125.0)
    observation, _, _, _ = self.env.reset(np.array([[rand_x, rand_y, np.radians(rand_t)]]))
    return observation['scans'][0]  # reward, done, info can't be included in the Gym format

  def convert_actions(self, actions):
    # convert actions from range [-1, 1] to the normal steering/speed range
    steer = (((actions[0] + 1) * self.range_s) / 2) + self.s_min
    speed = (((actions[1] + 1) * self.range_v) / 2) + self.v_min
    return np.array([steer, speed], dtype=np.float)