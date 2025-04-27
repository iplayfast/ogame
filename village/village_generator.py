"""
Village generation and utility functions.

This module provides functions to generate villages and handle village-related
operations including grid initialization for pathfinding.
"""

import random
import math
from village.village_base import Village

def generate_village(size, assets, tile_size=32, config=None):
    """
    Legacy compatibility wrapper for creating a village.
    
    Args:
        size: Base size parameter (will be scaled up)
        assets: Dictionary of game assets
        tile_size: Size of each tile in pixels
        config: Configuration dictionary
        
    Returns:
        Dictionary containing complete village data
    """
    # Create a new Village instance
    village = Village(size, assets, tile_size)
    
    # Store config for later use by building generator
    if config:
        village.config = config
    
    # Return the village data for compatibility with existing code
    return village.village_data

def initialize_village_grid(village_data, tile_size):
    """Initialize a grid representation of the village for pathfinding.
    
    This creates a 2D grid where each cell contains information about what's at
    that location (terrain, water, buildings, etc.) and whether it's passable.
    
    Args:
        village_data: Dictionary containing village data
        tile_size: Size of a tile in pixels
        
    Returns:
        None (modifies village_data in place)
    """
    # Calculate grid size using width and height instead of single size value
    grid_width = village_data['width'] // tile_size
    grid_height = village_data['height'] // tile_size
    
    # Initialize grid with empty cells (all passable by default)
    grid = [[{'type': 'empty', 'passable': True, 'preferred': False} 
             for _ in range(grid_width)] for _ in range(grid_height)]
    
    # Add terrain (grass types)
    for pos, terrain in village_data.get('terrain', {}).items():
        x, y = pos
        grid_x, grid_y = x // tile_size, y // tile_size
        
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
            grid[grid_y][grid_x] = {
                'type': 'terrain',
                'terrain_type': terrain['type'],
                'variant': terrain.get('variant', 1),
                'passable': True,
                'preferred': False
            }
    
    # Add water (impassable)
    for water in village_data.get('water', []):
        x, y = water['position']
        grid_x, grid_y = x // tile_size, y // tile_size
        
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
            grid[grid_y][grid_x] = {
                'type': 'water',
                'passable': False,
                'preferred': False
            }
    
    # Continue with the rest of the terrain initialization...
    # (bridges, paths, buildings)
    
    # Store the grid in village_data
    village_data['village_grid'] = grid
    print(f"Village grid initialized: {grid_width}x{grid_height}")
    
    # Create a utility method for grid access
    def get_cell_at(x, y):
        """Get the grid cell at the given pixel coordinates."""
        grid_x = int(x // tile_size)
        grid_y = int(y // tile_size)
        
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
            return grid[grid_y][grid_x]
        return None
    
    # Add the accessor function to village_data
    village_data['get_cell_at'] = get_cell_at
    
    # Initialize path cache for efficient pathfinding
    if 'path_cache' not in village_data:
        village_data['path_cache'] = {}