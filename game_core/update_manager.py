"""
Update Manager - Handles game state updates
"""
import pygame
import math
import random
from ui import Interface

class UpdateManager:
    """Manages game state updates and time management."""
    
    def __init__(self, game_state):
        """Initialize the update manager.
        
        Args:
            game_state: Reference to the main game state
        """
        self.game_state = game_state
    
    def update(self):
        """Update game state with Interface integration."""
        # Get current time and delta time
        current_time = pygame.time.get_ticks()
        dt = self.game_state.clock.get_time()  # ms since last frame
        
        # Update Interface time callbacks
        Interface.update(current_time, dt)
        
        # Apply time scaling
        scaled_dt = dt * self.game_state.time_scale
        
        # Update console even when paused
        self.game_state.console_manager.update(dt)
        
        # Update time manager (always update, even when paused, unless in console)
        if not self.game_state.paused:
            # Store old time data for change detection
            old_hour = self.game_state.time_manager.current_hour
            old_time_name = self.game_state.time_manager.get_time_name()
            
            # Update time
            self.game_state.time_manager.update(dt, self.game_state.time_scale)
            
            # Check if hour changed significantly or time period changed
            new_hour = self.game_state.time_manager.current_hour
            new_time_name = self.game_state.time_manager.get_time_name()
            
            # Notify of time change if the hour changed by at least 0.25 or the time period changed
            if abs(new_hour - old_hour) >= 0.25 or new_time_name != old_time_name:
                Interface.on_time_changed(new_hour, new_time_name)
                
                # Also update time system if available
                if hasattr(self.game_state, 'time_system'):
                    self.game_state.time_system.update(current_time, dt)
        
        # Don't update the rest if paused and not in console
        if self.game_state.paused and not self.game_state.console_manager.is_active():
            return
        
        # Update villagers with tracking of activity changes
        self._update_villagers(current_time)
        
        # Update animations
        self._update_animations()
        
        # Update interaction system if available
        if hasattr(self.game_state, 'interaction_system'):
            self.game_state.interaction_system.update(current_time)
    
    def _update_villagers(self, current_time):
        """Update all villagers with state change tracking.
        
        Args:
            current_time: Current game time in milliseconds
        """
        for villager in self.game_state.villagers:
            try:
                # Store old state for change detection
                old_position = (villager.position.x, villager.position.y)
                old_activity = villager.current_activity if hasattr(villager, 'current_activity') else None
                old_sleep_state = villager.is_sleeping if hasattr(villager, 'is_sleeping') else False
                
                # Update the villager
                villager.update(self.game_state.village_data, current_time, self.game_state.assets,self.game_state.time_manager)
                
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
    
    def _update_animations(self):
        """Update animation frames and timers."""
        self.game_state.animation_timer += 1
        if self.game_state.animation_timer >= 15:  # Change water frame every 15 frames (4 FPS)
            self.game_state.animation_timer = 0
            if self.game_state.assets['environment']['water']:  # Check if we have water frames
                self.game_state.water_frame = (self.game_state.water_frame + 1) % len(self.game_state.assets['environment']['water'])
                
                # Update water animation frames
                for water_tile in self.game_state.village_data['water']:
                    water_tile['frame'] = self.game_state.water_frame