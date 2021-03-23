import gym
import numpy as np

from gym import spaces

class F110_Wrapped(gym.Wrapper):

  def __init__(self, env):
    super().__init__(env)
    # action space, steer and speed
    self.action_space = spaces.Box(low=np.array([-1.0, -1.0]), high=np.array([1.0, 1.0]), dtype=np.float)
    # observations, just take the lidar scans
    self.observation_space = spaces.Box(low=0.0, high=30.0, shape=(1080,), dtype=np.float)
    # get action details for action scaling
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
    
    # TODO -> do some reward engineering here
    vel_magnitude = np.linalg.norm([observation['linear_vels_x'][0], observation['linear_vels_y'][0]])
    reward = vel_magnitude
    if observation['collisions'][0]:
      reward = -450
    # reward = self.env.lap_counts[0]

    return observation['scans'][0], reward, bool(done), info

  def reset(self):
    observation, _, _, _ = self.env.reset(np.array([[self.env.start_xs[0], self.env.start_ys[0], self.env.start_thetas[0]]]))
    return observation['scans'][0]  # reward, done, info can't be included

  def convert_actions(self, actions):
    steer = (((actions[0] + 1) * self.range_s) / 2) + self.s_min
    speed = (((actions[1] + 1) * self.range_v) / 2) + self.v_min
    return np.array([steer, speed], dtype=np.float)