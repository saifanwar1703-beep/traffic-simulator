# --- Simulation Configuration ---
SIMULATION_CONFIG = {
    'width': 800,
    'height': 800,
    'fps': 60,
    'train_spawn_rate': 0.75,  # Trains per second (approx)
    'train_speed': 2,
}

# --- AI Agent Configuration ---
AI_CONFIG = {
    'learning_rate': 0.1,         # How much the agent learns from new information
    'discount_factor': 0.95,      # How much future rewards are valued
    'exploration_rate': 1.0,      # Initial probability of taking a random action
    'exploration_decay': 0.9995,  # Rate at which exploration decreases
    'min_exploration_rate': 0.01, # Minimum exploration probability
}
