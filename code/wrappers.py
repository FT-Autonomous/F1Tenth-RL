# MIT License

# Copyright (c) 2020 FT Autonomous Team One

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

    def step(self, action):
        # convert normalised actions (from RL algorithms) back to actual actions for simulator
        action_convert = self.un_normalise_actions(action)
        observation, _, done, info = self.env.step(np.array([action_convert]))

        # TODO -> do some reward engineering here and mess around with this

        # currently setting the speed of the car to be a positive reward
        vel_magnitude = np.linalg.norm(
            [observation['linear_vels_x'][0], observation['linear_vels_y'][0]])
        reward = vel_magnitude

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

    def reset(self):
        # should start off in slightly different positions to help with training
        rand_x = np.random.uniform(-1.0, 1.0)
        rand_y = np.random.uniform(-1.0, 1.0)
        rand_t = np.random.uniform(65.0, 125.0)
        observation, _, _, _ = self.env.reset(
            np.array([[rand_x, rand_y, np.radians(rand_t)]]))
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
        self.step_count = step_interval
        # delete old maps and centerlines
        for f in Path('centerline').glob('*'):
            f.unlink()
        for f in Path('maps').glob('*'):
            f.unlink()

    def reset(self):
        # check map update interval
        if self.step_count >= self.step_interval:
            # create map
            for _ in range(self.MAX_CREATE_ATTEMPTS):
                try:
                    track, track_int, track_ext = create_track()
                    convert_track(track, track_int, track_ext, self._seed)
                    break
                except Exception:
                    print(
                        f"Random generator [{self._seed}] failed, trying again...")
            # update map
            self.update_map(f"./maps/map{self._seed}", ".png")
            # reset counter
            self.step_count = 0
        # reset environment
        return self.env.reset()

    def step(self, action):
        # increment class step counter
        self.step_count += 1
        # step environment
        return self.env.step(action)

    def seed(self, seed):
        self._seed = seed
        np.random.seed(self._seed)
        print(f"Seed -> {self._seed}")
