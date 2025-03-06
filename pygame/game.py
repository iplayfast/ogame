import pygame
import sys
import random
import math
from pygame.locals import *

# Import custom modules
from asset_loader import load_assets
from village_generator import generate_village
from villager import Villager
from ui_manager import UIManager
from renderer import Renderer
from console_manager import ConsoleManager
from time_manager import TimeManager
# Add these imports for housing functionality
from villager_housing import assign_housing_and_jobs, load_assignments, update_game_with_assignments
from housing_ui import HousingUI
from renderer_enhancement import enhance_renderer_for_interiors

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Screen setup
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 960
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Village Simulation with Console")

# Game constants
TILE_SIZE = 32
CAMERA_SPEED = 8
INTERACTION_RADIUS = 50

class VillageGame:

    def __init__(self):
        # Game setup
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.time_scale = 1.0  # Add time scale property for console commands
        self.screen = screen       
    
        # Load assets first - everything depends on this
        self.assets = load_assets()
    
        # Store tile size for console reference
        self.TILE_SIZE = TILE_SIZE
    
        # Initialize UI components after assets are loaded
        self.ui_manager = UIManager(screen, self.assets, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.renderer = Renderer(screen, self.assets, SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE)
        self.housing_ui = HousingUI(screen, self.assets, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.console_manager = ConsoleManager(screen, self.assets, SCREEN_WIDTH, SCREEN_HEIGHT)
    
        # Initialize time manager for day/night cycle
        self.time_manager = TimeManager(day_length_seconds=600)  # 10 minutes per day
    
        # Generate a larger village
        self.village_data = generate_village(60, self.assets, TILE_SIZE)  # 60x60 tiles
    
        # Enhance renderer for interiors AFTER village data is generated
        enhance_renderer_for_interiors(Renderer)
        self.renderer.initialize_interiors(self.village_data)

        # Add commands to console
        self.console_manager.commands.update({
            "daytime": self.console_manager._cmd_daytime,
            "timespeed": self.console_manager._cmd_timespeed,
            # New commands for housing
            "houses": self._cmd_houses,
            "assign": self._cmd_assign_housing
        })
    
        # Assign building types
        self.assign_building_types()
    
        # Create villagers
        self.villagers = pygame.sprite.Group()
        self.create_villagers(20)  # Create 20 villagers
    
        # Assign housing and jobs to villagers
        self.assign_housing()
    
        # Camera position - start at center of village
        self.camera_x = (self.village_data['size'] - SCREEN_WIDTH) // 2
        self.camera_y = (self.village_data['size'] - SCREEN_HEIGHT) // 2
    
        # Game state
        self.selected_villager = None
        self.paused = False
        self.show_debug = False
    
        # Mouse hover state
        self.hovered_building = None
    
        # Animation timer
        self.animation_timer = 0
        self.water_frame = 0


    def create_villagers(self, num_villagers):
        """Create villagers and place them in the village."""
        print(f"Creating {num_villagers} villagers...")
        for i in range(num_villagers):
            # Try to place on a path if possible
            if self.village_data['paths']:
                path = random.choice(self.village_data['paths'])
                x, y = path['position']
                # Add slight offset
                x += random.randint(-TILE_SIZE//2, TILE_SIZE//2)
                y += random.randint(-TILE_SIZE//2, TILE_SIZE//2)
            else:
                # Otherwise place randomly
                padding = TILE_SIZE * 3
                x = random.randint(padding, self.village_data['size'] - padding)
                y = random.randint(padding, self.village_data['size'] - padding)
            
            villager = Villager(x, y, self.assets, TILE_SIZE)
            self.villagers.add(villager)
            print(f"Created villager {i+1}: {villager.name} ({villager.job})")
        
        print("All villagers created successfully!")
    
    def assign_building_types(self):
        """Assign building types to buildings (house, store, inn, etc.)."""
        building_types = {
            "small": ["House", "Cottage", "Workshop", "Storage"],
            "medium": ["Inn", "Store", "Tavern", "Smithy", "Bakery"],
            "large": ["Town Hall", "Market", "Temple", "Manor"]
        }
        
        for building in self.village_data['buildings']:
            size = building['size']
            available_types = building_types.get(size, ["House"])
            building['building_type'] = random.choice(available_types)
    def assign_housing(self):
        """Assign housing and jobs to villagers."""
        # First check if assignments already exist
        assignments = load_assignments()
        if assignments and 'villagers' in assignments:
            print("Loading existing housing assignments...")
            update_game_with_assignments(self, assignments)
        else:
            print("Creating new housing assignments...")
            assignments = assign_housing_and_jobs(self.villagers, self.village_data)
            update_game_with_assignments(self, assignments)
    
        # Initialize home positions for all villagers (put them in bed at start)
        for villager in self.villagers:
            if hasattr(villager, 'initialize_home_position'):
                villager.initialize_home_position()
                villager.is_sleeping = True
                villager.current_activity = "Sleeping"

    
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            # First, check if the console should handle this event
            if self.console_manager.handle_event(event, self):
                continue
                
            if event.type == pygame.QUIT:
                self.running = False
                print("Quit event received")
            
            # Key press events
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    print("ESC key pressed - quitting")
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    print(f"Game {'paused' if self.paused else 'resumed'}")
                elif event.key == pygame.K_d:
                    self.show_debug = not self.show_debug
                    print(f"Debug display {'enabled' if self.show_debug else 'disabled'}")
                elif event.key == pygame.K_t:
                    # Test key for time adjustment - advance time by 1 hour
                    self.time_manager.set_time((self.time_manager.current_hour + 1) % 24)
                    print(f"Time advanced to {self.time_manager.get_time_string()}")
            
            # Mouse click events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_click(event.pos)
            
            # Mouse motion for hover effects
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)
    
    def handle_click(self, pos):
        """Handle mouse click, select villager if clicked."""
        # Don't handle clicks if console is active
        if self.console_manager.is_active():
            return
            
        # Convert screen position to world position
        world_x = pos[0] + self.camera_x
        world_y = pos[1] + self.camera_y
        
        # Deselect previous villager
        if self.selected_villager:
            self.selected_villager.is_selected = False
            self.selected_villager = None
            
        # Check if clicked on a building
        for building_index, building in enumerate(self.village_data['buildings']):
            x, y = building['position']
            size = TILE_SIZE * 3 if building['size'] == 'large' else (
                   TILE_SIZE * 2 if building['size'] == 'medium' else TILE_SIZE)
            
            if x <= world_x <= x + size and y <= world_y <= y + size:
                # Add building index
                building['id'] = building_index
                self.housing_ui.set_selected_building(building)
                print(f"Clicked on building: {building.get('building_type', 'house')}")
                return
        
        # Reset selected building if clicked elsewhere
        self.housing_ui.set_selected_building(None)
        
        # Check if clicked on a villager
        for villager in self.villagers:
            if villager.rect.collidepoint((world_x, world_y)):
                villager.is_selected = True
                self.selected_villager = villager
                print(f"Selected villager: {villager.name}")
                break
    
    def handle_mouse_motion(self, pos):
        """Handle mouse motion for hover effects."""
        # Convert screen position to world position
        world_x = pos[0] + self.camera_x
        world_y = pos[1] + self.camera_y
        
        # Reset hovered building
        self.hovered_building = None
        
        # Check if mouse is over a building
        for building in self.village_data['buildings']:
            x, y = building['position']
            size = TILE_SIZE * 3 if building['size'] == 'large' else (
                   TILE_SIZE * 2 if building['size'] == 'medium' else TILE_SIZE)
            
            if x <= world_x <= x + size and y <= world_y <= y + size:
                self.hovered_building = building
                break
    
    def handle_input(self):
        """Handle keyboard input for camera movement."""
        # Skip handling input if console is active
        if self.console_manager.is_active():
            return
            
        keys = pygame.key.get_pressed()
        
        # Camera movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.camera_x -= CAMERA_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.camera_x += CAMERA_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.camera_y -= CAMERA_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.camera_y += CAMERA_SPEED
        
        # Ensure camera stays within village bounds
        self.camera_x = max(0, min(self.camera_x, self.village_data['size'] - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.camera_y, self.village_data['size'] - SCREEN_HEIGHT))
    
    def update(self):
        """Update game state."""
        # Get current time and delta time
        current_time = pygame.time.get_ticks()
        dt = self.clock.get_time()  # ms since last frame
        
        # Apply time scaling
        scaled_dt = dt * self.time_scale
        
        # Update console even when paused
        self.console_manager.update(dt)
        
        # Update time manager (always update, even when paused, unless in console)
        if not self.paused:
            self.time_manager.update(dt, self.time_scale)
        
        # Don't update the rest if paused and not in console
        if self.paused and not self.console_manager.is_active():
            return
        
        # Update villagers
        for villager in self.villagers:
            try:
                # Use enhanced update if available, otherwise use normal update
                if hasattr(villager, 'enhanced_update'):
                    villager.enhanced_update(self.village_data, current_time, self.assets, self.time_manager)
                else:
                    villager.update(self.village_data, current_time, self.assets)
            except Exception as e:
                print(f"Error updating villager {villager.name}: {e}")
        
        # Update animations
        self.animation_timer += 1
        if self.animation_timer >= 15:  # Change water frame every 15 frames (4 FPS)
            self.animation_timer = 0
            if self.assets['environment']['water']:  # Check if we have water frames
                self.water_frame = (self.water_frame + 1) % len(self.assets['environment']['water'])
                
                # Update water animation frames
                for water_tile in self.village_data['water']:
                    water_tile['frame'] = self.water_frame
        
        # Check for villager interactions (conversations)
        self.check_villager_interactions()
    
    def check_villager_interactions(self):
        """Check for interactions between villagers."""
        # Find villagers that are close to each other
        for v1 in self.villagers:
            for v2 in self.villagers:
                if v1 != v2:  # Don't compare a villager with itself
                    # Calculate distance between villagers
                    distance = math.sqrt((v1.position.x - v2.position.x)**2 + 
                                        (v1.position.y - v2.position.y)**2)
                    
                    # If villagers are close and both are talking, they might be conversing
                    if distance < INTERACTION_RADIUS and v1.is_talking and v2.is_talking:
                        # There's a small chance they'll start a conversation
                        if random.random() < 0.01:  # 1% chance per frame
                            # Play conversation sound if not already playing
                            if not pygame.mixer.get_busy():
                                try:
                                    v1.conversation_sound.play()
                                except Exception as e:
                                    print(f"Error playing conversation sound: {e}")
    
    def render(self):
        """Delegate rendering to the renderer and console."""
        # Render the village and UI, telling renderer if console is active
        self.renderer.render_village(
            self.village_data,
            self.villagers,
            self.camera_x,
            self.camera_y,
            self.ui_manager,
            self.selected_villager,
            self.hovered_building,
            self.show_debug,
            self.clock,
            self.water_frame,
            self.console_manager.is_active(),  # Pass console state
            self.console_manager.console_height,  # Pass console height
            self.time_manager  # Pass time manager for day/night effects
        )
        
        # If a building is selected, draw its detailed info
        if self.housing_ui.selected_building:
            self.housing_ui.draw_enhanced_building_info(
                self.housing_ui.selected_building, 
                self.villagers, 
                self.camera_x, 
                self.camera_y
            )
        
        # If a villager is selected, add housing info
        if self.selected_villager:
            self.housing_ui.draw_villager_housing_info(
                self.selected_villager,
                self.camera_x,
                self.camera_y
            )
            
            # Draw daily activities
            self.housing_ui.draw_daily_activities(self.selected_villager)
        
        # Draw house names over buildings
        for building in self.village_data['buildings']:
            if 'name' in building:
                self.housing_ui.draw_building_name(building, self.camera_x, self.camera_y)
        
        for villager in self.villagers:
            if hasattr(villager, 'is_sleeping') and villager.is_sleeping and hasattr(villager, 'draw_sleep_indicator'):
                villager.draw_sleep_indicator(self.screen, self.camera_x, self.camera_y)

        # Render the console (if active)
        self.console_manager.draw()
        
        # Update display
        pygame.display.flip()
    
    # New console commands
    def _cmd_houses(self, args, game_state):
        """List all houses and their residents."""
        self.console_manager.add_output("Houses and Residents:")
        
        # Find houses with residents
        houses_with_residents = {}
        for villager in self.villagers:
            if hasattr(villager, 'home') and villager.home and 'id' in villager.home:
                house_id = villager.home['id']
                if house_id not in houses_with_residents:
                    houses_with_residents[house_id] = []
                houses_with_residents[house_id].append(villager)
        
        # Display houses
        for house_id, residents in houses_with_residents.items():
            if house_id < 0 or house_id >= len(self.village_data['buildings']):
                continue
                
            building = self.village_data['buildings'][house_id]
            house_name = building.get('name', f"House #{house_id}")
            house_type = building.get('building_type', 'Unknown')
            
            self.console_manager.add_output(f"{house_name} ({house_type}):")
            for resident in residents:
                self.console_manager.add_output(f"  - {resident.name} ({resident.job})")
    def _cmd_interiors(self,args,game_state):
        """Toggle building interiors visibilty"""
        if not args:
            current_state = self.renderer.show_interiors
            self.add_output(f"Building interiors are currently {'visible' if current_state else 'hidden'}.")
            self.add_output("Use 'interiors on' or 'interiors off' to change.")
            return
    
        command = args[0].lower()
    
        if command == "on":
            if not self.renderer.show_interiors:
                self.renderer.toggle_interiors()
            self.add_output("Building interiors turned ON.")
        elif command == "off":
            if self.renderer.show_interiors:
                self.renderer.toggle_interiors()
            self.add_output("Building interiors turned OFF.")
        elif command == "toggle":
            new_state = self.renderer.toggle_interiors()
            self.add_output(f"Building interiors {'shown' if new_state else 'hidden'}.")
        else:
            self.add_output(f"Unknown option: '{command}'")
            self.add_output("Use 'interiors on', 'interiors off', or 'interiors toggle'.")

    # Modify handle_events method in VillageGame to handle the toggle hotkey
    def modified_handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            # First, check if the console should handle this event
            if self.console_manager.handle_event(event, self):
                continue
            
            if event.type == pygame.QUIT:
                self.running = False
                print("Quit event received")
        
            # Key press events
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    print("ESC key pressed - quitting")
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    print(f"Game {'paused' if self.paused else 'resumed'}")
                elif event.key == pygame.K_d:
                    self.show_debug = not self.show_debug
                    print(f"Debug display {'enabled' if self.show_debug else 'disabled'}")
                elif event.key == pygame.K_t:
                    # Test key for time adjustment - advance time by 1 hour
                    self.time_manager.set_time((self.time_manager.current_hour + 1) % 24)
                    print(f"Time advanced to {self.time_manager.get_time_string()}")
                elif event.key == pygame.K_i:
                    # Toggle interiors
                    if hasattr(self.renderer, 'toggle_interiors'):
                        state = self.renderer.toggle_interiors()
                        print(f"Building interiors {'enabled' if state else 'disabled'}")
                elif event.key == pygame.K_i:
                    # Toggle interiors
                    if hasattr(self.renderer, 'toggle_interiors'):
                        state = self.renderer.toggle_interiors()
                        print(f"Building interiors {'enabled' if state else 'disabled'}")
        
            # Mouse click events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_click(event.pos)
        
            # Mouse motion for hover effects
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)





    def _cmd_assign_housing(self, args, game_state):
        """Generate or regenerate housing assignments."""
        if not args:
            self.console_manager.add_output("Usage: assign <new|reload>")
            self.console_manager.add_output("  new - Generate new housing assignments")
            self.console_manager.add_output("  reload - Reload existing assignments from file")
            return
        
        command = args[0].lower()
        
        if command == "new":
            self.console_manager.add_output("Generating new housing assignments...")
            assignments = assign_housing_and_jobs(self.villagers, self.village_data)
            update_game_with_assignments(self, assignments)
            self.console_manager.add_output("Housing assignments created and saved to village_assignments.json")
        
        elif command == "reload":
            self.console_manager.add_output("Reloading housing assignments from file...")
            assignments = load_assignments()
            if assignments and 'villagers' in assignments:
                update_game_with_assignments(self, assignments)
                self.console_manager.add_output("Housing assignments loaded successfully")
            else:
                self.console_manager.add_output("Error: No valid assignment file found")
        
        else:
            self.console_manager.add_output(f"Unknown option: '{command}'")
            self.console_manager.add_output("Use 'assign new' or 'assign reload'")


def main():
    # Initialize the game
    game = VillageGame()
    
    # Print instructions
    print("Village Simulation with Console")
    print("Controls:")
    print("  WASD/Arrows: Move camera")
    print("  Mouse click: Select villager or building")
    print("  P: Pause/resume game")
    print("  D: Toggle debug info")
    print("  T: Advance time by 1 hour (test key)")
    print("  ~ (tilde/backtick): Toggle console")
    print("  ESC: Quit")
    print()
    print("Console Commands:")
    print("  help - Show available commands")
    print("  daytime <hour> - View or set time of day")
    print("  timespeed <seconds> - Set day length in seconds")
    print("  time <scale> - Set game speed multiplier")
    print("  houses - List all houses and their residents")
    print("  assign <new|reload> - Manage housing assignments")
    
    # Main game loop
    while game.running:
        # Handle events
        game.handle_events()
        
        # Process input
        game.handle_input()
        
        # Update game state
        game.update()
        
        # Render
        game.render()
        
        # Cap the frame rate
        game.clock.tick(game.fps)
    
    # Clean up
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
