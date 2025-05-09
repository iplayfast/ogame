#!/usr/bin/env python
"""
Village Simulation - Main Entry Point

This is the main entry point for the village simulation game.
Modified to support configuration settings from config.json.
"""

import sys

# Apply compatibility patch to utils module
import utils.compatibility

# Then import pygame and other modules
import pygame
import random
import math
import entities
from pygame.locals import *

# Import Interface from ui directory
from ui.Interface import setup_default_callbacks

# Import game state and managers
from game_core.game_state import VillageGame

# Import Villager for patching
from entities.villager import Villager

# Import configuration manager from utils directory
from utils import config_manager

# Define the missing _ensure_bounds method for Villager class
def _ensure_bounds_patch(self, village_data):
    """Helper method to keep villager within village bounds."""
    padding = self.TILE_SIZE // 4  # Small padding
    village_w = village_data.get('width', 500)
    village_h = village_data.get('height', 500)

    if village_w <= 0 or village_h <= 0:
        return  # Cannot apply bounds

    # Clamp position using max/min
    self.position.x = max(padding, min(self.position.x, village_w - padding))  # Clamp X
    self.position.y = max(padding, min(self.position.y, village_h - padding))  # Clamp Y

    # Update rect center after clamping position
    if hasattr(self, 'rect') and self.rect:  # Check if rect exists
        current_center = (int(self.position.x), int(self.position.y))
        if self.rect.center != current_center:
            self.rect.center = current_center
    elif hasattr(self, 'image') and self.image:  # If rect is None but image exists, create rect
        print(f"Warning: Creating missing rect in _ensure_bounds for {self.name}")
        self.rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))

# Add method to handle activity movement if missing
def handle_activity_movement_patch(self, village_data, dt_ms, current_hour):
    """Handle movement based on current activity."""
    # This is a simplified version that at least prevents errors
    if not hasattr(self, 'destination') or self.destination is None:
        if hasattr(self, 'wandering_tendency') and random.random() < self.wandering_tendency:
            if hasattr(self, 'find_new_destination'):
                self.find_new_destination(village_data)
    
    if hasattr(self, 'destination') and self.destination and hasattr(self, 'path') and self.path:
        if hasattr(self, 'handle_path_movement'):
            self.handle_path_movement(dt_ms)

def apply_villager_patches():
    """Apply necessary patches to Villager class."""
    print("Checking for missing Villager methods...")
    
    # Add _ensure_bounds method if missing
    if not hasattr(Villager, '_ensure_bounds') or not callable(getattr(Villager, '_ensure_bounds')):
        print("Adding missing _ensure_bounds method to Villager class")
        setattr(Villager, '_ensure_bounds', _ensure_bounds_patch)
    
    # Add handle_activity_movement method if missing
    if not hasattr(Villager, 'handle_activity_movement') or not callable(getattr(Villager, 'handle_activity_movement')):
        print("Adding missing handle_activity_movement method to Villager class")
        setattr(Villager, 'handle_activity_movement', handle_activity_movement_patch)
    
    print("Villager patches applied successfully!")

def main():
    """
    Main entry point for the village simulation game.
    """
    # Load configuration
    config = config_manager.get_config()
    
    # Initialize pygame
    pygame.init()
    pygame.mixer.init()
    
    # Apply patches to Villager class
    apply_villager_patches()
    
    # Create the game instance
    game = VillageGame()
    
    # Apply configuration to game state
    config_manager.apply_config_to_game(game)
    
    # Initialize Interface
    setup_default_callbacks(enable_debug=config["system"].get("debug_mode", False))
    # Assign housing to villagers
    game.housing_manager.assign_housing()
    
    # IMPORTANT: Force all villagers to start in their homes
    game.housing_manager.force_villagers_to_homes()
    # Print instructions
    print("Village Simulation")
    print(f"Configuration: {game.num_villagers} villagers, {config['buildings']['size_multiplier']}x building size")
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
    print("  houses - List all houses and their residents")
    print("  assign <new|reload> - Manage housing assignments")
    print("  interiors <on|off|toggle> - Control building interior visibility")
    print("  wake <name|all> - Wake up specific villager or all villagers")
    print("  sleep <name|all> - Force specific villager or all villagers to sleep")
    print("  F: Toggle fullscreen mode")
    print("  fix <sleepers|homes|all> - Fix various game issues")
    print("  config - View or modify configuration settings")
    
    # Add config command to console if available
    if hasattr(game, 'console_manager') and hasattr(game.console_manager, 'commands'):
        game.console_manager.commands['config'] = config_command
    
    # Main game loop
    while game.running:
        # Handle events
        game.handle_events()
        
        # Process input
        game.handle_input()
        
        # Update game state
        game.update()

        try:
            # Render
            game.render()
        except pygame.error as e:
            if "display Surface quit" in str(e):
                print("Warning: Display surface quit during rendering - attempting recovery")
                # Let the next frame try again with the new surface
                pygame.time.delay(100)  # Short delay
            else:
                raise  # Re-raise other pygame errors
        
        # Cap the frame rate
        game.clock.tick(game.fps)
    
    # Clean up
    pygame.quit()
    sys.exit()

def config_command(args, game_state):
    """Console command to view and modify configuration settings.
    
    Args:
        args: Command arguments
        game_state: Game state object
    """
    config = config_manager.get_config()
    
    if not args:
        # Display current configuration
        game_state.console_manager.add_output("Current configuration:")
        for section in config:
            if section == "system" and not config["system"].get("debug_mode", False):
                continue  # Hide system section in non-debug mode
            
            game_state.console_manager.add_output(f"[{section}]")
            for key, value in config[section].items():
                if key != "comments":
                    game_state.console_manager.add_output(f"  {key}: {value}")
        
        game_state.console_manager.add_output("")
        game_state.console_manager.add_output("Usage: config <section> <key> <value>")
        game_state.console_manager.add_output("Example: config buildings size_multiplier 2.0")
        return True
    
    # Handle subcommands
    if args[0] == "save":
        # Save current config
        if config_manager.save_config():
            game_state.console_manager.add_output("Configuration saved to config.json")
        else:
            game_state.console_manager.add_output("Failed to save configuration")
        return True
    
    if args[0] == "reload":
        # Reload config from file
        config_manager._config = config_manager.load_config()
        config_manager.apply_config_to_game(game_state)
        game_state.console_manager.add_output("Configuration reloaded and applied")
        return True
    
    # Update a specific setting
    if len(args) >= 3:
        section = args[0]
        key = args[1]
        value_str = args[2]
        
        # Convert value to appropriate type
        try:
            # Try parsing as number
            if "." in value_str:
                value = float(value_str)
            else:
                value = int(value_str)
        except ValueError:
            # Handle boolean values
            if value_str.lower() in ("true", "yes", "on"):
                value = True
            elif value_str.lower() in ("false", "no", "off"):
                value = False
            else:
                # Keep as string
                value = value_str
        
        # Update config
        if config_manager.update_config(section, key, value):
            game_state.console_manager.add_output(f"Updated {section}.{key} to {value}")
            
            # Apply changes
            if section == "buildings" and key == "size_multiplier":
                config_manager.apply_building_size_multiplier(game_state, value)
                game_state.console_manager.add_output("Building size multiplier applied")
            
            return True
        else:
            game_state.console_manager.add_output(f"Failed to update {section}.{key}")
            return False
    
    # Invalid command format
    game_state.console_manager.add_output("Usage: config <section> <key> <value>")
    game_state.console_manager.add_output("Example: config buildings size_multiplier 2.0")
    return False

if __name__ == "__main__":
    main()