"""
Game State - Core game state class
"""
import pygame
from ui import Interface
import random

# Import managers and systems
from game_core.input_handler import InputHandler
from game_core.update_manager import UpdateManager
from game_core.render_manager import RenderManager
from entities.villager_manager import VillagerManager
from entities.housing_manager import HousingManager
from systems.command_system import CommandSystem
from systems.interaction_system import InteractionSystem
from systems.time_system import TimeSystem

# Import existing modules
from utils.asset_loader import load_assets
from village.village_generator import generate_village
from ui.ui_manager import UIManager
from ui.renderer import Renderer
from ui.console_manager import ConsoleManager
from systems.time_manager import TimeManager
from ui.housing_ui import HousingUI
from ui.renderer_enhancement import enhance_renderer_for_interiors

class VillageGame:
    """Main game state class that holds all game data and manager references."""
    
    def __init__(self):
        """Initialize the game state and all subsystems."""
        # Game setup
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.time_scale = 1.0
        
        # Get screen information
        infoObject = pygame.display.Info()
        self.SCREEN_WIDTH = infoObject.current_w
        self.SCREEN_HEIGHT = infoObject.current_h - 40
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Village Simulation")
        
        # Game constants
        self.TILE_SIZE = 32
        self.CAMERA_SPEED = 8
        self.INTERACTION_RADIUS = 50
        
        # Load assets first - everything depends on this
        self.assets = load_assets()
        
        # Initialize UI components
        self.ui_manager = UIManager(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.renderer = Renderer(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.TILE_SIZE)
        self.housing_ui = HousingUI(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.console_manager = ConsoleManager(self.screen, self.assets, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        
        # Initialize time manager
        self.time_manager = TimeManager(day_length_seconds=600)  # 10 minutes per day
        self.time_manager.set_time(6.0)  # 6 am
        
        # Generate village
        self.village_data = generate_village(60, self.assets, self.TILE_SIZE)
        
        # Enhance renderer for interiors
        enhance_renderer_for_interiors(Renderer)
        self.renderer.initialize_interiors(self.village_data)
        
        # Create villager manager and initialize villagers
        self.villager_manager = VillagerManager(self)
        self.villagers = pygame.sprite.Group()  # Sprite group for villagers
        self.villager_manager.create_villagers(20)  # Create 20 villagers
        
        # Create housing manager and assign housing
        self.housing_manager = HousingManager(self)
        self.housing_manager.assign_building_types()
        self.housing_manager.assign_housing()
        self.housing_manager.force_villagers_to_homes()
        
        # Create command system and register commands
        self.command_system = CommandSystem(self, self.console_manager)
        self.command_system.register_commands()
        
        # Create interaction system
        self.interaction_system = InteractionSystem(self)
        
        # Create time system
        self.time_system = TimeSystem(self)
        
        # Camera position - start at center of village
        self.camera_x = (self.village_data['size'] - self.SCREEN_WIDTH) // 2
        self.camera_y = (self.village_data['size'] - self.SCREEN_HEIGHT) // 2
        
        # Game state
        self.selected_villager = None
        self.paused = False
        self.show_debug = False
        self.show_paths = False
        
        # Mouse hover state
        self.hovered_building = None
        
        # Animation state
        self.animation_timer = 0
        self.water_frame = 0
        
        # Create additional managers
        self.input_handler = InputHandler(self)
        self.update_manager = UpdateManager(self)
        self.render_manager = RenderManager(self)
        
        # Notify Interface about game start
        Interface.on_game_started(self)
        current_time = pygame.time.get_ticks()
        Interface.update(current_time, 0)
        Interface.on_village_generated(self.village_data)
    
    def handle_events(self):
        """Handle pygame events."""
        self.input_handler.handle_events()
    
    def handle_input(self):
        """Handle keyboard input for camera movement."""
        self.input_handler.handle_input()
    
    def update(self):
        """Update game state."""
        self.update_manager.update()
    
    def render(self):
        """Render the game."""
        self.render_manager.render()
