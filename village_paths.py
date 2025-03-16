import random
import math
import utils

def create_village_layout(village):
    """Create village paths and roads based on the water feature.
    
    Args:
        village: Village instance
        
    Returns:
        Dictionary with updated village properties
    """
    print("Creating village layout...")
    
    # Map center
    center_x, center_y = village.grid_size // 2, village.grid_size // 2
    
    # Find closest non-water point to center to serve as village center
    village_center_x, village_center_y = find_village_center(village, center_x, center_y)
    
    # Store village center for later use
    village.village_center_x = village_center_x
    village.village_center_y = village_center_y
    
    # Create a central plaza
    create_central_plaza(village)
    
    # Create waterfront path that follows water edge
    create_waterfront_path(village)
    
    # Create main roads radiating out from village center
    create_main_roads(village)
    
    # Add some connecting paths around the center
    create_connecting_paths(village)
    
    # Update path positions for quick lookup
    village.path_positions = {(p['position'][0], p['position'][1]) for p in village.paths}
    
    print(f"Village layout created with {len(village.paths)} path tiles")
    
    return {
        'village_center_x': village_center_x,
        'village_center_y': village_center_y,
        'path_positions': village.path_positions
    }

def find_village_center(village, center_x, center_y):
    """Find the best location for village center (near map center but not on water).
    
    Args:
        village: Village instance
        center_x, center_y: Initial center coordinates
        
    Returns:
        Tuple of (x, y) coordinates for village center
    """
    # If center is not on water, use it
    if (center_x, center_y) not in village.water_positions:
        return center_x, center_y
    
    # Otherwise, search outward in spiral pattern to find closest non-water point
    for radius in range(1, village.grid_size // 4, village.tile_size):
        for angle in range(0, 360, 15):  # Check every 15 degrees
            angle_rad = math.radians(angle)
            x, y = utils.polar_to_cartesian(center_x, center_y, angle_rad, radius)
            
            # Align to grid
            x, y = utils.align_to_grid(x, y, village.tile_size)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(x, y, village.grid_size):
                continue
                
            # If this point is not water, use it
            if (x, y) not in village.water_positions:
                return x, y
    
    # Fallback: just use a point 1/4 of the way from top-left
    return village.grid_size // 4, village.grid_size // 4

def create_central_plaza(village):
    """Create a central plaza in the village.
    
    Args:
        village: Village instance
    """
    plaza_radius = village.grid_size // 16
    
    # Generate positions in a circular area
    for x in range(int(village.village_center_x - plaza_radius), int(village.village_center_x + plaza_radius) + 1, village.tile_size):
        for y in range(int(village.village_center_y - plaza_radius), int(village.village_center_y + plaza_radius) + 1, village.tile_size):
            # Skip if out of bounds or water
            if not utils.is_in_bounds(x, y, village.grid_size) or (x, y) in village.water_positions:
                continue
                
            # Create circular village center            
            distance = utils.calculate_distance(x, y, village.village_center_x, village.village_center_y)
            if distance < plaza_radius:
                # Central plaza with stone path (variant 2)
                village.paths.append({
                    'position': (x, y),
                    'variant': 2
                })
                village.path_positions.add((x, y))

def create_waterfront_path(village):
    """Create a path along the waterfront.
    
    Args:
        village: Village instance
    """
    # Identify water edge tiles (land tiles adjacent to water)
    water_edge = set()
    for water_pos in village.water_positions:
        # Check neighbors for non-water tiles
        for neighbor_pos in utils.get_neighbors(water_pos[0], water_pos[1], village.tile_size):
            # Skip if out of bounds
            if not utils.is_in_bounds(neighbor_pos[0], neighbor_pos[1], village.grid_size):
                continue
            
            # If neighbor is not water, it's a potential edge tile
            if neighbor_pos not in village.water_positions:
                water_edge.add(neighbor_pos)
    
    # Sort edge tiles for more consistent results
    sorted_edges = sorted(water_edge)
    
    # Add paths to every 3rd edge tile for a more natural look
    for i, edge_pos in enumerate(sorted_edges):
        if edge_pos not in village.path_positions and i % 3 == 0:
            village.paths.append({
                'position': edge_pos,
                'variant': 1  # Dirt path
            })
            village.path_positions.add(edge_pos)

def create_main_roads(village):
    """Create main roads radiating out from village center, avoiding water.
    
    Args:
        village: Village instance
    """
    # Create roads in 8 directions (every 45 degrees)
    for angle in range(0, 360, 45):
        create_road_from_center(village, angle)

def create_road_from_center(village, angle):
    """Create a road from village center outward in a specific direction, avoiding water.
    
    Args:
        village: Village instance
        angle: Angle in degrees
    """
    angle_rad = math.radians(angle)
    road_length = village.grid_size // 2 + random.randint(0, village.grid_size // 4)
    
    # Starting position is the village center
    current_x, current_y = village.village_center_x, village.village_center_y
    
    for dist in range(0, road_length, village.tile_size):
        # Calculate next position along the angle
        next_x, next_y = utils.polar_to_cartesian(village.village_center_x, village.village_center_y, angle_rad, dist)
        
        # Align to grid
        next_x, next_y = utils.align_to_grid(next_x, next_y, village.tile_size)
        
        # Skip if out of bounds
        if not utils.is_in_bounds(next_x, next_y, village.grid_size):
            break
        
        # If we hit water, try to route around it
        if (next_x, next_y) in village.water_positions:
            # Find a route around water
            detour_pos = find_detour_around_water(village, current_x, current_y, angle)
            
            if detour_pos:
                # Add path segment to detour point
                detour_x, detour_y = detour_pos
                if (detour_x, detour_y) not in village.path_positions:
                    village.paths.append({
                        'position': (detour_x, detour_y),
                        'variant': 1  # Dirt path
                    })
                    village.path_positions.add((detour_x, detour_y))
                
                # Update current position to continue from detour
                current_x, current_y = detour_x, detour_y
            else:
                # If no detour found, stop this road
                break
        else:
            # No water here, add path segment if needed
            if (next_x, next_y) not in village.path_positions:
                village.paths.append({
                    'position': (next_x, next_y),
                    'variant': 1  # Dirt path
                })
                village.path_positions.add((next_x, next_y))
            
            # Update current position for next segment
            current_x, current_y = next_x, next_y

def find_detour_around_water(village, current_x, current_y, angle):
    """Find a detour around water.
    
    Args:
        village: Village instance
        current_x, current_y: Current position
        angle: Current angle in degrees
        
    Returns:
        Tuple of (x, y) coordinates or None if no detour found
    """
    # Try different angles to detour around water
    for detour_angle_offset in [-30, -15, 15, 30, -45, 45, -60, 60]:
        detour_angle = angle + detour_angle_offset
        detour_angle_rad = math.radians(detour_angle)
        
        # Try different distances for detour
        for detour_dist in range(village.tile_size, 5 * village.tile_size, village.tile_size):
            detour_x, detour_y = utils.polar_to_cartesian(current_x, current_y, detour_angle_rad, detour_dist)
            
            # Align to grid
            detour_x, detour_y = utils.align_to_grid(detour_x, detour_y, village.tile_size)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(detour_x, detour_y, village.grid_size):
                continue
            
            # If this point is not water, use it to detour
            if (detour_x, detour_y) not in village.water_positions:
                return detour_x, detour_y
    
    # No detour found
    return None

def create_connecting_paths(village):
    """Add connecting paths between main roads around the village center.
    
    Args:
        village: Village instance
    """
    # Create rings of paths at different distances from center
    ring_distances = [
        village.grid_size // 10,   # Inner ring
        village.grid_size // 5,    # Middle ring
        village.grid_size // 3     # Outer ring
    ]
    
    for ring_radius in ring_distances:
        create_ring_path(village, ring_radius)

def create_ring_path(village, ring_radius):
    def path_filter(x, y, cell_data):
        # Position must be near the ring and not occupied
        pos = (x, y)
        if pos in village.path_positions or pos in village.water_positions:
            return False
            
        # Calculate distance from center
        distance = utils.calculate_distance(x, y, village.village_center_x, village.village_center_y)
        # Position is on the ring if distance is within tolerance
        return abs(distance - ring_radius) < village.tile_size * 0.75
        
    def path_processor(x, y, cell_data):
        pos = (x, y)
        # Add path if not already added
        if pos not in village.path_positions:
            village.paths.append({
                'position': pos,
                'variant': 1  # Dirt path
            })
            village.path_positions.add(pos)
            return pos
        return None
    
    # Define bounds around the ring for efficiency
    bounds = (
        village.village_center_x - ring_radius - village.tile_size,
        village.village_center_y - ring_radius - village.tile_size,
        village.village_center_x + ring_radius + village.tile_size,
        village.village_center_y + ring_radius + village.tile_size
    )
    
    return utils.scan_terrain(village, bounds, path_filter, path_processor)

def fix_path_issues(village):
    """Fix all path issues - diagonal paths and disconnected buildings.
    
    Args:
        village: Village instance
    """
    print("Fixing path issues...")
    
    # Ensure all paths have proper adjacency (no diagonal-only connections)
    ensure_path_adjacency(village)
    
    # Remove isolated paths (paths with fewer than 2 adjacent path neighbors)
    remove_isolated_paths(village)
    
    # Update the path_positions set after all fixes
    village.path_positions = {(p['position'][0], p['position'][1]) for p in village.paths}
    
    print("Path fixes complete.")

def ensure_path_adjacency(village):
    """Ensure all paths have at least one cardinal connection (not just diagonal).
    
    Args:
        village: Village instance
    """
    fixed_paths = village.paths.copy()
    new_paths = []
    
    # First pass: identify problematic paths (those with only diagonal connections)
    for path in village.paths:
        x, y = path['position']
        # Check cardinal directions (N, E, S, W)
        cardinal_neighbors = [
            (x, y - village.tile_size),  # North
            (x + village.tile_size, y),  # East
            (x, y + village.tile_size),  # South
            (x - village.tile_size, y)   # West
        ]
        
        # Count adjacent paths in cardinal directions
        cardinal_adjacent = sum(1 for pos in cardinal_neighbors if pos in village.path_positions)
        
        # If no cardinal adjacency but has diagonal neighbors, add connecting paths
        if cardinal_adjacent == 0:
            # Check diagonal directions
            diagonal_neighbors = [
                (x - village.tile_size, y - village.tile_size),  # NW
                (x + village.tile_size, y - village.tile_size),  # NE
                (x - village.tile_size, y + village.tile_size),  # SW
                (x + village.tile_size, y + village.tile_size)   # SE
            ]
            
            diagonal_connections = []
            for i, diag_pos in enumerate(diagonal_neighbors):
                if diag_pos in village.path_positions:
                    diagonal_connections.append((i, diag_pos))
            
            # Fix each diagonal connection by adding a cardinal connection
            for i, diag_pos in diagonal_connections:
                if i == 0:  # NW diagonal
                    # Try north first, then west
                    if (x, y - village.tile_size) not in village.path_positions and utils.is_in_bounds(x, y - village.tile_size, village.grid_size):
                        new_paths.append({
                            'position': (x, y - village.tile_size),
                            'variant': path['variant']
                        })
                        village.path_positions.add((x, y - village.tile_size))
                    elif (x - village.tile_size, y) not in village.path_positions and utils.is_in_bounds(x - village.tile_size, y, village.grid_size):
                        new_paths.append({
                            'position': (x - village.tile_size, y),
                            'variant': path['variant']
                        })
                        village.path_positions.add((x - village.tile_size, y))
                elif i == 1:  # NE diagonal
                    # Try north first, then east
                    if (x, y - village.tile_size) not in village.path_positions and utils.is_in_bounds(x, y - village.tile_size, village.grid_size):
                        new_paths.append({
                            'position': (x, y - village.tile_size),
                            'variant': path['variant']
                        })
                        village.path_positions.add((x, y - village.tile_size))
                    elif (x + village.tile_size, y) not in village.path_positions and utils.is_in_bounds(x + village.tile_size, y, village.grid_size):
                        new_paths.append({
                            'position': (x + village.tile_size, y),
                            'variant': path['variant']
                        })
                        village.path_positions.add((x + village.tile_size, y))
                elif i == 2:  # SW diagonal
                    # Try south first, then west
                    if (x, y + village.tile_size) not in village.path_positions and utils.is_in_bounds(x, y + village.tile_size, village.grid_size):
                        new_paths.append({
                            'position': (x, y + village.tile_size),
                            'variant': path['variant']
                        })
                        village.path_positions.add((x, y + village.tile_size))
                    elif (x - village.tile_size, y) not in village.path_positions and utils.is_in_bounds(x - village.tile_size, y, village.grid_size):
                        new_paths.append({
                            'position': (x - village.tile_size, y),
                            'variant': path['variant']
                        })
                        village.path_positions.add((x - village.tile_size, y))
                else:  # SE diagonal
                    # Try south first, then east
                    if (x, y + village.tile_size) not in village.path_positions and utils.is_in_bounds(x, y + village.tile_size, village.grid_size):
                        new_paths.append({
                            'position': (x, y + village.tile_size),
                            'variant': path['variant']
                        })
                        village.path_positions.add((x, y + village.tile_size))
                    elif (x + village.tile_size, y) not in village.path_positions and utils.is_in_bounds(x + village.tile_size, y, village.grid_size):
                        new_paths.append({
                            'position': (x + village.tile_size, y),
                            'variant': path['variant']
                        })
                        village.path_positions.add((x + village.tile_size, y))
    
    # Add all new connecting paths
    fixed_paths.extend(new_paths)
    village.paths = fixed_paths

def remove_isolated_paths(village):
    """Remove path tiles that have fewer than two cardinal neighbors and aren't connected to buildings.
    
    Args:
        village: Village instance
    """
    result_paths = []
    removed_positions = set()
    
    # First, identify isolated path tiles (fewer than 2 cardinal neighbors)
    for path in village.paths:
        x, y = path['position']
        # Check cardinal directions
        cardinal_neighbors = [
            (x, y - village.tile_size),  # North
            (x + village.tile_size, y),  # East
            (x, y + village.tile_size),  # South
            (x - village.tile_size, y)   # West
        ]
        
        # Count adjacent paths in cardinal directions
        adjacent_paths = sum(1 for pos in cardinal_neighbors if pos in village.path_positions)
        
        # Keep paths with at least two adjacent paths
        if adjacent_paths >= 2:
            result_paths.append(path)
        else:
            # Mark for potential removal
            removed_positions.add((x, y))
    
    # Second pass: preserve paths that are at map edges or connect to buildings
    for path in village.paths:
        x, y = path['position']
        pos = (x, y)
        if pos in removed_positions:
            # Check if at map edge
            if x == 0 or y == 0 or x == village.grid_size - village.tile_size or y == village.grid_size - village.tile_size:
                result_paths.append(path)
                removed_positions.discard(pos)
                continue
            
            # Check all 8 surrounding tiles for buildings
            has_potential_building = False
            for dx in [-village.tile_size, 0, village.tile_size]:
                for dy in [-village.tile_size, 0, village.tile_size]:
                    if dx == 0 and dy == 0:
                        continue  # Skip self
                        
                    # Check if this position has a building
                    check_x = x + dx
                    check_y = y + dy
                    check_pos = (check_x, check_y)
                    
                    if check_pos in village.building_positions:
                        has_potential_building = True
                        break
                        
                if has_potential_building:
                    break
            
            if has_potential_building:
                result_paths.append(path)
                removed_positions.discard(pos)
    
    # Update paths list
    village.paths = result_paths

def add_bridges(village):
    def bridge_filter(x, y, cell_data):
        # Position must be water with path connections on both sides
        pos = (x, y)
        if pos not in village.water_positions:
            return False
            
        # Check for horizontal bridge (path-water-path)
        horizontal_bridge = (
            (x - village.tile_size, y) in village.path_positions and
            (x + village.tile_size, y) in village.path_positions
        )
        
        # Check for vertical bridge (path-water-path)
        vertical_bridge = (
            (x, y - village.tile_size) in village.path_positions and
            (x, y + village.tile_size) in village.path_positions
        )
        
        return horizontal_bridge or vertical_bridge
        
    def bridge_processor(x, y, cell_data):
        pos = (x, y)
        # Determine bridge type based on connection direction
        horizontal_bridge = (
            (x - village.tile_size, y) in village.path_positions and
            (x + village.tile_size, y) in village.path_positions
        )
        
        bridge_type = "LeftRightBridge" if horizontal_bridge else "UpDownBridge"
        
        village.bridges.append({
            'position': pos,
            'type': bridge_type
        })
        return pos
    
    return utils.scan_terrain(village, None, bridge_filter, bridge_processor)

def create_direct_path_with_cardinal_adjacency(village, start_pos, end_pos):
    """Create a direct L-shaped path from start to end, avoiding water and ensuring cardinal adjacency.
    
    Args:
        village: Village instance
        start_pos: Starting position (x, y)
        end_pos: Ending position (x, y)
    """
    start_x, start_y = start_pos
    end_x, end_y = end_pos
    
    # Determine if we should go horizontally or vertically first
    horizontal_first = random.choice([True, False])
    
    # Add current position to the path if not already a path
    if start_pos not in village.path_positions:
        village.paths.append({
            'position': start_pos,
            'variant': 1  # Dirt path
        })
        village.path_positions.add(start_pos)
    
    # Create path using L-shape (always with cardinal connections)
    current_x, current_y = start_x, start_y
    
    if horizontal_first:
        # Move horizontally first
        dx = village.tile_size if end_x > current_x else -village.tile_size if end_x < current_x else 0
        
        while current_x != end_x and dx != 0:
            next_x = current_x + dx
            next_pos = (next_x, current_y)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(next_x, current_y, village.grid_size):
                break
            
            # Skip water or find detour
            if next_pos in village.water_positions:
                # Try to find a detour around water
                detour_found = False
                for detour_offset in [village.tile_size, -village.tile_size]:
                    detour_y = current_y + detour_offset
                    detour_pos = (current_x, detour_y)
                    next_detour_pos = (next_x, detour_y)
                    
                    # Check if detour is valid
                    if (utils.is_in_bounds(current_x, detour_y, village.grid_size) and 
                        utils.is_in_bounds(next_x, detour_y, village.grid_size) and
                        detour_pos not in village.water_positions and 
                        next_detour_pos not in village.water_positions):
                        
                        # Add detour path
                        if detour_pos not in village.path_positions:
                            village.paths.append({
                                'position': detour_pos,
                                'variant': 1  # Dirt path
                            })
                            village.path_positions.add(detour_pos)
                        
                        # Move to detour position
                        current_y = detour_y
                        detour_found = True
                        break
                
                if not detour_found:
                    # Can't continue - stop horizontal movement and try vertical
                    break
            
            # Move to next position
            current_x = next_x
            
            # Add path
            if next_pos not in village.path_positions:
                village.paths.append({
                    'position': next_pos,
                    'variant': 1  # Dirt path
                })
                village.path_positions.add(next_pos)
        
        # Then move vertically
        dy = village.tile_size if end_y > current_y else -village.tile_size if end_y < current_y else 0
        
        while current_y != end_y and dy != 0:
            next_y = current_y + dy
            next_pos = (current_x, next_y)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(current_x, next_y, village.grid_size):
                break
            
            # Skip water or find detour
            if next_pos in village.water_positions:
                # Try to find a detour around water
                detour_found = False
                for detour_offset in [village.tile_size, -village.tile_size]:
                    detour_x = current_x + detour_offset
                    detour_pos = (detour_x, current_y)
                    next_detour_pos = (detour_x, next_y)
                    
                    # Check if detour is valid
                    if (utils.is_in_bounds(detour_x, current_y, village.grid_size) and 
                        utils.is_in_bounds(detour_x, next_y, village.grid_size) and
                        detour_pos not in village.water_positions and 
                        next_detour_pos not in village.water_positions):
                        
                        # Add detour path
                        if detour_pos not in village.path_positions:
                            village.paths.append({
                                'position': detour_pos,
                                'variant': 1  # Dirt path
                            })
                            village.path_positions.add(detour_pos)
                        
                        # Move to detour position
                        current_x = detour_x
                        detour_found = True
                        break
                
                if not detour_found:
                    # Can't continue - stop movement
                    break
            
            # Move to next position
            current_y = next_y
            
            # Add path
            if next_pos not in village.path_positions:
                village.paths.append({
                    'position': next_pos,
                    'variant': 1  # Dirt path
                })
                village.path_positions.add(next_pos)
    else:
        # Move vertically first, then horizontally (similar logic to above)
        dy = village.tile_size if end_y > current_y else -village.tile_size if end_y < current_y else 0
        
        while current_y != end_y and dy != 0:
            next_y = current_y + dy
            next_pos = (current_x, next_y)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(current_x, next_y, village.grid_size):
                break
            
            # Skip water or find detour
            if next_pos in village.water_positions:
                # Try to find a detour around water
                detour_found = False
                for detour_offset in [village.tile_size, -village.tile_size]:
                    detour_x = current_x + detour_offset
                    detour_pos = (detour_x, current_y)
                    next_detour_pos = (detour_x, next_y)
                    
                    # Check if detour is valid
                    if (utils.is_in_bounds(detour_x, current_y, village.grid_size) and 
                        utils.is_in_bounds(detour_x, next_y, village.grid_size) and
                        detour_pos not in village.water_positions and 
                        next_detour_pos not in village.water_positions):
                        
                        # Add detour path
                        if detour_pos not in village.path_positions:
                            village.paths.append({
                                'position': detour_pos,
                                'variant': 1  # Dirt path
                            })
                            village.path_positions.add(detour_pos)
                        
                        # Move to detour position
                        current_x = detour_x
                        detour_found = True
                        break
                
                if not detour_found:
                    # Can't continue - stop vertical movement and try horizontal
                    break
            
            # Move to next position
            current_y = next_y
            
            # Add path
            if next_pos not in village.path_positions:
                village.paths.append({
                    'position': next_pos,
                    'variant': 1  # Dirt path
                })
                village.path_positions.add(next_pos)
        
        # Then move horizontally
        dx = village.tile_size if end_x > current_x else -village.tile_size if end_x < current_x else 0
        
        while current_x != end_x and dx != 0:
            next_x = current_x + dx
            next_pos = (next_x, current_y)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(next_x, current_y, village.grid_size):
                break
            
            # Skip water or find detour
            if next_pos in village.water_positions:
                # Try to find a detour around water
                detour_found = False
                for detour_offset in [village.tile_size, -village.tile_size]:
                    detour_y = current_y + detour_offset
                    detour_pos = (current_x, detour_y)
                    next_detour_pos = (next_x, detour_y)
                    
                    # Check if detour is valid
                    if (utils.is_in_bounds(current_x, detour_y, village.grid_size) and 
                        utils.is_in_bounds(next_x, detour_y, village.grid_size) and
                        detour_pos not in village.water_positions and 
                        next_detour_pos not in village.water_positions):
                        
                        # Add detour path
                        if detour_pos not in village.path_positions:
                            village.paths.append({
                                'position': detour_pos,
                                'variant': 1  # Dirt path
                            })
                            village.path_positions.add(detour_pos)
                        
                        # Move to detour position
                        current_y = detour_y
                        detour_found = True
                        break
                
                if not detour_found:
                    # Can't continue - stop movement
                    break
            
            # Move to next position
            current_x = next_x
            
            # Add path
            if next_pos not in village.path_positions:
                village.paths.append({
                    'position': next_pos,
                    'variant': 1  # Dirt path
                })
                village.path_positions.add(next_pos)
