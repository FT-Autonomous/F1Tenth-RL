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

import gym
import numpy as np

from gym import spaces
from pathlib import Path

from code.random_trackgen import create_track, convert_track


def convert_range(value, input_range, output_range):
    # converts value(s) from range to another range
    # ranges ---> [min, max]
    (in_min, in_max), (out_min, out_max) = input_range, output_range
    in_range = in_max - in_min
    out_range = out_max - out_min
    return (((value - in_min) * out_range) / in_range) + out_min


class F110_Wrapped(gym.Wrapper):
    """
    This is a wrapper for the F1Tenth Gym environment intended
    for only one car, but should be expanded to handle multi-agent scenarios
    """

    def __init__(self, env):
        super().__init__(env)

        # normalised action space, steer and speed
        self.action_space = spaces.Box(low=np.array(
            [-1.0, -1.0]), high=np.array([1.0, 1.0]), dtype=np.float)

        # normalised observations, just take the lidar scans
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(1080,), dtype=np.float)

        # store allowed steering/speed/lidar ranges for normalisation
        self.s_min = self.env.params['s_min']
        self.s_max = self.env.params['s_max']
        self.v_min = self.env.params['v_min']
        self.v_max = self.env.params['v_max']
        self.lidar_min = 0
        self.lidar_max = 30  # see ScanSimulator2D max_range

        # store car dimensions and some track info
        self.car_length = self.env.params['length']
        self.car_width = self.env.params['width']
        self.track_width = 3.2  # ~= track width, see random_trackgen.py

        # radius of circle where car can start on track, relative to a centerpoint
        self.start_radius = (self.track_width / 2) - \
            ((self.car_length + self.car_width) / 2)  # just extra wiggle room

        # set threshold for maximum angle of car, to prevent spinning
        self.max_theta = 100

    def step(self, action):
        # convert normalised actions (from RL algorithms) back to actual actions for simulator
        action_convert = self.un_normalise_actions(action)
        observation, _, done, info = self.env.step(np.array([action_convert]))

        # TODO -> do some reward engineering here and mess around with this

        # currently setting the speed of the car to be a positive reward
        vel_magnitude = np.linalg.norm(
            [observation['linear_vels_x'][0], observation['linear_vels_y'][0]])
        reward = vel_magnitude

        # end episode if car is spinning
        if abs(observation['poses_theta'][0]) > self.max_theta:
            done = True

        # penalise changes in car angular orientation (reward smoothness)
        # ang_magnitude = abs(observation['ang_vels_z'][0])
        # if ang_magnitude > 10: ang_magnitude = 10
        # reward = vel_magnitude - ang_magnitude

        # if collisions is true, then the car has crashed
        # if observation['collisions'][0]:
        #   reward = -1000

        # just a simple counter that increments when the car completes a lap
        # reward = self.env.lap_counts[0]

        return self.normalise_observations(observation['scans'][0]), reward, bool(done), info

    def reset(self, start_xy=None, direction=None):
        # should start off in slightly different position every time
        # position car anywhere along line from wall to wall facing
        # car will never face backwards, can face forwards at an angle

        # start from origin if no pose input
        if start_xy is None:
            start_xy = np.zeros(2)
        # start in random direction if no direction input
        if direction is None:
            direction = np.random.uniform(0, 2 * np.pi)
        # get slope perpendicular to track direction
        slope = np.tan(direction + np.pi / 2)
        # get magintude of slope to normalise parametric line
        magnitude = np.sqrt(1 + np.power(slope, 2))
        # get random point along line of width track
        rand_offset = np.random.uniform(-1, 1)
        rand_offset_scaled = rand_offset * self.start_radius
        # convert position along line to position between walls at current point
        x, y = start_xy + rand_offset_scaled * np.array([1, slope]) / magnitude
        # point car in random forward direction, not aiming at walls
        t = -np.random.uniform(max(-rand_offset * np.pi / 2, 0) - np.pi / 2,
                               min(-rand_offset * np.pi / 2, 0) + np.pi / 2) + direction
        # reset car with chosen pose
        observation, _, _, _ = self.env.reset(np.array([[x, y, t]]))
        # reward, done, info can't be included in the Gym format
        return self.normalise_observations(observation['scans'][0])

    def un_normalise_actions(self, actions):
        # convert actions from range [-1, 1] to normal steering/speed range
        steer = convert_range(actions[0], [-1, 1], [self.s_min, self.s_max])
        speed = convert_range(actions[1], [-1, 1], [self.v_min, self.v_max])
        return np.array([steer, speed], dtype=np.float)

    def normalise_observations(self, observations):
        # convert observations from normal lidar distances range to range [-1, 1]
        return convert_range(observations, [self.lidar_min, self.lidar_max], [-1, 1])

    def update_map(self, map_name, map_extension, update_render=True):
        self.env.map_name = map_name
        self.env.map_ext = map_extension
        self.env.update_map(f"{map_name}.yaml", map_extension)
        if update_render and self.env.renderer:
            self.env.renderer.close()
            self.env.renderer = None

    def seed(self, seed):
        self.current_seed = seed
        np.random.seed(self.current_seed)
        print(f"Seed -> {self.current_seed}")

#    def get_distance():
#       centerline = self.waypoints
#        x1 = observation['poses_x'][0]
#        y1 = observation['poses_y'][0]
#        dist = 10
#        i = 0
#        while dist < 1:
#            dist = np.sqrt(np.power((x1 - centerline[0][i]), 2) + np.power((y1 - centerline[1][i]), 2))
#            i += 1
#        completion = (i / len(centerline)) * 100
#        return completion


class RandomMap(gym.Wrapper):
    """
    Generates random maps at chosen intervals, when resetting car,
    and positions car at random point around new track
    """

    # stop function from trying to generate map after multiple failures
    MAX_CREATE_ATTEMPTS = 20

    def __init__(self, env, step_interval=5000):
        super().__init__(env)
        # initialise step counters
        self.step_interval = step_interval
        self.step_count = 0

    def reset(self):
        # check map update interval
        if self.step_count % self.step_interval == 0:
            # create map
            for _ in range(self.MAX_CREATE_ATTEMPTS):
                try:
                    track, track_int, track_ext = create_track()
                    convert_track(track,
                                  track_int,
                                  track_ext,
                                  self.current_seed)
                    break
                except Exception:
                    print(
                        f"Random generator [{self.current_seed}] failed, trying again...")
            # update map
            self.update_map(f"./maps/map{self.current_seed}", ".png")
            # store waypoints
            self.waypoints = np.genfromtxt(f"centerline/map{self.current_seed}.csv",
                                           delimiter=',')
        # get random starting position from centerline
        random_index = np.random.randint(len(self.waypoints))
        start_xy = self.waypoints[random_index]
        next_xy = self.waypoints[(random_index + 1) % len(self.waypoints)]
        # get forward direction by pointing at next point
        direction = np.arctan2(next_xy[1] - start_xy[1],
                               next_xy[0] - start_xy[0])
        # reset environment
        return self.env.reset(start_xy=start_xy, direction=direction)

    def step(self, action):
        # increment class step counter
        self.step_count += 1
        # step environment
        return self.env.step(action)

    def seed(self, seed):
        # seed class
        self.env.seed(seed)
        # delete old maps and centerlines
        for f in Path('centerline').glob('*'):
            if not ((seed - 100) < int(''.join(filter(str.isdigit, str(f)))) < (seed + 100)):
                try:
                    f.unlink()
                except:
                    pass
        for f in Path('maps').glob('*'):
            if not ((seed - 100) < int(''.join(filter(str.isdigit, str(f)))) < (seed + 100)):
                try:
                    f.unlink()
                except:
                    pass


class ThrottleMaxSpeedReward(gym.RewardWrapper):
    """
    Slowly increase maximum reward for going fast, so that car learns
    to drive well before trying to improve speed
    """

    def __init__(self, env, start_step, end_step, start_max_reward, end_max_reward=None):
        super().__init__(env)
        # initialise step boundaries
        self.end_step = end_step
        self.start_step = start_step
        self.start_max_reward = start_max_reward
        # set finishing maximum reward to be maximum possible speed by default
        self.end_max_reward = self.v_max if end_max_reward is None else end_max_reward

        # calculate slope for reward changing over time (steps)
        self.reward_slope = (
            self.end_max_reward - self.start_max_reward) / (self.end_step - self.start_step)

    def reward(self, reward):
        # maximum reward is start_max_reward
        if self.step_count < self.start_step:
            return min(reward, self.start_max_reward)
        # maximum reward is end_max_reward
        elif self.step_count > self.end_step:
            return min(reward, self.end_max_reward)
        # otherwise, proportional reward between two step endpoints
        else:
            return min(reward, self.start_max_reward + (self.step_count - self.start_step) * self.reward_slope)
