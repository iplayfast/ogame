"""
Enhanced villager class using the CharacterSprite system from sprite.py.

This class replaces the previous villager implementation with a more robust
animation system that supports multiple character types and animations.
"""

import pygame
import random
import math
import heapq
import utils

try:
    from ui import Interface
except ImportError:
    class Interface:
        """Dummy Interface class if the real one can't be imported."""
        @staticmethod
        def on_villager_sleep_state_changed(villager, is_sleeping): pass
        @staticmethod
        def on_villager_activity_changed(villager, old, new): pass
        @staticmethod
        def on_villager_moved(villager, old, new): pass
        @staticmethod
        def on_villager_selected(villager, is_selected): pass

try:
    from systems.activity_system import ActivitySystem
except ImportError:
    class ActivitySystem:
        """Dummy ActivitySystem class if the real one can't be imported."""
        def __init__(self, villager): pass
        def get_activity(self, hour, village_data): return "Wandering"
        def find_interaction_point(self, village_data, activity_result): return None

# Import the CharacterSprite class
from utils.sprite import CharacterSprite

class Villager(pygame.sprite.Sprite):
    """
    Represents a villager entity with behavior, stats, and animated sprites 
    using the CharacterSprite system for animation.
    """
    
    def __init__(self, x, y, assets, tile_size=32, character_type=None):
        """
        Initialize a Villager instance.

        Args:
            x (int): Initial X coordinate.
            y (int): Initial Y coordinate.
            assets (dict): Dictionary containing loaded game assets.
            tile_size (int): Size of a game tile in pixels.
            character_type (str, optional): Specific character type ('Old_man', 'Old_woman', 'Man', 'Woman', 'Boy', 'Girl').
                                           If None, a random character is chosen.
        """
        super().__init__()
        
        # Basic properties
        self.TILE_SIZE = tile_size
        self.assets = assets
        
        # Available character types
        available_char_types = ["Old_man", "Old_woman", "Man", "Woman", "Boy", "Girl"]
        
        # Select character type
        if character_type and character_type in available_char_types:
            self.character_type = character_type
        else:
            self.character_type = random.choice(available_char_types)
        
        # Create the CharacterSprite for animation
        try:
            self.sprite = CharacterSprite(self.character_type, x, y)
            
            # Link the sprite's rect to this villager's rect for pygame.sprite.Group handling
            self.rect = self.sprite.rect
            self.image = self.sprite.image  # Use the sprite's current frame as this villager's image
        except Exception as e:
            print(f"Error creating CharacterSprite: {e}")
            # Create a fallback surface if sprite creation fails
            self._create_fallback_sprite(x, y)
        
        # Store position as Vector2 for precise movement
        self.position = pygame.math.Vector2(x, y)
        
        # Basic properties
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
        self.personality = random.choice(["social", "solitary", "industrious", "lazy"])
        
        # Sleep state
        self.is_sleeping = True  # Start asleep
        self.bed_position = None  # Set when assigned housing
        self.wake_hour = random.uniform(6.0, 9.0)
        self.sleep_hour = random.uniform(21.0, 23.0)
        
        # Sleep override
        self.sleep_override = False
        self.sleep_override_time = 0
        self.sleep_override_duration = 0
        
        # Activity system
        self.activity_system = ActivitySystem(villager=self)
        
        # Initial activity
        self.current_activity = "Sleeping"
        self.target_interaction_point = None
        self.current_building_id = None  # Set when inside a building
        self.activity_duration = 0  # How long the current activity lasts
        self.activity_end_time = 0  # Timestamp when current activity should end
        
        # Location preferences (used by ActivitySystem)
        self.location_preferences = {
            'elevated': random.uniform(-1, 5),
            'indoors': random.uniform(-2, 4),
            'near_water': random.uniform(0, 3),
            'near_others': random.uniform(-3, 5)
        }
        
        # Pathfinding preferences
        self.path_preference = random.uniform(0.3, 0.95)  # Tendency to stick to paths
        self.direct_route_preference = random.uniform(0.1, 0.8)  # Tendency for straight lines
        self.wandering_tendency = random.uniform(0.05, 0.3)  # How often to wander randomly
        
        # Adjust path preference based on job
        if self.job in ["Guard", "Merchant", "Baker"]:
            self.path_preference = min(0.99, self.path_preference + random.uniform(0.1, 0.2))
        elif self.job in ["Hunter", "Miner"]:
            self.path_preference = max(0.1, self.path_preference - random.uniform(0.1, 0.2))
        
        # Movement
        self.destination = None  # Target position (x, y)
        self.path = []  # List of waypoints (x, y)
        self.current_path_index = 0  # Index for current waypoint
        self.speed = random.uniform(0.3, 1.0)  # Movement speed
        self.idle_timer = 0  # Timer for idle behavior
        
        # Interaction
        self.is_selected = False  # Whether selected by player
        self.is_talking = False  # Currently in conversation
        self.talk_timer = 0  # Timer for talking cooldown
        self.talk_cooldown = random.randint(5000, 15000)  # Time between talks
        
        # Sounds (Load actual sounds in asset loader)
        try:
            if self.assets.get('sounds', {}).get('conversations'):
                self.conversation_sound = random.choice(self.assets['sounds']['conversations'])
            else:
                # Fallback: create silent buffer sound if none loaded
                self.conversation_sound = pygame.mixer.Sound(buffer=bytearray(100))
        except Exception as e:
            print(f"Warning: Error initializing conversation sound for {self.name}: {e}")
            self.conversation_sound = None
        
        # Activity tracking
        self.activity_timer = 0  # Timer for current activity duration/check
        
        # Update timestamp
        self.last_update = pygame.time.get_ticks()
        
        # First frame flag
        self._first_frame = True
        
        # Home / Workplace (initialized later by HousingManager)
        self.home = {}  # Dict containing home building info
        self.workplace = {}  # Dict containing workplace building info
        self.daily_activities = []  # List of planned activities
    
    def _create_fallback_sprite(self, x, y):
        """Create a fallback sprite if the CharacterSprite creation fails."""
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 0, 0), (16, 16), 16)  # Red circle
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        
        # Create a dummy sprite object to allow consistent API
        class DummySprite:
            def __init__(self, image, rect):
                self.image = image
                self.rect = rect
                self.x = rect.x
                self.y = rect.y
                self.alive = True
                self.attacking = False
                self.sleeping = False
                self.current_action = "idle"
            
            def update(self, dt):
                pass
                
            def walk(self, direction):
                pass
                
            def idle(self):
                pass
                
            def sleep(self):
                pass
                
            def wake_up(self):
                pass
        
        self.sprite = DummySprite(self.image, self.rect)
    
    def update(self, village_data, current_time, assets, time_manager=None):
        """
        Update villager state, movement, and animation.

        Args:
            village_data (dict): Data about the village environment.
            current_time (int): Current game time in milliseconds.
            assets (dict): Loaded game assets.
            time_manager (TimeManager, optional): The game's time manager instance.
        """
        # Skip first frame update to allow full initialization
        if self._first_frame:
            self._first_frame = False
            self.last_update = current_time
            return
        
        # Calculate delta time
        dt_ms = current_time - self.last_update
        dt_ms = min(dt_ms, 100)  # Cap delta time to 100ms
        self.last_update = current_time
        
        # Store previous state for change detection
        old_position = (self.position.x, self.position.y)
        old_activity = self.current_activity
        old_sleep_state = self.is_sleeping
        
        # Handle sleep override
        in_override = False
        if self.sleep_override:
            if current_time - self.sleep_override_time > self.sleep_override_duration:
                self.sleep_override = False  # Override expired
            else:
                in_override = True  # Still in override
        
        # Get current hour from time manager
        current_hour = time_manager.current_hour if time_manager else 6.0
        
        # Normal behavior (not in override)
        if not in_override:
            # Check if it's time to sleep or wake up
            sleeping_time = current_hour < self.wake_hour or current_hour >= self.sleep_hour
            
            if sleeping_time and not self.is_sleeping:
                # Time to sleep
                self.is_sleeping = True
                self.current_activity = "Sleeping"
                self.sprite.sleep()  # Use CharacterSprite's sleep animation
                self.destination = None
                self.path = []
                self.current_path_index = 0
            
            elif not sleeping_time and self.is_sleeping:
                # Time to wake up
                self.is_sleeping = False
                self.current_activity = "Waking up"
                self.sprite.wake_up()  # Use CharacterSprite's wake_up method
                self.idle_timer = random.randint(1000, 3000)
            
            # Update activity periodically if awake
            if not self.is_sleeping:
                self.activity_timer += dt_ms
                activity_check_interval = random.randint(5000, 10000)
                
                if self.activity_timer > activity_check_interval or self.current_activity == "Waking up":
                    self.activity_timer = 0
                    
                    # Get activity from activity system
                    new_activity_result = self.activity_system.get_activity(current_hour, village_data)
                    new_activity_name = "Wandering"  # Default
                    target_location = None
                    
                    if isinstance(new_activity_result, dict):
                        new_activity_name = new_activity_result.get("name", "Wandering")
                        location_result = self.activity_system.find_interaction_point(village_data, new_activity_result)
                        if location_result:
                            building_id, interaction_point = location_result
                            if interaction_point and 'position' in interaction_point:
                                target_location = tuple(interaction_point['position'])
                    
                    elif isinstance(new_activity_result, str):
                        new_activity_name = new_activity_result
                    
                    # Update activity if it changed
                    if new_activity_name != self.current_activity:
                        Interface.on_villager_activity_changed(self, self.current_activity, new_activity_name)
                        self.current_activity = new_activity_name
                        
                        # Set destination if provided
                        if target_location:
                            self.set_destination(target_location, village_data)
                    
                    # Clear idle timer
                    self.idle_timer = 0
        
        # Handle movement
        is_moving = False
        if self.is_sleeping:
            self.handle_sleep_behavior(dt_ms)
            self.sprite.sleep()  # Ensure sleep animation
        elif not in_override:
            if self.destination and self.path:
                is_moving = self.handle_path_movement(dt_ms)
                
                if not is_moving:
                    # Reached destination
                    self.destination = None
                    self.path = []
                    self.current_path_index = 0
                    self.idle_timer = random.randint(2000, 5000)
                    
                    # Update activity if it was "Traveling to"
                    if "Traveling to" in self.current_activity:
                        new_activity = self.current_activity.replace("Traveling to ", "")
                        Interface.on_villager_activity_changed(self, self.current_activity, new_activity)
                        self.current_activity = new_activity
                    
                    # Stop walking animation
                    self.sprite.idle()
            else:
                # No destination, handle idle behavior
                self.idle_timer -= dt_ms
                if self.idle_timer <= 0:
                    # Find a new destination
                    self.find_new_destination(village_data)
                    self.idle_timer = random.randint(3000, 8000)
                
                # Ensure idle animation
                self.sprite.idle()
        
        # Update talking state
        if not self.is_sleeping:
            self.talk_timer += dt_ms
            if self.talk_timer > self.talk_cooldown:
                self.talk_timer = 0
                self.is_talking = random.random() < 0.1
                
                # Play conversation sound
                if self.is_talking and self.conversation_sound:
                    try:
                        self.conversation_sound.play()
                    except Exception as e:
                        print(f"Warning: Failed to play conversation sound for {self.name}: {e}")
            
            elif self.is_talking and self.talk_timer > 5000:
                self.is_talking = False
        else:
            self.is_talking = False
        
        # Ensure villager stays within map bounds
        self._ensure_bounds(village_data)
        
        # Update sprite position and animation
        self.sprite.x = self.position.x
        self.sprite.y = self.position.y
        
        # Update sprite state based on villager state
        if not self.is_sleeping and is_moving:
            # Determine direction based on movement
            if self.sprite.facing_right and self.position.x < old_position[0]:
                self.sprite.facing_right = False
            elif not self.sprite.facing_right and self.position.x > old_position[0]:
                self.sprite.facing_right = True
        
        # Update sprite animation
        self.sprite.update(dt_ms)
        
        # Ensure villager's image and rect are updated from sprite
        self.image = self.sprite.image
        self.rect.center = (int(self.position.x), int(self.position.y))
        self.sprite.rect.center = (int(self.position.x), int(self.position.y))
        
        # Notify Interface of state changes
        new_position = (self.position.x, self.position.y)
        if old_position != new_position:
            if ((new_position[0] - old_position[0])**2 + (new_position[1] - old_position[1])**2) > 1:
                Interface.on_villager_moved(self, old_position, new_position)
        
        if old_sleep_state != self.is_sleeping:
            Interface.on_villager_sleep_state_changed(self, self.is_sleeping)
    
    def handle_path_movement(self, dt_ms):
        """Move the villager along the calculated path."""
        if not self.path or self.current_path_index >= len(self.path):
            return False  # No path or at the end
        
        target_waypoint = self.path[self.current_path_index]
        try:
            target_pos = pygame.math.Vector2(target_waypoint[0], target_waypoint[1])
            direction = target_pos - self.position
            
            # Update sprite facing direction based on movement
            if direction.x > 0.1:
                self.sprite.facing_right = True
                self.sprite.walk("right")
            elif direction.x < -0.1:
                self.sprite.facing_right = False
                self.sprite.walk("left")
            elif direction.y > 0.1:
                self.sprite.walk("down")
            elif direction.y < -0.1:
                self.sprite.walk("up")
            
            distance = direction.length()
            move_distance = self.speed * (dt_ms / 16.67)  # Scale by dt
            move_distance = max(move_distance, 0.1)  # Minimum movement
            
            if distance < move_distance or distance < 1.0:
                # Reached waypoint
                self.position = target_pos
                self.current_path_index += 1
                
                if self.current_path_index >= len(self.path):
                    return False  # Path complete
            else:
                # Move toward waypoint
                self.position += direction.normalize() * move_distance
            
            return True  # Still moving
            
        except (TypeError, IndexError) as e:
            print(f"Error in path movement for {self.name}: {e}")
            self.path = []
            return False
    
    def handle_sleep_behavior(self, dt_ms):
        """Handle villager behavior while sleeping."""
        # If we have a bed position, stay there
        if self.bed_position:
            if self.position.x != self.bed_position[0] or self.position.y != self.bed_position[1]:
                self.position.x = self.bed_position[0]
                self.position.y = self.bed_position[1]
        
        # If no bed but has home, go to home center
        elif self.home and 'position' in self.home:
            home_pos = self.home['position']
            home_center_x = home_pos[0] + self.TILE_SIZE // 2
            home_center_y = home_pos[1] + self.TILE_SIZE // 2
            
            if self.position.x != home_center_x or self.position.y != home_center_y:
                self.position.x = home_center_x
                self.position.y = home_center_y
        
        # No movement while sleeping
        self.destination = None
        self.path = []
        self.current_path_index = 0
        
        # Ensure sleep animation
        self.sprite.sleep()
    
    def find_new_destination(self, village_data):
        """Find a new destination for the villager based on current activity."""
        # Try to use home or workplace based on time and activity
        if "home" in self.current_activity.lower() and self.home and 'position' in self.home:
            home_pos = self.home['position']
            self.set_destination((home_pos[0] + random.randint(-10, 10), 
                                 home_pos[1] + random.randint(-10, 10)), 
                                village_data)
            return
        
        elif "work" in self.current_activity.lower() and self.workplace and 'position' in self.workplace:
            work_pos = self.workplace['position']
            self.set_destination((work_pos[0] + random.randint(-10, 10), 
                                 work_pos[1] + random.randint(-10, 10)), 
                                village_data)
            return
        
        # Otherwise, use a combination of path following and random wandering
        if random.random() < self.path_preference and village_data.get('paths', []):
            # Follow paths
            path = random.choice(village_data['paths'])
            path_pos = path['position']
            self.set_destination((path_pos[0] + random.randint(-10, 10), 
                                 path_pos[1] + random.randint(-10, 10)), 
                                village_data)
        else:
            # Random position
            min_x, min_y = 50, 50
            max_x = village_data.get('width', 1000) - 50
            max_y = village_data.get('height', 1000) - 50
            
            rand_x = random.randint(min_x, max_x)
            rand_y = random.randint(min_y, max_y)
            
            self.set_destination((rand_x, rand_y), village_data)
    
    def set_destination(self, destination, village_data):
        """Set a new destination and calculate path."""
        if not destination:
            return
        
        self.destination = destination
        
        # If we have path_cache in village_data, use it for pathfinding
        if 'path_cache' in village_data:
            cache_key = ((int(self.position.x), int(self.position.y)), destination)
            if cache_key in village_data['path_cache']:
                self.path = village_data['path_cache'][cache_key]
            else:
                self.path = self._find_path(destination, village_data)
                village_data['path_cache'][cache_key] = self.path
        else:
            self.path = self._find_path(destination, village_data)
        
        self.current_path_index = 0
    
    def _find_path(self, destination, village_data):
        """A* pathfinding algorithm."""
        # Simple direct path for now - replace with A* if needed
        return [destination]
    
    def _ensure_bounds(self, village_data):
        """Ensure villager stays within map bounds."""
        min_x, min_y = 0, 0
        max_x = village_data.get('width', 1000)
        max_y = village_data.get('height', 1000)
        
        self.position.x = max(min_x, min(self.position.x, max_x))
        self.position.y = max(min_y, min(self.position.y, max_y))
    
    def get_status(self):
        """Get villager status for UI display."""
        return {
            "Name": self.name,
            "Job": self.job,
            "Health": self.health,
            "Energy": self.energy,
            "Mood": self.mood,
            "Money": self.money,
            "Activity": self.current_activity
        }
    
    def override_sleep_state(self, force_awake, duration=30000, village_data=None):
        """Override normal sleep behavior for a duration."""
        self.sleep_override = True
        self.sleep_override_time = pygame.time.get_ticks()
        self.sleep_override_duration = duration
        
        if force_awake and self.is_sleeping:
            # Wake up
            self.is_sleeping = False
            self.current_activity = "Waking up (forced)"
            self.sprite.wake_up()
            Interface.on_villager_sleep_state_changed(self, False)
        
        elif not force_awake and not self.is_sleeping:
            # Go to sleep
            self.is_sleeping = True
            self.current_activity = "Sleeping (forced)"
            self.sprite.sleep()
            
            # Try to move to bed
            if village_data:
                self.handle_sleep_behavior(0)
            
            Interface.on_villager_sleep_state_changed(self, True)
    
    def draw_selection_indicator(self, screen, camera_x, camera_y):
        """Draw an indicator when this villager is selected."""
        if not self.is_selected:
            return
        
        x = int(self.position.x - camera_x)
        y = int(self.position.y - camera_y)
        radius = 20
        
        # Draw a pulsing circle around the villager
        thickness = 2 + int(math.sin(pygame.time.get_ticks() / 200) * 1.5)
        pygame.draw.circle(screen, (0, 255, 255), (x, y), radius, thickness)
    
    def draw_sleep_indicator(self, screen, camera_x, camera_y):
        """Draw a sleep indicator when villager is sleeping."""
        if not self.is_sleeping:
            return
        
        x = int(self.position.x - camera_x)
        y = int(self.position.y - camera_y) - 25  # Above head
        
        # Draw a "Z" sleep indicator
        font = pygame.font.SysFont(None, 24)
        z_text = font.render("Z", True, (100, 200, 255))
        screen.blit(z_text, (x + 10, y - 10))
        
        z_text2 = font.render("z", True, (100, 200, 255))
        screen.blit(z_text2, (x + 18, y - 20))
        
        z_text3 = font.render("z", True, (100, 200, 255))
        screen.blit(z_text3, (x + 24, y - 30))
    
    def draw_path(self, screen, camera_x, camera_y):
        """Debug function to draw the villager's path."""
        if not self.path:
            return
        
        # Draw path as a series of lines
        for i in range(len(self.path) - 1):
            start_pos = (int(self.path[i][0] - camera_x), int(self.path[i][1] - camera_y))
            end_pos = (int(self.path[i+1][0] - camera_x), int(self.path[i+1][1] - camera_y))
            
            # Use different colors for visited and upcoming waypoints
            color = (100, 100, 255) if i < self.current_path_index else (255, 100, 100)
            pygame.draw.line(screen, color, start_pos, end_pos, 2)
            pygame.draw.circle(screen, color, start_pos, 3)
        
        # Draw the final point
        if self.path:
            final_pos = (int(self.path[-1][0] - camera_x), int(self.path[-1][1] - camera_y))
            pygame.draw.circle(screen, (255, 0, 0), final_pos, 5)