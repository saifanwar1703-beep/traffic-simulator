import numpy as np
import random
from config import AI_CONFIG

class TrafficLightAI:
    """A Q-learning agent to control the traffic lights."""
    def __init__(self):
        self.q_table = {}
        self.learning_rate = AI_CONFIG['learning_rate']
        self.discount_factor = AI_CONFIG['discount_factor']
        self.exploration_rate = AI_CONFIG['exploration_rate']
        self.exploration_decay = AI_CONFIG['exploration_decay']
        self.min_exploration_rate = AI_CONFIG['min_exploration_rate']
        self.actions = [0, 1]  # 0: Set N/S to Green, 1: Set E/W to Green

    def get_q_value(self, state, action):
        """Safely get a Q-value from the table, defaulting to 0."""
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state):
        """Chooses an action based on the epsilon-greedy policy."""
        if random.uniform(0, 1) < self.exploration_rate:
            return random.choice(self.actions)  # Explore
        else:
            q_values = [self.get_q_value(state, a) for a in self.actions]
            return self.actions[np.argmax(q_values)] # Exploit

    def learn(self, state, action, reward, next_state, done):
        """Updates the Q-table using the Bellman equation."""
        next_q_values = [self.get_q_value(next_state, a) for a in self.actions]
        max_next_q = max(next_q_values)

        current_q = self.get_q_value(state, action)
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)

        self.q_table[(state, action)] = new_q

        if self.exploration_rate > self.min_exploration_rate:
            self.exploration_rate *= self.exploration_decay

