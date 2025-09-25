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
TRACK_COLOR = (50, 50, 50)
TIE_COLOR = (70, 50, 30)


class Train(pygame.sprite.Sprite):
    """Represents a train in the simulation."""
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface([40, 15]) # Made the sprite longer
        if direction in ['north', 'south']:
            self.image = pygame.transform.rotate(self.image, 90)
            self.rect = self.image.get_rect(topleft=(x, y))
        else:
            self.rect = self.image.get_rect(topleft=(x,y))

        self.image.fill(random.choice([(150, 150, 150), (100, 100, 120), (180, 180, 180)]))
        self.direction = direction
        self.speed = SIMULATION_CONFIG['train_speed']

    def update(self, traffic_light_status, all_trains):
        """Move the train based on its direction, signals, and other trains."""
        # --- Front Collision Check ---
        can_move_forward = True
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

        for train in all_trains:
            if train is not self and sensor_rect.colliderect(train.rect):
                can_move_forward = False
                break

        # --- Red Light Check at precise stop lines ---
        should_stop_for_light = False
        if self.direction == "east" and self.rect.right >= 340 and self.rect.right <= 350 and traffic_light_status == 1:
            should_stop_for_light = True
        elif self.direction == "west" and self.rect.left <= 460 and self.rect.left >= 450 and traffic_light_status == 1:
            should_stop_for_light = True
        elif self.direction == "south" and self.rect.bottom >= 340 and self.rect.bottom <= 350 and traffic_light_status == 0:
            should_stop_for_light = True
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

        if not pygame.Rect(-60, -60, SIMULATION_CONFIG['width'] + 120, SIMULATION_CONFIG['height'] + 120).colliderect(self.rect):
            self.kill()


class TrafficSimulation:
    """Manages the entire traffic simulation environment."""
    def __init__(self):
        self.screen = pygame.display.set_mode((SIMULATION_CONFIG['width'], SIMULATION_CONFIG['height']))
        pygame.display.set_caption("AI Train Control")
        self.all_sprites = pygame.sprite.Group()
        self.trains = pygame.sprite.Group()
        self.light_status = 0 # 0 for N/S green, 1 for E/W green
        self.light_timer = 0
        self.spawn_timer = 0
        self.font = pygame.font.SysFont(None, 36)
        self.total_trains_spawned = 0
        self.waiting_trains = 0

    def run_step(self, action):
        """Run one step of the simulation for the AI."""
        self.light_status = action
        self._spawn_trains()
        self.all_sprites.update(self.light_status, self.trains)
        reward = self._calculate_reward()
        next_state = self.get_state()
        done = False
        return next_state, reward, done

    def update(self):
        """Update all game objects. Used for non-AI mode."""
        self._spawn_trains()
        self.all_sprites.update(self.light_status, self.trains)
        self._calculate_reward()
        self.light_timer -= 1
        if self.light_timer <= 0:
            self.light_status = 1 - self.light_status
            self.light_timer = 360

    def _calculate_reward(self):
        """Calculate reward based on waiting trains and update the counter."""
        waiting_trains = 0
        for train in self.trains:
            # Check for trains stopped at their respective stop lines for red lights
            if train.direction in ["east", "west"] and self.light_status == 1: # E/W light is RED
                if train.rect.right >= 340 and train.rect.right <= 350 or \
                   train.rect.left <= 460 and train.rect.left >= 450:
                    waiting_trains += 1
            elif train.direction in ["north", "south"] and self.light_status == 0: # N/S light is RED
                if train.rect.bottom >= 340 and train.rect.bottom <= 350 or \
                   train.rect.top <= 460 and train.rect.top >= 450:
                    waiting_trains += 1

        self.waiting_trains = waiting_trains
        return -waiting_trains

    def get_state(self):
        """Get a simplified state for the AI."""
        ns_wait = 0
        ew_wait = 0
        for train in self.trains:
             if train.direction in ["north", "south"]:
                 ns_wait += 1
             else:
                 ew_wait += 1
        return (ns_wait, ew_wait)

    def _spawn_trains(self):
        """Randomly spawn new trains, avoiding collisions at spawn points."""
        self.spawn_timer += 1
        if self.spawn_timer > (SIMULATION_CONFIG['fps'] / SIMULATION_CONFIG['train_spawn_rate']):
            self.spawn_timer = 0
            lane = random.choice(['N', 'S', 'E', 'W'])

            spawn_points = {
                'N': {'pos': (420, -50), 'rect': pygame.Rect(420, 0, 15, 40), 'dir': 'south'},
                'S': {'pos': (365, 850), 'rect': pygame.Rect(365, 800, 15, 40), 'dir': 'north'},
                'E': {'pos': (-50, 365), 'rect': pygame.Rect(0, 365, 40, 15), 'dir': 'east'},
                'W': {'pos': (850, 420), 'rect': pygame.Rect(800, 420, 40, 15), 'dir': 'west'}
            }
            
            info = spawn_points[lane]
            spawn_rect = info['rect']
            is_spawn_blocked = any(train.rect.colliderect(spawn_rect) for train in self.trains)

            if not is_spawn_blocked:
                self.total_trains_spawned += 1
                x, y = info['pos']
                direction = info['dir']
                train = Train(x, y, direction)
                self.all_sprites.add(train)
                self.trains.add(train)

    def draw(self):
        """Draw everything on the screen."""
        self.screen.fill(GRAY)
        
        # --- Draw Railway Tracks ---
        # Draw horizontal ties
        for y in range(0, SIMULATION_CONFIG['width'], 20):
             pygame.draw.rect(self.screen, TIE_COLOR, (y, 385, 15, 30))
             pygame.draw.rect(self.screen, TIE_COLOR, (y, 415, 15, 30))

        # Draw vertical ties
        for x in range(0, SIMULATION_CONFIG['height'], 20):
             pygame.draw.rect(self.screen, TIE_COLOR, (385, x, 30, 15))
             pygame.draw.rect(self.screen, TIE_COLOR, (415, x, 30, 15))

        # Draw rails
        pygame.draw.rect(self.screen, TRACK_COLOR, (0, 375, 800, 10))
        pygame.draw.rect(self.screen, TRACK_COLOR, (0, 415, 800, 10))
        pygame.draw.rect(self.screen, TRACK_COLOR, (375, 0, 10, 800))
        pygame.draw.rect(self.screen, TRACK_COLOR, (415, 0, 10, 800))

        # Draw traffic lights (signals)
        ns_color = GREEN if self.light_status == 0 else RED
        ew_color = GREEN if self.light_status == 1 else RED
        pygame.draw.circle(self.screen, ns_color, (440, 330), 15)
        pygame.draw.circle(self.screen, ew_color, (330, 440), 15)
        
        self.all_sprites.draw(self.screen)
        
        # --- Display Train Counters ---
        ns_trains, ew_trains = self.get_state()
        ns_text = self.font.render(f"N/S Line Trains: {ns_trains}", True, WHITE)
        ew_text = self.font.render(f"E/W Line Trains: {ew_trains}", True, WHITE)
        total_text = self.font.render(f"Total Trains: {self.total_trains_spawned}", True, WHITE)
        waiting_text = self.font.render(f"Currently Waiting: {self.waiting_trains}", True, WHITE)
        self.screen.blit(ns_text, (10, 10))
        self.screen.blit(ew_text, (10, 50))
        self.screen.blit(total_text, (10, 90))
        self.screen.blit(waiting_text, (10, 130))
        
        pygame.display.flip()



