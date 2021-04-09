import os

import gym
import time
import wandb
import numpy as np

from datetime import datetime

from stable_baselines3.common.results_plotter import load_results, ts2xy, plot_results
from stable_baselines3.common.callbacks import BaseCallback


class SaveOnBestTrainingRewardCallback(BaseCallback):
    """
    Callback for saving a model (the check is done every ``check_freq`` steps)
    based on the training reward (in practice, we recommend using ``EvalCallback``).

    :param check_freq: (int)
    :param log_dir: (str) Path to the folder where the model will be saved.
      It must contains the file created by the ``Monitor`` wrapper.
    :param verbose: (int)
    """

    def __init__(self, check_freq: int, log_dir: str, save_dir: str, use_wandb: bool, always_save=False, verbose=1):
        super(SaveOnBestTrainingRewardCallback, self).__init__(verbose)
        self.check_freq = check_freq
        self.log_dir = log_dir
        self.save_path = save_dir
        self.best_mean_reward = -np.inf
        self.use_wandb = use_wandb
        self.always_save = always_save

    def _init_callback(self) -> None:
        # Create folder if needed
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:

            # Retrieve training reward
            x, y = ts2xy(load_results(self.log_dir), 'timesteps')
            if len(x) > 0:
                # Mean training reward over the last 100 episodes
                mean_reward = np.mean(y[-100:])
                if self.verbose > 0:
                    print("Num timesteps: {}".format(self.num_timesteps))
                    print("Best mean reward: {:.2f} - Last mean reward per episode: {:.2f}".format(
                        self.best_mean_reward, mean_reward))

                # New best model, you could save the agent here
                if (mean_reward > self.best_mean_reward) or self.always_save:
                    self.best_mean_reward = mean_reward
                    # Example for saving best model
                    if self.verbose > 0:
                        if self.always_save:
                            print("Saving current model to {}".format(self.save_path))
                        else:
                            print("Saving new best model to {}".format(self.save_path))
                    # save model with unique timestamp
                    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
                    self.model.save(
                        f"{self.save_path}/ppo-{timestamp}-{int(mean_reward)}R.zip")
                    if self.use_wandb:
                        wandb.save(
                            f"{self.save_path}/ppo-{timestamp}-{int(mean_reward)}R.zip")

        return True
