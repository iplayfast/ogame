import pygame
import random
import math
import utils
import heapq

from ui import Interface
from systems.activity_system import ActivitySystem
from village.village_generator import initialize_village_grid
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
        # Add properties for location-based activities
        self.target_interaction_point = None
        self.current_building_id = None
        self.activity_duration = 0
        self.activity_end_time = 0
        self.location_preferences = {
            "elevated": random.uniform(-1, 5),
            "indoors": random.uniform(-2, 4),
            "near_water": random.uniform(0, 3),
            "near_others": random.uniform(-3, 5)
        }
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
        self.activity_system = ActivitySystem()
        if hasattr(self, 'daily_activities') and self.daily_activities:
            self.current_activity.add_custom_activity(self.daily_activities)
        self.target_interaction_point = None
        self.current_building_id = None
        self.personality = random.choice(["social", "solitary", "industrious", "lazy"])
    
        # Add location preferences
        self.location_preferences = {
            'elevated': random.uniform(-1, 5),
            'indoors': random.uniform(-2, 4),
            'near_water': random.uniform(0, 3),
            'near_others': random.uniform(-3, 5)
        }
        
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
        grid_size = (self.village_data['width'] * self.village_dta['height']) // self.TILE_SIZE
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
    
    # Modification 1: Fix for villager activity descriptions
# Update the handle_activity_movement method in villager.py

    def handle_activity_movement(self, village_data, dt, current_hour):
        """Handle movement based on current activity and time of day.
        
        Args:
            village_data: Village data dictionary containing terrain info
            dt: Delta time in milliseconds
            current_hour: Current hour (0-24)
        """
        # Handle sleep behavior at night
        if "Sleeping" in self.current_activity and hasattr(self, 'home') and self.home:
            # Stay at home position during sleep
            home_pos = self.home.get('position')
            if home_pos and hasattr(self, 'bed_position') and self.bed_position:
                # Use bed position as destination
                bed_x, bed_y = self.bed_position
                
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
                else:
                    # Occasionally make small movements to simulate restless sleep
                    if random.random() < 0.01:  # 1% chance per update
                        self.position.x += random.uniform(-0.5, 0.5)
                        self.position.y += random.uniform(-0.5, 0.5)
                    
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
                # Check if we're at the workplace
                dx = workplace_pos[0] - self.position.x
                dy = workplace_pos[1] - self.position.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Get workplace building size
                workplace_id = self.workplace.get('id', -1)
                workplace_size = self.TILE_SIZE  # Default
                if 0 <= workplace_id < len(village_data['buildings']):
                    building = village_data['buildings'][workplace_id]
                    size_name = building['size']
                    size_multiplier = 3 if size_name == 'large' else (2 if size_name == 'medium' else 1)
                    workplace_size = self.TILE_SIZE * size_multiplier
                
                # Change activity to "Traveling to work" if we're not there yet
                if distance > workplace_size:
                    if self.current_activity == "Working":
                        self.current_activity = "Traveling to work"
                    
                    # Set destination to workplace if not already there
                    if not self.destination:
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
                else:
                    # We've arrived at the workplace - now we can actually work
                    if self.current_activity == "Traveling to work":
                        self.current_activity = "Working"
                    
                    # Occasionally change position within the workplace
                    if random.random() < 0.05:  # 5% chance to move around workplace
                        offset_x = random.randint(-workplace_size // 2, workplace_size // 2)
                        offset_y = random.randint(-workplace_size // 2, workplace_size // 2)
                        self.destination = (
                            workplace_pos[0] + offset_x,
                            workplace_pos[1] + offset_y
                        )
                        # Recalculate path to the new destination
                        start_pos = (self.position.x, self.position.y)
                        self.path = self.calculate_path(start_pos, self.destination, village_data)
                        self.current_path_index = 0
        
        # Handle "heading home" or evening activities
        if "home" in self.current_activity.lower() and hasattr(self, 'home') and self.home:
            home_pos = self.home.get('position')
            if home_pos:
                # Check if we're at home
                dx = home_pos[0] - self.position.x
                dy = home_pos[1] - self.position.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Get home building size
                home_id = self.home.get('id', -1)
                home_size = self.TILE_SIZE  # Default
                if 0 <= home_id < len(village_data['buildings']):
                    building = village_data['buildings'][home_id]
                    size_name = building['size']
                    size_multiplier = 3 if size_name == 'large' else (2 if size_name == 'medium' else 1)
                    home_size = self.TILE_SIZE * size_multiplier
                
                # Change activity to "Returning home" if we're not there yet
                if distance > home_size and "Return" not in self.current_activity:
                    self.current_activity = "Returning home"
                    
                if not self.destination or random.random() < 0.1:
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
        
        # Follow the path if we have one and we're not sleeping
        if (not self.is_sleeping and hasattr(self, 'path') and self.path and 
            len(self.path) > 0 and hasattr(self, 'current_path_index')):
            
            # Skip if we're at the end of the path
            if self.current_path_index >= len(self.path):
                self.destination = None
                self.idle_timer = random.randint(2000, 5000)  # Idle for 2-5 seconds
                
                # If we have an activity that's "Traveling to X", change it to appropriate
                # activity now that we've arrived
                if "Traveling to" in self.current_activity:
                    if "work" in self.current_activity.lower():
                        self.current_activity = "Working"
                    elif "home" in self.current_activity.lower():
                        self.current_activity = "At home"
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
                    
                    # If we have an activity that's "Traveling to X", change it to appropriate
                    # activity now that we've arrived
                    if "Traveling to" in self.current_activity:
                        if "work" in self.current_activity.lower():
                            self.current_activity = "Working"
                        elif "home" in self.current_activity.lower():
                            self.current_activity = "At home"
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
            # Regular movement handling (find new destination if needed)
            if self.destination is None or self.idle_timer > 0:
                # If no destination or idle, handle idle timer
                if self.idle_timer > 0:
                    self.idle_timer -= dt
                else:
                    # Find new destination based on activity
                    self.find_new_destination(village_data)
                    self.idle_timer = 0
            else:
                # Make sure we have a path to the destination
                if not hasattr(self, 'path') or not self.path or len(self.path) == 0:
                    start_pos = (self.position.x, self.position.y)
                    self.path = self.calculate_path(start_pos, self.destination, village_data)
                    self.current_path_index = 0


    # Modification 2: Fix for villagers not starting in bed
    # Modify the housing_manager.py file

    def initialize_unique_bed_position(self, villager, occupied_bed_positions=None):
        """Initialize home position with a unique bed position for each villager.
        
        Args:
            villager: Villager to position
            occupied_bed_positions: Dictionary of already occupied bed positions
        """
        if occupied_bed_positions is None:
            occupied_bed_positions = {}
                
        if not hasattr(villager, 'home') or not villager.home or 'position' not in villager.home:
            # No home assigned, can't initialize
            return
                
        home_pos = villager.home['position']
        home_id = villager.home.get('id', -1)
        
        # Find the actual building
        if 0 <= home_id < len(self.game_state.village_data['buildings']):
            building = self.game_state.village_data['buildings'][home_id]
            building_pos = building['position']
            building_size = building['size']
            
            # Convert to pixel sizes
            size_multiplier = 3 if building_size == 'large' else (2 if building_size == 'medium' else 1)
            building_size_px = self.game_state.TILE_SIZE * size_multiplier
            
            # Get the number of roommates to determine how to spread beds
            roommates = villager.home.get('roommates', [])
            num_roommates = len(roommates)
            
            # Default position (for safety)
            bed_x = building_pos[0] + building_size_px // 2
            bed_y = building_pos[1] + building_size_px // 2
            
            # Try to find an available position
            attempt_count = 0
            padding = self.game_state.TILE_SIZE // 3
            
            # Keep trying to find an unoccupied position
            while attempt_count < 10:  # Limit attempts to avoid infinite loops
                # Calculate positions based on number of roommates and building size
                if building_size == 'large':
                    # For large buildings (manor), we can have up to 4 beds in a grid pattern
                    row = attempt_count % 2
                    col = (attempt_count // 2) % 2
                    
                    # Divide the building interior into a 2x2 grid
                    cell_size = (building_size_px - padding * 2) // 2
                    bed_x = building_pos[0] + padding + col * cell_size + cell_size // 2
                    bed_y = building_pos[1] + padding + row * cell_size + cell_size // 2
                elif building_size == 'medium':
                    # For medium buildings, we can have up to 2 beds in a row
                    if num_roommates <= 1:
                        # Single occupant - place in center
                        bed_x = building_pos[0] + building_size_px // 2
                        bed_y = building_pos[1] + building_size_px // 2
                    else:
                        # Two occupants - place side by side
                        col = attempt_count % 2
                        bed_x = building_pos[0] + padding + col * (building_size_px - padding * 2 - self.game_state.TILE_SIZE)
                        bed_y = building_pos[1] + building_size_px // 2
                else:  # small
                    # For small buildings, we have limited space
                    if num_roommates <= 1:
                        # Single occupant - place in center
                        bed_x = building_pos[0] + building_size_px // 2
                        bed_y = building_pos[1] + building_size_px // 2
                    else:
                        # Multiple occupants - stagger positions slightly
                        offset_x = (attempt_count % 3 - 1) * (self.game_state.TILE_SIZE // 3)
                        offset_y = (attempt_count // 3 - 1) * (self.game_state.TILE_SIZE // 3)
                        bed_x = building_pos[0] + building_size_px // 2 + offset_x
                        bed_y = building_pos[1] + building_size_px // 2 + offset_y
                
                # Check if this position is already occupied
                position_key = f"{int(bed_x)},{int(bed_y)}"
                if position_key not in occupied_bed_positions:
                    # Found an unoccupied position
                    occupied_bed_positions[position_key] = villager.name
                    break
                    
                # Try another position
                attempt_count += 1
                
            # Add some randomness to avoid perfect alignment
            bed_x += random.randint(-3, 3)
            bed_y += random.randint(-3, 3)
            
            # Set the villager's bed position
            villager.bed_position = (bed_x, bed_y)
            
            # Move villager to bed
            villager.position.x = bed_x
            villager.position.y = bed_y
            
            # Update rect
            villager.rect.centerx = int(villager.position.x)
            villager.rect.centery = int(villager.position.y)
            
            # Clear destination
            villager.destination = None


    # Modification 3: Ensure all villagers start asleep in bed
    # Modify the update_game_with_assignments method in villager_housing.py

    def update_game_with_assignments(game_state, assignments):
        """
        Update the game state with the villager assignments.
        
        Args:
            game_state: Game state object
            assignments: Villager assignments dictionary
        """
        if not assignments or 'villagers' not in assignments:
            return
        
        # Update buildings with names
        if 'house_names' in assignments:
            for building in game_state.village_data['buildings']:
                building_id = game_state.village_data['buildings'].index(building)
                if str(building_id) in assignments['house_names']:
                    building['name'] = assignments['house_names'][str(building_id)]
        
        # Keep track of occupied bed positions
        occupied_bed_positions = {}
        
        # Update villagers with home and workplace info
        for villager in game_state.villagers:
            for v_data in assignments['villagers']:
                if villager.name == v_data['name']:
                    # Add home and workplace references
                    villager.home = v_data.get('home', {})
                    villager.workplace = v_data.get('workplace', {})
                    villager.daily_activities = v_data.get('daily_activities', [])
                    villager.is_sleeping = True  # Ensure all villagers start asleep
                    villager.current_activity = "Sleeping"

                    # Initialize bed position and place villager there
                    if hasattr(game_state.housing_manager, 'initialize_unique_bed_position'):
                        game_state.housing_manager.initialize_unique_bed_position(villager, occupied_bed_positions)

                    # Update villager's AI to consider home and workplace
                    if hasattr(villager, 'find_new_destination'):
                        # Store the original method
                        villager._original_find_destination = villager.find_new_destination
                        
                        # Replace with our enhanced method that considers home and workplace
                        def enhanced_find_destination(self, village_data):
                            # 40% chance to go to home or workplace, 60% chance for normal behavior
                            if random.random() < 0.4:
                                if hasattr(self, 'home') and hasattr(self, 'workplace'):
                                    # Decide between home and workplace based on time of day
                                    # For now we'll just randomly choose
                                    if random.random() < 0.5 and self.workplace:
                                        # Go to workplace
                                        workplace_pos = self.workplace.get('position')
                                        if workplace_pos:
                                            offset_x = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
                                            offset_y = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
                                            self.destination = (
                                                workplace_pos[0] + offset_x,
                                                workplace_pos[1] + offset_y
                                            )
                                            self.current_activity = f"Traveling to {self.workplace.get('type', 'workplace')}"
                                            return
                                    else:
                                        # Go home
                                        home_pos = self.home.get('position')
                                        if home_pos:
                                            offset_x = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
                                            offset_y = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
                                            self.destination = (
                                                home_pos[0] + offset_x,
                                                home_pos[1] + offset_y
                                            )
                                            self.current_activity = "Returning home"
                                            return
                            
                            # Fall back to original behavior
                            self._original_find_destination(village_data)
                        
                        # Bind our enhanced method to the villager
                        import types
                        villager.find_new_destination = types.MethodType(enhanced_find_destination, villager)

    def find_new_destination(self, village_data):
        """Find a new destination for the villager and calculate a path to it.
        
        Args:
            village_data: Village data containing terrain and path information
        """
        # Before choosing a destination, update the pathfinding grid
        if hasattr(self, 'update_pathfinding_grid'):
            self.update_pathfinding_grid(village_data)
        
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
            # Random destination, with preference for paths
            if random.random() < self.path_preference and village_data['paths']:
                # Choose random path - preferences paths for movement
                possible_paths = random.sample(village_data['paths'], min(5, len(village_data['paths'])))
                
                # Try to find a path not too far away
                current_pos = (self.position.x, self.position.y)
                
                # Sort by distance (closer paths first)
                sorted_paths = sorted(possible_paths, 
                                key=lambda p: ((p['position'][0] - current_pos[0])**2 + 
                                            (p['position'][1] - current_pos[1])**2))
                
                # Choose one of the closer paths (with some randomness)
                path_index = min(int(random.expovariate(0.5)), len(sorted_paths) - 1)
                chosen_path = sorted_paths[path_index]
                
                self.destination = chosen_path['position']
            elif random.random() < 0.6 and village_data['buildings']:
                # Head to a random building (not too far away)
                closest_buildings = []
                for building in village_data['buildings']:
                    dist = ((building['position'][0] - self.position.x)**2 + 
                        (building['position'][1] - self.position.y)**2)**0.5
                    if dist < village_data['width'] * village_data['height'] // 2:  # Limit to reasonably close buildings
                        closest_buildings.append((building, dist))
                
                if closest_buildings:
                    # Sort by distance
                    closest_buildings.sort(key=lambda x: x[1])
                    # Choose one of the closer buildings
                    building_index = min(int(random.expovariate(0.5)), len(closest_buildings) - 1)
                    building = closest_buildings[building_index][0]
                    
                    # Try to find the door
                    door_found = False
                    for point in village_data.get('interaction_points', []):
                        if point.get('type') == 'door' and point.get('building_id') == village_data['buildings'].index(building):
                            self.destination = point['position']
                            door_found = True
                            break
                    
                    if not door_found:
                        # No door found, just go near the building
                        offset_x = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
                        offset_y = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
                        self.destination = (
                            building['position'][0] + offset_x,
                            building['position'][1] + offset_y
                        )
                else:
                    # No close buildings, choose a random position
                    padding = self.TILE_SIZE * 3
                    self.destination = (
                        random.randint(padding, village_data['width'] - padding),
                        random.randint(padding, village_data['height'] - padding)
                    )
            else:
                # Head to a random position (but keep within village borders and not in water)
                padding = self.TILE_SIZE * 3
                
                # Try up to 10 times to find a valid position not in water
                for _ in range(10):
                    dest_x = random.randint(padding, village_data['width'] - padding)
                    dest_y = random.randint(padding, village_data['height'] - padding)
                    
                    # Check if this position is in water
                    if (dest_x, dest_y) not in village_data.get('water_positions', set()):
                        self.destination = (dest_x, dest_y)
                        break
                else:
                    # If all attempts failed, just use current position
                    self.destination = (self.position.x, self.position.y)
        
        # Calculate path to the destination using A* pathfinding
        start_pos = (self.position.x, self.position.y)
        self.path = self.calculate_path(start_pos, self.destination, village_data)
        
        # Reset path index
        self.current_path_index = 0
        
        # Debug output for selected villager
        if self.is_selected:
            print(f"Found new destination for {self.name}: {self.destination}")
            print(f"Calculated path with {len(self.path)} waypoints")
    
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
                elif self.position.x > village_data['width'] - padding:
                    self.position.x = village_data['height'] - padding

                if self.position.y < padding:
                    self.position.y = padding
                elif self.position.y > village_data['width'] - padding:
                    self.position.y = village_data['height'] - padding
                
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
            
        
        # Determine if it's sleeping time with clearer conditions
        sleeping_time = current_hour < self.wake_hour or current_hour >= self.sleep_hour

        # Force wake up if it's well past wake time (at least half hour after wake hour)
        if current_hour >= (self.wake_hour + 0.5) and current_hour < (self.sleep_hour - 1.0) and self.is_sleeping:
            if self.is_selected:
                print(f"FORCE WAKING UP {self.name} at hour {current_hour:.2f}")
            self.is_sleeping = False
            self.current_activity = "Waking up"
            
            # Create a destination away from bed to force movement
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
            
            # Create a destination away from bed to force movement
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

        # Update activity based on time of day
        self.activity_timer += dt
        if self.activity_timer > 5000:  # Change activity every 5 seconds
            old_activity = self.current_activity
            self.activity_timer = 0

            # If sleeping, keep the sleeping activity
            if self.is_sleeping:
                self.current_activity = "Sleeping"
            else:
                # Use the activity system for all activity management
                activity_result = self.activity_system.get_activity(current_hour, village_data)
                
                if isinstance(activity_result, dict):
                    # Location-aware activity
                    self.current_activity = activity_result["name"]
                    
                    # Find appropriate interaction point if needed
                    if ("location_type" in activity_result or "interaction_type" in activity_result) and hasattr(self.activity_system, 'find_interaction_point'):
                        result = self.activity_system.find_interaction_point(village_data, activity_result)
                        
                        if result:
                            building_id, interaction_point = result
                            
                            # Set as target
                            self.target_interaction_point = interaction_point
                            self.current_building_id = building_id
                            
                            # If we have a specific point to move to
                            if interaction_point:
                                # Set destination to the interaction point
                                self.destination = interaction_point["position"]
                                
                                # Calculate path to destination
                                start_pos = (self.position.x, self.position.y)
                                self.path = self.calculate_path(start_pos, self.destination, village_data)
                                self.current_path_index = 0
                else:
                    # Simple string activity
                    self.current_activity = activity_result

        # Update talking state only if not sleeping
        if not self.is_sleeping:
            self.talk_timer += dt
            if self.talk_timer > self.talk_cooldown:
                self.talk_timer = 0
                self.is_talking = random.random() < 0.3  # 30% chance to be talking
        else:
            self.is_talking = False  # Don't talk while sleeping
        
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
            # If we just woke up and don't have a destination, find one
            if "Waking" in self.current_activity and not self.destination:
                self.find_new_destination(village_data)
            
            self.handle_activity_movement(village_data, dt, current_hour)

        # Ensure villager stays within village bounds
        padding = self.TILE_SIZE * 2
        if self.position.x < padding:
            self.position.x = padding
        elif self.position.x > village_data['width'] - padding:
            self.position.x = village_data['height'] - padding

        if self.position.y < padding:
            self.position.y = padding
        elif self.position.y > village_data['width'] - padding:
            self.position.y = village_data['height'] - padding

        # Make sure rect position matches
        self.rect.centerx = int(self.position.x)
        self.rect.centery = int(self.position.y)
        
        # Notify Interface of position change if it's significant (more than 1 pixel)
        new_position = (self.position.x, self.position.y)
        position_change = ((new_position[0] - old_position[0])**2 + (new_position[1] - old_position[1])**2)
        if position_change > 1 and hasattr(Interface, 'on_villager_moved'):
            Interface.on_villager_moved(self, old_position, new_position)
           # Add this section near where the debug output occurs (where time_manager is used)
        
    def choose_activity_and_location(self, village_data, current_hour):
        """Choose an appropriate activity and location based on time of day."""
        # If we have an activity system, use it
        if hasattr(self, 'activity_system'):
            activity_name = self.activity_system.get_activity(current_hour)
            
            # Check if this is a job-specific activity that needs a specific location
            if "Working" in activity_name or self.job.lower() in activity_name.lower():
                # Look for job-specific location
                if hasattr(self, 'workplace') and self.workplace:
                    workplace_id = self.workplace.get('id', -1)
                    if 0 <= workplace_id < len(village_data['buildings']):
                        building = village_data['buildings'][workplace_id]
                        
                        # Find appropriate interaction point in this building
                        if 'interaction_points' in building:
                            # Choose a non-door interaction point
                            work_points = [p for p in building['interaction_points'] 
                                        if p['type'] != 'door']
                            if work_points:
                                return activity_name, (workplace_id, random.choice(work_points))
            
            # Handle specific activities
            if "fishing" in activity_name.lower():
                # Find a fishing spot
                fishing_points = [p for p in village_data.get('interaction_points', [])
                                if p['type'] == 'fishing_spot']
                if fishing_points:
                    # Rate fishing spots based on preferences
                    rated_spots = []
                    for point in fishing_points:
                        score = 10  # Base score
                        # Apply preferences
                        if 'elevated' in point['properties'] and point['properties']['elevated']:
                            score += self.location_preferences.get('elevated', 0)
                        # Add more preference calculations...
                        
                        rated_spots.append((None, point, score))  # No building ID for outdoor spots
                    
                    if rated_spots:
                        # Sort by score and choose the best
                        rated_spots.sort(key=lambda x: x[2], reverse=True)
                        return activity_name, (rated_spots[0][0], rated_spots[0][1])
            
            # For most activities, just return the name without location
            return activity_name
        
        # Fallback to generic activities
        return "Wandering"

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
                    random.randint(padding, village_data['width'] - padding),
                    random.randint(padding, village_data['height'] - padding)
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
        """Calculate a path from start to goal using A* pathfinding with grid-based terrain awareness.
        
        Args:
            start: Starting position (x, y)
            goal: Goal position (x, y)
            village_data: Village data dictionary containing the grid representation
                
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
        
        # Initialize or update the village grid if needed
        if 'village_grid' not in village_data:
            from village.village_generator import initialize_village_grid
            initialize_village_grid(village_data, self.TILE_SIZE)
        
        # Get the village grid
        grid = village_data['village_grid']
        grid_size = len(grid[0])
        
        # Define function to check if a position is valid
        def is_valid_position(pos):
            x, y = pos
            
            # Check boundaries
            if x < 0 or x >= grid_size or y < 0 or y >= grid_size:
                return False
            
            # Check if cell is passable
            if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                cell = grid[y][x]
                return cell.get('passable', True)
            return False
        
        def get_movement_cost(from_pos, to_pos):
            """Get the cost to move from one position to another based on terrain."""
            from_x, from_y = from_pos
            to_x, to_y = to_pos
            
            # Base cost (1.0 for cardinal moves, 1.414 for diagonal)
            is_diagonal = from_x != to_x and from_y != to_y
            base_cost = 1.414 if is_diagonal else 1.0
            
            # Get cell data for destination
            if 0 <= to_y < len(grid) and 0 <= to_x < len(grid[0]):
                cell = grid[to_y][to_x]
                cell_type = cell.get('type', 'empty')
                
                # Prefer paths (reduced cost)
                if cell_type == 'path' or cell.get('preferred', False):
                    return base_cost * (1.0 - self.path_preference)
                # Slight reduction for building interiors
                elif cell_type == 'building' and cell.get('passable', False):
                    return base_cost * 0.9
                # Increase cost for terrain types (less preferred than paths)
                elif cell_type == 'terrain':
                    terrain_type = cell.get('terrain_type', '')
                    if terrain_type == 'grass':
                        # Different costs for grass variants
                        variant = cell.get('variant', 1)
                        if variant == 1:  # Normal grass
                            return base_cost
                        elif variant == 2:  # Grass near water - slightly avoid
                            return base_cost * 1.2
                        elif variant == 3:  # Grass near building entrances - prefer
                            return base_cost * 0.8
            
            # Default cost
            return base_cost
        
        def heuristic(pos, goal):
            """Estimate cost from position to goal."""
            # Manhattan distance
            return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])
        
        # A* pathfinding
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
        
        # Perform A* search with a limit to prevent infinite loops
        max_iterations = 1000
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
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
                
                # Skip if not valid
                if not is_valid_position(neighbor):
                    continue
                
                # Calculate movement cost based on terrain
                tentative_g = g_score[current] + get_movement_cost(current, neighbor)
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    # This path is better
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, goal_grid)
                    
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
        
        # If we reached here, either no path was found or search limit reached
        if self.is_selected:
            print(f"A* failed to find path for {self.name} after {iterations} iterations. Using fallback.")
        
        # Fallback: Create a simple direct path with water avoidance
        direct_path = []
        current_pos = start_grid
        direct_path.append((
            current_pos[0] * self.TILE_SIZE + self.TILE_SIZE // 2,
            current_pos[1] * self.TILE_SIZE + self.TILE_SIZE // 2
        ))
        
        # Try to find a safe path by choosing the best next step each time
        max_steps = 20
        for _ in range(max_steps):
            best_dir = None
            best_score = float('inf')
            
            for dx, dy in directions:
                next_pos = (current_pos[0] + dx, current_pos[1] + dy)
                
                # Skip if not valid
                if not is_valid_position(next_pos):
                    continue
                
                # Calculate score (distance to goal plus penalties)
                dist_to_goal = abs(next_pos[0] - goal_grid[0]) + abs(next_pos[1] - goal_grid[1])
                move_cost = get_movement_cost(current_pos, next_pos)
                total_score = dist_to_goal * move_cost
                
                if total_score < best_score:
                    best_score = total_score
                    best_dir = (dx, dy)
            
            # If no valid direction, break
            if best_dir is None:
                break
            
            # Move in best direction
            current_pos = (current_pos[0] + best_dir[0], current_pos[1] + best_dir[1])
            direct_path.append((
                current_pos[0] * self.TILE_SIZE + self.TILE_SIZE // 2,
                current_pos[1] * self.TILE_SIZE + self.TILE_SIZE // 2
            ))
            
            # Check if we reached the goal
            if current_pos == goal_grid:
                break
        
        # Add goal if not reached
        if current_pos != goal_grid:
            direct_path.append(goal)
        
        # Cache this fallback path
        if village_data and 'path_cache' in village_data:
            village_data['path_cache'][(start_grid, goal_grid)] = direct_path.copy()
        
        return direct_path

    def update_pathfinding_grid(self, village_data):
        """Create and update a grid representation of the village for efficient pathfinding.
        
        Args:
            village_data: Village data dictionary
        """
        # Calculate grid size
        grid_size = village_data['width'] * village_data['height'] // self.TILE_SIZE
        
        # Initialize the grid with empty passable cells
        grid = [[{'type': 'empty', 'passable': True, 'preferred': False} 
                for _ in range(grid_size)] for _ in range(grid_size)]
        
        # Add terrain (grass, etc.)
        for pos, terrain_data in village_data.get('terrain', {}).items():
            x, y = pos
            grid_x, grid_y = x // self.TILE_SIZE, y // self.TILE_SIZE
            
            if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                grid[grid_y][grid_x] = {
                    'type': 'terrain',
                    'terrain_type': terrain_data['type'],
                    'variant': terrain_data.get('variant', 1),
                    'passable': True,
                    'preferred': False
                }
        
        # Add water (impassable)
        for water in village_data.get('water', []):
            x, y = water['position']
            grid_x, grid_y = x // self.TILE_SIZE, y // self.TILE_SIZE
            
            if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                grid[grid_y][grid_x] = {
                    'type': 'water',
                    'passable': False,
                    'preferred': False
                }
        
        # Add bridges (passable, preferred)
        for bridge in village_data.get('bridges', []):
            x, y = bridge['position']
            grid_x, grid_y = x // self.TILE_SIZE, y // self.TILE_SIZE
            
            if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                grid[grid_y][grid_x] = {
                    'type': 'bridge',
                    'bridge_type': bridge.get('type', 'bridge'),
                    'passable': True,
                    'preferred': True
                }
        
        # Add paths (passable, preferred)
        for path in village_data.get('paths', []):
            x, y = path['position']
            grid_x, grid_y = x // self.TILE_SIZE, y // self.TILE_SIZE
            
            if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                grid[grid_y][grid_x] = {
                    'type': 'path',
                    'variant': path.get('variant', 1),
                    'passable': True,
                    'preferred': True
                }
        
        # Add buildings (generally impassable)
        for i, building in enumerate(village_data.get('buildings', [])):
            pos = building['position']
            size_name = building['size']
            
            # Determine building size in tiles
            size_multiplier = 3 if size_name == 'large' else (
                            2 if size_name == 'medium' else 1)
            size_tiles = size_multiplier
            
            # Add building footprint to grid
            for dx in range(size_tiles):
                for dy in range(size_tiles):
                    pos_x, pos_y = pos
                    grid_x = (pos_x // self.TILE_SIZE) + dx
                    grid_y = (pos_y // self.TILE_SIZE) + dy
                    
                    if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                        grid[grid_y][grid_x] = {
                            'type': 'building',
                            'building_id': i,
                            'building_type': building.get('building_type', 'Unknown'),
                            'passable': False,  # Buildings are generally impassable
                            'preferred': False
                        }
        
        # Add furniture from building interiors
        if hasattr(village_data, 'interior_manager') or 'game_state' in village_data:
            interior_manager = None
            if hasattr(village_data, 'interior_manager'):
                interior_manager = village_data.interior_manager
            elif 'game_state' in village_data and hasattr(village_data['game_state'], 'interior_manager'):
                interior_manager = village_data['game_state'].interior_manager
                
            if interior_manager and hasattr(interior_manager, 'interiors'):
                for building_id, interior in interior_manager.interiors.items():
                    for furniture in interior.get('furniture', []):
                        # Skip if furniture doesn't have a rect
                        if 'rect' not in furniture:
                            continue
                            
                        rect = furniture['rect']
                        # Convert furniture rect to grid coordinates
                        furn_left = rect.left // self.TILE_SIZE
                        furn_top = rect.top // self.TILE_SIZE
                        furn_right = (rect.right + self.TILE_SIZE - 1) // self.TILE_SIZE
                        furn_bottom = (rect.bottom + self.TILE_SIZE - 1) // self.TILE_SIZE
                        
                        # Mark furniture in grid
                        for grid_x in range(furn_left, furn_right):
                            for grid_y in range(furn_top, furn_bottom):
                                if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                                    # Special case for beds - allow walking on them for sleeping
                                    is_bed = furniture.get('type') == 'bed'
                                    grid[grid_y][grid_x] = {
                                        'type': 'furniture',
                                        'furniture_type': furniture.get('type', 'generic'),
                                        'building_id': building_id,
                                        'passable': is_bed,  # Beds are passable for sleeping
                                        'preferred': False
                                    }
        
        # Add doors to buildings (passable, preferred)
        for point in village_data.get('interaction_points', []):
            if point.get('type') == 'door':
                x, y = point['position']
                grid_x, grid_y = x // self.TILE_SIZE, y // self.TILE_SIZE
                
                if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                    grid[grid_y][grid_x] = {
                        'type': 'door',
                        'building_id': point.get('building_id'),
                        'passable': True,
                        'preferred': True
                    }
        
        # Store the grid in village_data
        village_data['village_grid'] = grid
        
        # Reset path cache when grid changes
        if hasattr(self, 'path_cache'):
            self.path_cache = {}
        if 'path_cache' in village_data:
            village_data['path_cache'] = {}
        
        if hasattr(self, 'pathfinding_grid'):
            self.pathfinding_grid = grid

    
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
