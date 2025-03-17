"""
Input Handler - Processes all user input and events
"""
import pygame
from ui import Interface

class InputHandler:
    """Handles all user input and pygame events."""
    
    def __init__(self, game_state):
        """Initialize the input handler.
        
        Args:
            game_state: Reference to the main game state
        """
        self.game_state = game_state
    
    def handle_events(self):
        """Handle pygame events with Interface integration."""
        old_camera_pos = (self.game_state.camera_x, self.game_state.camera_y)
        
        # Store previous game state
        was_paused = self.game_state.paused
        was_debug_enabled = self.game_state.show_debug
        
        for event in pygame.event.get():
            # First, check if the console should handle this event
            if self.game_state.console_manager.handle_event(event, self.game_state):
                continue
                
            if event.type == pygame.QUIT:
                self.game_state.running = False
                print("Quit event received")
            
            # Key press events
            elif event.type == pygame.KEYDOWN:
                self._handle_key_press(event)
            
            # Mouse click events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_click(event.pos)
                    
                    # Check if click is on the minimap
                    minimap_rect = pygame.Rect(
                        self.game_state.SCREEN_WIDTH - 160, 
                        self.game_state.SCREEN_HEIGHT - 160, 
                        150, 150
                    )  # Approximate minimap position
                    if minimap_rect.collidepoint(event.pos):
                        # Convert minimap click to world position
                        map_x = event.pos[0] - minimap_rect.left
                        map_y = event.pos[1] - minimap_rect.top
                        scale = minimap_rect.width / self.game_state.village_data['size']
                        world_x = int(map_x / scale)
                        world_y = int(map_y / scale)
                        Interface.on_minimap_clicked(event.pos, (world_x, world_y))
            
            # Mouse motion for hover effects
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)
        
        # After all events, check if camera position changed
        new_camera_pos = (self.game_state.camera_x, self.game_state.camera_y)
        if old_camera_pos != new_camera_pos:
            Interface.on_camera_moved(old_camera_pos, new_camera_pos)
    
    def _handle_key_press(self, event):
        """Handle keyboard key press events.
        
        Args:
            event: The pygame key event
        """
        if event.key == pygame.K_ESCAPE:
            self.game_state.running = False
            print("ESC key pressed - quitting")
        elif event.key == pygame.K_p:
            self.game_state.paused = not self.game_state.paused
            print(f"Game {'paused' if self.game_state.paused else 'resumed'}")
            # Notify through Interface
            Interface.on_game_paused(self.game_state.paused)
        elif event.key == pygame.K_d:
            self.game_state.show_debug = not self.game_state.show_debug
            print(f"Debug display {'enabled' if self.game_state.show_debug else 'disabled'}")
            # Notify through Interface
            Interface.on_debug_toggled(self.game_state.show_debug)
        elif event.key == pygame.K_v:
            # Toggle path visualization
            self.game_state.show_paths = not self.game_state.show_paths
            print(f"Path visualization {'enabled' if self.game_state.show_paths else 'disabled'}")
        elif event.key == pygame.K_t:
            # Test key for time adjustment - advance time by 1 hour
            old_hour = self.game_state.time_manager.current_hour
            old_time_name = self.game_state.time_manager.get_time_name()
            
            self.game_state.time_manager.set_time((self.game_state.time_manager.current_hour + 1) % 24)
            print(f"Time advanced to {self.game_state.time_manager.get_time_string()}")
            
            # Notify through Interface
            new_hour = self.game_state.time_manager.current_hour
            new_time_name = self.game_state.time_manager.get_time_name()
            Interface.on_time_changed(new_hour, new_time_name)
        elif event.key == pygame.K_i:
            # Toggle interiors
            if hasattr(self.game_state.renderer, 'toggle_interiors'):
                state = self.game_state.renderer.toggle_interiors()
                print(f"Building interiors {'enabled' if state else 'disabled'}")
                # Notify through Interface
                Interface.on_ui_panel_toggled("building_interiors", state)
    
    def handle_input(self):
        """Handle continuous keyboard input for camera movement."""
        # Skip handling input if console is active
        if self.game_state.console_manager.is_active():
            return
            
        keys = pygame.key.get_pressed()
        
        # Camera movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.game_state.camera_x -= self.game_state.CAMERA_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.game_state.camera_x += self.game_state.CAMERA_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.game_state.camera_y -= self.game_state.CAMERA_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.game_state.camera_y += self.game_state.CAMERA_SPEED
        
        # Ensure camera stays within village bounds
        self.game_state.camera_x = max(0, min(self.game_state.camera_x, 
                                      self.game_state.village_data['size'] - self.game_state.SCREEN_WIDTH))
        self.game_state.camera_y = max(0, min(self.game_state.camera_y, 
                                      self.game_state.village_data['size'] - self.game_state.SCREEN_HEIGHT))
    
    def handle_click(self, pos):
        """Handle mouse click with Interface integration.
        
        Args:
            pos: Mouse position (x, y)
        """
        # Don't handle clicks if console is active
        if self.game_state.console_manager.is_active():
            return
            
        # Store previously selected villager and building
        old_selected_villager = self.game_state.selected_villager
        old_selected_building = self.game_state.housing_ui.selected_building if hasattr(self.game_state.housing_ui, 'selected_building') else None
            
        # Convert screen position to world position
        world_x = pos[0] + self.game_state.camera_x
        world_y = pos[1] + self.game_state.camera_y
        
        # Check if clicked on a building
        self._check_building_click(world_x, world_y)
        
        # If a building wasn't clicked, check if clicked on a villager
        if not self.game_state.housing_ui.selected_building:
            self._check_villager_click(world_x, world_y)
    
    def _check_building_click(self, world_x, world_y):
        """Check if the click is on a building and select it if so.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
        """
        for building_index, building in enumerate(self.game_state.village_data['buildings']):
            x, y = building['position']
            size = self.game_state.TILE_SIZE * 3 if building['size'] == 'large' else (
                   self.game_state.TILE_SIZE * 2 if building['size'] == 'medium' else self.game_state.TILE_SIZE)
            
            if x <= world_x <= x + size and y <= world_y <= y + size:
                # Add building index
                building['id'] = building_index
                self.game_state.housing_ui.set_selected_building(building)
                
                # Notify through Interface
                Interface.on_building_selected(building)
                
                print(f"Clicked on building: {building.get('building_type', 'house')}")
                return True
        
        # Reset selected building if clicked elsewhere
        if hasattr(self.game_state.housing_ui, 'selected_building') and self.game_state.housing_ui.selected_building is not None:
            self.game_state.housing_ui.set_selected_building(None)
        
        return False
    
    def _check_villager_click(self, world_x, world_y):
        """Check if the click is on a villager and select it if so.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
        """
        # Find all villagers at click point
        clicked_villagers = []
        for villager in self.game_state.villagers:
            if villager.rect.collidepoint((world_x, world_y)):
                clicked_villagers.append(villager)
        
        # If no villagers were clicked, deselect current villager
        if not clicked_villagers:
            if self.game_state.selected_villager:
                # Deselect current villager
                self.game_state.selected_villager.is_selected = False
                
                # Notify through Interface
                Interface.on_villager_selected(self.game_state.selected_villager, False)
                
                self.game_state.selected_villager = None
            return False
        
        # If multiple villagers at the same spot
        if len(clicked_villagers) > 1:
            self._handle_multiple_villagers_click(clicked_villagers)
        else:
            # Just one villager clicked - normal selection
            self._select_villager(clicked_villagers[0])
        
        return True
    
    def _handle_multiple_villagers_click(self, clicked_villagers):
        """Handle click when multiple villagers are at the same position.
        
        Args:
            clicked_villagers: List of villagers that were clicked
        """
        # If we already have a selected villager that's in the clicked list
        if self.game_state.selected_villager in clicked_villagers:
            # Get index of current selected villager
            current_index = clicked_villagers.index(self.game_state.selected_villager)
            # Select the next villager in the list (cycle through)
            next_index = (current_index + 1) % len(clicked_villagers)
            
            # Deselect current villager
            self.game_state.selected_villager.is_selected = False
            
            # Notify through Interface
            Interface.on_villager_selected(self.game_state.selected_villager, False)
            
            # Select next villager
            self._select_villager(clicked_villagers[next_index])
        else:
            # If no current selection among these villagers, select the first one
            if self.game_state.selected_villager:
                self.game_state.selected_villager.is_selected = False
                
                # Notify through Interface
                Interface.on_villager_selected(self.game_state.selected_villager, False)
            
            self._select_villager(clicked_villagers[0])
    
    def _select_villager(self, villager):
        """Select a villager and notify Interface.
        
        Args:
            villager: The villager to select
        """
        self.game_state.selected_villager = villager
        self.game_state.selected_villager.is_selected = True
        
        # Notify through Interface
        Interface.on_villager_selected(self.game_state.selected_villager, True)
        
        print(f"Selected villager: {self.game_state.selected_villager.name}")
    
    def handle_mouse_motion(self, pos):
        """Handle mouse motion for hover effects.
        
        Args:
            pos: Mouse position (x, y)
        """
        # Convert screen position to world position
        world_x = pos[0] + self.game_state.camera_x
        world_y = pos[1] + self.game_state.camera_y
        
        # Reset hovered building
        self.game_state.hovered_building = None
        
        # Check if mouse is over a building
        for building in self.game_state.village_data['buildings']:
            x, y = building['position']
            size = self.game_state.TILE_SIZE * 3 if building['size'] == 'large' else (
                   self.game_state.TILE_SIZE * 2 if building['size'] == 'medium' else self.game_state.TILE_SIZE)
            
            if x <= world_x <= x + size and y <= world_y <= y + size:
                self.game_state.hovered_building = building
                break