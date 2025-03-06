import pygame
import random
import math
import heapq  # Add this for pathfinding
import utils

class Villager(pygame.sprite.Sprite):
    def __init__(self, x, y, assets, tile_size=32):
        super().__init__()
        
        self.TILE_SIZE = tile_size
        # Sleep state
        self.is_sleeping = True  # Start asleep
        self.bed_position = None  # Will be set when home is assigned
        self.wake_hour = random.uniform(6.0, 9.0)  # Random wake time between 6-9 AM
        self.sleep_hour = random.uniform(21.0, 23.0)  # Random sleep time between 9-11 PM

        # Modify initial activity
        self.current_activity = "Sleeping"
        
        # Select a random villager sprite
        villager_keys = list(assets['characters'].keys())
        if villager_keys:
            sprite_key = random.choice(villager_keys)
            self.base_image = assets['characters'][sprite_key]
            self.image = self.base_image.copy()
            self.rect = self.image.get_rect(center=(x, y))
        else:
            # Fallback if no sprites available
            self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 0, 0), (12, 12), 12)
            self.rect = self.image.get_rect(center=(x, y))
            self.base_image = self.image.copy()
        
        # Villager properties
        self.name = utils.generate_name()
        self.job = random.choice([
            "Farmer", "Blacksmith", "Merchant", "Guard", "Baker",
            "Tailor", "Carpenter", "Miner", "Hunter", "Innkeeper"
        ])
        self.mood = random.choice([
            "Happy", "Content", "Neutral", "Tired", "Excited",
            "Curious", "Busy", "Relaxed", "Bored", "Worried"
        ])
        self.health = random.randint(70, 100)
        self.energy = random.randint(50, 100)
        self.money = random.randint(10, 100)
        
        # Movement
        self.position = pygame.math.Vector2(x, y)
        self.destination = None
        self.path = []
        self.speed = random.uniform(0.3, 1.0)  # Villager movement speed
        self.idle_timer = 0
        
        # Interaction
        self.is_selected = False
        self.is_talking = False
        self.talk_timer = 0
        self.talk_cooldown = random.randint(5000, 15000)  # 5-15 seconds between talks
        
        # Make sure conversations is not empty before choosing
        if assets['sounds']['conversations']:
            self.conversation_sound = random.choice(assets['sounds']['conversations'])
        else:
            # Create a dummy sound if needed
            self.conversation_sound = pygame.mixer.Sound(buffer=bytearray(100))
        
        # Activity tracking
        self.activity_timer = 0
        
        # Update timestamp
        self.last_update = pygame.time.get_ticks()
    
    def update(self, village_data, current_time, assets):
        # Calculate delta time
        dt = current_time - self.last_update
        self.last_update = current_time
        
        # Update talking state
        self.talk_timer += dt
        if self.talk_timer > self.talk_cooldown:
            self.talk_timer = 0
            self.is_talking = random.random() < 0.3  # 30% chance to be talking
        
        # Update activity
        self.activity_timer += dt
        if self.activity_timer > 10000:  # Change activity every 10 seconds
            self.activity_timer = 0
            self.current_activity = random.choice([
                "Wandering", "Working", "Shopping", "Resting", "Socializing"
            ])
        
        # Handle movement
        if self.destination is None or self.idle_timer > 0:
            # If no destination or idle, handle idle timer
            if self.idle_timer > 0:
                self.idle_timer -= dt
            else:
                # Find new destination
                self.find_new_destination(village_data)
                self.idle_timer = 0
        else:
            # Move toward destination
            dx = self.destination[0] - self.position.x
            dy = self.destination[1] - self.position.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 2:  # Close enough to destination
                self.position.x = self.destination[0]
                self.position.y = self.destination[1]
                self.destination = None
                self.idle_timer = random.randint(2000, 5000)  # Idle for 2-5 seconds
            else:
                # Move toward destination
                move_x = dx / distance * self.speed * (dt / 16.67)
                move_y = dy / distance * self.speed * (dt / 16.67)
                
                self.position.x += move_x
                self.position.y += move_y
                
                # Update rect position
                self.rect.centerx = int(self.position.x)
                self.rect.centery = int(self.position.y)
        
        # Ensure villager stays within village bounds
        padding = self.TILE_SIZE * 2
        if self.position.x < padding:
            self.position.x = padding
        elif self.position.x > village_data['size'] - padding:
            self.position.x = village_data['size'] - padding
            
        if self.position.y < padding:
            self.position.y = padding
        elif self.position.y > village_data['size'] - padding:
            self.position.y = village_data['size'] - padding
        
        # Make sure rect position matches
        self.rect.centerx = int(self.position.x)
        self.rect.centery = int(self.position.y)
    
    def find_new_destination(self, village_data):
        """Find a new destination for the villager."""
        destination_type = random.choice(["random", "building", "path"])
        
        if destination_type == "building" and village_data['buildings']:
            # Head to a random building
            building = random.choice(village_data['buildings'])
            offset_x = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
            offset_y = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
            self.destination = (
                building['position'][0] + offset_x,
                building['position'][1] + offset_y
            )
        elif destination_type == "path" and village_data['paths']:
            # Head to a random path
            path = random.choice(village_data['paths'])
            self.destination = path['position']
        else:
            # Head to a random position but keep within village borders
            # Add padding to keep villagers away from the edge
            padding = self.TILE_SIZE * 3
            self.destination = (
                random.randint(padding, village_data['size'] - padding),
                random.randint(padding, village_data['size'] - padding)
            )
    
    def get_status(self):
        """Get villager status for display."""
        return {
            "Name": self.name,
            "Job": self.job,
            "Mood": self.mood,
            "Health": self.health,
            "Energy": self.energy,
            "Money": self.money,
            "Activity": self.current_activity
        }
    
    def draw_selection_indicator(self, surface, camera_offset_x, camera_offset_y):
        """Draw a selection indicator around the villager if selected."""
        if self.is_selected:
            # Draw circle around villager
            center_x = self.rect.centerx - camera_offset_x
            center_y = self.rect.centery - camera_offset_y
            radius = max(self.rect.width, self.rect.height) // 2 + 5
            pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), radius, 2)
            
            # Draw speech indicator if talking
            if self.is_talking:
                bubble_x = center_x + radius
                bubble_y = center_y - radius
                pygame.draw.circle(surface, (255, 255, 255), (bubble_x, bubble_y), 8)
                pygame.draw.circle(surface, (0, 0, 0), (bubble_x, bubble_y), 8, 1)
                
                # Speech dots
                for i in range(3):
                    dot_x = bubble_x - 4 + i * 4
                    dot_y = bubble_y
                    pygame.draw.circle(surface, (0, 0, 0), (dot_x, dot_y), 1)

    def enhanced_update(self, village_data, current_time, assets, time_manager=None):
        """Enhanced update method that considers time of day for activities."""
        # Calculate delta time
        dt = current_time - self.last_update
        self.last_update = current_time

        # Get current time of day if available
        current_hour = 6  # Default to 6am
        if time_manager:
            current_hour = time_manager.current_hour

        # Determine if it's sleeping time
        # Use personalized sleep/wake hours instead of fixed times
        sleeping_time = current_hour < self.wake_hour or current_hour >= self.sleep_hour

        # Handle sleep state changes
        if sleeping_time and not self.is_sleeping:
            # Time to go to sleep
            self.is_sleeping = True
            self.current_activity = "Sleeping"
            # Cancel any current destination
            self.destination = None
        elif not sleeping_time and self.is_sleeping:
            # Time to wake up
            self.is_sleeping = False
            self.current_activity = "Waking up"
            # Add some "grogginess" - slower movement for a short while
            self.speed = self.speed * 0.7
            # Reset speed after a few minutes (game time)
            pygame.time.set_timer(pygame.USEREVENT, int(random.uniform(1000, 3000)), 1)

        # Update talking state only if not sleeping
        if not self.is_sleeping:
            self.talk_timer += dt
            if self.talk_timer > self.talk_cooldown:
                self.talk_timer = 0
                self.is_talking = random.random() < 0.3  # 30% chance to be talking
        else:
            self.is_talking = False  # Don't talk while sleeping

        # Update activity based on time of day
        self.activity_timer += dt
        if self.activity_timer > 10000:  # Change activity every 10 seconds
            self.activity_timer = 0

            # If sleeping, keep the sleeping activity
            if self.is_sleeping:
                self.current_activity = "Sleeping"
            else:
                # Determine activity based on time of day if not sleeping
                if hasattr(self, 'daily_activities') and self.daily_activities:
                    # Early morning activities (6 AM - 9 AM)
                    if 6 <= current_hour < 9:
                        # Morning routines - wake up, breakfast
                        morning_activities = ["Waking up", "Getting ready", "Having breakfast"]
                        if self.job in ["Baker", "Farmer"]:
                            self.current_activity = "Starting early shift"
                        else:
                            self.current_activity = random.choice(morning_activities)

                    # Morning work activities (9 AM - 12 PM)
                    elif 9 <= current_hour < 12:
                        if self.job in ["Baker", "Farmer", "Blacksmith", "Tailor", "Carpenter"]:
                            self.current_activity = "Working"
                        else:
                            activity_index = int((current_hour - 9) / 3 * len(self.daily_activities))
                            self.current_activity = self.daily_activities[min(activity_index, len(self.daily_activities)-1)]

                    # Midday activities (12 PM - 2 PM)
                    elif 12 <= current_hour < 14:
                        lunch_activities = ["Having lunch", "Taking a break", "Socializing"]
                        self.current_activity = random.choice(lunch_activities)

                    # Afternoon activities (2 PM - 6 PM)
                    elif 14 <= current_hour < 18:
                        if self.job in ["Merchant", "Guard", "Innkeeper"]:
                            self.current_activity = "Working"
                        else:
                            activity_index = int((current_hour - 14) / 4 * len(self.daily_activities))
                            self.current_activity = self.daily_activities[min(activity_index, len(self.daily_activities)-1)]

                    # Evening activities (6 PM - sleep time)
                    elif 18 <= current_hour < self.sleep_hour:
                        if self.job in ["Guard", "Innkeeper"]:
                            self.current_activity = "Working evening shift"
                        else:
                            # Activities like eating dinner, relaxing
                            evening_activities = [act for act in self.daily_activities
                                                if "home" in act.lower() or "inn" in act.lower()
                                                or "relax" in act.lower()]
                            if evening_activities:
                                self.current_activity = random.choice(evening_activities)
                            else:
                                self.current_activity = "Heading home"
                else:
                    # Fallback to random activities
                    self.current_activity = random.choice([
                        "Wandering", "Working", "Shopping", "Resting", "Socializing"
                    ])

        # Handle movement based on current activity and sleep state
        if self.is_sleeping:
            self.handle_sleep_behavior(dt)
        else:
            self.handle_activity_movement(village_data, dt, current_hour)

        # Ensure villager stays within village bounds
        padding = self.TILE_SIZE * 2
        if self.position.x < padding:
            self.position.x = padding
        elif self.position.x > village_data['size'] - padding:
            self.position.x = village_data['size'] - padding

        if self.position.y < padding:
            self.position.y = padding
        elif self.position.y > village_data['size'] - padding:
            self.position.y = village_data['size'] - padding

        # Make sure rect position matches
        self.rect.centerx = int(self.position.x)
        self.rect.centery = int(self.position.y)
        
    def handle_activity_movement(self, village_data, dt, current_hour):
        """Handle movement based on current activity and time of day."""
        # Handle sleep behavior at night
        if "Sleeping" in self.current_activity and hasattr(self, 'home') and self.home:
            # Stay at home position during sleep
            home_pos = self.home.get('position')
            if home_pos:
                # Gradually move closer to bed position (slightly offset from home center)
                bed_x = home_pos[0] + self.TILE_SIZE // 2
                bed_y = home_pos[1] + self.TILE_SIZE // 2
                
                # If not at bed, move toward it
                dx = bed_x - self.position.x
                dy = bed_y - self.position.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > 5:  # Not at bed yet
                    # Move slowly to bed
                    move_x = dx / distance * self.speed * 0.5 * (dt / 16.67)
                    move_y = dy / distance * self.speed * 0.5 * (dt / 16.67)
                    
                    self.position.x += move_x
                    self.position.y += move_y
                    
                # Always clear destination during sleep
                self.destination = None
                return
        
        # Handle work activity during work hours
        if ("Working" in self.current_activity and 
            hasattr(self, 'workplace') and self.workplace and 
            8 <= current_hour < 18):  # Work hours
            
            workplace_pos = self.workplace.get('position')
            if workplace_pos:
                # Set destination to workplace if not already there
                if not self.destination or random.random() < 0.1:  # Occasionally change position
                    offset_x = random.randint(-self.TILE_SIZE // 2, self.TILE_SIZE // 2)
                    offset_y = random.randint(-self.TILE_SIZE // 2, self.TILE_SIZE // 2)
                    self.destination = (
                        workplace_pos[0] + offset_x,
                        workplace_pos[1] + offset_y
                    )
        
        # Handle "heading home" or evening activities
        if ("home" in self.current_activity.lower() and 
            hasattr(self, 'home') and self.home):
            
            home_pos = self.home.get('position')
            if home_pos and (not self.destination or random.random() < 0.1):
                offset_x = random.randint(-self.TILE_SIZE // 2, self.TILE_SIZE // 2)
                offset_y = random.randint(-self.TILE_SIZE // 2, self.TILE_SIZE // 2)
                self.destination = (
                    home_pos[0] + offset_x,
                    home_pos[1] + offset_y
                )
        
        # Regular movement handling
        if self.destination is None or self.idle_timer > 0:
            # If no destination or idle, handle idle timer
            if self.idle_timer > 0:
                self.idle_timer -= dt
            else:
                # Find new destination
                self.find_new_destination(village_data)
                self.idle_timer = 0
        else:
            # Move toward destination
            dx = self.destination[0] - self.position.x
            dy = self.destination[1] - self.position.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 2:  # Close enough to destination
                self.position.x = self.destination[0]
                self.position.y = self.destination[1]
                self.destination = None
                self.idle_timer = random.randint(2000, 5000)  # Idle for 2-5 seconds
            else:
                # Move toward destination
                move_x = dx / distance * self.speed * (dt / 16.67)
                move_y = dy / distance * self.speed * (dt / 16.67)
                
                self.position.x += move_x
                self.position.y += move_y
                
                # Update rect position
                self.rect.centerx = int(self.position.x)
                self.rect.centery = int(self.position.y)

    def initialize_home_position(self):
        """Initialize home position and put villager there at game start."""
        if hasattr(self, 'home') and self.home and 'position' in self.home:
            home_pos = self.home['position']

            # Set bed position (slightly offset from home center)
            self.bed_position = (
                home_pos[0] + self.TILE_SIZE // 2 + random.randint(-5, 5),
                home_pos[1] + self.TILE_SIZE // 2 + random.randint(-5, 5)
            )

            # Move to bed
            self.position.x = self.bed_position[0]
            self.position.y = self.bed_position[1]
            self.rect.centerx = int(self.position.x)
            self.rect.centery = int(self.position.y)

            # Clear destination
            self.destination = None

    def handle_sleep_behavior(self, dt):
        """Handle sleeping behavior - stay in bed with occasional subtle movements."""
        # If we have a bed position, move toward it
        if self.bed_position:
            # Calculate distance to bed
            dx = self.bed_position[0] - self.position.x
            dy = self.bed_position[1] - self.position.y
            distance = math.sqrt(dx*dx + dy*dy)

            if distance > 5:  # Not at bed yet
                # Move slowly to bed
                move_x = dx / distance * self.speed * 0.5 * (dt / 16.67)
                move_y = dy / distance * self.speed * 0.5 * (dt / 16.67)

                self.position.x += move_x
                self.position.y += move_y
            else:
                # Occasionally make small movements to simulate restless sleep
                if random.random() < 0.01:  # Reduced 1% chance per update (from 2%)
                    # Much smaller movement amplitude during sleep
                    self.position.x += random.uniform(-0.5, 0.5)
                    self.position.y += random.uniform(-0.5, 0.5)

        # Always clear destination during sleep
        self.destination = None

    def draw_sleep_indicator(self, surface, camera_offset_x, camera_offset_y):
        """Draw sleep indicators (ZZZs) above the villager if sleeping."""
        if self.is_sleeping:
            center_x = self.rect.centerx - camera_offset_x
            center_y = self.rect.centery - camera_offset_y - 15

            # Draw small ZZZs
            font = pygame.font.SysFont(None, 16)
            zzz_text = font.render("ZZZ", True, (200, 200, 255))

            # Create a small shadow for better visibility
            shadow_text = font.render("ZZZ", True, (0, 0, 0))
            surface.blit(shadow_text, (center_x - zzz_text.get_width() // 2 + 1, center_y + 1))
            surface.blit(zzz_text, (center_x - zzz_text.get_width() // 2, center_y))

    def find_path(self, start, goal, village_data):
        """Find a path from start to goal using A* algorithm."""
        # Convert positions to grid coordinates
        grid_size = self.TILE_SIZE
        start_grid = (start[0] // grid_size, start[1] // grid_size)
        goal_grid = (goal[0] // grid_size, goal[1] // grid_size)
        
        # If start and goal are the same, return empty path
        if start_grid == goal_grid:
            return []
        
        # Create a set of path tiles for faster checking
        path_positions = set()
        for path in village_data['paths']:
            pos = path['position']
            path_positions.add((pos[0] // grid_size, pos[1] // grid_size))
        
        # Create a set of blocked tiles (buildings, water)
        blocked_positions = set()
        for building in village_data['buildings']:
            pos = building['position']
            size = 3 if building['size'] == 'large' else (2 if building['size'] == 'medium' else 1)
            for dx in range(size):
                for dy in range(size):
                    blocked_positions.add(((pos[0] // grid_size) + dx, (pos[1] // grid_size) + dy))
        
        for water_tile in village_data['water']:
            pos = water_tile['position']
            blocked_positions.add((pos[0] // grid_size, pos[1] // grid_size))
        
        # Initialize A* algorithm
        open_set = []
        heapq.heappush(open_set, (0, start_grid))
        came_from = {}
        g_score = {start_grid: 0}
        f_score = {start_grid: self.heuristic(start_grid, goal_grid)}
        
        village_size_grid = village_data['size'] // grid_size
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == goal_grid:
                # Goal reached, reconstruct path
                path = [goal]
                grid_pos = goal_grid
                while grid_pos in came_from:
                    grid_pos = came_from[grid_pos]
                    path.append((grid_pos[0] * grid_size + grid_size // 2, 
                                grid_pos[1] * grid_size + grid_size // 2))
                path.reverse()
                return path
            
            # Check neighbors
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Skip if out of bounds
                if (neighbor[0] < 0 or neighbor[0] >= village_size_grid or
                    neighbor[1] < 0 or neighbor[1] >= village_size_grid):
                    continue
                
                # Skip if blocked
                if neighbor in blocked_positions:
                    continue
                
                # Calculate costs
                tentative_g = g_score.get(current, float('inf'))
                if dx == 0 or dy == 0:
                    # Cardinal direction
                    move_cost = 1.0
                else:
                    # Diagonal
                    move_cost = 1.414
                
                # Prefer paths
                if neighbor in path_positions:
                    move_cost *= 0.8  # 20% discount for paths
                
                tentative_g += move_cost
                
                if tentative_g < g_score.get(neighbor, float('inf')):
                    # This path is better
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal_grid)
                    
                    # Add to open set if not already there
                    for i, (_, pos) in enumerate(open_set):
                        if pos == neighbor:
                            break
                    else:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # No path found
        return []
    
    def heuristic(self, a, b):
        """Calculate heuristic distance between two points."""
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
