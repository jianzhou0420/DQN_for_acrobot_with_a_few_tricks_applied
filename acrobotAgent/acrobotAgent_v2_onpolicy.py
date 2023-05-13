import gymnasium as gym
import torch
import numpy as np
import torch.nn as nn
import random
import matplotlib.pyplot as plt
from IPython import display

env = gym.make("Acrobot-v1", render_mode='rgb_array')
observation, info = env.reset(seed=42)
# for _ in range(1):
#     action = env.action_space.sample()  # this is where you would insert your policy
#     observation, reward, terminated, truncated, info = env.step(action)
#
#     if terminated or truncated:
#         observation, info = env.reset()
# env.close()

dataPath = 'acrobotAgent/data/'
modelPath = 'acrobotAgent/model/'

"""
the general agent should be able to:
1. be able to analysis the env and understand the state space and action space



this is on-policy training, it has bad performance as well.
it is caused by the reward constanly equal to -1, which means the agent is not able to learn anything.
we need to make the reward function more reasonable.

"""


class Agent():
    def __init__(self, env, epsilon=1, epsilon_decay=0.995, epsilon_min=0.01, batch_size=32, discount_factor=0.9,
                 num_of_episodes=500):
        # hyper parameters
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.batch_size = batch_size
        self.discount_factor = discount_factor
        self.num_of_episodes = num_of_episodes
        self.env = env

        # get the shape of the state and action
        self.state_shape = env.observation_space.shape
        self.action_shape = env.action_space.shape

        # define the model
        self.__buildd_model()
        pass

    def __buildd_model(self):
        self.net = torch.nn.Sequential(
            nn.Linear(self.state_shape[0], 25),
            nn.ReLU(),
            nn.Linear(25, 25),
            nn.ReLU(),
            nn.Linear(25, 25),
            nn.ReLU(),
            nn.Linear(25, self.env.action_space.n)
        )
        self.loss = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.net.parameters(), lr=0.001)
        self.net.apply(self._init_weights)
        pass

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            module.weight.data.normal_(mean=0.0, std=1.0)

    def onPolicyTraining(self, episodes=1000, batch_size=1000):
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        device = "cpu"
        print("Using device:", device)

        action_field = [env.action_space.start + i for i in range(env.action_space.n)]
        done = False
        for i in range(episodes):
            state, _ = self.env.reset()
            for j in range(batch_size):
                # forward pass
                prediction = self.net(torch.tensor(state).to(device))

                # epsilon greedy
                if random.random() < self.epsilon:
                    action = random.choice(action_field)
                else:
                    action = action_field[torch.argmax(prediction).item()]
                    if self.epsilon >= self.epsilon_min:
                        self.epsilon *= self.epsilon_decay

                next_state, reward, done, _, _ = self.env.step(action)

                target = prediction.clone()
                if not done:
                    target[action] = reward + self.discount_factor * torch.max(self.net(torch.tensor(next_state).to(device)))
                else:
                    break

                self.optimizer.zero_grad()
                self.loss(prediction, target).backward()
                self.optimizer.step()
            print("\repisode: ", i, " loss: ", self.loss(prediction, target).item(), flush=True)
        torch.save(self.net, 'model_test1.pt')
        pass

    def test(self, num_frames=100):
        model = torch.load('model_test1.pt')
        model.eval()
        state, _ = env.reset()
        frames = []

        import imageio

        for i in range(num_frames):
            action = model(torch.tensor(state)).argmax()
            state, reward, done, truncated, info = env.step(action)

            if done:
                state, _ = env.reset()
            img = env.render()
            frames.append(img)

        env.close()

        imageio.mimsave('test.gif', frames, duration=1 / 60)

        pass


bot = Agent(env)

bot.onPolicyTraining(1000, 200)

bot.test(2000)
