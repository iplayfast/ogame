import pygame
import random
import math
import heapq
import enum # Added for states
import utils

# Assuming Interface is available or a dummy is defined
try:
    from ui import Interface
except ImportError:
    class Interface:
        """Dummy Interface class if the real one can't be imported."""
        @staticmethod
        def on_villager_sleep_state_changed(villager, is_sleeping): pass
        @staticmethod
        def on_villager_activity_changed(villager, old, new): pass # Will now pass state names
        @staticmethod
        def on_villager_moved(villager, old, new): pass
        @staticmethod
        def on_villager_selected(villager, is_selected): pass

# ActivitySystem is likely less relevant now, but keep the import/dummy for now
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

# --- NEW: Villager State Enum ---
class VillagerState(enum.Enum):
    SLEEPING = 0
    WAKING = 1
    IDLE = 2
    EATING_BREAKFAST = 3
    GETTING_READY_FOR_WORK = 4
    GOING_TO_WORK = 5
    WORKING = 6
    EATING_LUNCH = 7
    GETTING_READY_TO_GO_HOME = 8
    GOING_HOME = 9 # Also used for wandering/visiting movement
    EATING_SUPPER = 10
    SPECIAL_STATE = 11
    # Add potential future states like GETTING_READY_FOR_BED, WANDERING

class Villager(pygame.sprite.Sprite):
    """
    Represents a villager entity with behavior, stats, and animated sprites
    using a discrete state machine for daily routines.
    """

    def __init__(self, x, y, assets, tile_size=32, character_type=None, game_state=None):
        """
        Initialize a Villager instance.
        Args:
            x (int): Initial X coordinate.
            y (int): Initial Y coordinate.
            assets (dict): Dictionary containing loaded game assets.
            tile_size (int): Size of a game tile in pixels.
            character_type (str, optional): Specific character type.
            game_state (obj, optional): Reference to the main game state for accessing time, etc.
        """
        super().__init__()

        self.TILE_SIZE = tile_size
        self.assets = assets
        self.game_state = game_state

        available_char_types = ["Old_man", "Old_woman", "Man", "Woman", "Boy", "Girl"]
        if character_type and character_type in available_char_types:
            self.character_type = character_type
        else:
            self.character_type = random.choice(available_char_types)

        try:
            self.sprite = CharacterSprite(self.character_type, x, y)
            self.rect = self.sprite.rect
            self.image = self.sprite.image
        except Exception as e:
            print(f"Error creating CharacterSprite: {e}")
            self._create_fallback_sprite(x, y)

        self.position = pygame.math.Vector2(x, y)
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

        self.bed_position = None
        self.wake_hour = random.uniform(6.0, 9.0)
        self.sleep_hour = random.uniform(21.0, 23.0)

        self.current_state = VillagerState.SLEEPING
        self.previous_state = None
        self.state_timer = 0
        self.state_duration = 0
        self._idle_sub_state = None

        self.location_preferences = {
            'elevated': random.uniform(-1, 5), 'indoors': random.uniform(-2, 4),
            'near_water': random.uniform(0, 3), 'near_others': random.uniform(-3, 5)
        }
        self.path_preference = random.uniform(0.3, 0.95)
        self.direct_route_preference = random.uniform(0.1, 0.8)
        self.wandering_tendency = random.uniform(0.05, 0.3)
        if self.job in ["Guard", "Merchant", "Baker"]: self.path_preference = min(0.99, self.path_preference + random.uniform(0.1, 0.2))
        elif self.job in ["Hunter", "Miner"]: self.path_preference = max(0.1, self.path_preference - random.uniform(0.1, 0.2))

        self.destination = None
        self.path = []
        self.current_path_index = 0
        self.speed = random.uniform(0.3, 1.0)

        self.is_selected = False
        self.is_talking = False
        self.talk_timer = 0
        self.talk_cooldown = random.randint(5000, 15000)
        try:
             if self.assets.get('sounds', {}).get('conversations'):
                 self.conversation_sound = random.choice(self.assets['sounds']['conversations'])
             else:
                 self.conversation_sound = pygame.mixer.Sound(buffer=bytearray(100))
        except Exception as e:
             # print(f"Warning: Error initializing conversation sound for {self.name}: {e}") # Reduced print
             self.conversation_sound = None

        self.last_update = pygame.time.get_ticks()
        self._first_frame = True
        self.home = {}
        self.workplace = {}

        if self.sprite and self.rect:
             self.sprite.sleep()

    # Inside the Villager class in entities/villager.py

    def _create_fallback_sprite(self, x, y):
        """Create a fallback sprite if the CharacterSprite creation fails."""
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 0, 0), (16, 16), 16) # Red circle
        self.rect = self.image.get_rect(center=(int(x), int(y)))

        # --- Corrected DummySprite Class Definition ---
        class DummySprite:
            def __init__(self, image, rect): # Pass image and rect to init
                self.image = image
                self.rect = rect
                self.x = rect.centerx # Use center x/y for consistency
                self.y = rect.centery
                self.alive = True
                self.attacking = False
                self.sleeping = False
                self.current_action = "idle"
                self.facing_right = True

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
        # --- End Correction ---

        # Create instance and pass the image/rect
        self.sprite = DummySprite(self.image, self.rect)
        # Attributes like image, rect, x, y are now set within DummySprite's init
    # --- Add this method inside the Villager class ---

    def _is_at_location(self, target_location, threshold=15): # Increased threshold slightly
        """Check if villager is close to a target location."""
        if target_location is None:
            return False
        try:
            # Ensure target_location is usable for distance calculation
            if isinstance(target_location, (list, tuple)) and len(target_location) == 2:
                target_vec = pygame.math.Vector2(target_location[0], target_location[1])
            else:
                 # Attempt conversion if it's already a Vector2 or similar duck-typed object
                 target_vec = pygame.math.Vector2(target_location)

            # Calculate distance using Vector2 for robustness
            distance = self.position.distance_to(target_vec)
            return distance < threshold
        except (TypeError, ValueError, AttributeError) as e:
            print(f"Error in _is_at_location for {self.name}: Target={target_location}, Error={e}")
            return False # Treat errors as not being at the location
            

    def _calculate_duration_ms(self, minutes):
        """Helper to convert game minutes to milliseconds based on time scale."""
        if not self.game_state or not hasattr(self.game_state, 'time_manager'):
            # print(f"Warning: Time manager unavailable for {self.name}, using fallback duration.") # Reduced print
            return minutes * 60 * 1000
        time_manager = self.game_state.time_manager
        day_length_real_seconds = time_manager.day_length_seconds
        if day_length_real_seconds <= 0: return minutes * 60 * 1000
        game_minutes_per_real_second = (24 * 60) / day_length_real_seconds
        if game_minutes_per_real_second <= 0: return minutes * 60 * 1000
        real_seconds_per_game_minute = 1 / game_minutes_per_real_second
        duration_seconds = minutes * real_seconds_per_game_minute
        if hasattr(self.game_state, 'time_scale') and self.game_state.time_scale > 0:
            duration_seconds /= self.game_state.time_scale
        return int(duration_seconds * 1000)

    def _find_random_walk_target(self, max_dist=250):
        """Find a random nearby, valid location to walk to."""
        if not self.game_state or not hasattr(self.game_state, 'village_data'): return None
        village_data = self.game_state.village_data
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(self.TILE_SIZE * 3, max_dist)
            target_x = self.position.x + math.cos(angle) * distance
            target_y = self.position.y + math.sin(angle) * distance
            if not (0 <= target_x < village_data['width'] and 0 <= target_y < village_data['height']): continue
            if 'get_cell_at' in village_data:
                 cell = village_data['get_cell_at'](target_x, target_y)
                 if cell and cell.get('passable', False) and cell.get('type') != 'building': # Allow walking on path/terrain
                      return (target_x, target_y)
            else: # Fallback check
                 check_pos = utils.align_to_grid(target_x, target_y, self.TILE_SIZE)
                 if (check_pos not in village_data.get('water_positions', set()) and
                     check_pos not in village_data.get('building_positions', set())):
                     return (target_x, target_y)
        return None

    def _find_wilderness_spot(self):
        """Find a random spot away from the village center, avoiding obstacles."""
        if not self.game_state or not hasattr(self.game_state, 'village_data'): return None
        village_data = self.game_state.village_data
        center_x = village_data['width'] / 2; center_y = village_data['height'] / 2
        min_dist_from_center_sq = (village_data['width'] / 4)**2
        for _ in range(25):
            target_x = random.uniform(0, village_data['width']); target_y = random.uniform(0, village_data['height'])
            if (target_x - center_x)**2 + (target_y - center_y)**2 < min_dist_from_center_sq: continue
            if 'get_cell_at' in village_data:
                 cell = village_data['get_cell_at'](target_x, target_y)
                 if cell and cell.get('passable', True) and cell.get('type') in ['terrain', 'empty']:
                      too_close = False
                      for bldg_pos in village_data.get('building_positions', set()):
                           if utils.calculate_distance(target_x, target_y, bldg_pos[0], bldg_pos[1]) < self.TILE_SIZE * 4: # Increased buffer
                                too_close = True; break
                      if not too_close: return (target_x, target_y)
        return None

    def _find_random_building_target(self):
         """Find a random building (not self's home/work) as a target."""
         if not self.game_state or not self.game_state.village_data or not self.game_state.village_data.get('buildings'): return None
         possible_targets = []
         my_home_id = self.home.get('id', -99); my_work_id = self.workplace.get('id', -99)
         buildings = self.game_state.village_data['buildings']
         if not buildings: return None
         indices = list(range(len(buildings))); random.shuffle(indices)
         for idx in indices:
             building = buildings[idx]
             building_id = building.get('id', idx)
             if building_id != my_home_id and building_id != my_work_id:
                 pos = building['position']; size_str = building.get('size', 'small')
                 size_mult = 3 if size_str == 'large' else (2 if size_str == 'medium' else 1)
                 size_px = size_mult * self.TILE_SIZE
                 possible_targets.append((pos[0] + size_px / 2, pos[1] + size_px / 2))
                 if len(possible_targets) > 5: break
         return random.choice(possible_targets) if possible_targets else None

    def _determine_idle_action(self):
        """Decides next state from IDLE, including optional activities."""
        if not self.game_state or not hasattr(self.game_state, 'time_manager'): return VillagerState.IDLE
        current_hour = self.game_state.time_manager.current_hour
        scheduled_state = None
        self._idle_sub_state = None

        # Check for scheduled transitions
        # Simplified: Check if time is right AND not already doing it
        if 6.5 <= current_hour < 7.5 and self.current_state != VillagerState.EATING_BREAKFAST: scheduled_state = VillagerState.EATING_BREAKFAST
        elif 7.5 <= current_hour < 8.5 and self.current_state != VillagerState.GETTING_READY_FOR_WORK: scheduled_state = VillagerState.GETTING_READY_FOR_WORK
        elif 17.0 <= current_hour < 18.0 and self.current_state != VillagerState.GETTING_READY_TO_GO_HOME: scheduled_state = VillagerState.GETTING_READY_TO_GO_HOME
        elif 18.5 <= current_hour < 20.0 and self.current_state != VillagerState.EATING_SUPPER: scheduled_state = VillagerState.EATING_SUPPER
        # Add checks for starting work / going home if not already there during work/home hours?
        elif 8.5 <= current_hour < 17.0 and hasattr(self, 'workplace') and self.workplace and not self._is_at_location(self.workplace.get('position'), threshold=self.TILE_SIZE * 2) and self.current_state not in [VillagerState.GOING_TO_WORK, VillagerState.WORKING]:
             scheduled_state = VillagerState.GOING_TO_WORK # Go to work if not there during work hours
        elif current_hour >= 17.5 and hasattr(self, 'home') and self.home and not self._is_at_location(self.home.get('position')) and self.current_state != VillagerState.GOING_HOME:
              scheduled_state = VillagerState.GOING_HOME # Go home if not there after work hours


        if scheduled_state is None:
            # Consider optional actions
            if random.random() < self.wandering_tendency * 0.5: # Adjusted probability
                action_choice = random.choice(['walk']) # Expand later
                if action_choice == 'walk':
                    walk_target = self._find_random_walk_target()
                    if walk_target:
                        # print(f"{self.name} decided to go for a walk.") # Reduced print
                        self._idle_sub_state = ('walking', walk_target) # Store target
                        return VillagerState.GOING_HOME # Reuse movement state
                    else: return VillagerState.IDLE # Stay idle if fail
                else: return VillagerState.IDLE
            else: return VillagerState.IDLE # Stay idle
        else: return scheduled_state # Perform scheduled action

    def _determine_special_state_action(self):
        """Checks for and potentially initiates a special state action."""
        if self.game_state and random.random() < 0.02:
            if self.personality == "social":
                for other in self.game_state.villagers:
                    if other != self and hasattr(other, 'current_state') and other.current_state not in [VillagerState.SLEEPING, VillagerState.SPECIAL_STATE]:
                        if self.position.distance_to(other.position) < 50:
                            if other.current_state in [VillagerState.IDLE, VillagerState.GOING_HOME]:
                                # print(f"{self.name} sees {other.name} ({other.current_state.name}), stopping to chat!") # Reduced print
                                duration_ms = self._calculate_duration_ms(random.uniform(1, 4))
                                return duration_ms
        return None

    def _transition_state(self):
        """Determines the next state and sets its duration and initial actions."""
        next_state = VillagerState.IDLE
        duration_ms = self._calculate_duration_ms(5)
        target_for_movement_state = None
        move_during_work = False

        # --- Determine next state logic ---
        current_state_logic = self.current_state # Store current state for checks

        if current_state_logic == VillagerState.SLEEPING:
            next_state = VillagerState.WAKING
            duration_ms = self._calculate_duration_ms(random.uniform(5, 10))
        elif current_state_logic == VillagerState.WAKING:
            next_state = VillagerState.IDLE
        elif current_state_logic == VillagerState.IDLE:
            idle_decision_result = self._determine_idle_action()
            next_state = idle_decision_result
            if hasattr(self, '_idle_sub_state') and self._idle_sub_state and next_state == VillagerState.GOING_HOME:
                if isinstance(self._idle_sub_state, tuple) and len(self._idle_sub_state) == 2:
                    action_type, target_pos = self._idle_sub_state
                    if action_type == 'walking':
                        target_for_movement_state = target_pos; duration_ms = float('inf')
                self._idle_sub_state = None # Clear flag
            elif next_state == VillagerState.EATING_BREAKFAST: duration_ms = self._calculate_duration_ms(10)
            elif next_state == VillagerState.GETTING_READY_FOR_WORK: duration_ms = self._calculate_duration_ms(10)
            elif next_state == VillagerState.GETTING_READY_TO_GO_HOME: duration_ms = self._calculate_duration_ms(5)
            elif next_state == VillagerState.EATING_SUPPER: duration_ms = self._calculate_duration_ms(random.uniform(20, 40))
            elif next_state == VillagerState.GOING_TO_WORK: duration_ms = float('inf')
            elif next_state == VillagerState.GOING_HOME: duration_ms = float('inf')
            # If stays IDLE, duration set on entry

        elif current_state_logic == VillagerState.EATING_BREAKFAST:
            next_state = VillagerState.GETTING_READY_FOR_WORK; duration_ms = self._calculate_duration_ms(10)
        elif current_state_logic == VillagerState.GETTING_READY_FOR_WORK:
            if hasattr(self, 'workplace') and self.workplace: next_state = VillagerState.GOING_TO_WORK; duration_ms = float('inf')
            else: next_state = VillagerState.IDLE
        elif current_state_logic == VillagerState.GOING_TO_WORK:
            next_state = VillagerState.WORKING # Duration set on entry
        elif current_state_logic == VillagerState.WORKING:
             # Check mandatory time transitions first
             current_hour = self.game_state.time_manager.current_hour if self.game_state and hasattr(self.game_state, 'time_manager') else -1
             if current_hour != -1:
                 if 12.0 <= current_hour < 13.0: next_state = VillagerState.EATING_LUNCH; duration_ms = self._calculate_duration_ms(random.uniform(10, 30))
                 elif current_hour >= 17.0: next_state = VillagerState.GETTING_READY_TO_GO_HOME; duration_ms = self._calculate_duration_ms(5)
                 else: # Still working hours
                     if self.job in ["Hunter", "Carpenter"] and random.random() < 0.1: # Chance to move
                         move_during_work = True
                         if self.job == "Hunter": target_for_movement_state = self._find_wilderness_spot()
                         elif self.job == "Carpenter": target_for_movement_state = self._find_random_building_target()
                         if target_for_movement_state: next_state = VillagerState.WORKING; duration_ms = float('inf')
                         else: next_state = VillagerState.WORKING; duration_ms = 5000 # Failed find, wait longer
                     else: next_state = VillagerState.WORKING; duration_ms = 5000 # Stay working idle (longer interval)
             else: next_state = VillagerState.IDLE # Fallback

        elif current_state_logic == VillagerState.EATING_LUNCH:
             current_hour = self.game_state.time_manager.current_hour if self.game_state and hasattr(self.game_state, 'time_manager') else -1
             if current_hour != -1 and hasattr(self, 'workplace') and self.workplace:
                 if current_hour < 17.0: next_state = VillagerState.WORKING # Duration set on entry
                 else: next_state = VillagerState.GETTING_READY_TO_GO_HOME; duration_ms = self._calculate_duration_ms(5)
             else: next_state = VillagerState.IDLE
        elif current_state_logic == VillagerState.GETTING_READY_TO_GO_HOME:
            if hasattr(self, 'home') and self.home: next_state = VillagerState.GOING_HOME; duration_ms = float('inf')
            else: next_state = VillagerState.IDLE
        elif current_state_logic == VillagerState.GOING_HOME:
            # Check if this was an idle walk based on previous state
            was_walking = (self.previous_state == VillagerState.IDLE) # Simple check
            if was_walking: next_state = VillagerState.IDLE # Return to idle after walk
            else: # Arrived home
                 current_hour = self.game_state.time_manager.current_hour if self.game_state and hasattr(self.game_state, 'time_manager') else -1
                 if 18.0 <= current_hour < 20.5: # Supper time window
                      next_state = VillagerState.EATING_SUPPER
                      duration_ms = self._calculate_duration_ms(random.uniform(20, 40))
                 else: # Not supper time, just idle at home
                      next_state = VillagerState.IDLE
        elif current_state_logic == VillagerState.EATING_SUPPER:
            next_state = VillagerState.IDLE
        elif current_state_logic == VillagerState.SPECIAL_STATE:
             next_state = self.previous_state if self.previous_state else VillagerState.IDLE
             self.previous_state = None

        # --- Set up the new state ---
        old_state = self.current_state
        self.current_state = next_state
        # Correct duration might have been calculated above
        self.state_duration = duration_ms
        self.state_timer = self.state_duration

        # Interface Notification & Simplified Print
        if old_state != self.current_state:
            print(f"{self.name}: {self.current_state.name}") # Simplified Log
            if hasattr(Interface, 'on_villager_activity_changed'):
                 Interface.on_villager_activity_changed(self, old_state.name, self.current_state.name)

        # --- Actions on entering the new state ---
        # Clear destination unless moving
        is_moving_state = (self.current_state in [VillagerState.GOING_HOME, VillagerState.GOING_TO_WORK] or \
                           (self.current_state == VillagerState.WORKING and move_during_work and target_for_movement_state))
        if not is_moving_state:
            self.destination = None; self.path = []; self.current_path_index = 0

        if self.current_state == VillagerState.SLEEPING: pass # Handled in update
        elif self.current_state == VillagerState.WAKING: self.sprite.wake_up()
        elif self.current_state == VillagerState.IDLE:
            self.sprite.idle()
            if self.state_duration == float('inf') or self.state_duration <= 0:
                 self.state_duration = self.state_timer = 1500 # Ensure idle checks again soon
        elif self.current_state == VillagerState.GOING_TO_WORK:
            if hasattr(self, 'workplace') and self.workplace and 'position' in self.workplace:
                 target_pos = self.workplace['position']
                 offset = self.TILE_SIZE // 4
                 final_target = (target_pos[0] + random.randint(-offset, offset), target_pos[1] + random.randint(-offset, offset))
                 village_data = self.game_state.village_data if self.game_state else {}
                 self.set_destination(final_target, village_data)
                 if not self.path: self.current_state = VillagerState.IDLE; self.state_timer = 0
                 else: self.sprite.walk("down")
            else: self.current_state = VillagerState.IDLE; self.state_timer = 0
        elif self.current_state == VillagerState.GOING_HOME:
             final_target = target_for_movement_state # Use walk target if set
             if not final_target: # Find home/bed if not walking
                 if hasattr(self, 'home') and self.home:
                     target_pos = self.bed_position
                     if not target_pos and 'position' in self.home: target_pos = (self.home['position'][0] + self.TILE_SIZE // 2, self.home['position'][1] + self.TILE_SIZE // 2)
                     final_target = target_pos
             if final_target:
                 village_data = self.game_state.village_data if self.game_state else {}
                 self.set_destination(final_target, village_data)
                 if not self.path: self.current_state = VillagerState.IDLE; self.state_timer = 0
                 else: self.sprite.walk("down")
             else: self.current_state = VillagerState.IDLE; self.state_timer = 0
        elif self.current_state == VillagerState.WORKING:
            if move_during_work and target_for_movement_state: # Entering WORKING and moving
                village_data = self.game_state.village_data if self.game_state else {}
                self.set_destination(target_for_movement_state, village_data)
                if self.path: self.sprite.walk("down") # Duration already set to inf
                else: self.sprite.idle(); self.state_duration = self.state_timer = 5000; self.destination = None # Path failed
            else: # Entering WORKING and staying put (or arrived)
                self.sprite.idle()
                if self.destination is None and (self.state_duration == float('inf') or self.state_duration <= 0):
                     self.state_duration = self.state_timer = 5000 # Ensure check interval if not moving

        elif self.current_state == VillagerState.SPECIAL_STATE: self.sprite.idle()
        elif self.current_state in [VillagerState.EATING_BREAKFAST, VillagerState.GETTING_READY_FOR_WORK, VillagerState.EATING_LUNCH, VillagerState.GETTING_READY_TO_GO_HOME, VillagerState.EATING_SUPPER]:
            self.sprite.idle()

    # --- Main Update Method ---
    def update(self, village_data, current_time, assets, time_manager=None):
        if not hasattr(self, 'game_state') or self.game_state is None:
             if 'game_state' in village_data: self.game_state = village_data['game_state']
        current_hour = -1
        if time_manager: current_hour = time_manager.current_hour
        elif self.game_state and hasattr(self.game_state, 'time_manager'): time_manager = self.game_state.time_manager; current_hour = time_manager.current_hour
        if self._first_frame:
            self._first_frame = False; self.last_update = current_time
            if not hasattr(self, 'current_state'): self.current_state = VillagerState.SLEEPING
            self._transition_state(); return
        dt_ms = current_time - self.last_update; dt_ms = min(dt_ms, 100); self.last_update = current_time

        # 1. Check Sleep/Wake Time Transitions
        if time_manager:
            is_sleep_time = (current_hour >= self.sleep_hour or current_hour < self.wake_hour)
            should_wake = (current_hour >= self.wake_hour and current_hour < self.sleep_hour)
            if self.current_state == VillagerState.SLEEPING and should_wake: self.state_timer = 0
            elif self.current_state != VillagerState.SLEEPING and is_sleep_time and self.current_state != VillagerState.SPECIAL_STATE:
                self.current_state = VillagerState.SLEEPING
                wake_diff = (self.wake_hour - current_hour + 24) % 24
                sleep_duration_ms = self._calculate_duration_ms(wake_diff * 60)
                self.state_duration = sleep_duration_ms; self.state_timer = self.state_duration
                self.sprite.sleep(); self.destination = None; self.path = []
                target_pos = self.bed_position or ( (self.home['position'][0] + self.TILE_SIZE // 2, self.home['position'][1] + self.TILE_SIZE // 2) if self.home and 'position' in self.home else None)
                if target_pos: self.position.x, self.position.y = target_pos; self.rect.center = (int(self.position.x), int(self.position.y))

        # 2. Decrement Timer
        if self.state_duration != float('inf'): self.state_timer -= dt_ms

        # 3. Check Special State Trigger
        if self.current_state not in [VillagerState.SLEEPING, VillagerState.SPECIAL_STATE]:
             if random.random() < (dt_ms / 1000.0) * 0.05: # Reduced check frequency
                special_duration = self._determine_special_state_action()
                if special_duration is not None and special_duration > 0:
                    self.previous_state = self.current_state; self.current_state = VillagerState.SPECIAL_STATE
                    self.state_duration = special_duration; self.state_timer = self.state_duration
                    self.destination = None; self.path = []
                    # print(f"{self.name} entering SPECIAL_STATE from {self.previous_state.name}") # Reduced print
                    self.sprite.idle()

        # 4. Handle Actions Within State (Movement, Staying Put)
        is_moving = False
        is_moving_state = self.current_state in [VillagerState.GOING_TO_WORK, VillagerState.GOING_HOME] or \
                          (self.current_state == VillagerState.WORKING and self.destination is not None)
        if is_moving_state:
             if self.destination and self.path:
                 is_moving = self.handle_path_movement(dt_ms)
                 if not is_moving: # Arrived
                     # print(f"{self.name} arrived: {self.current_state.name}") # Debug
                     arrival_state = self.current_state # Remember state on arrival
                     # Clear movement vars first
                     self.destination = None; self.path = []; self.current_path_index = 0
                     self.sprite.idle()
                     # Decide next step based on state during arrival
                     if arrival_state == VillagerState.WORKING:
                          # Arrived at temp work spot, stay WORKING idle
                          self.state_duration = self.state_timer = self._calculate_duration_ms(random.uniform(5, 15)) # Work 5-15 mins
                     else: # Arrived after GOING_TO_WORK or GOING_HOME
                          self.state_timer = 0 # Force transition
             elif not self.destination and self.state_duration == float('inf'): # Error case
                  # print(f"Error/Interrupt: {self.name} in state {self.current_state.name} (inf dur) but no destination. Resetting.") # Reduced print
                  self.state_timer = 0

        elif self.current_state == VillagerState.SLEEPING: # Ensure stays put
             target_pos = self.bed_position or ( (self.home['position'][0] + self.TILE_SIZE // 2, self.home['position'][1] + self.TILE_SIZE // 2) if self.home and 'position' in self.home else None)
             if target_pos and self.position.distance_to(target_pos) > 1:
                   self.position.x, self.position.y = target_pos; self.rect.center = (int(self.position.x), int(self.position.y))
             self.sprite.sleep()
        elif self.current_state == VillagerState.SPECIAL_STATE:
             # Add any actions needed during special state
             pass


        # 5. Check if State Timer Expired
        if self.state_timer <= 0:
            self._transition_state()

        # --- Update Sprite and Bounds ---
        self.sprite.x = self.position.x; self.sprite.y = self.position.y
        self.sprite.update(dt_ms)
        self.image = self.sprite.image
        if self.rect: self.rect.center = (int(self.position.x), int(self.position.y))
        elif self.image: self.rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))
        if hasattr(self, '_ensure_bounds'): self._ensure_bounds(village_data)

    # --- Existing Methods ---
    # (Keep handle_path_movement, set_destination, _find_path, get_status, draw_*, _ensure_bounds)
    # Ensure get_status provides the formatted state name
    def handle_path_movement(self, dt_ms):
        if not self.path or self.current_path_index >= len(self.path): return False
        try:
            target_waypoint = self.path[self.current_path_index]; target_pos = pygame.math.Vector2(target_waypoint[0], target_waypoint[1])
            direction = target_pos - self.position; distance = direction.length()
            move_distance = self.speed * (dt_ms / 16.67); move_distance = max(move_distance, 0.1)
            if abs(direction.x) > abs(direction.y):
                if direction.x > 0.1: self.sprite.walk("right")
                elif direction.x < -0.1: self.sprite.walk("left")
            else:
                if direction.y > 0.1: self.sprite.walk("down")
                elif direction.y < -0.1: self.sprite.walk("up")
            if distance < move_distance or distance < 1.0:
                self.position = target_pos; self.current_path_index += 1
                return self.current_path_index < len(self.path)
            else: self.position += direction.normalize() * move_distance; return True
        except Exception as e: print(f"❌ Movement Error for {self.name}: {e}"); import traceback; traceback.print_exc(); self.path = []; self.destination = None; self.current_path_index = 0; return False

    def set_destination(self, destination, village_data):
        if not destination: self.path = []; self.destination = None; self.current_path_index = 0; return
        destination_vec = pygame.math.Vector2(destination)
        if self.position.distance_to(destination_vec) < self.TILE_SIZE / 2:
             self.destination = tuple(map(int, destination)); self.path = []; self.current_path_index = 0; return
        if 'path_cache' not in village_data: village_data['path_cache'] = {}
        start_key = (int(self.position.x), int(self.position.y)); end_key = tuple(map(int, destination)); cache_key = (start_key, end_key)
        if cache_key in village_data['path_cache']: self.path = village_data['path_cache'][cache_key]
        else:
            self.path = self._find_path(destination, village_data)
            if self.path: village_data['path_cache'][cache_key] = self.path
        if self.path: self.destination = end_key; self.current_path_index = 0
        else:
            # print(f"❌ WARNING: Path generation failed for {self.name} to {destination}!") # Reduced print
            self.destination = None; self.path = []; self.current_path_index = 0
            is_moving_state = self.current_state in [VillagerState.GOING_HOME, VillagerState.GOING_TO_WORK] or \
                              (self.current_state == VillagerState.WORKING and self.state_duration == float('inf'))
            if is_moving_state: self.state_timer = 0 # Trigger transition if path fails during movement

    def _find_path(self, destination, village_data):
        if self.game_state and hasattr(self.game_state, 'find_path'):
            try:
                 start_pos = (self.position.x, self.position.y)
                 path = self.game_state.find_path(start_pos, destination)
                 return path if path else [] # Ensure empty list on failure
            except Exception as e: print(f"Error using game_state.find_path for {self.name}: {e}")
        # Fallback
        start = (self.position.x, self.position.y); end = tuple(map(float, destination))
        mid_x = start[0] + (end[0] - start[0]) / 2 + random.uniform(-10, 10); mid_y = start[1] + (end[1] - start[1]) / 2 + random.uniform(-10, 10)
        return [start, (mid_x, mid_y), end]

    def get_status(self):
        activity_name = self.current_state.name.replace('_', ' ').title()
        return {"Name": self.name, "Job": self.job, "Health": self.health, "Energy": self.energy, "Mood": self.mood, "Money": self.money, "Activity": activity_name}

    def draw_selection_indicator(self, screen, camera_x, camera_y):
        if not self.is_selected: return
        x = int(self.position.x - camera_x); y = int(self.position.y - camera_y); radius = 20
        thickness = 2 + int(math.sin(pygame.time.get_ticks() / 200) * 1.5)
        pygame.draw.circle(screen, (0, 255, 255), (x, y), radius, thickness)

    def draw_sleep_indicator(self, screen, camera_x, camera_y):
        if self.current_state != VillagerState.SLEEPING: return
        x = int(self.position.x - camera_x); y = int(self.position.y - camera_y) - 25
        try:
            font = pygame.font.SysFont(None, 24)
            z_text = font.render("Z", True, (100, 200, 255)); screen.blit(z_text, (x + 10, y - 10))
            z_text2 = font.render("z", True, (100, 200, 255)); screen.blit(z_text2, (x + 18, y - 20))
            z_text3 = font.render("z", True, (100, 200, 255)); screen.blit(z_text3, (x + 24, y - 30))
        except Exception as e: pass # Reduced print

    def draw_path(self, screen, camera_x, camera_y):
         if not self.path or len(self.path) < 2: return
         for i in range(len(self.path) - 1):
             try:
                 start_node = self.path[i]; end_node = self.path[i+1]
                 start_pos = (int(start_node[0] - camera_x), int(start_node[1] - camera_y))
                 end_pos = (int(end_node[0] - camera_x), int(end_node[1] - camera_y))
                 color = (100, 100, 255) if i < self.current_path_index else (255, 100, 100)
                 pygame.draw.line(screen, color, start_pos, end_pos, 2)
                 pygame.draw.circle(screen, color, start_pos, 3)
             except (TypeError, IndexError) as e: continue
         try:
             final_node = self.path[-1]; final_pos = (int(final_node[0] - camera_x), int(final_node[1] - camera_y))
             pygame.draw.circle(screen, (255, 0, 0), final_pos, 5)
         except (TypeError, IndexError) as e: pass

    def _ensure_bounds(self, village_data):
         pass # Implementation patched in game.py