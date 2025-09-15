import pygame
import random
from config import SIMULATION_CONFIG

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
YELLOW = (200, 200, 0)

class Car(pygame.sprite.Sprite):
    """Represents a car in the simulation."""
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface([20, 10])
        if direction in ['east', 'west']:
            self.image = pygame.transform.rotate(self.image, 90)
            self.rect = self.image.get_rect(topleft=(x, y))
        else:
            self.rect = self.image.get_rect(topleft=(x,y))

        self.image.fill(random.choice([(30, 144, 255), (255, 165, 0), (128, 0, 128)]))
        self.direction = direction
        self.speed = SIMULATION_CONFIG['car_speed']

    def update(self, traffic_light_status, all_cars):
        """Move the car based on its direction, traffic lights, and other cars."""
        # --- Front Collision Check ---
        can_move_forward = True
        # Create a sensor rect just in front of the car to detect cars ahead
        sensor_distance = self.speed + 3 
        sensor_rect = self.rect.copy()
        if self.direction == "east":
            sensor_rect.move_ip(sensor_distance, 0)
        elif self.direction == "west":
            sensor_rect.move_ip(-sensor_distance, 0)
        elif self.direction == "south":
            sensor_rect.move_ip(0, sensor_distance)
        elif self.direction == "north":
            sensor_rect.move_ip(0, -sensor_distance)
        
        # Check if the sensor collides with any other car
        for car in all_cars:
            if car is not self and sensor_rect.colliderect(car.rect):
                can_move_forward = False
                break

        # --- Red Light Check at precise stop lines ---
        should_stop_for_light = False
        # Eastbound car approaching a red light
        if self.direction == "east" and self.rect.right >= 340 and self.rect.right <= 350 and traffic_light_status == 1:
            should_stop_for_light = True
        # Westbound car approaching a red light
        elif self.direction == "west" and self.rect.left <= 460 and self.rect.left >= 450 and traffic_light_status == 1:
            should_stop_for_light = True
        # Southbound car approaching a red light
        elif self.direction == "south" and self.rect.bottom >= 340 and self.rect.bottom <= 350 and traffic_light_status == 0:
            should_stop_for_light = True
        # Northbound car approaching a red light
        elif self.direction == "north" and self.rect.top <= 460 and self.rect.top >= 450 and traffic_light_status == 0:
            should_stop_for_light = True
        
        # --- Movement Logic ---
        if can_move_forward and not should_stop_for_light:
            if self.direction == "east":
                self.rect.x += self.speed
            elif self.direction == "west":
                self.rect.x -= self.speed
            elif self.direction == "south":
                self.rect.y += self.speed
            elif self.direction == "north":
                self.rect.y -= self.speed
        
        # Remove car if it goes well off-screen
        if not pygame.Rect(-50, -50, SIMULATION_CONFIG['width'] + 100, SIMULATION_CONFIG['height'] + 100).colliderect(self.rect):
            self.kill()


class TrafficSimulation:
    """Manages the entire traffic simulation environment."""
    def __init__(self):
        self.screen = pygame.display.set_mode((SIMULATION_CONFIG['width'], SIMULATION_CONFIG['height']))
        pygame.display.set_caption("AI Traffic Control")
        self.all_sprites = pygame.sprite.Group()
        self.cars = pygame.sprite.Group()
        self.light_status = 0 # 0 for N/S green, 1 for E/W green
        self.light_timer = 0
        self.spawn_timer = 0
        self.font = pygame.font.SysFont(None, 36)
        self.total_vehicles_spawned = 0
        self.waiting_vehicles = 0

    def run_step(self, action):
        """Run one step of the simulation for the AI."""
        # Action: 0 = N/S green, 1 = E/W green
        self.light_status = action
        
        self._spawn_cars()
        self.all_sprites.update(self.light_status, self.cars)
        
        reward = self._calculate_reward()
        next_state = self.get_state()
        done = False # This simulation runs continuously
        
        return next_state, reward, done

    def update(self):
        """Update all game objects. Used for non-AI mode."""
        self._spawn_cars()
        # Pass the group of cars to each car for collision detection
        self.all_sprites.update(self.light_status, self.cars)
        self._calculate_reward() # Update waiting counter for display
        self.light_timer -= 1
        if self.light_timer <= 0:
            self.light_status = 1 - self.light_status # Flip light
            self.light_timer = 360 # Reset timer - SLOWED DOWN from 180

    def _calculate_reward(self):
        """Calculate reward based on waiting cars and update the counter."""
        waiting_cars = 0
        # Check for cars stopped at their respective stop lines for red lights
        for car in self.cars:
            if car.direction in ["east", "west"] and self.light_status == 1: # E/W light is RED
                if car.rect.right >= 340 and car.rect.right <= 350:
                    waiting_cars += 1
            if car.direction in ["west", "east"] and self.light_status == 1: # E/W light is RED
                 if car.rect.left <= 460 and car.rect.left >= 450:
                    waiting_cars += 1
            if car.direction in ["north", "south"] and self.light_status == 0: # N/S light is RED
                if car.rect.bottom >= 340 and car.rect.bottom <= 350:
                    waiting_cars +=1
            if car.direction in ["south", "north"] and self.light_status == 0: # N/S light is RED
                if car.rect.top <= 460 and car.rect.top >= 450:
                    waiting_cars += 1

        self.waiting_vehicles = waiting_cars
        return -waiting_cars # Negative reward for waiting cars

    def get_state(self):
        """Get a simplified state for the AI."""
        ns_wait = 0
        ew_wait = 0
        for car in self.cars:
             if car.direction in ["north", "south"]:
                 ns_wait += 1
             else:
                 ew_wait += 1
        return (ns_wait, ew_wait)

    def _spawn_cars(self):
        """Randomly spawn new cars, avoiding collisions at spawn points."""
        self.spawn_timer += 1
        if self.spawn_timer > (SIMULATION_CONFIG['fps'] / SIMULATION_CONFIG['car_spawn_rate']):
            self.spawn_timer = 0
            
            lane = random.choice(['N', 'S', 'E', 'W'])
            
            # Define spawn points and check if they are clear
            spawn_points = {
                'N': {'pos': (420, -40), 'rect': pygame.Rect(420, 0, 10, 20), 'dir': 'south'},
                'S': {'pos': (370, 820), 'rect': pygame.Rect(370, 800, 10, 20), 'dir': 'north'},
                'E': {'pos': (-40, 370), 'rect': pygame.Rect(0, 370, 20, 10), 'dir': 'east'},
                'W': {'pos': (820, 420), 'rect': pygame.Rect(800, 420, 20, 10), 'dir': 'west'}
            }
            
            info = spawn_points[lane]
            spawn_rect = info['rect']
            
            # Check for collision at spawn point
            is_spawn_blocked = any(car.rect.colliderect(spawn_rect) for car in self.cars)

            if not is_spawn_blocked:
                self.total_vehicles_spawned += 1 # Increment vehicle counter
                x, y = info['pos']
                direction = info['dir']
                car = Car(x, y, direction)
                self.all_sprites.add(car)
                self.cars.add(car)

    def draw(self):
        """Draw everything on the screen."""
        self.screen.fill(GRAY)
        # Draw roads
        pygame.draw.rect(self.screen, BLACK, (350, 0, 100, 800))
        pygame.draw.rect(self.screen, BLACK, (0, 350, 800, 100))
        
        # Draw traffic lights
        ns_color = GREEN if self.light_status == 0 else RED
        ew_color = GREEN if self.light_status == 1 else RED
        pygame.draw.circle(self.screen, ns_color, (470, 330), 15) # N/S light
        pygame.draw.circle(self.screen, ew_color, (330, 470), 15) # E/W light
        
        self.all_sprites.draw(self.screen)
        
        # Display car counts
        ns_wait, ew_wait = self.get_state()
        ns_text = self.font.render(f"N/S Lane Cars: {ns_wait}", True, WHITE)
        ew_text = self.font.render(f"E/W Lane Cars: {ew_wait}", True, WHITE)
        total_text = self.font.render(f"Total Vehicles: {self.total_vehicles_spawned}", True, WHITE)
        waiting_text = self.font.render(f"Currently Waiting: {self.waiting_vehicles}", True, WHITE)
        self.screen.blit(ns_text, (10, 10))
        self.screen.blit(ew_text, (10, 50))
        self.screen.blit(total_text, (10, 90))
        self.screen.blit(waiting_text, (10, 130))
        
        pygame.display.flip()



