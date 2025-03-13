import pygame
import random
import math
import utils
import Interface

class Villager(pygame.sprite.Sprite):
    def __init__(self, x, y, assets, tile_size=32):
        super().__init__()
        
        self.TILE_SIZE = tile_size
        # Sleep state
        self.is_sleeping = True  # Start asleep
        self.bed_position = None  # Will be set when home is assigned
        self.wake_hour = random.uniform(6.0, 9.0)  # Random wake time between 6-9 AM
        self.sleep_hour = random.uniform(21.0, 23.0)  # Random sleep time between 9-11 PM
        
        # Sleep state override system
        self.sleep_override = False
        self.sleep_override_time = 0
        self.sleep_override_duration = 0

        # Modify initial activity
        self.current_activity = "Sleeping"
        self.pathfinding_grid = None
        self.path_cache = {}
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
        
        # Personality traits
        self.path_preference = random.uniform(0.3, 0.95) # How much they prefer to stay on paths
        self.direct_route_preference = random.uniform(0.1, 0.8)  # How much they prefer direct routes
        self.wandering_tendency = random.uniform(0.05, 0.3)  # Tendency to wander off course

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

        
        if self.job in ["Guard", "Merchant", "Baker"]:
            # These jobs tend to follow proper paths more (add 0.1-0.2 to preference)
            self.path_preference = min(0.99, self.path_preference + random.uniform(0.1, 0.2))
        elif self.job in ["Hunter", "Miner"]:
            # These jobs are used to wilderness and take shortcuts more often
            self.path_preference = max(0.1, self.path_preference - random.uniform(0.1, 0.2))

        self.health = random.randint(70, 100)
        self.energy = random.randint(50, 100)
        self.money = random.randint(10, 100)
        
        # Movement
        self.position = pygame.math.Vector2(x, y)
        self.destination = None
        self.path = [] # store calculated path
        self.current_path_index = 0 # current index in the path
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
        
        # First frame flag to preserve bed position on first update
        self._first_frame = True
    
    def get_status(self):
        """Get villager status for display with sleep override info."""
        status = {
            "Name": self.name,
            "Job": self.job,
            "Mood": self.mood,
            "Health": self.health,
            "Energy": self.energy,
            "Money": self.money,
            "Activity": self.current_activity
        }
        
        # Add sleep override info if applicable
        if hasattr(self, 'sleep_override') and self.sleep_override:
            status["Sleep"] = "OVERRIDDEN"
        else:
            status["Sleep"] = "Sleeping" if self.is_sleeping else "Awake"
            
        return status

    def override_sleep_state(self, force_awake=True, duration=10000, village_data=None):
        """
        Override the sleep state for a specific duration.
        
        Args:
            force_awake: If True, force villager awake; if False, force asleep
            duration: Duration in milliseconds before normal sleep cycle resumes
            village_data: Optional village data for path calculation
        """
        print(f"OVERRIDE: Setting {self.name} to {'awake' if force_awake else 'asleep'} for {duration}ms")
        
        self.sleep_override = True
        self.sleep_override_time = pygame.time.get_ticks()
        self.sleep_override_duration = duration
        
        if force_awake:
            old_sleep_state = self.is_sleeping
            self.is_sleeping = False
            self.current_activity = "Waking up (forced)"
            
            # Notify of state change if it actually changed
            if old_sleep_state and hasattr(Interface, 'on_villager_sleep_state_changed'):
                Interface.on_villager_sleep_state_changed(self, False)
                
            # Set an immediate destination
            if hasattr(self, 'home') and self.home and 'position' in self.home:
                # Move away from bed
                home_pos = self.home['position']
                offset_x = random.randint(-20, 20)
                offset_y = random.randint(-20, 20)
                self.destination = (home_pos[0] + offset_x, home_pos[1] + offset_y)
                
                # Calculate path if village data is provided
                if village_data and hasattr(self, 'calculate_path'):
                    start_pos = (self.position.x, self.position.y)
                    self.path = self.calculate_path(start_pos, self.destination, village_data)
                    self.current_path_index = 0
        else:
            old_sleep_state = self.is_sleeping
            self.is_sleeping = True
            self.current_activity = "Sleeping (forced)"
            
            # Notify of state change if it actually changed
            if not old_sleep_state and hasattr(Interface, 'on_villager_sleep_state_changed'):
                Interface.on_villager_sleep_state_changed(self, True)
            
            # Clear destination
            self.destination = None
            self.path = []
            self.current_path_index = 0
        
        # Reset activity timer
        self.activity_timer = 9999

    def update_pathfinding_grid(self):
        # Create a grid representation of obstacles
        grid_size = self.village_data['size'] // self.TILE_SIZE
        self.pathfinding_grid = [[True for _ in range(grid_size)] for _ in range(grid_size)]
        
        # Mark water as impassable
        for water in self.village_data['water']:
            x, y = water['position'][0] // self.TILE_SIZE, water['position'][1] // self.TILE_SIZE
            if 0 <= x < grid_size and 0 <= y < grid_size:
                self.pathfinding_grid[y][x] = False
                
        # Clear path cache when grid changes
        self.path_cache = {}

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
    
    def draw_sleep_indicator(self, surface, camera_offset_x, camera_offset_y):
        """Draw sleep indicators (ZZZs) above the villager if sleeping."""
        if self.is_sleeping:
            center_x = self.rect.centerx - camera_offset_x
            center_y = self.rect.centery - camera_offset_y - 15

            # Create animated "ZZZ" with slight movement
            current_time = pygame.time.get_ticks()
            offset_y = math.sin(current_time / 500) * 2  # Gentle up/down motion
            
            # Draw small ZZZs with animation
            font = pygame.font.SysFont(None, 16)
            zzz_text = font.render("ZZZ", True, (200, 200, 255))

            # Create a small shadow for better visibility
            shadow_text = font.render("ZZZ", True, (0, 0, 0))
            
            # Add shadow
            surface.blit(shadow_text, (center_x - zzz_text.get_width() // 2 + 1, 
                                    center_y + offset_y + 1))
            
            # Add main text
            surface.blit(zzz_text, (center_x - zzz_text.get_width() // 2, 
                                center_y + offset_y))
    
    def initialize_home_position(self):
        """Initialize home position and put villager there at game start."""
        if hasattr(self, 'home') and self.home and 'position' in self.home:
            home_pos = self.home['position']

            # For homes with a size property
            if 'size' in self.home:
                # Calculate home size based on size category
                home_size_tiles = 3 if self.home['size'] == 'large' else (
                                2 if self.home['size'] == 'medium' else 1)
                home_size_px = home_size_tiles * self.TILE_SIZE
                
                # Place bed away from edges
                padding = self.TILE_SIZE // 2
                # Try to place the bed in the top half of the house (away from door)
                bed_x = home_pos[0] + random.randint(padding, home_size_px - padding)
                bed_y = home_pos[1] + random.randint(padding, home_size_px // 2)
            else:
                # Default behavior for homes without size info
                bed_x = home_pos[0] + self.TILE_SIZE // 2 + random.randint(-5, 5)
                bed_y = home_pos[1] + self.TILE_SIZE // 2 + random.randint(-5, 5)

            # Set bed position
            self.bed_position = (bed_x, bed_y)

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
        if hasattr(self, 'bed_position') and self.bed_position:
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
                if random.random() < 0.01:  # 1% chance per update
                    # Much smaller movement amplitude during sleep
                    self.position.x += random.uniform(-0.5, 0.5)
                    self.position.y += random.uniform(-0.5, 0.5)

            # Update rect position to match position vector
            self.rect.centerx = int(self.position.x)
            self.rect.centery = int(self.position.y)
        
        # If no bed position but we have a home, initialize it
        elif hasattr(self, 'home') and self.home and 'position' in self.home:
            # Use the home center as a fallback if bed position is not initialized
            home_pos = self.home['position']
            self.bed_position = (home_pos[0] + self.TILE_SIZE // 2, home_pos[1] + self.TILE_SIZE // 2)
            
            # Add some random offset to avoid perfect overlap with roommates
            self.bed_position = (
                self.bed_position[0] + random.randint(-5, 5),
                self.bed_position[1] + random.randint(-5, 5)
            )

        # Always clear destination during sleep
        self.destination = None

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
                self.path = []
                self.current_path_index = 0
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
                    # Recalculate path to the new destination
                    start_pos = (self.position.x, self.position.y)
                    self.path = self.calculate_path(start_pos, self.destination, village_data)
                    self.current_path_index = 0
        
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
                # Recalculate path to the new destination
                start_pos = (self.position.x, self.position.y)
                self.path = self.calculate_path(start_pos, self.destination, village_data)
                self.current_path_index = 0
        
        # Follow the path if we have one
        if hasattr(self, 'path') and self.path and len(self.path) > 0 and hasattr(self, 'current_path_index'):
            # Skip if we're at the end of the path
            if self.current_path_index >= len(self.path):
                self.destination = None
                self.idle_timer = random.randint(2000, 5000)  # Idle for 2-5 seconds
                return
                
            # Get current waypoint
            waypoint = self.path[self.current_path_index]
            
            # Move toward waypoint
            dx = waypoint[0] - self.position.x
            dy = waypoint[1] - self.position.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 2:  # Close enough to waypoint
                # Move to next waypoint
                self.current_path_index += 1
                
                # Check if we've reached the end of the path
                if self.current_path_index >= len(self.path):
                    self.destination = None
                    self.idle_timer = random.randint(2000, 5000)  # Idle for 2-5 seconds
            else:
                # Move toward waypoint
                move_x = dx / distance * self.speed * (dt / 16.67)
                move_y = dy / distance * self.speed * (dt / 16.67)
                
                self.position.x += move_x
                self.position.y += move_y
                
                # Update rect position
                self.rect.centerx = int(self.position.x)
                self.rect.centery = int(self.position.y)
        else:
            # Regular movement handling (direct path to destination)
            if self.destination is None or self.idle_timer > 0:
                # If no destination or idle, handle idle timer
                if self.idle_timer > 0:
                    self.idle_timer -= dt
                else:
                    # Find new destination
                    self.find_new_destination(village_data)
                    self.idle_timer = 0
            else:
                # No path available, move directly to destination
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
    
    def update(self, village_data, current_time, assets, time_manager=None):
        """Update method that respects manual sleep state overrides."""
        # Store current state for change detection
        old_position = (self.position.x, self.position.y)
        old_activity = self.current_activity if hasattr(self, 'current_activity') else None
        old_sleep_state = self.is_sleeping if hasattr(self, 'is_sleeping') else False
        
        # Calculate delta time
        dt = current_time - self.last_update
        self.last_update = current_time
        
        # First, check if we have a sleep override and if it's still active
        if hasattr(self, 'sleep_override') and self.sleep_override:
            # Check if override has expired
            if current_time - self.sleep_override_time > self.sleep_override_duration:
                # Clear the override
                self.sleep_override = False
                if self.is_selected:
                    print(f"{self.name}'s sleep override has expired")
            else:
                # During override, we still handle movement but skip normal sleep state changes
                if self.is_selected:
                    print(f"{self.name} has an active sleep override - normal sleep cycle suspended")
                    
                # Handle movement based on current sleep state
                if self.is_sleeping:
                    self.handle_sleep_behavior(dt)
                else:
                    # Update talking state only if not sleeping
                    self.talk_timer += dt
                    if self.talk_timer > self.talk_cooldown:
                        self.talk_timer = 0
                        self.is_talking = random.random() < 0.3  # 30% chance to be talking
                    
                    if hasattr(self, 'handle_activity_movement'):
                        current_hour = time_manager.current_hour if time_manager else 6
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
                
                # Update rect position
                self.rect.centerx = int(self.position.x)
                self.rect.centery = int(self.position.y)
                
                # Notify Interface of position change if it's significant
                new_position = (self.position.x, self.position.y)
                position_change = ((new_position[0] - old_position[0])**2 + (new_position[1] - old_position[1])**2)
                if position_change > 1 and hasattr(Interface, 'on_villager_moved'):
                    Interface.on_villager_moved(self, old_position, new_position)
                
                # Skip normal update since we're in override mode
                return
    
        # Skip first frame to preserve bed position
        if hasattr(self, '_first_frame') and self._first_frame:
            self._first_frame = False
            return
                
        # Get current time of day if available
        current_hour = 6  # Default to 6am
        if time_manager:
            current_hour = time_manager.current_hour
            
            # Debug logging for selected villager
            if self.is_selected:
                print(f"Current hour: {current_hour:.2f}, Wake hour: {self.wake_hour:.2f}, Sleep hour: {self.sleep_hour:.2f}")
                print(f"Sleep state: {self.is_sleeping}, Activity: {self.current_activity}")
        
        # FIXED: Determine if it's sleeping time with clearer conditions
        sleeping_time = current_hour < self.wake_hour or current_hour >= self.sleep_hour

        # FIX: Force wake up if it's well past wake time (at least half hour after wake hour)
        if current_hour >= (self.wake_hour + 0.5) and current_hour < (self.sleep_hour - 1.0) and self.is_sleeping:
            if self.is_selected:
                print(f"FORCE WAKING UP {self.name} at hour {current_hour:.2f}")
            self.is_sleeping = False
            self.current_activity = "Waking up"
            
            # IMPORTANT: Create a destination away from bed to force movement
            if hasattr(self, 'home') and self.home and 'position' in self.home:
                home_pos = self.home['position']
                offset_x = random.randint(-10, 10) 
                offset_y = random.randint(-10, 10)
                self.destination = (home_pos[0] + offset_x, home_pos[1] + offset_y)
                
                # Calculate path
                start_pos = (self.position.x, self.position.y)
                self.path = self.calculate_path(start_pos, self.destination, village_data)
                self.current_path_index = 0
            
            # Notify Interface of sleep state change
            if hasattr(Interface, 'on_villager_sleep_state_changed'):
                Interface.on_villager_sleep_state_changed(self, False)

        # Normal sleep state changes
        elif sleeping_time and not self.is_sleeping:
            # Time to go to sleep
            self.is_sleeping = True
            self.current_activity = "Sleeping"
            
            # Notify Interface of sleep state change
            if hasattr(Interface, 'on_villager_sleep_state_changed'):
                Interface.on_villager_sleep_state_changed(self, True)
            
            # Cancel any current destination
            self.destination = None
            self.path = []
            self.current_path_index = 0
            
        elif not sleeping_time and self.is_sleeping:
            # Regular wake up
            self.is_sleeping = False
            self.current_activity = "Waking up"
            
            # IMPORTANT: Create a destination away from bed to force movement
            if hasattr(self, 'home') and self.home and 'position' in self.home:
                home_pos = self.home['position']
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-10, 10)
                self.destination = (home_pos[0] + offset_x, home_pos[1] + offset_y)
                
                # Recalculate path
                start_pos = (self.position.x, self.position.y)
                if hasattr(self, 'calculate_path'):
                    self.path = self.calculate_path(start_pos, self.destination, village_data)
                    self.current_path_index = 0
            
            # Notify Interface of sleep state change
            if hasattr(Interface, 'on_villager_sleep_state_changed'):
                Interface.on_villager_sleep_state_changed(self, False)
            
            # Add some "grogginess" - slower movement for a short while
            self.speed = self.speed * 0.7
            # Reset speed after a short time
            pygame.time.set_timer(pygame.USEREVENT, int(random.uniform(1000, 3000)), 1)

        # Update talking state only if not sleeping
        if not self.is_sleeping:
            self.talk_timer += dt
            if self.talk_timer > self.talk_cooldown:
                self.talk_timer = 0
                self.is_talking = random.random() < 0.3  # 30% chance to be talking
        else:
            self.is_talking = False  # Don't talk while sleeping

        # Update activity based on time of day - with shorter timer for faster updates
        self.activity_timer += dt
        if self.activity_timer > 5000:  # Change activity every 5 seconds (faster updates)
            old_activity = self.current_activity
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
                            activity_index = min(activity_index, len(self.daily_activities)-1)
                            self.current_activity = self.daily_activities[activity_index]
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
                            activity_index = min(activity_index, len(self.daily_activities)-1)
                            self.current_activity = self.daily_activities[activity_index]
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
                
            # Ensure we have a current_path_index value
            if not hasattr(self, 'current_path_index'):
                self.current_path_index = 0
                
        # Notify Interface if activity changed
        if old_activity != self.current_activity and old_activity is not None:
            if hasattr(Interface, 'on_villager_activity_changed'):
                Interface.on_villager_activity_changed(self, old_activity, self.current_activity)

        # Handle movement based on current activity and sleep state
        if self.is_sleeping:
            self.handle_sleep_behavior(dt)
        else:
            # IMPORTANT FIX: If we just woke up and don't have a destination, find one
            if "Waking" in self.current_activity and not self.destination:
                self.find_new_destination(village_data)
            
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
        
        # Notify Interface of position change if it's significant (more than 1 pixel)
        new_position = (self.position.x, self.position.y)
        position_change = ((new_position[0] - old_position[0])**2 + (new_position[1] - old_position[1])**2)
        if position_change > 1 and hasattr(Interface, 'on_villager_moved'):
            Interface.on_villager_moved(self, old_position, new_position)

    def find_new_destination(self, village_data):
        """Find a new destination for the villager and calculate a path to it."""
        # Check for home or workplace based on activity
        if hasattr(self, 'home') and self.home and "home" in self.current_activity.lower():
            # Go home if activity involves home
            home_pos = self.home['position']
            offset_x = random.randint(-self.TILE_SIZE//2, self.TILE_SIZE//2)
            offset_y = random.randint(-self.TILE_SIZE//2, self.TILE_SIZE//2)
            self.destination = (
                home_pos[0] + offset_x,
                home_pos[1] + offset_y
            )
        elif hasattr(self, 'workplace') and self.workplace and "Working" in self.current_activity:
            # Go to workplace if working
            workplace_pos = self.workplace['position']
            offset_x = random.randint(-self.TILE_SIZE//2, self.TILE_SIZE//2)
            offset_y = random.randint(-self.TILE_SIZE//2, self.TILE_SIZE//2)
            self.destination = (
                workplace_pos[0] + offset_x,
                workplace_pos[1] + offset_y
            )
        else:
            # Random destination
            destination_type = random.choice(["building", "path", "random"])
            
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
                padding = self.TILE_SIZE * 3
                self.destination = (
                    random.randint(padding, village_data['size'] - padding),
                    random.randint(padding, village_data['size'] - padding)
                )
        
        # Calculate path to the destination using A* pathfinding
        start_pos = (self.position.x, self.position.y)
        self.path = self.calculate_path(start_pos, self.destination, village_data)
        
        # Ensure current_path_index is initialized
        if not hasattr(self, 'current_path_index'):
            self.current_path_index = 0
        else:
            self.current_path_index = 0
            
        # Debug output for path calculation
        if self.is_selected:
            print(f"Calculated path for {self.name}: {len(self.path)} waypoints")
        
    def calculate_path(self, start, goal, village_data):
        """Calculate a path from start to goal using A* pathfinding with caching.
        
        Args:
            start: Starting position (x, y)
            goal: Goal position (x, y)
            village_data: Village data dictionary
                
        Returns:
            List of positions forming the path
        """
        # Convert positions to grid-aligned coordinates
        start_grid = (int(start[0] // self.TILE_SIZE), int(start[1] // self.TILE_SIZE))
        goal_grid = (int(goal[0] // self.TILE_SIZE), int(goal[1] // self.TILE_SIZE))
        
        # Check if start and goal are the same
        if start_grid == goal_grid:
            return [start, goal]  # Just return direct path
        
        # Check path cache first (if it exists in village_data)
        if village_data and 'path_cache' in village_data:
            cache_key = (start_grid, goal_grid)
            if cache_key in village_data['path_cache']:
                cached_path = village_data['path_cache'][cache_key]
                # Return a copy to prevent modifying the cached path
                return cached_path.copy()
        elif village_data:
            # Initialize path cache if it doesn't exist
            village_data['path_cache'] = {}
        
        # Initialize or get the pathfinding grid
        if village_data and 'pathfinding_grid' not in village_data:
            # Create grid representation of the village
            grid_size = village_data['size'] // self.TILE_SIZE
            pathfinding_grid = [[True for _ in range(grid_size)] for _ in range(grid_size)]
            
            # Mark water tiles as impassable
            water_positions = set()
            for water in village_data['water']:
                water_x = water['position'][0] // self.TILE_SIZE
                water_y = water['position'][1] // self.TILE_SIZE
                if 0 <= water_x < grid_size and 0 <= water_y < grid_size:
                    pathfinding_grid[water_y][water_x] = False
                    water_positions.add((water['position'][0], water['position'][1]))
            
            # Store grid in village_data for reuse
            village_data['pathfinding_grid'] = pathfinding_grid
            village_data['water_positions'] = water_positions
        elif village_data:
            # Use existing grid
            pathfinding_grid = village_data['pathfinding_grid']
            water_positions = village_data.get('water_positions', set())
        else:
            # No village data provided, create a simple grid
            grid_size = 100  # Default size
            pathfinding_grid = [[True for _ in range(grid_size)] for _ in range(grid_size)]
            water_positions = set()
        
        # Define function to check if a position is valid using the grid
        def is_valid_position(pos):
            x, y = pos
            grid_size = len(pathfinding_grid[0]) if pathfinding_grid else 100
            
            # Check boundaries
            if x < 0 or x >= grid_size or y < 0 or y >= grid_size:
                return False
            
            # Check grid value (True = passable, False = impassable)
            try:
                if not pathfinding_grid[y][x]:
                    return False
            except IndexError:
                # If grid access fails, consider position invalid
                return False
            
            return True
        
        def heuristic(a, b):
            # Base heuristic: Manhattan distance
            base_h = abs(a[0] - b[0]) + abs(a[1] - b[1])
            
            # Check if position is on a preferred path
            grid_pos = (a[0] * self.TILE_SIZE, a[1] * self.TILE_SIZE)
            
            # Lookup table for checking path positions (faster than list iteration)
            path_positions = None
            if village_data:
                path_positions = village_data.get('path_positions_set')
                if path_positions is None and 'paths' in village_data:
                    # Create lookup set for path positions if it doesn't exist
                    path_positions = set(tuple(p['position']) for p in village_data['paths'])
                    # Add bridge positions if available
                    if 'bridges' in village_data:
                        path_positions.update(tuple(b['position']) for b in village_data['bridges'])
                    # Store for future use
                    village_data['path_positions_set'] = path_positions
            
            # Apply personality-based path preference if we have path positions
            if path_positions and grid_pos in path_positions:
                # Strong discount for paths based on personality
                return base_h * (1.0 - self.path_preference)
            
            # Apply normal heuristic
            return base_h
        
        # Use A* pathfinding
        import heapq
        
        # Initialize search variables
        open_set = []
        heapq.heappush(open_set, (0, start_grid))
        came_from = {}
        g_score = {start_grid: 0}
        f_score = {start_grid: heuristic(start_grid, goal_grid)}
        open_set_hash = {start_grid}
        
        # Direction vectors - 8-way movement
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),  # Cardinal
            (1, 1), (1, -1), (-1, 1), (-1, -1)  # Diagonal
        ]
        
        # Perform A* search
        while open_set:
            current = heapq.heappop(open_set)[1]
            open_set_hash.remove(current)
            
            # Check if reached goal
            if current == goal_grid:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                
                # Convert grid path to pixel positions (centered in tiles)
                pixel_path = []
                for grid_pos in path:
                    pixel_pos = (
                        grid_pos[0] * self.TILE_SIZE + self.TILE_SIZE // 2,
                        grid_pos[1] * self.TILE_SIZE + self.TILE_SIZE // 2
                    )
                    pixel_path.append(pixel_pos)
                
                # Cache the result for future use
                if village_data and 'path_cache' in village_data:
                    if len(village_data['path_cache']) > 1000:
                        # Remove oldest entry to prevent unbounded growth
                        village_data['path_cache'].pop(next(iter(village_data['path_cache'])))
                    
                    village_data['path_cache'][(start_grid, goal_grid)] = pixel_path.copy()
                
                return pixel_path
            
            # Explore neighbors
            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Skip invalid positions
                if not is_valid_position(neighbor):
                    continue
                
                # Calculate cost (diagonal moves cost more)
                is_diagonal = dx != 0 and dy != 0
                move_cost = 1.414 if is_diagonal else 1.0
                
                tentative_g = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    # This path is better
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, goal_grid)
                    
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
        
        # If no path found or search limit reached, fall back to direct path
        direct_path = [start, goal]
        
        # Cache the failure result too, to avoid repeat searches for impossible paths
        if village_data and 'path_cache' in village_data:
            village_data['path_cache'][(start_grid, goal_grid)] = direct_path.copy()
        
        return direct_path
        
    def draw_path(self, surface, camera_offset_x, camera_offset_y):
        """Draw the villager's planned path for debugging."""
        if hasattr(self, 'path') and self.path and len(self.path) > 1:
            # Draw each segment of the path
            for i in range(len(self.path) - 1):
                start_pos = self.path[i]
                end_pos = self.path[i+1]
                
                # Convert to screen coordinates
                screen_start = (
                    int(start_pos[0] - camera_offset_x),
                    int(start_pos[1] - camera_offset_y)
                )
                screen_end = (
                    int(end_pos[0] - camera_offset_x),
                    int(end_pos[1] - camera_offset_y)
                )
                
                # Draw line segment - green for selected villager, gray for others
                color = (0, 255, 0) if self.is_selected else (200, 200, 200)
                pygame.draw.line(surface, color, screen_start, screen_end, 2 if self.is_selected else 1)
                
                # Draw a dot at each waypoint
                if i == 0 or i == len(self.path) - 2:  # Start and end points
                    dot_color = (255, 0, 0) if i == 0 else (0, 0, 255)
                    pygame.draw.circle(surface, dot_color, screen_start, 3)
            
            # Draw final waypoint
            final_pos = self.path[-1]
            screen_final = (
                int(final_pos[0] - camera_offset_x),
                int(final_pos[1] - camera_offset_y)
            )
            pygame.draw.circle(surface, (0, 0, 255), screen_final, 3)
        
    # Enhanced update method with detailed sleep handling
    def enhanced_update(self, village_data, current_time, assets, time_manager=None):
        """Enhanced update method with better wake-up behavior."""
        # This is an alias to the main update method for backward compatibility
        return self.update(village_data, current_time, assets, time_manager)                    