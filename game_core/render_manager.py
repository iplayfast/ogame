"""
Render Manager - Handles game rendering
"""
import pygame

class RenderManager:
    """Manages rendering of the game world and UI."""
    
    def __init__(self, game_state):
        """Initialize the render manager.
        
        Args:
            game_state: Reference to the main game state
        """
        self.game_state = game_state
    
    def render(self):
        """Render the game world and UI with frame skipping support."""
        # Check if we're in frame skip mode (for fullscreen toggle)
        if hasattr(self.game_state, 'frame_skip_count') and self.game_state.frame_skip_count > 0:
            self.game_state.frame_skip_count -= 1
            print(f"Skipping render frame during display transition ({self.game_state.frame_skip_count} remaining)")
            
            # If this is the last skipped frame, now update all UI components
            if self.game_state.frame_skip_count == 0:
                print("Resuming rendering - updating UI components")
                # Update all component screen references
                if hasattr(self.game_state, 'renderer'):
                    self.game_state.renderer.screen = self.game_state.screen
                    self.game_state.renderer.screen_width = self.game_state.SCREEN_WIDTH
                    self.game_state.renderer.screen_height = self.game_state.SCREEN_HEIGHT
                
                if hasattr(self.game_state, 'ui_manager'):
                    self.game_state.ui_manager.screen = self.game_state.screen
                    self.game_state.ui_manager.screen_width = self.game_state.SCREEN_WIDTH
                    self.game_state.ui_manager.screen_height = self.game_state.SCREEN_HEIGHT
                
                if hasattr(self.game_state, 'console_manager'):
                    self.game_state.console_manager.screen = self.game_state.screen
                
                if hasattr(self.game_state, 'housing_ui'):
                    self.game_state.housing_ui.screen = self.game_state.screen
                    self.game_state.housing_ui.screen_width = self.game_state.SCREEN_WIDTH
                    self.game_state.housing_ui.screen_height = self.game_state.SCREEN_HEIGHT
                
                # Update UI for new size
                self.game_state.input_handler.update_ui_for_resize()
                self.game_state.input_handler._adjust_camera_after_resize()
                
                # Clear event queue again
                pygame.event.clear()
            
            # During skipped frames, just draw a simple color fill to refresh the screen
            try:
                self.game_state.screen.fill((0, 0, 0))  # Black screen during transition
                pygame.display.flip()  # Update display
            except Exception as e:
                print(f"Error during transition frame: {e}")
            
            return  # Skip the rest of rendering
            
        # Call the main rendering code
        self.game_state.renderer.render_village(
            self.game_state.village_data,
            self.game_state.villagers,
            self.game_state.camera_x,
            self.game_state.camera_y,
            self.game_state.ui_manager,
            self.game_state.selected_villager,
            self.game_state.hovered_building,
            self.game_state.show_debug,
            self.game_state.clock,
            self.game_state.water_frame,
            self.game_state.console_manager.is_active(),
            self.game_state.console_manager.console_height,
            self.game_state.time_manager
        )
        
        # Render villager paths if enabled
        self._render_villager_paths()
        
        # Render building information for selected buildings
        self._render_building_info()
        
        # Render villager housing info if a villager is selected
        self._render_villager_info()
        
        # Render building names
        self._render_building_names()
        
        # Render sleep indicators
        self._render_sleep_indicators()
        
        # Draw console if active
        self.game_state.console_manager.draw()
        
        # Update display
        pygame.display.flip()
    
    def _render_villager_paths(self):
        """Render paths for villagers if path display is enabled."""
        if self.game_state.show_paths:
            for villager in self.game_state.villagers:
                if hasattr(villager, 'draw_path'):
                    villager.draw_path(
                        self.game_state.screen, 
                        self.game_state.camera_x, 
                        self.game_state.camera_y
                    )
    
    def _render_building_info(self):
        """Render building information for selected buildings."""
        if self.game_state.housing_ui.selected_building:
            self.game_state.housing_ui.draw_enhanced_building_info(
                self.game_state.housing_ui.selected_building, 
                self.game_state.villagers, 
                self.game_state.camera_x, 
                self.game_state.camera_y
            )
    
    def _render_villager_info(self):
        """Render information for selected villagers."""
        if self.game_state.selected_villager:
            # Draw housing information
            self.game_state.housing_ui.draw_villager_housing_info(
                self.game_state.selected_villager,
                self.game_state.camera_x,
                self.game_state.camera_y
            )
            
            # Draw daily activities
            self.game_state.housing_ui.draw_daily_activities(self.game_state.selected_villager)
            
            # Draw multiple villagers indicator
            self.game_state.ui_manager.draw_multiple_villagers_indicator(
                self.game_state.selected_villager,
                self.game_state.villagers,
                self.game_state.camera_x,
                self.game_state.camera_y
            )
    
    def _render_building_names(self):
        """Render names above buildings."""
        for building in self.game_state.village_data['buildings']:
            if 'name' in building:
                self.game_state.housing_ui.draw_building_name(
                    building, 
                    self.game_state.camera_x, 
                    self.game_state.camera_y
                )
    
    def _render_sleep_indicators(self):
        """Render sleep indicators for sleeping villagers."""
        for villager in self.game_state.villagers:
            if hasattr(villager, 'is_sleeping') and villager.is_sleeping and hasattr(villager, 'draw_sleep_indicator'):
                villager.draw_sleep_indicator(
                    self.game_state.screen, 
                    self.game_state.camera_x, 
                    self.game_state.camera_y
                )