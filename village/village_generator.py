"""
Village generation and utility functions.

This module provides functions to generate villages and handle village-related
operations including grid initialization for pathfinding.
"""

import random
import math
from village.village_base import Village

def generate_village(size, assets, tile_size=32):
    """
    Legacy compatibility wrapper for creating a village.
    
    Args:
        size: Base size parameter (will be scaled up)
        assets: Dictionary of game assets
        tile_size: Size of each tile in pixels
        
    Returns:
        Dictionary containing complete village data
    """
    # Create a new Village instance
    village = Village(size, assets, tile_size)
    
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
    # Calculate grid size
    grid_size = village_data['size'] // tile_size
    
    # Initialize grid with empty cells (all passable by default)
    grid = [[{'type': 'empty', 'passable': True, 'preferred': False} 
             for _ in range(grid_size)] for _ in range(grid_size)]
    
    # Add terrain (grass types)
    for pos, terrain in village_data.get('terrain', {}).items():
        x, y = pos
        grid_x, grid_y = x // tile_size, y // tile_size
        
        if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
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
        
        if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
            grid[grid_y][grid_x] = {
                'type': 'water',
                'passable': False,
                'preferred': False
            }
    
    # Add bridges (passable)
    for bridge in village_data.get('bridges', []):
        x, y = bridge['position']
        grid_x, grid_y = x // tile_size, y // tile_size
        
        if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
            grid[grid_y][grid_x] = {
                'type': 'bridge',
                'bridge_type': bridge.get('type', 'bridge'),
                'passable': True,
                'preferred': True
            }
    
    # Add paths (passable, preferred)
    for path in village_data.get('paths', []):
        x, y = path['position']
        grid_x, grid_y = x // tile_size, y // tile_size
        
        if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
            grid[grid_y][grid_x] = {
                'type': 'path',
                'variant': path.get('variant', 1),
                'passable': True,
                'preferred': True
            }
    
    # Add buildings (generally impassable)
    for i, building in enumerate(village_data.get('buildings', [])):
        pos = building['position']
        size_name = building['size']
        
        # Determine building size in tiles
        size_multiplier = 3 if size_name == 'large' else (
                        2 if size_name == 'medium' else 1)
        size_tiles = size_multiplier
        
        # Add building footprint to grid
        for dx in range(size_tiles):
            for dy in range(size_tiles):
                pos_x, pos_y = pos
                grid_x = (pos_x // tile_size) + dx
                grid_y = (pos_y // tile_size) + dy
                
                if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                    grid[grid_y][grid_x] = {
                        'type': 'building',
                        'building_id': i,
                        'building_type': building.get('building_type', 'Unknown'),
                        'passable': False,  # Buildings are generally impassable
                        'preferred': False
                    }
    
    # Store the grid in village_data
    village_data['village_grid'] = grid
    print(f"Village grid initialized: {grid_size}x{grid_size}")
    
    # Create a utility method for grid access
    def get_cell_at(x, y):
        """Get the grid cell at the given pixel coordinates."""
        grid_x = int(x // tile_size)
        grid_y = int(y // tile_size)
        
        if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
            return grid[grid_y][grid_x]
        return None
    
    # Add the accessor function to village_data
    village_data['get_cell_at'] = get_cell_at
    
    # Initialize path cache for efficient pathfinding
    if 'path_cache' not in village_data:
        village_data['path_cache'] = {}
