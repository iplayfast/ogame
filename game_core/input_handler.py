"""
Input Handler - Processes all user input and events
"""
import traceback
import sys
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
        # Skip standard event handling if in resize mode - it's handled in update
        if self.game_state.resize_mode:
            return
        
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
            
            # Handle window resize events - this will enter resize mode
            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize_event(event)
                return  # Exit event handling to let resize mode take over
            
            # Handle window exposure (un-minimizing, etc.)
            elif event.type == pygame.VIDEOEXPOSE:
                print("Window exposed - refreshing display")
                if hasattr(self.game_state, 'render_manager'):
                    self.game_state.render_manager.render()
            
            # Handle delayed UI updates after fullscreen toggle
            elif event.type == pygame.USEREVENT + 1:
                print("Processing delayed UI updates after display mode change")
                self.update_ui_for_resize()
                self._adjust_camera_after_resize()
            
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
            
    
    def _handle_resize_event(self, event):
        """Handle window resize events properly."""
        # Store old screen size for Interface notification
        old_screen_width = self.game_state.SCREEN_WIDTH
        old_screen_height = self.game_state.SCREEN_HEIGHT
        old_screen_size = (old_screen_width, old_screen_height)
        
        # Get new size from the event
        new_width, new_height = event.size
        
        # Enter resize mode if not already in it
        if not self.game_state.resize_mode:
            self.game_state.resize_mode = True
            self.game_state.resize_timer = pygame.time.get_ticks()
            print("Entered resize mode")
        
        # Update screen size
        self.game_state.SCREEN_WIDTH = new_width
        self.game_state.SCREEN_HEIGHT = new_height
        
        # Get updated surface (no need to create a new one)
        self.game_state.screen = pygame.display.get_surface()
        
        # Adjust camera bounds based on new screen size
        self._adjust_camera_after_resize()
        
        # Update UI components for new screen size
        self.update_ui_for_resize()
        
        # Force a render to update display
        if hasattr(self.game_state, 'render_manager'):
            self.game_state.render_manager.render()
        
        # Reset the resize timer
        self.game_state.resize_timer = pygame.time.get_ticks()
        
        # Notify Interface about screen resize 
        if hasattr(Interface, 'on_screen_resized'):
            Interface.on_screen_resized(old_screen_size, (new_width, new_height))
        
        print(f"Window resized to: {new_width}x{new_height}")

    def update_ui_for_resize(self):
        """Update UI components when screen is resized."""
        print("Updating UI components for new screen size...")
        
        # Get the new screen dimensions
        new_width = self.game_state.SCREEN_WIDTH
        new_height = self.game_state.SCREEN_HEIGHT
        
        # Update console dimensions
        if hasattr(self.game_state, 'console_manager'):
            self.game_state.console_manager.console_width = new_width
            self.game_state.console_manager.console_y = new_height - self.game_state.console_manager.console_height
            self.game_state.console_manager.input_width = new_width - 20
            self.game_state.console_manager.input_y = new_height - 40
            self.game_state.console_manager.screen = self.game_state.screen
        
        # Update UI manager components
        if hasattr(self.game_state, 'ui_manager'):
            self.game_state.ui_manager.screen_width = new_width
            self.game_state.ui_manager.screen_height = new_height
            self.game_state.ui_manager.screen = self.game_state.screen
        
        # Update housing UI components
        if hasattr(self.game_state, 'housing_ui'):
            self.game_state.housing_ui.screen_width = new_width
            self.game_state.housing_ui.screen_height = new_height
            self.game_state.housing_ui.screen = self.game_state.screen
        
        # Update renderer viewport
        if hasattr(self.game_state, 'renderer'):
            self.game_state.renderer.screen_width = new_width
            self.game_state.renderer.screen_height = new_height
            self.game_state.renderer.screen = self.game_state.screen
            
            # Call update_viewport if it exists
            if hasattr(self.game_state.renderer, 'update_viewport'):
                self.game_state.renderer.update_viewport(new_width, new_height)
        
        # Update render manager 
        if hasattr(self.game_state, 'render_manager'):
            # Make sure render manager uses the updated screen
            if hasattr(self.game_state.render_manager, 'screen'):
                self.game_state.render_manager.screen = self.game_state.screen
        
        print("UI components updated for new screen size")

    def _handle_key_press(self, event):
        """Handle keyboard key press events.
        
        Args:
            event: The pygame key event
        """
        if event.key == pygame.K_f:
            # Toggle fullscreen mode
            self._toggle_fullscreen()
        elif event.key == pygame.K_ESCAPE:
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

    def _toggle_fullscreen(self):
        """Toggle fullscreen using a more direct approach similar to demofullscreen.py."""
        # Check current fullscreen state
        is_fullscreen = bool(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
        
        try:
            if is_fullscreen:
                # Switch to windowed mode with the last used windowed size
                if hasattr(self.game_state, '_windowed_size'):
                    windowed_width, windowed_height = self.game_state._windowed_size
                else:
                    # Default if no size is stored
                    windowed_width, windowed_height = 1280, 720
                    
                print(f"Switching to windowed mode: {windowed_width}x{windowed_height}")
                self.game_state.screen = pygame.display.set_mode((windowed_width, windowed_height), pygame.RESIZABLE)
                self.game_state.SCREEN_WIDTH = windowed_width
                self.game_state.SCREEN_HEIGHT = windowed_height
            else:
                # Save current windowed size before switching to fullscreen
                self.game_state._windowed_size = (self.game_state.SCREEN_WIDTH, self.game_state.SCREEN_HEIGHT)
                print(f"Saving current windowed size: {self.game_state._windowed_size}")
                
                # Switch to fullscreen
                print("Switching to fullscreen mode")
                self.game_state.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                # Update screen dimensions to match the fullscreen resolution
                self.game_state.SCREEN_WIDTH = self.game_state.screen.get_width()
                self.game_state.SCREEN_HEIGHT = self.game_state.screen.get_height()
            
            # Skip a few frames to let the display change settle
            self.game_state.frame_skip_count = 3
            
            # Update UI components for new screen size - we'll do this after a brief delay
            # Set a timer to do the UI update
            pygame.time.set_timer(pygame.USEREVENT + 1, 100, 1)  # 100ms delay, once
            
            print(f"New screen size: {self.game_state.SCREEN_WIDTH}x{self.game_state.SCREEN_HEIGHT}")
            return True
            
        except Exception as e:
            print(f"ERROR during display toggle: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _add_drawing_safety_wrapper(self):
        """Add a safety wrapper to UI manager's drawing functions to check surface validity."""
        # Specifically target the circle drawing function that's causing issues
        if hasattr(self.game_state, 'ui_manager'):
            ui_manager = self.game_state.ui_manager
            
            # Store original drawing function
            if not hasattr(ui_manager, '_original_draw_building_type_indicator'):
                ui_manager._original_draw_building_type_indicator = ui_manager.draw_building_type_indicator
            
            # Create safer version with surface check
            def safe_draw_building_type_indicator(building, x, y, camera_x, camera_y, tile_size):
                try:
                    # Ensure screen is valid
                    if ui_manager.screen is None or not pygame.display.get_surface():
                        ui_manager.screen = pygame.display.get_surface()
                        if ui_manager.screen is None:
                            print("Skipping building indicator draw - no valid surface")
                            return
                    
                    # Check bit depth - if invalid, update reference
                    if ui_manager.screen.get_bitsize() > 32:  # Invalid bit depth
                        print(f"Invalid bit depth detected: {ui_manager.screen.get_bitsize()}, updating reference")
                        ui_manager.screen = pygame.display.get_surface()
                    
                    # Now call original with validated surface
                    ui_manager._original_draw_building_type_indicator(building, x, y, camera_x, camera_y, tile_size)
                except Exception as e:
                    print(f"Error in building indicator draw: {e}")
            
            # Replace the function
            ui_manager.draw_building_type_indicator = safe_draw_building_type_indicator

    def _patch_render_for_safe_surface(self):
        """Patch the render method to safely handle surface quits during mode change."""
        # Store original render method
        if not hasattr(self.game_state.render_manager, '_original_render'):
            self.game_state.render_manager._original_render = self.game_state.render_manager.render
        
        # Create a safe version that checks for valid surface
        def safe_render():
            try:
                # Check if display is initialized and surface exists
                if pygame.get_init() and pygame.display.get_surface():
                    # Call original render
                    self.game_state.render_manager._original_render()
                else:
                    print("Skipping render - display not initialized")
            except Exception as e:
                print(f"Error in safe_render: {e}")
        
        # Replace the render method
        self.game_state.render_manager.render = safe_render

    def _patch_render_for_surface_check(self):
        """Patch renderer to check surface validity before each rendering operation."""
        # First, fix the main renderer class to check surface validity
        original_render_village = self.game_state.renderer.render_village
        
        def safe_render_village(*args, **kwargs):
            try:
                # Check if surface is valid before using
                if not pygame.display.get_init() or not pygame.display.get_surface():
                    print("Skipping render - display not available")
                    return
                    
                # Extra safety - update screen reference
                self.game_state.renderer.screen = pygame.display.get_surface()
                
                # Now call the original render
                return original_render_village(*args, **kwargs)
            except pygame.error as e:
                if "display Surface quit" in str(e):
                    print("Surface quit detected - skipping render cycle")
                else:
                    print(f"Render error: {e}")
            except Exception as e:
                print(f"Unexpected render error: {e}")
        
        # Replace the render method
        self.game_state.renderer.render_village = safe_render_village

    def _update_screen_references(self, new_screen):
        """Update all screen references throughout the application."""
        # Core components
        if hasattr(self.game_state, 'renderer'):
            self.game_state.renderer.screen = new_screen
        
        if hasattr(self.game_state, 'ui_manager'):
            self.game_state.ui_manager.screen = new_screen
        
        if hasattr(self.game_state, 'console_manager'):
            self.game_state.console_manager.screen = new_screen
        
        if hasattr(self.game_state, 'housing_ui'):
            self.game_state.housing_ui.screen = new_screen

    def _reload_critical_assets(self):
        """Reload any critical assets that might be tied to the screen surface."""
        # This might include UI elements, overlays, etc.
        # For now, focus on the essential renderer components
        
        if hasattr(self.game_state, 'renderer'):
            # Reset any renderer-specific surfaces
            renderer = self.game_state.renderer
            
            # If renderer has overlay surface, recreate it
            if hasattr(renderer, 'overlay_surface'):
                renderer.overlay_surface = pygame.Surface(
                    (self.game_state.SCREEN_WIDTH, self.game_state.SCREEN_HEIGHT), 
                    pygame.SRCALPHA
                )


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
    
    def _adjust_camera_after_resize(self):
        """Adjust camera boundaries after screen resize to ensure view stays centered."""
        # Calculate camera movement to keep the view centered after resize
        # This helps maintain focus on the area being viewed when resizing
        
        # Get village size
        village_size = self.game_state.village_data['size']
        
        # Calculate old center position
        old_center_x = self.game_state.camera_x + self.game_state.SCREEN_WIDTH // 2
        old_center_y = self.game_state.camera_y + self.game_state.SCREEN_HEIGHT // 2
        
        # Calculate new camera position based on old center
        new_camera_x = old_center_x - self.game_state.SCREEN_WIDTH // 2
        new_camera_y = old_center_y - self.game_state.SCREEN_HEIGHT // 2
        
        # Ensure camera stays within village bounds
        new_camera_x = max(0, min(new_camera_x, village_size - self.game_state.SCREEN_WIDTH))
        new_camera_y = max(0, min(new_camera_y, village_size - self.game_state.SCREEN_HEIGHT))
        
        # Apply the new camera position
        self.game_state.camera_x = new_camera_x
        self.game_state.camera_y = new_camera_y
        
        print(f"Camera adjusted to ({new_camera_x}, {new_camera_y}) to maintain view center")

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