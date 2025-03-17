"""
Compatibility patch for utils module.

This file adds any missing functions to the utils module for backward compatibility.
Import this at the beginning of any file that needs the old utils module functionality.

Usage:
    import utils.compatibility  # This imports and patches the utils module
"""

import sys
import utils
import math
import random

# Define all the utility functions directly in compatibility.py

def is_in_bounds(x, y, grid_size):
    """Check if coordinates are within bounds."""
    return 0 <= x < grid_size and 0 <= y < grid_size

def get_neighbors(x, y, tile_size, include_self=False):
    """Get neighboring positions (8-way)."""
    neighbors = []
    for dx in [-tile_size, 0, tile_size]:
        for dy in [-tile_size, 0, tile_size]:
            if dx == 0 and dy == 0 and not include_self:
                continue
            neighbors.append((x + dx, y + dy))
    return neighbors

def calculate_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points."""
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx*dx + dy*dy)

def align_to_grid(x, y, tile_size):
    """Align coordinates to the nearest grid point."""
    return ((x // tile_size) * tile_size, (y // tile_size) * tile_size)

def polar_to_cartesian(cx, cy, angle, distance):
    """Convert polar coordinates to Cartesian coordinates."""
    x = cx + math.cos(angle) * distance
    y = cy + math.sin(angle) * distance
    return x, y

def generate_points_in_irregular_shape(center_x, center_y, base_radius, irregularity, num_points=12):
    """Generate points forming an irregular shape."""
    points = []
    for i in range(num_points):
        angle = i * (2 * math.pi / num_points)
        # Vary the radius at this angle to create irregularity
        radius_modifier = 1.0 - irregularity/2 + random.random() * irregularity
        radius = base_radius * radius_modifier
        
        x = center_x + math.cos(angle) * radius
        y = center_y + math.sin(angle) * radius
        points.append((x, y))
    return points

def is_point_in_shape(x, y, shape_points, center_x=None, center_y=None):
    """Test if a point is inside a shape defined by points."""
    # If center is provided, use radial approach
    if center_x is not None and center_y is not None:
        # Calculate angle from center to point
        angle = math.atan2(y - center_y, x - center_x)
        if angle < 0:
            angle += 2 * math.pi
        
        # Find which sector this angle falls into
        num_points = len(shape_points)
        sector = int(angle / (2 * math.pi) * num_points)
        if sector >= num_points:
            sector = 0
        
        p1 = shape_points[sector]
        p2 = shape_points[(sector + 1) % num_points]
        
        # Calculate how far along the sector this angle is
        sector_start_angle = sector * (2 * math.pi / num_points)
        sector_angle_range = 2 * math.pi / num_points
        sector_progress = (angle - sector_start_angle) / sector_angle_range
        
        # Interpolate between the two points
        edge_x = p1[0] + (p2[0] - p1[0]) * sector_progress
        edge_y = p1[1] + (p2[1] - p1[1]) * sector_progress
        
        # Calculate distance from center to edge and from center to point
        edge_distance = math.sqrt((center_x - edge_x)**2 + (center_y - edge_y)**2)
        point_distance = math.sqrt((center_x - x)**2 + (center_y - y)**2)
        
        # If point is closer to center than edge, it's inside the shape
        return point_distance <= edge_distance
    
    # Otherwise, use ray casting algorithm for general polygons
    else:
        inside = False
        j = len(shape_points) - 1
        
        for i in range(len(shape_points)):
            # Check if ray from point crosses this edge
            xi, yi = shape_points[i]
            xj, yj = shape_points[j]
            
            # Point is on a vertex
            if (xi == x and yi == y) or (xj == x and yj == y):
                return True
                
            # Check if ray from point crosses this edge
            intersect = ((yi > y) != (yj > y)) and (x < xi + ((y - yi) / (yj - yi)) * (xj - xi))
            if intersect:
                inside = not inside
            j = i
            
        return inside

def scan_terrain(village, bounds=None, filter_fn=None, processor_fn=None):
    """Scan village terrain and process matching positions."""
    results = []
    
    # Determine scan bounds
    left = bounds[0] if bounds else 0
    top = bounds[1] if bounds else 0
    right = bounds[2] if bounds else village.grid_size
    bottom = bounds[3] if bounds else village.grid_size
    
    # Align to tile grid
    left = int((left // village.tile_size) * village.tile_size)
    top = int((top // village.tile_size) * village.tile_size)
    right = int((right // village.tile_size) * village.tile_size)
    bottom = int((bottom // village.tile_size) * village.tile_size)
    
    # Ensure we have at least one tile to scan
    if right <= left:
        right = left + village.tile_size
    if bottom <= top:
        bottom = top + village.tile_size
    
    # Scan territory
    for y in range(top, bottom, village.tile_size):
        for x in range(left, right, village.tile_size):
            pos = (x, y)
            cell_data = {}
            
            # Gather data about this position
            if hasattr(village, 'terrain') and pos in village.terrain:
                cell_data['terrain'] = village.terrain[pos]
            if hasattr(village, 'water_positions') and pos in village.water_positions:
                cell_data['water'] = True
            if hasattr(village, 'path_positions') and pos in village.path_positions:
                cell_data['path'] = True
            if hasattr(village, 'building_positions') and pos in village.building_positions:
                cell_data['building'] = True
                
            # Apply filter if provided
            if filter_fn and not filter_fn(x, y, cell_data):
                continue
                
            # Process position if processor provided
            if processor_fn:
                result = processor_fn(x, y, cell_data)
                if result is not None:
                    results.append(result)
    
    return results
# Add this function to utils/compatibility.py

def generate_name():
    """Generate a random NPC name.
    
    Returns:
        String with first and last name
    """
    first_names = [
        "Aiden", "Bela", "Clara", "Doran", "Eliza", "Finn", "Greta", "Hilda", 
        "Ivan", "Julia", "Kai", "Lily", "Milo", "Nina", "Otto", "Petra", 
        "Quinn", "Rosa", "Sven", "Tilly", "Ulric", "Vera", "Wren", "Xander", 
        "Yara", "Zeke"
    ]
    
    last_names = [
        "Smith", "Miller", "Fisher", "Baker", "Cooper", "Fletcher", "Thatcher",
        "Wood", "Stone", "Field", "Hill", "Brook", "River", "Dale", "Ford",
        "Green", "White", "Black", "Brown", "Gray", "Reed", "Swift", "Strong"
    ]
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"

# Additional utility functions you might need:

def get_random_building_type(size):
    """Return a random building type appropriate for the size."""
    if size == "large":
        return random.choice(["Town Hall", "Market", "Temple", "Manor"])
    elif size == "medium":
        return random.choice(["Inn", "Store", "Tavern", "Smithy", "Bakery"])
    else:  # small
        return random.choice(["House", "Cottage", "Workshop", "Storage"])

def iterate_area(x, y, width, height, tile_size):
    """Generate positions within a rectangular area."""
    for dx in range(0, width, tile_size):
        for dy in range(0, height, tile_size):
            yield (x + dx, y + dy)

def get_buffer_positions(x, y, buffer_tiles, tile_size):
    """Get all positions in a buffer zone around a position."""
    for dx in range(-buffer_tiles, buffer_tiles + 1):
        for dy in range(-buffer_tiles, buffer_tiles + 1):
            if dx == 0 and dy == 0:  # Skip the center tile
                continue
            yield (x + dx * tile_size, y + dy * tile_size)


utils.get_random_building_type = get_random_building_type
utils.iterate_area = iterate_area
utils.get_buffer_positions = get_buffer_positions
utils.is_in_bounds = is_in_bounds
utils.get_neighbors = get_neighbors
utils.calculate_distance = calculate_distance
utils.align_to_grid = align_to_grid
utils.polar_to_cartesian = polar_to_cartesian
utils.generate_points_in_irregular_shape = generate_points_in_irregular_shape
utils.is_point_in_shape = is_point_in_shape
utils.scan_terrain = scan_terrain
utils.generate_name = generate_name
# This ensures the module is properly patched
print("Utils module compatibility patch applied.")