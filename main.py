import pygame
import sys
from traffic_simulation import TrafficSimulation
from traffic_light_ai import TrafficLightAI
from config import SIMULATION_CONFIG, AI_CONFIG

def main():
    # --- Initialize Pygame ---
    pygame.init()
    
    simulation = TrafficSimulation()
    ai_controller = TrafficLightAI()
    
    running = True
    clock = pygame.time.Clock()
    
    # Training parameters
    episode = 0
    total_reward = 0
    state = simulation.get_state()
    
    print("Starting AI Traffic Control Simulation...")
    print("Press 'T' to toggle AI control")
    print("Press 'R' to reset simulation")
    print("Press 'ESC' to exit")
    
    ai_enabled = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_t:
                    ai_enabled = not ai_enabled
                    print(f"AI Control: {'Enabled' if ai_enabled else 'Disabled'}")
                elif event.key == pygame.K_r:
                    simulation = TrafficSimulation()
                    ai_controller = TrafficLightAI()
                    state = simulation.get_state()
                    total_reward = 0
                    episode = 0
                    print("Simulation reset")
        
        # AI decision making
        if ai_enabled:
            action = ai_controller.choose_action(state)
            next_state, reward, done = simulation.run_step(action)
            ai_controller.learn(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
        else:
            # Manual control for testing
            simulation.update()
        
        # Always draw the simulation state
        simulation.draw()
        
        # Control the frame rate
        clock.tick(SIMULATION_CONFIG['fps'])
        
        # Print training progress occasionally
        if episode % 100 == 0 and ai_enabled:
            print(f"Episode: {episode}, Total Reward: {total_reward:.2f}, Exploration: {ai_controller.exploration_rate:.3f}")
        
        episode += 1
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()