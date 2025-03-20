"""
Villager Manager - Handles villager creation and management
"""
import random
import pygame
from entities.villager import Villager
from ui import Interface
class VillagerManager:
    """Manages villager creation and behavior."""
    
    def __init__(self, game_state):
        """Initialize the villager manager.
        
        Args:
            game_state: Reference to the main game state
        """
        self.game_state = game_state
    
    def create_villagers(self, num_villagers):
        """Create villagers with pathfinding capability.
        
        Args:
            num_villagers: Number of villagers to create
        """
        print(f"Creating {num_villagers} villagers...")
        for i in range(num_villagers):
            # Get initial placement position
            x, y = self._get_initial_villager_position()
            
            # Create villager
            villager = Villager(x, y, self.game_state.assets, self.game_state.TILE_SIZE)
            
            # Add to the sprite group
            self.game_state.villagers.add(villager)
            print(f"Created villager {i+1}: {villager.name} ({villager.job})")
        
        print("All villagers created successfully!")
    
    def _get_initial_villager_position(self):
        """Get an initial position for a new villager.
        
        Returns:
            Tuple of (x, y) coordinates
        """
        # Try to place on a path if possible
        if self.game_state.village_data['paths']:
            path = random.choice(self.game_state.village_data['paths'])
            x, y = path['position']
            # Add slight offset
            x += random.randint(-self.game_state.TILE_SIZE//2, self.game_state.TILE_SIZE//2)
            y += random.randint(-self.game_state.TILE_SIZE//2, self.game_state.TILE_SIZE//2)
        else:
            # Otherwise place randomly
            padding = self.game_state.TILE_SIZE * 3
            x = random.randint(padding, self.game_state.village_data['width'] - padding)
            y = random.randint(padding, self.game_state.village_data['height'] - padding)
        
        return x, y
    
    def wake_villager(self, villager_name=None, force_all=False, duration=30000):
        """Force villager(s) to wake up.
        
        Args:
            villager_name: Name of villager to wake (None to wake all)
            force_all: If True, wake all villagers
            duration: Duration of sleep override in milliseconds
            
        Returns:
            Number of villagers woken up
        """
        count = 0
        
        if force_all:
            # Wake up all villagers
            for villager in self.game_state.villagers:
                if villager.is_sleeping:
                    # Use the override method for stable wake state
                    villager.override_sleep_state(
                        force_awake=True, 
                        duration=duration, 
                        village_data=self.game_state.village_data
                    )
                    count += 1
            
            print(f"Wake command executed: {count} villagers instructed to wake up")
            return count
        
        elif villager_name:
            # Try to find villager by name
            for villager in self.game_state.villagers:
                if villager_name.lower() in villager.name.lower():
                    if villager.is_sleeping:
                        # Use the override method
                        villager.override_sleep_state(
                            force_awake=True, 
                            duration=duration, 
                            village_data=self.game_state.village_data
                        )
                        
                        print(f"Wake command executed: {villager.name} instructed to wake up")
                        return 1
                    return 0
        
        return 0
    
    def sleep_villager(self, villager_name=None, force_all=False, duration=30000):
        """Force villager(s) to sleep.
        
        Args:
            villager_name: Name of villager to put to sleep (None to put all to sleep)
            force_all: If True, put all villagers to sleep
            duration: Duration of sleep override in milliseconds
            
        Returns:
            Number of villagers put to sleep
        """
        count = 0
        
        if force_all:
            # Put all villagers to sleep
            for villager in self.game_state.villagers:
                if not villager.is_sleeping:
                    # Use the override method
                    villager.override_sleep_state(
                        force_awake=False, 
                        duration=duration, 
                        village_data=self.game_state.village_data
                    )
                    count += 1
            
            print(f"Sleep command executed: {count} villagers instructed to sleep")
            return count
        
        elif villager_name:
            # Try to find villager by name
            for villager in self.game_state.villagers:
                if villager_name.lower() in villager.name.lower():
                    if not villager.is_sleeping:
                        # Use the override method
                        villager.override_sleep_state(
                            force_awake=False, 
                            duration=duration, 
                            village_data=self.game_state.village_data
                        )
                        
                        print(f"Sleep command executed: {villager.name} instructed to sleep")
                        return 1
                    return 0
        
        return 0
    
    def fix_villager_sleep_states(self):
        """Fix villagers that are sleeping or waking at wrong times.
        
        Returns:
            Number of villagers fixed
        """
        current_hour = self.game_state.time_manager.current_hour
        fixed_count = 0
        
        for villager in self.game_state.villagers:
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
        
        return fixed_count
