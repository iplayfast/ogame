"""
Landscape utility functions for the village simulation.

This module provides helper functions for generating landscape elements
like water features, terrain, and other natural elements.
"""

import random

import math
import random

def generate_points_in_irregular_shape(center_x, center_y, base_radius, irregularity, num_points=12):
    """Generate points forming an irregular shape.
    
    Args:
        center_x, center_y: Center of the shape
        base_radius: Base radius of the shape
        irregularity: Amount of irregularity (0.0-1.0)
        num_points: Number of points to generate
        
    Returns:
        List of (x, y) points forming the shape
    """
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
    """Test if a point is inside a shape defined by points.
    
    Args:
        x, y: Point to test
        shape_points: List of (x, y) points defining the shape
        center_x, center_y: Optional center point for radial shapes
        
    Returns:
        Boolean indicating if the point is inside the shape
    """
    # If center is provided, use radial approach (for irregular shapes with known center)
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

def calculate_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points.
    
    Args:
        x1, y1: First point coordinates
        x2, y2: Second point coordinates
        
    Returns:
        Distance between the points
    """
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx*dx + dy*dy)

def align_to_grid(x, y, tile_size):
    """Align a position to the grid.
    
    Args:
        x, y: Position coordinates
        tile_size: Size of a tile in pixels
        
    Returns:
        Tuple of (x, y) aligned to the grid
    """
    grid_x = (x // tile_size) * tile_size
    grid_y = (y // tile_size) * tile_size
    return grid_x, grid_y

def polar_to_cartesian(cx, cy, angle, distance):
    """Convert polar coordinates to Cartesian coordinates.
    
    Args:
        cx, cy: Center point coordinates
        angle: Angle in radians
        distance: Distance from center
        
    Returns:
        Tuple of (x, y) in Cartesian coordinates
    """
    x = cx + math.cos(angle) * distance
    y = cy + math.sin(angle) * distance
    return x, y

def scan_terrain(village, bounds=None, filter_fn=None, processor_fn=None):
    """Scan village terrain and process matching positions.
    
    Args:
        village: Village instance
        bounds: Optional (left, top, right, bottom) bounds to limit scan
        filter_fn: Function that takes (x, y, cell_data) and returns True if position should be processed
        processor_fn: Function that takes (x, y, cell_data) to process matching positions
        
    Returns:
        List of results from processor_fn if it returns values
    """
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

def is_in_bounds(x, y, grid_size):
    """Check if coordinates are within bounds.
    
    Args:
        x: X coordinate
        y: Y coordinate
        grid_size: Size of the grid in pixels
        
    Returns:
        Boolean indicating if the coordinates are within bounds
    """
    return 0 <= x < grid_size and 0 <= y < grid_size