#!/usr/bin/env python
"""
Village Simulation - Main Entry Point

This is the main entry point for the village simulation game.
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
from ui import Interface

# Import game state and managers
from game_core.game_state import VillageGame

def main():
    """
    Main entry point for the village simulation game.
    """
    # Initialize pygame
    pygame.init()
    pygame.mixer.init()
    
    # Create the game instance
    game = VillageGame()
    
    # Initialize Interface
    Interface.setup_default_callbacks(enable_debug=False)
    
    # Print instructions
    print("Village Simulation")
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
    print("  fix <sleepers|homes|all> - Fix various game issues")
    
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
