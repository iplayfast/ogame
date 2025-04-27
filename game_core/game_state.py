"""
Game State - Handles overall game state management
"""
import pygame
import random
import math
import os
import json # <-- Added
import traceback # <-- Added
from utils import config_manager
from ui.Interface import setup_default_callbacks, on_game_started
from ui.console_manager import ConsoleManager
from ui.housing_ui import HousingUI
from ui.renderer import Renderer
from ui.ui_manager import UIManager
from systems.time_manager import TimeManager
from systems.time_system import TimeSystem
from systems.interaction_system import InteractionSystem
from systems.command_system import CommandSystem
from utils.asset_loader import load_assets
from village.village_generator import generate_village
from entities.villager_manager import VillagerManager
from entities.housing_manager import HousingManager
from entities.villager import Villager # <-- Added
from game_core.input_handler import InputHandler
from game_core.render_manager import RenderManager
from game_core.update_manager import UpdateManager
import utils # <-- Added

class VillageGame:
    """Main game state class that coordinates all game components."""

    def __init__(self): # [ref: 2297]
        """Initialize the game state."""
        print("Initializing VillageGame...") # Debug print
        # Load configuration
        self.config = config_manager.get_config() #

        # Basic setup
        self.SCREEN_WIDTH = 1280 #
        self.SCREEN_HEIGHT = 720 #
        self.TILE_SIZE = 32 #
        self.CAMERA_SPEED = 10 #

        # Initialize screen
        self._windowed_size = (self.SCREEN_WIDTH, self.SCREEN_HEIGHT) #
        self.resize_mode = False #
        self.resize_timer = 0 #
        self.resize_timeout = 100 #

        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.RESIZABLE) #
        pygame.display.set_caption("Village Simulation") #
        self._windowed_size = (self.SCREEN_WIDTH, self.SCREEN_HEIGHT) #
        print(f"Initial window size saved: {self._windowed_size}") #

        # Store reference to window for better position management
        try: #
            from pygame._sdl2.video import Window #
            self.window = Window.from_display_module() #
        except (ImportError, AttributeError) as e: #
            print(f"Warning: SDL2 window management not available: {e}") #
            self.window = None #


        # Load assets
        self.assets = load_assets() #
        print("Assets loaded.") # Debug print

        # Create game clock
        self.clock = pygame.time.Clock() #
        self.fps = 60 #

        # Create UI components
        self.console_manager = ConsoleManager(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT) #
        self.housing_ui = HousingUI(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT) #
        self.renderer = Renderer(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.TILE_SIZE) #
        self.ui_manager = UIManager(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT) #
        print("UI components created.") # Debug print

        # Load village size from config
        self.village_size = self.config.get("village", {}).get("size", 60) #

        # Generate village with the configured size
        self.village_data = generate_village(self.village_size, self.assets, self.TILE_SIZE) #
        print("Village generated.") # Debug print


        # Initialize systems
        self.time_manager = TimeManager() #
        self.time_system = TimeSystem(self) #
        self.interaction_system = InteractionSystem(self) #

        # Initialize entity managers
        self.villager_manager = VillagerManager(self) #
        self.housing_manager = HousingManager(self) #

        # Initialize core game managers
        self.input_handler = InputHandler(self) #
        self.render_manager = RenderManager(self) #
        self.update_manager = UpdateManager(self) #

        # Initialize command system for console
        self.command_system = CommandSystem(self, self.console_manager) #
        self.command_system.register_commands() #
        print("Managers and Systems initialized.") # Debug print

        # Get number of villagers from config
        self.num_villagers = self.config["villagers"].get("count", 10) #

        # Create villagers
        self.villagers = pygame.sprite.Group() #
        self.villager_manager.create_villagers(self.num_villagers) #
        print(f"{self.num_villagers} villagers created.") # Debug print

        # Assign housing to villagers
        self.housing_manager.assign_housing() #
        print("Housing assigned.") # Debug print

        # Initialize building interiors (if renderer supports it)
        # if hasattr(self.renderer, 'initialize_interiors'):
        #     self.renderer.initialize_interiors(self.village_data)

        # Camera position (starts at center of village)
        self._update_camera_bounds() #
        self.camera_x = (self.village_data['width'] - self.SCREEN_WIDTH) // 2 #
        self.camera_y = (self.village_data['height'] - self.SCREEN_HEIGHT) // 2 #

        # Game state flags
        self.running = True #
        self.paused = False #

        # Debug flags
        self.show_debug = False #
        self.show_paths = False #

        # Animation state
        self.animation_timer = 0 #
        self.water_frame = 0 #

        # Currently selected villager
        self.selected_villager = None #

        # Currently hovered building
        self.hovered_building = None #

        # Time scale factor
        self.time_scale = 1.0 #

        # Add self to village_data for reference (Important: Do this *after* main generation)
        self.village_data['game_state'] = self #

        # Ensure path cache exists
        if 'path_cache' not in self.village_data:
            self.village_data['path_cache'] = {}
        self.path_cache = self.village_data['path_cache'] # Link instance variable


        # IMPORTANT: Force villagers to start in their homes AFTER everything else is set up
        self.housing_manager.force_villagers_to_homes() # [ref: 2308]
        print("Forced villagers to homes.") # Debug print

        # Notify Interface that game has started
        self.input_handler._adjust_camera_after_resize() #
        on_game_started(self) #
        print("VillageGame initialization complete.") # Debug print


    def handle_events(self): #
        """Delegate event handling to input handler."""
        self.input_handler.handle_events() #

    def handle_input(self): #
        """Delegate input processing to input handler."""
        self.input_handler.handle_input() #

    def render(self): #
        """Delegate rendering to render manager."""
        self.render_manager.render() #

    def _update_camera_bounds(self): #
        """Update camera boundaries based on current screen and village size."""
        if not hasattr(self, 'village_data') or 'width' not in self.village_data or 'height' not in self.village_data: #
            print("Warning: Cannot update camera bounds - missing village dimensions") #
            return #

        if self.village_data['width'] <= 0 or self.village_data['height'] <= 0: #
            print(f"Warning: Invalid village dimensions: {self.village_data['width']}x{self.village_data['height']}") #
            return #

        if self.SCREEN_WIDTH <= 0 or self.SCREEN_HEIGHT <= 0: #
            print(f"Warning: Invalid screen dimensions: {self.SCREEN_WIDTH}x{self.SCREEN_HEIGHT}") #
            return #

        # print(f"Updating camera bounds - Screen: {self.SCREEN_WIDTH}x{self.SCREEN_HEIGHT}, Village: {self.village_data['width']}x{self.village_data['height']}") #


    def update(self): #
        """Delegate game state updates to update manager or handle resize mode."""
        if self.resize_mode: #
            pygame.event.pump() #

            if pygame.event.peek(pygame.VIDEORESIZE): #
                event = pygame.event.get(pygame.VIDEORESIZE)[0] #
                self.input_handler._handle_resize_event(event) #
                self.resize_timer = pygame.time.get_ticks() #
            else: #
                current_time = pygame.time.get_ticks() #
                if current_time - self.resize_timer > self.resize_timeout: #
                    self.resize_mode = False #
                    print("Exiting resize mode") #

            for event_type in [pygame.QUIT, pygame.KEYDOWN]: #
                if pygame.event.peek(event_type): #
                    event = pygame.event.get(event_type)[0] #
                    if event.type == pygame.QUIT: #
                        self.running = False #
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: #
                        self.running = False #
        else: #
            # Normal update when not in resize mode
            self.update_manager.update() #

    # =============================================== #
    # ==         SAVE / LOAD FUNCTIONALITY         == #
    # =============================================== #

    def get_game_state_dict(self): #
        """Gather all serializable game state into a dictionary."""
        print("Gathering game state for saving...") #
        state = {
            'camera_x': self.camera_x, #
            'camera_y': self.camera_y, #
            'time_manager': { #
                'current_hour': self.time_manager.current_hour, #
                'day_length_seconds': self.time_manager.day_length_seconds, #
            }, #
            'game_flags': { #
                'paused': self.paused, #
                'show_debug': self.show_debug, #
                'show_paths': self.show_paths, #
            }, #
            'village_data': {}, #
            'villagers': [], #
            'selected_villager_name': self.selected_villager.name if self.selected_villager else None, #
        }

        # --- Carefully serialize village_data ---
        serializable_village_data = {} #
        # Explicitly list all keys expected to be saved from village_data
        keys_to_save = ['width', 'height', 'buildings', 'trees', 'paths', 'water', #
                        'bridges', 'interaction_points', 'terrain', #
                        'water_positions', 'path_positions', 'building_positions'] #

        for key in keys_to_save: #
            if key not in self.village_data: #
                print(f"Warning: Key '{key}' not found in village_data during save.") #
                continue #

            try: #
                value = self.village_data[key] #

                if key == 'terrain': #
                    # Convert terrain tuple keys to strings ("x,y")
                    # Check for tuple instance and handle potential errors
                    temp_terrain = {}
                    for k, v in value.items():
                        if isinstance(k, (tuple, list)) and len(k) == 2:
                            try:
                                temp_terrain[f"{int(k[0])},{int(k[1])}"] = v
                            except (ValueError, TypeError):
                                print(f"Warning: Could not convert terrain key {k} to string. Skipping.")
                        else:
                             print(f"Warning: Invalid terrain key format {k}. Skipping.")
                    serializable_village_data[key] = temp_terrain
                    if not serializable_village_data[key] and value: #
                         print(f"Warning: Terrain data might be empty after serialization attempt: {value}") #

                elif key in ['water_positions', 'path_positions', 'building_positions']: #
                    # Convert sets of tuples to lists of lists for JSON
                    serializable_village_data[key] = [list(item) for item in value if isinstance(item, (tuple, list))] # Added check

                elif key in ['buildings', 'trees', 'paths', 'water', 'bridges', 'interaction_points', 'width', 'height']: #
                     # Assume these are already JSON serializable (lists/dicts/primitives)
                     serializable_village_data[key] = value #
                # Add other keys if necessary

            except Exception as e_data: #
                 print(f"ERROR serializing village_data key '{key}': {e_data}") #
                 traceback.print_exc() #
                 serializable_village_data[key] = {'error': f'Serialization failed for key {key}: {e_data}'} # Placeholder on error


        state['village_data'] = serializable_village_data #
        print(f"Serialized village_data keys: {list(serializable_village_data.keys())}") #
        # ---------------------------------------

        # --- Serialize Villagers with Error Handling ---
        print("Serializing villagers...") #
        try: #
            villager_list = [] #
            for i, v in enumerate(self.villagers): #
                try: #
                    villager_dict = v.to_dict() #
                    # You could add a more robust check here if needed
                    # json.dumps(villager_dict) # Example check (can be slow)
                    villager_list.append(villager_dict) #
                except Exception as e_villager: #
                    print(f"ERROR serializing villager {getattr(v, 'name', f'#{i}')}: {e_villager}") #
                    traceback.print_exc() #
                    villager_list.append({'error': f'Serialization failed for {getattr(v, "name", f"#{i}")}: {e_villager}', 'name': getattr(v, 'name', f'Unknown #{i}')}) #
            state['villagers'] = villager_list #
            print(f"Finished serializing {len(state['villagers'])} villagers.") #
        except Exception as e_group: #
             print(f"ERROR during villager group serialization: {e_group}") #
             traceback.print_exc() #
             state['villagers'] = [{'error': f'Group serialization failed: {e_group}'}] #

        print("Finished gathering game state.") #
        return state #

    def save_game(self, filename="savegame.json"): #
        """Save the current game state to a JSON file."""
        try: #
            game_state_dict = self.get_game_state_dict() #
            filepath = os.path.join(".", filename) #

            with open(filepath, 'w') as f: #
                json.dump(game_state_dict, f, indent=4) #

            self.console_manager.add_output(f"Game saved successfully to {filename}") #
            return True #

        except Exception as e: #
            error_msg = f"Error saving game: {e}" #
            print(error_msg) #
            traceback.print_exc() #
            if hasattr(self, 'console_manager'): #
                 self.console_manager.add_output(error_msg) #
            return False #

    def load_game_state_from_dict(self, state): #
        """Load game state from a dictionary (complex and potentially unsafe)."""
        print("Applying loaded game state...") # Debug print
        try: #
            # --- Restore Basic State ---
            self.camera_x = state.get('camera_x', self.SCREEN_WIDTH // 2) #
            self.camera_y = state.get('camera_y', self.SCREEN_HEIGHT // 2) #

            time_state = state.get('time_manager', {}) #
            self.time_manager.current_hour = time_state.get('current_hour', 6.0) #
            self.time_manager.day_length_seconds = time_state.get('day_length_seconds', 300) #

            flag_state = state.get('game_flags', {}) #
            self.paused = flag_state.get('paused', False) #
            self.show_debug = flag_state.get('show_debug', False) #
            self.show_paths = flag_state.get('show_paths', False) #
            print("Restored basic state (camera, time, flags).") # Debug print

            # --- Restore Village Data ---
            print("Restoring village data...") # Debug print
            # Clear existing complex structures before loading
            self.village_data['terrain'] = {} #
            self.village_data['buildings'] = [] #
            self.village_data['trees'] = [] #
            self.village_data['paths'] = [] #
            self.village_data['water'] = [] #
            self.village_data['bridges'] = [] #
            self.village_data['interaction_points'] = [] #
            self.village_data['water_positions'] = set() #
            self.village_data['path_positions'] = set() #
            self.village_data['building_positions'] = set() #

            loaded_village_data = state.get('village_data', {}) #
            if not loaded_village_data:
                 print("Warning: Loaded village_data is empty.")

            for key, value in loaded_village_data.items(): #
                 if key in ['water_positions', 'path_positions', 'building_positions']: #
                     try: #
                         # Convert lists of lists back to sets of tuples
                         self.village_data[key] = set(tuple(item) for item in value if isinstance(item, list) and len(item)==2) # Added length check
                     except TypeError as e: #
                         print(f"Warning: Could not convert positions for key '{key}'. Data: {value}. Error: {e}") #
                         self.village_data[key] = set() #

                 elif key == 'terrain': #
                    # Convert string keys "x,y" back to tuple keys (int(x), int(y))
                    parsed_terrain = {} #
                    if isinstance(value, dict): #
                        for k_str, v_terrain in value.items(): #
                            try: #
                                parts = k_str.split(',')
                                if len(parts) == 2:
                                     pos_tuple = (int(parts[0]), int(parts[1])) #
                                     parsed_terrain[pos_tuple] = v_terrain #
                                else:
                                     print(f"Warning: Invalid terrain key format '{k_str}'. Skipping.")
                            except (ValueError, AttributeError, IndexError, TypeError) as e_parse: # Catch more errors
                                print(f"Warning: Could not parse terrain key '{k_str}'. Skipping entry. Error: {e_parse}") #
                    else: #
                        print(f"Warning: Expected dict for terrain, got {type(value)}. Skipping.") #
                    self.village_data[key] = parsed_terrain #

                 elif key in ['width', 'height', 'buildings', 'trees', 'paths', 'water', 'bridges', 'interaction_points']: #
                     # Directly assign lists/dicts/primitives, ensure lists are lists etc.
                     expected_type = list if key.endswith('s') or key == 'water' else (int if key in ['width', 'height'] else dict)
                     if isinstance(value, expected_type):
                          self.village_data[key] = value #
                     else:
                          print(f"Warning: Invalid type for key '{key}' in loaded village_data: Expected {expected_type}, got {type(value)}. Assigning default.")
                          self.village_data[key] = [] if expected_type is list else ({} if expected_type is dict else 0)

            print(f"Restored village_data keys: {list(self.village_data.keys())}") # Debug print
            # Re-link self reference and re-initialize grid/cache
            self.village_data['game_state'] = self #
            self._initialize_grid() #
            self.path_cache = {} # Always reset cache on load #
            self.village_data['path_cache'] = self.path_cache #


            # --- Restore Villagers ---
            self.villagers.empty() #
            loaded_villagers = state.get('villagers', []) #
            temp_selected = None #
            selected_name = state.get('selected_villager_name') #
            print(f"Attempting to load {len(loaded_villagers)} villagers...") #
            num_loaded = 0 #
            for i, v_state in enumerate(loaded_villagers): #
                try: #
                    if not isinstance(v_state, dict): #
                        print(f"Warning: Villager state at index {i} is not a dictionary. Skipping.") #
                        continue #
                    if 'error' in v_state: #
                        print(f"Skipping villager {v_state.get('name', f'#{i}')} due to previous save error: {v_state['error']}") #
                        continue #

                    villager = Villager.from_dict(v_state, self.assets, self.TILE_SIZE) #
                    self.villagers.add(villager) #
                    num_loaded += 1 #
                    if villager.name == selected_name: #
                        temp_selected = villager #
                        villager.is_selected = True #
                except Exception as e_villager: #
                    print(f"Error loading villager {v_state.get('name', 'Unknown')} at index {i}: {e_villager}") #
                    traceback.print_exc() #
            self.selected_villager = temp_selected #
            print(f"Successfully loaded {num_loaded} villagers.") #


            # --- Restore Other Systems ---
            if hasattr(self, 'housing_ui') and hasattr(self.housing_ui, 'selected_building'): #
                 self.housing_ui.selected_building = None #


            print("Game state loaded successfully.") #
            return True #

        except Exception as e: #
            error_msg = f"Error applying loaded game state: {e}" #
            print(error_msg) #
            traceback.print_exc() #
            if hasattr(self, 'console_manager'): #
                 self.console_manager.add_output(error_msg) #
            return False #

    def load_game(self, filename="savegame.json"): #
        """Load game state from a JSON file."""
        try: #
            filepath = os.path.join(".", filename) #
            if not os.path.exists(filepath): #
                self.console_manager.add_output(f"Save file not found: {filename}") #
                return False #

            with open(filepath, 'r') as f: #
                print(f"Loading state from {filename}...") # Debug print
                loaded_state = json.load(f) #

            # Attempt to apply the loaded state
            if self.load_game_state_from_dict(loaded_state): #
                 self.console_manager.add_output(f"Game loaded successfully from {filename}") #
                 return True #
            else: #
                 self.console_manager.add_output(f"Failed to apply loaded state from {filename}") #
                 return False #

        except json.JSONDecodeError: #
            error_msg = f"Error: Save file '{filename}' is corrupted or not valid JSON." #
            print(error_msg) #
            if hasattr(self, 'console_manager'): #
                self.console_manager.add_output(error_msg) #
            return False #
        except Exception as e: #
            error_msg = f"Error loading game: {e}" #
            print(error_msg) #
            traceback.print_exc() #
            if hasattr(self, 'console_manager'): #
                 self.console_manager.add_output(error_msg) #
            return False #

    def _initialize_grid(self): #
        """Initialize or re-initialize the village grid for pathfinding based on current village_data."""
        print("Initializing/Re-initializing village grid...") #
        if 'village_data' not in self.__dict__ or not isinstance(self.village_data, dict): #
             print("Error: village_data not found or not a dictionary during grid init.") #
             return #

        # Ensure essential keys exist
        if 'width' not in self.village_data or 'height' not in self.village_data: #
            print("Error: Missing width/height in village_data for grid init.") #
            return #

        tile_size = self.TILE_SIZE #
        grid_width = self.village_data['width'] // tile_size #
        grid_height = self.village_data['height'] // tile_size #

        if grid_width <= 0 or grid_height <= 0: #
            print(f"Error: Invalid grid dimensions ({grid_width}x{grid_height}) for grid init.") #
            return #

        grid = [[{'type': 'empty', 'passable': True, 'preferred': False} #
                 for _ in range(grid_width)] for _ in range(grid_height)] #

        def safe_grid_access(grid, y, x, value=None): #
            # Ensure y and x are integers
            grid_y, grid_x = int(y), int(x) #
            if 0 <= grid_y < grid_height and 0 <= grid_x < grid_width: #
                if value is not None: grid[grid_y][grid_x] = value; return True #
                return grid[grid_y][grid_x] #
            return False if value is not None else None #

        # Terrain
        for pos_key, terrain in self.village_data.get('terrain', {}).items(): #
             # Ensure pos_key is a tuple before accessing elements
             if not isinstance(pos_key, tuple) or len(pos_key) != 2:
                 print(f"Warning: Skipping invalid terrain key {pos_key}")
                 continue
             pos = pos_key #
             x, y = pos #
             grid_x, grid_y = x // tile_size, y // tile_size #
             safe_grid_access(grid, grid_y, grid_x, { #
                 'type': 'terrain', 'terrain_type': terrain.get('type', 'grass'), # Added .get()
                 'variant': terrain.get('variant', 1), 'passable': True, 'preferred': False}) #

        # Water
        for water_pos in self.village_data.get('water_positions', set()): #
            x, y = water_pos #
            grid_x, grid_y = x // tile_size, y // tile_size #
            safe_grid_access(grid, grid_y, grid_x, {'type': 'water', 'passable': False, 'preferred': False}) #

        # Bridges
        for bridge in self.village_data.get('bridges', []): #
            x, y = bridge['position'] #
            grid_x, grid_y = x // tile_size, y // tile_size #
            safe_grid_access(grid, grid_y, grid_x, { #
                'type': 'bridge', 'bridge_type': bridge.get('type', 'bridge'), #
                'passable': True, 'preferred': True}) #

        # Paths
        for path_pos in self.village_data.get('path_positions', set()): #
             path_variant = 1 #
             for p_dict in self.village_data.get('paths', []): #
                 # Ensure positions are comparable (tuples)
                 if isinstance(p_dict.get('position'), (list, tuple)) and tuple(p_dict['position']) == path_pos: #
                     path_variant = p_dict.get('variant', 1) #
                     break #
             x, y = path_pos #
             grid_x, grid_y = x // tile_size, y // tile_size #
             safe_grid_access(grid, grid_y, grid_x, { #
                 'type': 'path', 'variant': path_variant, #
                 'passable': True, 'preferred': True}) #

        # Buildings
        for i, building in enumerate(self.village_data.get('buildings', [])): #
            pos = building['position'] #
            size_name = building['size'] #
            size_multiplier = 3 if size_name == 'large' else (2 if size_name == 'medium' else 1) #
            for dx in range(size_multiplier): #
                for dy in range(size_multiplier): #
                    grid_x = (pos[0] // tile_size) + dx #
                    grid_y = (pos[1] // tile_size) + dy #
                    safe_grid_access(grid, grid_y, grid_x, { #
                        'type': 'building', 'building_id': i, #
                        'building_type': building.get('building_type', 'Unknown'), #
                        'passable': False, 'preferred': False}) #

        # Furniture (simplified check - assumes renderer exists if interiors are used)
        # You might need a more direct way to access interior data if renderer isn't always present
        if hasattr(self, 'renderer') and hasattr(self.renderer, 'interior_manager'):
             interior_manager = self.renderer.interior_manager #
             if hasattr(interior_manager, 'interiors'):
                 for building_id, interior in interior_manager.interiors.items(): #
                        for furniture in interior.get('furniture', []): #
                            if 'rect' not in furniture: continue #
                            rect = furniture['rect'] #
                            furn_left = rect.left // tile_size #
                            furn_top = rect.top // tile_size #
                            furn_right = (rect.right + tile_size - 1) // tile_size #
                            furn_bottom = (rect.bottom + tile_size - 1) // tile_size #
                            for grid_x in range(furn_left, furn_right): #
                                for grid_y in range(furn_top, furn_bottom): #
                                    if safe_grid_access(grid, grid_y, grid_x) is not None: #
                                        is_bed = furniture.get('type') == 'bed' #
                                        safe_grid_access(grid, grid_y, grid_x, { #
                                            'type': 'furniture', #
                                            'furniture_type': furniture.get('type', 'generic'), #
                                            'building_id': building_id, #
                                            'passable': is_bed, #
                                            'preferred': False #
                                        }) #

        # Doors
        for point in self.village_data.get('interaction_points', []): #
            if point.get('type') == 'door': #
                x, y = point['position'] #
                grid_x, grid_y = x // tile_size, y // tile_size #
                safe_grid_access(grid, grid_y, grid_x, { #
                        'type': 'door', #
                        'building_id': point.get('building_id'), #
                        'passable': True, #
                        'preferred': True #
                    }) #


        self.village_data['village_grid'] = grid #
        print("Village grid initialization complete.") #

        # Add utility method for access
        def get_cell_at(x, y): #
            grid_x = int(x // tile_size); grid_y = int(y // tile_size) # Ensure int conversion
            return safe_grid_access(grid, grid_y, grid_x) #
        self.village_data['get_cell_at'] = get_cell_at #

    # --- End of Save/Load Methods ---