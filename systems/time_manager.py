import pygame
import math

class TimeManager:
    """Manages game time, day/night cycle, and lighting effects."""
    
    def __init__(self, day_length_seconds=300):
        """Initialize the time manager.
        
        Args:
            day_length_seconds: Length of a full day-night cycle in real seconds
        """
        # Time settings
        self.day_length_seconds = day_length_seconds  # 5 minutes for a full day by default
        self.start_time = pygame.time.get_ticks()
        
        # Current time values (0.0 to 24.0)
        self.current_hour = 6.0 # Start at 6 am
        self.old_hour = 6.0

        # Time names
        self.time_names = {
            (5, 7): "Dawn",
            (7, 11): "Morning",
            (11, 13): "Noon",
            (13, 17): "Afternoon",
            (17, 19): "Evening",
            (19, 21): "Dusk",
            (21, 5): "Night"
        }
        
        # Light settings
        self.max_darkness = 150  # Maximum darkness overlay alpha (0-255)
    
    def update(self, dt, time_scale=1.0):
        """Update the time of day.
        
        Args:
            dt: Delta time in milliseconds
            time_scale: Time scale multiplier
        """        
        old_time_name = self.get_time_name()
        
        # Calculate seconds per game hour
        seconds_per_hour = self.day_length_seconds / 24
        
        # Convert dt to seconds and apply time scale
        dt_seconds = dt / 1000 * time_scale
        
        # Update current hour
        hour_change = dt_seconds / seconds_per_hour
        self.current_hour = (self.current_hour + hour_change) % 24.0
        
        # Debug time progress for significant changes (at least 15 minutes)
        if abs(self.current_hour - self.old_hour) > 0.25 or self.get_time_name() != old_time_name:
            # Format time strings
            old_time_str = f"{int(self.old_hour)}:{int((self.old_hour % 1) * 60):02d}"
            new_time_str = f"{int(self.current_hour)}:{int((self.current_hour % 1) * 60):02d}"
            #print(f"Time advanced from {old_time_str} ({old_time_name}) to {new_time_str} ({self.get_time_name()})")
            #print(f"Time change: {hour_change:.4f} hours, Speed: {time_scale}x")
            
            # Print wake/sleep info for selected villager if any
            for villager in [v for v in globals().get('game_state', {}).get('villagers', []) if hasattr(v, 'is_selected') and v.is_selected]:
                print(f"Selected villager {villager.name}: Wake at {villager.wake_hour:.2f}, Sleep at {villager.sleep_hour:.2f}")
                print(f"Current sleep state: {'Sleeping' if villager.is_sleeping else 'Awake'}")
    
    def set_time(self, hour):
        """Set the current time to a specific hour.
        
        Args:
            hour: Hour to set (0-24)
        """
        if 0 <= hour <= 24:
            self.current_hour = hour
    
    def get_time_name(self):
        """Get the current time of day name (Morning, Noon, etc.)."""
        hour = self.current_hour
        
        # Special case for night which crosses midnight
        if self.time_names[(21, 5)]:
            if hour >= 21 or hour < 5:
                return self.time_names[(21, 5)]
        
        # Check other time ranges
        for (start, end), name in self.time_names.items():
            if start <= hour < end:
                return name
        
        return "Day"  # Fallback
    
    def get_time_string(self):
        """Get a formatted time string (HH:MM)."""
        hours = int(self.current_hour)
        minutes = int((self.current_hour % 1) * 60)
        
        am_pm = "AM" if hours < 12 else "PM"
        display_hour = hours % 12
        if display_hour == 0:
            display_hour = 12
            
        return f"{display_hour}:{minutes:02d} {am_pm} ({self.get_time_name()})"
    

    def get_light_level(self):
        """Get the current light level (0.0 to 1.0) using a smoother curve."""
        hour = self.current_hour
        
        # Use a continuous function instead of multiple if-else blocks
        if 5 <= hour < 21:  # Daytime hours - use a cosine curve
            # Scale from 5am to 9pm (16 hour period)
            phase = (hour - 5) / 16
            # Cosine curve peaks at noon (0.5 phase)
            return 0.5 + 0.5 * math.cos(math.pi * (phase - 0.5))
        else:  # Night hours
            # Base night level is 0.1
            if hour < 5:  # Late night to early morning
                # Gradual increase from 0.1 at midnight to 0.3 at 5am
                return 0.1 + 0.2 * (hour / 5)
            else:  # Evening to midnight
                # Gradual decrease from 0.3 at 9pm to 0.1 at midnight
                return 0.3 - 0.2 * ((hour - 21) / 3)

    def get_darkness_overlay(self, screen_width, screen_height):
        """Get a darkness overlay surface for the current time.
        
        Args:
            screen_width: Width of the screen
            screen_height: Height of the screen
            
        Returns:
            A semi-transparent surface to overlay on the screen
        """
        # Create a surface for the darkness overlay
        darkness = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
        # Get light level and determine overlay opacity
        light_level = self.get_light_level()
        alpha = int((1.0 - light_level) * self.max_darkness)
        
        # At night (after 8 PM or before 5 AM), use a dark blue tint
        # At dawn/dusk, use a orange/reddish tint
        if 19 <= self.current_hour or self.current_hour < 5:
            # Night - dark blue
            color = (20, 20, 50, alpha)
        elif 5 <= self.current_hour < 7:
            # Dawn - orange to blue
            dawn_progress = (self.current_hour - 5) / 2  # 0 to 1
            r = int(50 + (1 - dawn_progress) * 30)
            g = int(20 + (1 - dawn_progress) * 10)
            b = int(50 + dawn_progress * 10)
            color = (r, g, b, alpha)
        elif 17 <= self.current_hour < 19:
            # Dusk - orange/red
            dusk_progress = (self.current_hour - 17) / 2  # 0 to 1
            r = int(50 + dusk_progress * 30)
            g = int(20 + dusk_progress * 10)
            b = int(50 - dusk_progress * 10)
            color = (r, g, b, alpha)
        else:
            # Daytime - slight yellow tint
            color = (20, 20, 10, alpha)
        
        # Fill the surface with the calculated color
        darkness.fill(color)
        
        return darkness
    
    def get_shadow_length(self):
        """Get the current shadow length multiplier based on sun position.
        
        Returns:
            A multiplier for shadow length (0.0 to 2.0)
        """
        # Calculate shadow length based on sun position
        # Noon = shortest shadows, Dawn/Dusk = longest shadows
        hour = self.current_hour
        
        # No shadows at night
        if hour < 5 or hour >= 19:
            return 0.0
            
        # Morning and afternoon
        if 5 <= hour < 12:
            # Morning: Shadows shorten toward noon
            return 2.0 - 1.8 * ((hour - 5) / 7)
        elif 12 <= hour < 19:
            # Afternoon: Shadows lengthen toward evening
            return 0.2 + 1.8 * ((hour - 12) / 7)
            
        return 0.2  # Minimum shadow length at noon
