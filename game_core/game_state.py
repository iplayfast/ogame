"""
Game State - Handles overall game state management
"""
import pygame
import random
import math
import os
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
from village.village_generator import generate_village  # Fixed import
from entities.villager_manager import VillagerManager
from entities.housing_manager import HousingManager
from game_core.input_handler import InputHandler
from game_core.render_manager import RenderManager
from game_core.update_manager import UpdateManager

class VillageGame:
    """Main game state class that coordinates all game components."""
    
    def __init__(self):
        """Initialize the game state."""
        # Load configuration
        self.config = config_manager.get_config()
        
        # Basic setup
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 720
        self.TILE_SIZE = 32
        self.CAMERA_SPEED = 10
        
        # Initialize screen
        # In the __init__ method of VillageGame

        self._windowed_size = (self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.resize_mode = False
        self.resize_timer = 0
        self.resize_timeout = 100
    
        # Initialize screen
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Village Simulation")
        self._windowed_size = (self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        print(f"Initial window size saved: {self._windowed_size}")
        # Store reference to window for better position management
        try:
            from pygame._sdl2.video import Window
            self.window = Window.from_display_module()
        except (ImportError, AttributeError) as e:
            print(f"Warning: SDL2 window management not available: {e}")
            self.window = None
        
        
        # Load assets
        self.assets = load_assets()
        
        # Create game clock
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Create UI components
        self.console_manager = ConsoleManager(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.housing_ui = HousingUI(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.renderer = Renderer(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.TILE_SIZE)
        self.ui_manager = UIManager(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        
        # Load village size from config
        self.village_size = self.config.get("village", {}).get("size", 60)  # Default to 60 if not specified

        # Generate village with the configured size
        self.village_data = generate_village(self.village_size, self.assets, self.TILE_SIZE)
        
        
        # Initialize systems
        self.time_manager = TimeManager()
        self.time_system = TimeSystem(self)
        self.interaction_system = InteractionSystem(self)
        
        # Initialize entity managers
        self.villager_manager = VillagerManager(self)
        self.housing_manager = HousingManager(self)
        
        # Initialize core game managers
        self.input_handler = InputHandler(self)
        self.render_manager = RenderManager(self)
        self.update_manager = UpdateManager(self)
        
        # Initialize command system for console
        self.command_system = CommandSystem(self, self.console_manager)
        self.command_system.register_commands()
        
        # Get number of villagers from config
        self.num_villagers = self.config["villagers"].get("count", 10)
        
        # Create villagers
        self.villagers = pygame.sprite.Group()
        self.villager_manager.create_villagers(self.num_villagers)
        
        # Assign housing to villagers
        self.housing_manager.assign_housing()
        
        # Initialize building interiors
        if hasattr(self.renderer, 'initialize_interiors'):
            self.renderer.initialize_interiors(self.village_data)
        
        # Camera position (starts at center of village)
        self._update_camera_bounds()
        self.camera_x = (self.village_data['width'] - self.SCREEN_WIDTH) // 2
        self.camera_y = (self.village_data['height'] - self.SCREEN_HEIGHT) // 2
        # Get screen size from config
        #self.SCREEN_WIDTH = self.config.get("system", {}).get("window_width", 1280)
        #self.SCREEN_HEIGHT = self.config.get("system", {}).get("window_height", 720)
        # Game state flags
        self.running = True
        self.paused = False
        
        # Debug flags
        self.show_debug = False
        self.show_paths = False
        
        # Animation state
        self.animation_timer = 0
        self.water_frame = 0
        
        # Currently selected villager
        self.selected_villager = None
        
        # Currently hovered building
        self.hovered_building = None
        
        # Time scale factor
        self.time_scale = 1.0
        
        # Add self to village_data for reference
        self.village_data['game_state'] = self
            # Assign housing to villagers
        self.housing_manager.assign_housing()
    
        # Force villagers to start in their homes
        self.housing_manager.force_villagers_to_homes()
        # Notify Interface that game has started
        self.input_handler._adjust_camera_after_resize()
        on_game_started(self)
    
    def handle_events(self):
        """Delegate event handling to input handler."""
        self.input_handler.handle_events()
    
    def handle_input(self):
        """Delegate input processing to input handler."""
        self.input_handler.handle_input()
        
    def render(self):
        """Delegate rendering to render manager."""
        self.render_manager.render()
    
    def _update_camera_bounds(self):
        """Update camera boundaries based on current screen and village size."""
        # Ensure we have valid width and height values for both village and screen
        if not hasattr(self, 'village_data') or 'width' not in self.village_data or 'height' not in self.village_data:
            print("Warning: Cannot update camera bounds - missing village dimensions")
            return
            
        # Validate that village dimensions make sense
        if self.village_data['width'] <= 0 or self.village_data['height'] <= 0:
            print(f"Warning: Invalid village dimensions: {self.village_data['width']}x{self.village_data['height']}")
            return
            
        # Validate screen dimensions
        if self.SCREEN_WIDTH <= 0 or self.SCREEN_HEIGHT <= 0:
            print(f"Warning: Invalid screen dimensions: {self.SCREEN_WIDTH}x{self.SCREEN_HEIGHT}")
            return
            
        # Log current values for debugging
        print(f"Updating camera bounds - Screen: {self.SCREEN_WIDTH}x{self.SCREEN_HEIGHT}, Village: {self.village_data['width']}x{self.village_data['height']}")


    def update(self):
        """Delegate game state updates to update manager or handle resize mode."""
        if self.resize_mode:
            # In resize mode, we use a different event model
            # Process events one at a time like in the demo
            pygame.event.pump()
            
            # Check if we have events waiting
            if pygame.event.peek(pygame.VIDEORESIZE):
                # Process the resize event
                event = pygame.event.get(pygame.VIDEORESIZE)[0]
                self.input_handler._handle_resize_event(event)
                
                # Reset the resize timer
                self.resize_timer = pygame.time.get_ticks()
            else:
                # Check if we should exit resize mode
                current_time = pygame.time.get_ticks()
                if current_time - self.resize_timer > self.resize_timeout:
                    self.resize_mode = False
                    print("Exiting resize mode")
            
            # Still process other critical events, but one at a time
            for event_type in [pygame.QUIT, pygame.KEYDOWN]:
                if pygame.event.peek(event_type):
                    event = pygame.event.get(event_type)[0]
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.running = False
        else:
            # Normal update when not in resize mode
            self.update_manager.update()
