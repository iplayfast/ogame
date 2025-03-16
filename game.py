import pygame
import sys
import random
import math
import Interface
from pygame.locals import *

# Import custom modules
from asset_loader import load_assets
# Replace this import
# from village_generator import generate_village
# With this import
from village_generator_class import generate_village
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
        self.time_manager.set_time(6.0) #6 am
        # Generate a larger village
        self.village_data = generate_village(60, self.assets, TILE_SIZE)  # 60x60 tiles
    
        # Enhance renderer for interiors AFTER village data is generated
        enhance_renderer_for_interiors(Renderer)
        self.renderer.initialize_interiors(self.village_data)

        # Add commands to console
        
        self.console_manager.commands.update({
            "daytime": self.console_manager._cmd_daytime,
            "timespeed": self.console_manager._cmd_timespeed,
            "houses": self._cmd_houses,
            "assign": self._cmd_assign_housing,
            "interiors": self._cmd_interiors,
            "wake": self._cmd_wake,      # New command to wake villagers
            "sleep": self._cmd_sleep,    # New command to make villagers sleep
            "fix": self._cmd_fix         # New command to fix various issues
        })
        # Assign building types
        self.assign_building_types()
    
        # Create villagers
        self.villagers = pygame.sprite.Group()
        self.create_villagers(20)  # Create 20 villagers
    
        # Assign housing and jobs to villagers
        self.assign_housing()

        # IMPORTANT: Force villagers to their homes
        print("Forcing villagers to their home positions...")
        self.force_villagers_to_homes()
    
        # Camera position - start at center of village
        self.camera_x = (self.village_data['size'] - SCREEN_WIDTH) // 2
        self.camera_y = (self.village_data['size'] - SCREEN_HEIGHT) // 2
    
        # Game state
        self.selected_villager = None
        self.paused = False
        self.show_debug = False
        self.show_paths = False
        # Mouse hover state
        self.hovered_building = None
    
        # Animation timer
        self.animation_timer = 0
        self.water_frame = 0
        Interface.on_game_started(self)
        current_time = pygame.time.get_ticks()
        Interface.update(current_time, 0)
        Interface.on_village_generated(self.village_data)

        
        
    def create_villagers(self, num_villagers):
        """Create villagers with pathfinding capability."""
        print(f"Creating {num_villagers} villagers...")
        for i in range(num_villagers):
            # Try to place on a path if possible
            if self.village_data['paths']:
                path = random.choice(self.village_data['paths'])
                x, y = path['position']
                # Add slight offset
                x += random.randint(-self.TILE_SIZE//2, self.TILE_SIZE//2)
                y += random.randint(-self.TILE_SIZE//2, self.TILE_SIZE//2)
            else:
                # Otherwise place randomly
                padding = self.TILE_SIZE * 3
                x = random.randint(padding, self.village_data['size'] - padding)
                y = random.randint(padding, self.village_data['size'] - padding)
            
            villager = Villager(x, y, self.assets, self.TILE_SIZE)
            
            # The villager class already has the necessary pathfinding methods
            # We don't need to assign them here as they're part of the class
            
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
        # Force creation of new housing assignments
        print("Creating new housing assignments...")
        assignments = assign_housing_and_jobs(self.villagers, self.village_data)
        update_game_with_assignments(self, assignments)
        
        # Track occupied bed positions to avoid overlap
        occupied_bed_positions = {}
        # Initialize home positions for all villagers
        print("Placing villagers in their homes...")
        for villager in self.villagers:
            if hasattr(villager, 'initialize_home_position'):
                self.initialize_unique_bed_position(villager, occupied_bed_positions)
                villager.is_sleeping = True
                villager.current_activity = "Sleeping"
        
    
    def initialize_unique_bed_position(self, villager, occupied_bed_positions):
        """Initialize home position with a unique bed position for each villager."""
        if not hasattr(villager, 'home') or not villager.home or 'position' not in villager.home:
            # No home assigned, can't initialize
            return
            
        home_pos = villager.home['position']
        home_id = villager.home.get('id', -1)
        
        # Find the actual building
        if 0 <= home_id < len(self.village_data['buildings']):
            building = self.village_data['buildings'][home_id]
            building_pos = building['position']
            building_size = building['size']
            
            # Convert to pixel sizes
            size_multiplier = 3 if building_size == 'large' else (2 if building_size == 'medium' else 1)
            building_size_px = self.TILE_SIZE * size_multiplier
            
            # Get the number of roommates to determine how to spread beds
            roommates = villager.home.get('roommates', [])
            num_roommates = len(roommates)
            
            # Default position (for safety)
            bed_x = building_pos[0] + building_size_px // 2
            bed_y = building_pos[1] + building_size_px // 2
            
            # Try to find an available position
            attempt_count = 0
            padding = self.TILE_SIZE // 3
            
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
                        bed_x = building_pos[0] + padding + col * (building_size_px - padding * 2 - self.TILE_SIZE)
                        bed_y = building_pos[1] + building_size_px // 2
                else:  # small
                    # For small buildings, we have limited space
                    if num_roommates <= 1:
                        # Single occupant - place in center
                        bed_x = building_pos[0] + building_size_px // 2
                        bed_y = building_pos[1] + building_size_px // 2
                    else:
                        # Multiple occupants - stagger positions slightly
                        offset_x = (attempt_count % 3 - 1) * (self.TILE_SIZE // 3)
                        offset_y = (attempt_count // 3 - 1) * (self.TILE_SIZE // 3)
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
            
            #print(f"Positioned {villager.name} at home ID {home_id} ({building['building_type']}): position ({bed_x}, {bed_y})")
        else:
            print(f"Warning: {villager.name} has invalid home ID: {home_id}")


    def force_villagers_to_homes(self):
        """Force all villagers to be positioned in their assigned homes."""
        villagers_with_homes = 0
        villagers_without_homes = 0
        
        for villager in self.villagers:
            # Check if villager has a home assigned
            if hasattr(villager, 'home') and villager.home and 'position' in villager.home:
                villagers_with_homes += 1
                home_pos = villager.home['position']
                home_id = villager.home.get('id', -1)
                
                # Find the actual building
                if 0 <= home_id < len(self.village_data['buildings']):
                    building = self.village_data['buildings'][home_id]
                    building_pos = building['position']
                    building_size = building['size']
                    
                    # Convert to pixel sizes
                    size_multiplier = 3 if building_size == 'large' else (2 if building_size == 'medium' else 1)
                    building_size_px = self.TILE_SIZE * size_multiplier
                    
                    # Calculate a position inside the house (near top area for bed)
                    padding = self.TILE_SIZE // 2
                    bed_x = building_pos[0] + random.randint(padding, building_size_px - padding)
                    bed_y = building_pos[1] + random.randint(padding, building_size_px // 2)
                    
                    # Set the villager's bed position
                    villager.bed_position = (bed_x, bed_y)
                    
                    # Directly set position
                    villager.position.x = bed_x
                    villager.position.y = bed_y
                    
                    # Update rect
                    villager.rect.centerx = int(villager.position.x)
                    villager.rect.centery = int(villager.position.y)
                    
                    # Set sleep state
                    villager.is_sleeping = True
                    villager.current_activity = "Sleeping"
                    
                    # Clear any destination
                    villager.destination = None
                    
                    #print(f"Positioned {villager.name} at home ID {home_id} ({building['building_type']}): position ({bed_x}, {bed_y})")
                else:
                    print(f"Warning: {villager.name} has invalid home ID: {home_id}")
                    villagers_without_homes += 1
            else:
                villagers_without_homes += 1
                print(f"Warning: {villager.name} has no home assigned")
        
        print(f"Villager home stats: {villagers_with_homes} with homes, {villagers_without_homes} without homes")
    

    def modified_handle_events(self):
        """Handle pygame events with Interface integration."""
        old_camera_pos = (self.camera_x, self.camera_y)
        
        # Store previous game state
        was_paused = self.paused
        was_debug_enabled = self.show_debug
        
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
                    # Notify through Interface
                    Interface.on_game_paused(self.paused)
                elif event.key == pygame.K_d:
                    self.show_debug = not self.show_debug
                    print(f"Debug display {'enabled' if self.show_debug else 'disabled'}")
                    # Notify through Interface
                    Interface.on_debug_toggled(self.show_debug)
                elif event.key == pygame.K_t:
                    # Test key for time adjustment - advance time by 1 hour
                    old_hour = self.time_manager.current_hour
                    old_time_name = self.time_manager.get_time_name()
                    
                    self.time_manager.set_time((self.time_manager.current_hour + 1) % 24)
                    print(f"Time advanced to {self.time_manager.get_time_string()}")
                    
                    # Notify through Interface
                    new_hour = self.time_manager.current_hour
                    new_time_name = self.time_manager.get_time_name()
                    Interface.on_time_changed(new_hour, new_time_name)
                elif event.key == pygame.K_i:
                    # Toggle interiors
                    if hasattr(self.renderer, 'toggle_interiors'):
                        state = self.renderer.toggle_interiors()
                        print(f"Building interiors {'enabled' if state else 'disabled'}")
                        # Notify through Interface
                        Interface.on_ui_panel_toggled("building_interiors", state)
            
            # Mouse click events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_click(event.pos)
                    
                    # If click is on the minimap, notify Interface
                    minimap_rect = self.ui_manager.get_minimap_rect()  # You would need to add this method
                    if minimap_rect and minimap_rect.collidepoint(event.pos):
                        # Convert minimap click to world position
                        world_x, world_y = self.ui_manager.minimap_to_world(event.pos)
                        Interface.on_minimap_clicked(event.pos, (world_x, world_y))
                        
            # Mouse motion for hover effects
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)
        
        # After all events, check if camera position changed
        new_camera_pos = (self.camera_x, self.camera_y)
        if old_camera_pos != new_camera_pos:
            Interface.on_camera_moved(old_camera_pos, new_camera_pos)
            
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
                elif event.key == pygame.K_v:
                    # Toggle path visualization
                    self.show_paths = not self.show_paths
                    print(f"Path visualization {'enabled' if self.show_paths else 'disabled'}")
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


    def handle_click(self, pos):
        """Handle mouse click, select villager if clicked."""
        # Don't handle clicks if console is active
        if self.console_manager.is_active():
            return
            
        # Convert screen position to world position
        world_x = pos[0] + self.camera_x
        world_y = pos[1] + self.camera_y
        
        # Check if clicked on a building
        for building_index, building in enumerate(self.village_data['buildings']):
            x, y = building['position']
            size = self.TILE_SIZE * 3 if building['size'] == 'large' else (
                self.TILE_SIZE * 2 if building['size'] == 'medium' else self.TILE_SIZE)
            
            if x <= world_x <= x + size and y <= world_y <= y + size:
                # Add building index
                building['id'] = building_index
                self.housing_ui.set_selected_building(building)
                print(f"Clicked on building: {building.get('building_type', 'house')}")
                return
        
        # Reset selected building if clicked elsewhere
        self.housing_ui.set_selected_building(None)
        
        # Find all villagers at click point
        clicked_villagers = []
        for villager in self.villagers:
            if villager.rect.collidepoint((world_x, world_y)):
                clicked_villagers.append(villager)
        
        # If no villagers were clicked, deselect current villager
        if not clicked_villagers:
            if self.selected_villager:
                self.selected_villager.is_selected = False
                self.selected_villager = None
            return
        
        # If multiple villagers at the same spot
        if len(clicked_villagers) > 1:
            # If we already have a selected villager that's in the clicked list
            if self.selected_villager in clicked_villagers:
                # Get index of current selected villager
                current_index = clicked_villagers.index(self.selected_villager)
                # Select the next villager in the list (cycle through)
                next_index = (current_index + 1) % len(clicked_villagers)
                
                # Deselect current villager
                self.selected_villager.is_selected = False
                
                # Select next villager
                self.selected_villager = clicked_villagers[next_index]
                self.selected_villager.is_selected = True
                print(f"Selected villager: {self.selected_villager.name}")
            else:
                # If no current selection among these villagers, select the first one
                if self.selected_villager:
                    self.selected_villager.is_selected = False
                
                self.selected_villager = clicked_villagers[0]
                self.selected_villager.is_selected = True
                print(f"Selected villager: {self.selected_villager.name}")
        else:
            # Just one villager clicked - normal selection
            if self.selected_villager:
                self.selected_villager.is_selected = False
            
            self.selected_villager = clicked_villagers[0]
            self.selected_villager.is_selected = True
            print(f"Selected villager: {self.selected_villager.name}")


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
        """Render the game."""
        # Call the original rendering code
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
            self.console_manager.is_active(),
            self.console_manager.console_height,
            self.time_manager
        )
        
        # Render villager paths if enabled
        if self.show_paths:
            for villager in self.villagers:
                if hasattr(villager, 'draw_path'):
                    villager.draw_path(self.screen, self.camera_x, self.camera_y)
        
        # Draw housing UI if a building is selected
        if self.housing_ui.selected_building:
            self.housing_ui.draw_enhanced_building_info(
                self.housing_ui.selected_building, 
                self.villagers, 
                self.camera_x, 
                self.camera_y
            )
        
        # Draw villager housing info if a villager is selected
        if self.selected_villager:
            self.housing_ui.draw_villager_housing_info(
                self.selected_villager,
                self.camera_x,
                self.camera_y
            )
            
            # Draw daily activities
            self.housing_ui.draw_daily_activities(self.selected_villager)
            
            # Draw multiple villagers indicator
            self.ui_manager.draw_multiple_villagers_indicator(
                self.selected_villager,
                self.villagers,
                self.camera_x,
                self.camera_y
            )
        
        # Draw house names over buildings
        for building in self.village_data['buildings']:
            if 'name' in building:
                self.housing_ui.draw_building_name(building, self.camera_x, self.camera_y)
        
        # Draw sleep indicators
        for villager in self.villagers:
            if hasattr(villager, 'is_sleeping') and villager.is_sleeping and hasattr(villager, 'draw_sleep_indicator'):
                villager.draw_sleep_indicator(self.screen, self.camera_x, self.camera_y)
        
        # Draw console if active
        self.console_manager.draw()
        
        # Update display
        pygame.display.flip()

    # Add these methods to your VillageGame class

    def initialize_interface(self):
        """Initialize Interface with default callbacks."""
        # Register initial time update
        current_time = pygame.time.get_ticks()
        Interface.update(current_time, 0)
        
        # Notify that game started
        Interface.on_game_started(self)
        
        # Set up default callbacks
        Interface.setup_default_callbacks(enable_debug=False)

    def check_villager_interactions_with_interface(self):
        """Check for interactions between villagers and notify Interface."""
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
                            # Notify through Interface
                            Interface.on_villager_interaction(v1, v2, "conversation")
                            
                            # Play conversation sound if not already playing
                            if not pygame.mixer.get_busy():
                                try:
                                    v1.conversation_sound.play()
                                except Exception as e:
                                    print(f"Error playing conversation sound: {e}")
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
    def handle_click_with_interface(self, pos):
        """Handle mouse click with Interface integration."""
        # Don't handle clicks if console is active
        if self.console_manager.is_active():
            return
            
        # Store previously selected villager and building
        old_selected_villager = self.selected_villager
        old_selected_building = self.housing_ui.selected_building if hasattr(self.housing_ui, 'selected_building') else None
            
        # Convert screen position to world position
        world_x = pos[0] + self.camera_x
        world_y = pos[1] + self.camera_y
        
        # Check if clicked on a building
        for building_index, building in enumerate(self.village_data['buildings']):
            x, y = building['position']
            size = self.TILE_SIZE * 3 if building['size'] == 'large' else (
                self.TILE_SIZE * 2 if building['size'] == 'medium' else self.TILE_SIZE)
            
            if x <= world_x <= x + size and y <= world_y <= y + size:
                # Add building index
                building['id'] = building_index
                self.housing_ui.set_selected_building(building)
                
                # Notify through Interface
                Interface.on_building_selected(building)
                
                print(f"Clicked on building: {building.get('building_type', 'house')}")
                return
        
        # Reset selected building if clicked elsewhere
        if hasattr(self.housing_ui, 'selected_building') and self.housing_ui.selected_building is not None:
            self.housing_ui.set_selected_building(None)
        
        # Find all villagers at click point
        clicked_villagers = []
        for villager in self.villagers:
            if villager.rect.collidepoint((world_x, world_y)):
                clicked_villagers.append(villager)
        
        # If no villagers were clicked, deselect current villager
        if not clicked_villagers:
            if self.selected_villager:
                # Deselect current villager
                self.selected_villager.is_selected = False
                
                # Notify through Interface
                Interface.on_villager_selected(self.selected_villager, False)
                
                self.selected_villager = None
            return
        
        # If multiple villagers at the same spot
        if len(clicked_villagers) > 1:
            # If we already have a selected villager that's in the clicked list
            if self.selected_villager in clicked_villagers:
                # Get index of current selected villager
                current_index = clicked_villagers.index(self.selected_villager)
                # Select the next villager in the list (cycle through)
                next_index = (current_index + 1) % len(clicked_villagers)
                
                # Deselect current villager
                self.selected_villager.is_selected = False
                
                # Notify through Interface
                Interface.on_villager_selected(self.selected_villager, False)
                
                # Select next villager
                self.selected_villager = clicked_villagers[next_index]
                self.selected_villager.is_selected = True
                
                # Notify through Interface
                Interface.on_villager_selected(self.selected_villager, True)
                
                print(f"Selected villager: {self.selected_villager.name}")
            else:
                # If no current selection among these villagers, select the first one
                if self.selected_villager:
                    self.selected_villager.is_selected = False
                    
                    # Notify through Interface
                    Interface.on_villager_selected(self.selected_villager, False)
                
                self.selected_villager = clicked_villagers[0]
                self.selected_villager.is_selected = True
                
                # Notify through Interface
                Interface.on_villager_selected(self.selected_villager, True)
                
                print(f"Selected villager: {self.selected_villager.name}")
        else:
            # Just one villager clicked - normal selection
            if self.selected_villager:
                self.selected_villager.is_selected = False
                
                # Notify through Interface
                Interface.on_villager_selected(self.selected_villager, False)
            
            self.selected_villager = clicked_villagers[0]
            self.selected_villager.is_selected = True
            
            # Notify through Interface
            Interface.on_villager_selected(self.selected_villager, True)
            
            print(f"Selected villager: {self.selected_villager.name}")

    def handle_events_with_interface(self):
        """Handle pygame events with Interface integration."""
        old_camera_pos = (self.camera_x, self.camera_y)
        
        # Store previous game state
        was_paused = self.paused
        was_debug_enabled = self.show_debug
        
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
                    # Notify through Interface
                    Interface.on_game_paused(self.paused)
                elif event.key == pygame.K_d:
                    self.show_debug = not self.show_debug
                    print(f"Debug display {'enabled' if self.show_debug else 'disabled'}")
                    # Notify through Interface
                    Interface.on_debug_toggled(self.show_debug)
                elif event.key == pygame.K_t:
                    # Test key for time adjustment - advance time by 1 hour
                    old_hour = self.time_manager.current_hour
                    old_time_name = self.time_manager.get_time_name()
                    
                    self.time_manager.set_time((self.time_manager.current_hour + 1) % 24)
                    print(f"Time advanced to {self.time_manager.get_time_string()}")
                    
                    # Notify through Interface
                    new_hour = self.time_manager.current_hour
                    new_time_name = self.time_manager.get_time_name()
                    Interface.on_time_changed(new_hour, new_time_name)
                elif event.key == pygame.K_i:
                    # Toggle interiors
                    if hasattr(self.renderer, 'toggle_interiors'):
                        state = self.renderer.toggle_interiors()
                        print(f"Building interiors {'enabled' if state else 'disabled'}")
                        # Notify through Interface
                        Interface.on_ui_panel_toggled("building_interiors", state)
            
            # Mouse click events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_click_with_interface(event.pos)
                    
                    # If click is on the minimap, notify Interface
                    minimap_rect = pygame.Rect(
                        self.screen_width - 160, self.screen_height - 160, 150, 150
                    )  # Approximate minimap position
                    if minimap_rect.collidepoint(event.pos):
                        # Convert minimap click to world position
                        map_x = event.pos[0] - minimap_rect.left
                        map_y = event.pos[1] - minimap_rect.top
                        scale = minimap_rect.width / self.village_data['size']
                        world_x = int(map_x / scale)
                        world_y = int(map_y / scale)
                        Interface.on_minimap_clicked(event.pos, (world_x, world_y))
                    
            # Mouse motion for hover effects
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)
        
        # After all events, check if camera position changed
        new_camera_pos = (self.camera_x, self.camera_y)
        if old_camera_pos != new_camera_pos:
            Interface.on_camera_moved(old_camera_pos, new_camera_pos)

    def update_with_interface(self):
        """Update game state with Interface integration."""
        # Get current time and delta time
        current_time = pygame.time.get_ticks()
        dt = self.clock.get_time()  # ms since last frame
        
        # Update Interface time callbacks
        Interface.update(current_time, dt)
        
        # Apply time scaling
        scaled_dt = dt * self.time_scale
        
        # Update console even when paused
        self.console_manager.update(dt)
        
        # Update time manager (always update, even when paused, unless in console)
        if not self.paused:
            # Store old time data for change detection
            old_hour = self.time_manager.current_hour
            old_time_name = self.time_manager.get_time_name()
            
            # Update time
            self.time_manager.update(dt, self.time_scale)
            
            # Check if hour changed significantly or time period changed
            new_hour = self.time_manager.current_hour
            new_time_name = self.time_manager.get_time_name()
            
            # Notify of time change if the hour changed by at least 0.25 or the time period changed
            if abs(new_hour - old_hour) >= 0.25 or new_time_name != old_time_name:
                Interface.on_time_changed(new_hour, new_time_name)
        
        # Don't update the rest if paused and not in console
        if self.paused and not self.console_manager.is_active():
            return
        
        # Update villagers with tracking of activity changes
        for villager in self.villagers:
            try:
                # Use enhanced update with Interface if available
                if hasattr(villager, 'enhanced_update_with_interface'):
                    villager.enhanced_update_with_interface(self.village_data, current_time, self.assets, self.time_manager)
                elif hasattr(villager, 'enhanced_update'):
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
        
        # Check for villager interactions
        self.check_villager_interactions_with_interface()
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
                
# Replace the _cmd_wake method in your VillageGame class with this improved version

    def _cmd_wake(self, args, game_state):
        """Force villagers to wake up with proper state override."""
        if len(args) > 0 and args[0].lower() == "all":
            # Wake up all villagers
            count = 0
            for villager in self.villagers:
                if villager.is_sleeping:
                    # Use the override method for stable wake state
                    villager.override_sleep_state(force_awake=True, duration=30000, village_data=self.village_data)
                    count += 1
            
            self.console_manager.add_output(f"Forced {count} villagers to wake up")
            print(f"Wake command executed: {count} villagers instructed to wake up")
            return count
        else:
            # Try to find villager by name
            name_query = " ".join(args) if args else ""
            
            if not name_query:
                self.console_manager.add_output("Please specify a villager name or use 'wake all'")
                return False
                
            for villager in self.villagers:
                if name_query.lower() in villager.name.lower():
                    if villager.is_sleeping:
                        # Use the override method
                        villager.override_sleep_state(force_awake=True, duration=30000, village_data=self.village_data)
                        
                        self.console_manager.add_output(f"{villager.name} has been woken up")
                        print(f"Wake command executed: {villager.name} instructed to wake up")
                    else:
                        self.console_manager.add_output(f"{villager.name} is already awake")
                    return True
                    
            self.console_manager.add_output(f"Could not find villager: '{name_query}'")
            return False

    # And similarly for the sleep command:

    def _cmd_sleep(self, args, game_state):
        """Force villagers to sleep."""
        if len(args) > 0 and args[0].lower() == "all":
            # Put all villagers to sleep
            count = 0
            for villager in self.villagers:
                if not villager.is_sleeping:
                    # Use the override method
                    villager.override_sleep_state(force_awake=False, duration=30000, village_data=self.village_data)
                    count += 1
            
            self.console_manager.add_output(f"Forced {count} villagers to sleep")
            print(f"Sleep command executed: {count} villagers instructed to sleep")
            return count
        else:
            # Try to find villager by name
            name_query = " ".join(args) if args else ""
            
            if not name_query:
                self.console_manager.add_output("Please specify a villager name or use 'sleep all'")
                return False
                
            for villager in self.villagers:
                if name_query.lower() in villager.name.lower():
                    if not villager.is_sleeping:
                        # Use the override method
                        villager.override_sleep_state(force_awake=False, duration=30000, village_data=self.village_data)
                        
                        self.console_manager.add_output(f"{villager.name} has been put to sleep")
                        print(f"Sleep command executed: {villager.name} instructed to sleep")
                    else:
                        self.console_manager.add_output(f"{villager.name} is already sleeping")
                    return True
                    
            self.console_manager.add_output(f"Could not find villager: '{name_query}'")
            return False
    def _cmd_fix(self, args, game_state):
        """Fix common issues with villagers or game state."""
        if not args:
            self.console_manager.add_output("Available fixes:")
            self.console_manager.add_output("  fix sleepers - Force all villagers to follow correct sleep schedule")
            self.console_manager.add_output("  fix homes - Reset villagers to their home positions")
            self.console_manager.add_output("  fix all - Apply all fixes")
            return None
            
        fix_type = args[0].lower()
        
        if fix_type == "sleepers":
            # Fix villagers that are sleeping or waking at wrong times
            current_hour = self.time_manager.current_hour
            fixed_count = 0
            
            for villager in self.villagers:
                sleeping_time = current_hour < villager.wake_hour or current_hour >= villager.sleep_hour
                
                # Fix incorrect sleep state
                if sleeping_time and not villager.is_sleeping:
                    villager.is_sleeping = True
                    villager.current_activity = "Sleeping"
                    fixed_count += 1
                elif not sleeping_time and villager.is_sleeping:
                    villager.is_sleeping = False
                    villager.current_activity = "Waking up"
                    fixed_count += 1
                    
            self.console_manager.add_output(f"Fixed sleep states for {fixed_count} villagers")
            return fixed_count
            
        elif fix_type == "homes":
            # Reset villagers to their homes
            self.force_villagers_to_homes()
            self.console_manager.add_output("Reset villagers to their home positions")
            return True
            
        elif fix_type == "all":
            # Apply all fixes
            self._cmd_fix(["sleepers"], game_state)
            self._cmd_fix(["homes"], game_state)
            self.console_manager.add_output("Applied all fixes")
            return True
            
        else:
            self.console_manager.add_output(f"Unknown fix type: '{fix_type}'")
            self.console_manager.add_output("Use 'fix sleepers', 'fix homes', or 'fix all'")
            return False

    def _cmd_interiors(self, args, game_state):
        """Toggle building interiors visibility"""
        if not args:
            current_state = getattr(self.renderer, 'show_interiors', False)
            self.console_manager.add_output(f"Building interiors are currently {'visible' if current_state else 'hidden'}.")
            self.console_manager.add_output("Use 'interiors on' or 'interiors off' to change.")
            return
        
        command = args[0].lower()
        
        if command == "on":
            if hasattr(self.renderer, 'show_interiors'):
                self.renderer.show_interiors = True
                self.console_manager.add_output("Building interiors turned ON.")
            else:
                self.console_manager.add_output("Interior toggle functionality not available.")
        elif command == "off":
            if hasattr(self.renderer, 'show_interiors'):
                self.renderer.show_interiors = False
                self.console_manager.add_output("Building interiors turned OFF.")
            else:
                self.console_manager.add_output("Interior toggle functionality not available.")
        elif command == "toggle":
            if hasattr(self.renderer, 'show_interiors'):
                self.renderer.show_interiors = not self.renderer.show_interiors
                new_state = self.renderer.show_interiors
                self.console_manager.add_output(f"Building interiors {'shown' if new_state else 'hidden'}.")
            else:
                self.console_manager.add_output("Interior toggle functionality not available.")
        else:
            self.console_manager.add_output(f"Unknown option: '{command}'")
            self.console_manager.add_output("Use 'interiors on', 'interiors off', or 'interiors toggle'.")
    def _cmd_interiors(self, args, game_state):
        """Toggle building interiors visibility"""
        if not args:
            current_state = getattr(self.renderer, 'show_interiors', False)
            self.console_manager.add_output(f"Building interiors are currently {'visible' if current_state else 'hidden'}.")
            self.console_manager.add_output("Use 'interiors on' or 'interiors off' to change.")
            return
    
        command = args[0].lower()
    
        if command == "on":
            if hasattr(self.renderer, 'toggle_interiors'):
                if not getattr(self.renderer, 'show_interiors', False):
                    self.renderer.toggle_interiors()
                self.console_manager.add_output("Building interiors turned ON.")
            else:
                self.console_manager.add_output("Interior toggle functionality not available.")
        elif command == "off":
            if hasattr(self.renderer, 'toggle_interiors'):
                if getattr(self.renderer, 'show_interiors', True):
                    self.renderer.toggle_interiors()
                self.console_manager.add_output("Building interiors turned OFF.")
            else:
                self.console_manager.add_output("Interior toggle functionality not available.")
        elif command == "toggle":
            if hasattr(self.renderer, 'toggle_interiors'):
                new_state = self.renderer.toggle_interiors()
                self.console_manager.add_output(f"Building interiors {'shown' if new_state else 'hidden'}.")
            else:
                self.console_manager.add_output("Interior toggle functionality not available.")
        else:
            self.console_manager.add_output(f"Unknown option: '{command}'")
        self.console_manager.add_output("Use 'interiors on', 'interiors off', or 'interiors toggle'.")
            
def modified_handle_click(self, pos):
    """Handle mouse click with Interface integration."""
    # Don't handle clicks if console is active
    if self.console_manager.is_active():
        return
        
    # Store previously selected villager and building
    old_selected_villager = self.selected_villager
    old_selected_building = self.housing_ui.selected_building if hasattr(self.housing_ui, 'selected_building') else None
        
    # Convert screen position to world position
    world_x = pos[0] + self.camera_x
    world_y = pos[1] + self.camera_y
    
    # Check if clicked on a building
    for building_index, building in enumerate(self.village_data['buildings']):
        x, y = building['position']
        size = self.TILE_SIZE * 3 if building['size'] == 'large' else (
            self.TILE_SIZE * 2 if building['size'] == 'medium' else self.TILE_SIZE)
        
        if x <= world_x <= x + size and y <= world_y <= y + size:
            # Add building index
            building['id'] = building_index
            self.housing_ui.set_selected_building(building)
            
            # Notify through Interface
            Interface.on_building_selected(building)
            
            print(f"Clicked on building: {building.get('building_type', 'house')}")
            return
    
    # Reset selected building if clicked elsewhere
    if hasattr(self.housing_ui, 'selected_building') and self.housing_ui.selected_building is not None:
        self.housing_ui.set_selected_building(None)
    
    # Find all villagers at click point
    clicked_villagers = []
    for villager in self.villagers:
        if villager.rect.collidepoint((world_x, world_y)):
            clicked_villagers.append(villager)
    
    # If no villagers were clicked, deselect current villager
    if not clicked_villagers:
        if self.selected_villager:
            # Deselect current villager
            self.selected_villager.is_selected = False
            
            # Notify through Interface
            Interface.on_villager_selected(self.selected_villager, False)
            
            self.selected_villager = None
        return
    
    # If multiple villagers at the same spot
    if len(clicked_villagers) > 1:
        # If we already have a selected villager that's in the clicked list
        if self.selected_villager in clicked_villagers:
            # Get index of current selected villager
            current_index = clicked_villagers.index(self.selected_villager)
            # Select the next villager in the list (cycle through)
            next_index = (current_index + 1) % len(clicked_villagers)
            
            # Deselect current villager
            self.selected_villager.is_selected = False
            
            # Notify through Interface
            Interface.on_villager_selected(self.selected_villager, False)
            
            # Select next villager
            self.selected_villager = clicked_villagers[next_index]
            self.selected_villager.is_selected = True
            
            # Notify through Interface
            Interface.on_villager_selected(self.selected_villager, True)
            
            print(f"Selected villager: {self.selected_villager.name}")
        else:
            # If no current selection among these villagers, select the first one
            if self.selected_villager:
                self.selected_villager.is_selected = False
                
                # Notify through Interface
                Interface.on_villager_selected(self.selected_villager, False)
            
            self.selected_villager = clicked_villagers[0]
            self.selected_villager.is_selected = True
            
            # Notify through Interface
            Interface.on_villager_selected(self.selected_villager, True)
            
            print(f"Selected villager: {self.selected_villager.name}")
    else:
        # Just one villager clicked - normal selection
        if self.selected_villager:
            self.selected_villager.is_selected = False
            
            # Notify through Interface
            Interface.on_villager_selected(self.selected_villager, False)
        
        self.selected_villager = clicked_villagers[0]
        self.selected_villager.is_selected = True
        
        # Notify through Interface
        Interface.on_villager_selected(self.selected_villager, True)
        
        print(f"Selected villager: {self.selected_villager.name}")


# --- MODIFY VillageGame.update ---

def modified_update(self):
    """Update game state with Interface integration."""
    # Get current time and delta time
    current_time = pygame.time.get_ticks()
    dt = self.clock.get_time()  # ms since last frame
    
    # Update Interface time callbacks
    Interface.update(current_time, dt)
    
    # Apply time scaling
    scaled_dt = dt * self.time_scale
    
    # Update console even when paused
    self.console_manager.update(dt)
    
    # Update time manager (always update, even when paused, unless in console)
    if not self.paused:
        # Store old time data for change detection
        old_hour = self.time_manager.current_hour
        old_time_name = self.time_manager.get_time_name()
        
        # Update time
        self.time_manager.update(dt, self.time_scale)
        
        # Check if hour changed significantly or time period changed
        new_hour = self.time_manager.current_hour
        new_time_name = self.time_manager.get_time_name()
        
        # Notify of time change if the hour changed by at least 0.25 or the time period changed
        if abs(new_hour - old_hour) >= 0.25 or new_time_name != old_time_name:
            Interface.on_time_changed(new_hour, new_time_name)
    
    # Don't update the rest if paused and not in console
    if self.paused and not self.console_manager.is_active():
        return
    
    # Update villagers with tracking of activity changes
    for villager in self.villagers:
        try:
            # Store old state for change detection
            old_position = (villager.position.x, villager.position.y)
            old_activity = villager.current_activity if hasattr(villager, 'current_activity') else None
            old_sleep_state = villager.is_sleeping if hasattr(villager, 'is_sleeping') else False
            
            # Update the villager
            if hasattr(villager, 'enhanced_update'):
                villager.enhanced_update(self.village_data, current_time, self.assets, self.time_manager)
            else:
                villager.update(self.village_data, current_time, self.assets)
            
            # Check for state changes to notify Interface
            
            # Position change
            new_position = (villager.position.x, villager.position.y)
            if old_position != new_position:
                # Notify significant movements (more than 1 pixel)
                if ((new_position[0] - old_position[0])**2 + 
                    (new_position[1] - old_position[1])**2) > 1:
                    Interface.on_villager_moved(villager, old_position, new_position)
            
            # Activity change
            new_activity = villager.current_activity if hasattr(villager, 'current_activity') else None
            if old_activity != new_activity and old_activity is not None and new_activity is not None:
                Interface.on_villager_activity_changed(villager, old_activity, new_activity)
            
            # Sleep state change
            new_sleep_state = villager.is_sleeping if hasattr(villager, 'is_sleeping') else False
            if old_sleep_state != new_sleep_state:
                Interface.on_villager_sleep_state_changed(villager, new_sleep_state)
                
        except Exception as e:
            print(f"Error updating villager {villager.name}: {e}")
    
    # Update animations and other game elements
    # ... existing animation update code ...
    
    # Check for villager interactions (conversations)
    self.check_villager_interactions_with_interface()


# --- ADD NEW METHODS to VillageGame ---

def check_villager_interactions_with_interface(self):
    """Check for interactions between villagers and notify Interface."""
    # Find villagers that are close to each other
    for v1 in self.villagers:
        for v2 in self.villagers:
            if v1 != v2:  # Don't compare a villager with itself
                # Calculate distance between villagers
                distance = math.sqrt((v1.position.x - v2.position.x)**2 + 
                                    (v1.position.y - v2.position.y)**2)
                
                # If villagers are close and both are talking, they might be conversing
                if distance < self.INTERACTION_RADIUS and v1.is_talking and v2.is_talking:
                    # There's a small chance they'll start a conversation
                    if random.random() < 0.01:  # 1% chance per frame
                        # Notify through Interface
                        Interface.on_villager_interaction(v1, v2, "conversation")
                        
                        # Play conversation sound if not already playing
                        if not pygame.mixer.get_busy():
                            try:
                                v1.conversation_sound.play()
                            except Exception as e:
                                print(f"Error playing conversation sound: {e}")


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
    Interface.setup_default_callbacks(enable_debug=False)
    # Print instructions
    print("Village Simulation with Console")
    print("Controls:")
    print("  WASD/Arrows: Move camera")
    print("  Mouse click: Select villager or building")
    print("  P: Pause/resume game")
    print("  D: Toggle debug info")
    print("  V: Toggle path visualization")
    print("  T: Advance time by 1 hour (test key)")
    print("  I: Toggle building interiors")
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
    print("  interiors <on|off|toggle> - Control building interior visibility")
    
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