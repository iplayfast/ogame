"""
Time System - Extended time management functionality
"""
from ui import Interface

class TimeSystem:
    """Extended time management functionality."""
    
    def __init__(self, game_state):
        """Initialize the time system.
        
        Args:
            game_state: Reference to the main game state
        """
        self.game_state = game_state
        self.last_time_period = None
    
    def update(self, current_time, delta_time):
        """Update time-related events.
        
        Args:
            current_time: Current time in milliseconds
            delta_time: Time elapsed since last update in milliseconds
        """
        # Skip if time manager is not available
        if not hasattr(self.game_state, 'time_manager'):
            return
            
        # Get current time period
        current_hour = self.game_state.time_manager.current_hour
        current_period = self.game_state.time_manager.get_time_name()
        
        # Check for time period changes
        if self.last_time_period is not None and current_period != self.last_time_period:
            # Time period has changed
            Interface.on_environment_changed(current_period, self.last_time_period, current_hour)
            
            # Perform time period change actions
            self._handle_time_period_change(current_period, self.last_time_period, current_hour)
        
        # Update last time period
        self.last_time_period = current_period
    
    def _handle_time_period_change(self, new_period, old_period, hour):
        """Handle time period changes.
        
        Args:
            new_period: New time period name
            old_period: Previous time period name
            hour: Current hour (0-24)
        """
        print(f"Time period changed from {old_period} to {new_period} at {hour:.2f} hours")
        
        # Night to morning transition (sunrise)
        if old_period == "Night" and new_period in ["Dawn", "Morning"]:
            self._handle_sunrise()
        
        # Evening to night transition (sunset)
        elif old_period in ["Evening", "Dusk"] and new_period == "Night":
            self._handle_sunset()
    
    def _handle_sunrise(self):
        """Handle sunrise events."""
        # This could include special events that happen at sunrise
        pass
    
    def _handle_sunset(self):
        """Handle sunset events."""
        # This could include special events that happen at sunset
        pass
    
    def fast_forward(self, hours):
        """Fast forward time by a number of hours.
        
        Args:
            hours: Number of hours to advance time
            
        Returns:
            New hour after fast forward
        """
        if not hasattr(self.game_state, 'time_manager'):
            return None
            
        # Get current hour
        current_hour = self.game_state.time_manager.current_hour
        
        # Calculate new hour
        new_hour = (current_hour + hours) % 24
        
        # Set new time
        self.game_state.time_manager.set_time(new_hour)
        
        # Notify Interface
        Interface.on_time_changed(new_hour, self.game_state.time_manager.get_time_name())
        
        return new_hour
    
    def set_time_of_day(self, time_of_day):
        """Set time to a specific time of day.
        
        Args:
            time_of_day: String time of day ("morning", "noon", "evening", "night")
            
        Returns:
            New hour after setting time
        """
        if not hasattr(self.game_state, 'time_manager'):
            return None
            
        # Map time of day to hour
        time_map = {
            "morning": 8.0,
            "noon": 12.0,
            "afternoon": 15.0,
            "evening": 18.0,
            "night": 22.0,
            "midnight": 0.0,
            "dawn": 6.0,
            "dusk": 20.0
        }
        
        # Default to noon if invalid time provided
        hour = time_map.get(time_of_day.lower(), 12.0)
        
        # Set new time
        self.game_state.time_manager.set_time(hour)
        
        # Notify Interface
        Interface.on_time_changed(hour, self.game_state.time_manager.get_time_name())
        
        return hour