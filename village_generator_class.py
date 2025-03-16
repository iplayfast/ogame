"""
This module provides a backward compatibility layer for the village generation.
It allows older code to continue using the procedural function interface
while leveraging the new object-oriented Village class internally.
"""

from village_base import Village

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
