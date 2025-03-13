import random
import math
import utils
import landscape_generator

# In village_generator.py, modify the generate_village function like this:

def generate_village(size, assets, tile_size=32):
    """Generate a procedural village with buildings, roads, and paths.
    
    Args:
        size: Base size parameter (will be scaled up)
        assets: Dictionary of game assets
        tile_size: Size of each tile in pixels
        
    Returns:
        Dictionary containing complete village data
    """
    # First, generate the landscape
    landscape = landscape_generator.generate_landscape(size, tile_size)
    
    # Extract landscape components
    grid_size = landscape['size']
    terrain = landscape['terrain']
    water = landscape['water']
    water_positions = landscape['water_positions']
    trees = []  # Clear any trees from initial landscape generation
    
    # Create additional village components
    bridges = []
    buildings = []
    paths = []
    
    print(f"Building village on landscape with size {grid_size}x{grid_size} pixels...")
    
    # Create a village layout based on the water feature
    # First, plan the main roads and paths around the water
    create_village_layout(paths, water_positions, grid_size, tile_size)
    
    # Convert path positions to a set for quick checking
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Place buildings with appropriate types based on proximity to water and village center
    target_building_count = int(size * 0.5)  # Scale with village size
    
    # Define building sizes for lookup
    building_sizes = {
        "large": 3 * tile_size,
        "medium": 2 * tile_size,
        "small": 1 * tile_size
    }
    
    place_buildings_by_zones(buildings, paths, water_positions, path_positions, 
                            grid_size, tile_size, assets, building_sizes, target_building_count, terrain)
    
    # Connect buildings to paths with proper adjacency
    connect_buildings_to_paths(buildings, paths, water_positions, grid_size, tile_size)
    
    # FIX 1: Ensure path adjacency (no diagonal-only connections)
    paths = ensure_path_adjacency(paths, grid_size, tile_size)
    
    # FIX 2: Remove isolated paths (paths with fewer than 2 adjacent path neighbors)
    paths = remove_isolated_paths(paths, grid_size, tile_size)
    
    # Update path_positions after fixing paths
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Update grass near building entrances and ensure they connect to paths
    update_grass_near_building_entrances(terrain, buildings, building_sizes, grid_size, 
                                        tile_size, water_positions, path_positions)
    
    # FIX 3: Ensure grass type 2 is properly around water
    fix_grass_around_water(terrain, water_positions, grid_size, tile_size)
    
    # Add bridges where paths cross water
    bridges = landscape_generator.add_bridges_at_path_water_intersections(terrain, water, paths, grid_size, tile_size, assets)
    
    # Create a set of building positions and occupied spaces to avoid when placing trees
    building_positions = set()
    occupied_spaces = set()
    
    for building in buildings:
        # Get building properties
        building_pos = building['position']
        building_size_name = building['size']
        
        # Convert size name to pixel size
        building_size_px = building_sizes[building_size_name]
        
        # Calculate footprint size in tiles
        footprint_tiles = building_size_px // tile_size
        
        # Mark all tiles occupied by the building
        for dx in range(footprint_tiles):
            for dy in range(footprint_tiles):
                pos = (building_pos[0] + dx * tile_size, building_pos[1] + dy * tile_size)
                building_positions.add(pos)
                occupied_spaces.add(pos)
        
        # Add a buffer zone around buildings to occupied spaces
        buffer_size = 1  # 1 tile buffer
        for dx in range(-buffer_size, footprint_tiles + buffer_size):
            for dy in range(-buffer_size, footprint_tiles + buffer_size):
                if 0 <= dx < footprint_tiles and 0 <= dy < footprint_tiles:
                    continue  # Skip the actual building tiles (already added)
                
                buffer_pos = (building_pos[0] + dx * tile_size, building_pos[1] + dy * tile_size)
                if utils.is_in_bounds(buffer_pos[0], buffer_pos[1], grid_size):
                    occupied_spaces.add(buffer_pos)
    
    # Now that we have buildings and paths, place trees with proper positioning
    tree_target = int(size * size * 0.03)  # 3% of tiles as trees
    landscape_generator.place_trees_improved(trees, water_positions, occupied_spaces, path_positions, 
                                           building_positions, grid_size, tile_size, size, tree_target)
    
    # Print some stats about the village
    print(f"Village generation complete! {len(buildings)} buildings, {len(paths)} path tiles, {len(bridges)} bridges, {len(trees)} trees")

    # Return the complete village data
    return {
        'size': grid_size,
        'terrain': terrain,
        'buildings': buildings,
        'trees': trees,
        'paths': paths,
        'water': water,
        'bridges': bridges
    }

def create_village_layout(paths, water_positions, grid_size, tile_size):
    """Create village paths and roads based on the water feature."""
    # Map center
    center_x, center_y = grid_size // 2, grid_size // 2
    
    # Find closest non-water point to center to serve as village center
    village_center_x, village_center_y = find_village_center(center_x, center_y, water_positions, grid_size, tile_size)
    
    # Create a village center plaza
    create_central_plaza(paths, village_center_x, village_center_y, grid_size, tile_size, water_positions)
    
    # Create waterfront path that follows water edge
    create_waterfront_path(paths, water_positions, grid_size, tile_size)
    
    # Create main roads radiating out from village center
    # Roads avoid water and connect to the edge of the map
    for angle in range(0, 360, 45):  # 8 directions
        create_road_from_center(paths, water_positions, village_center_x, village_center_y, 
                                angle, grid_size, tile_size)
    
    # Add some connecting paths between main roads
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    add_connecting_paths_around_center(paths, path_positions, water_positions, 
                                       village_center_x, village_center_y, grid_size, tile_size)
    
def connect_buildings_to_paths(buildings, paths, water_positions, grid_size, tile_size):
    """
    Ensure that each building has a path connecting it to the existing path network.
    
    Args:
        buildings: List of building dictionaries
        paths: List of path dictionaries
        water_positions: Set of water positions
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
    """
    # Convert path positions to a set for quick checking
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Process each building
    for building in buildings:
        # Get building properties
        building_pos = building['position']
        building_size_name = building['size']
        
        # Convert size name to pixel size
        building_size_px = 256 if building_size_name == 'large' else (
                           192 if building_size_name == 'medium' else 128)
        
        # Determine building footprint
        footprint_tiles = building_size_px // tile_size
        
        # Calculate the center of the building
        building_center_x = building_pos[0] + building_size_px // 2
        building_center_y = building_pos[1] + building_size_px // 2
        
        # Align to grid
        building_center_x, building_center_y = utils.align_to_grid(building_center_x, building_center_y, tile_size)
        
        # Generate building perimeter positions - these are possible door locations
        perimeter_positions = []
        
        # FIX: Focus on cardinal sides only for door placement (no corners)
        # Bottom side - priority for door position
        for x in range(0, footprint_tiles):
            perimeter_positions.append((
                building_pos[0] + x * tile_size,
                building_pos[1] + footprint_tiles * tile_size
            ))
        
        # Right side
        for y in range(0, footprint_tiles):
            perimeter_positions.append((
                building_pos[0] + footprint_tiles * tile_size,
                building_pos[1] + y * tile_size
            ))
        
        # Top side
        for x in range(0, footprint_tiles):
            perimeter_positions.append((
                building_pos[0] + x * tile_size,
                building_pos[1] - tile_size
            ))
        
        # Left side
        for y in range(0, footprint_tiles):
            perimeter_positions.append((
                building_pos[0] - tile_size,
                building_pos[1] + y * tile_size
            ))
        
        # Check if building already has a path adjacent to it
        has_adjacent_path = False
        for perimeter_pos in perimeter_positions:
            # Check only for cardinal adjacency (not diagonal)
            x, y = perimeter_pos
            
            if perimeter_pos in path_positions:
                has_adjacent_path = True
                break
        
        # If building already has adjacent path, skip to next building
        if has_adjacent_path:
            continue
        
        # Find closest path to this building
        closest_path = None
        min_distance = float('inf')
        
        for path in paths:
            path_pos = path['position']
            distance = utils.calculate_distance(
                building_center_x, building_center_y,
                path_pos[0], path_pos[1]
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_path = path_pos
        
        # If no path was found, skip this building (shouldn't happen in normal generation)
        if not closest_path:
            continue
        
        # Determine which perimeter position is closest to the path
        door_pos = None
        min_door_distance = float('inf')
        
        for perimeter_pos in perimeter_positions:
            distance = utils.calculate_distance(
                perimeter_pos[0], perimeter_pos[1],
                closest_path[0], closest_path[1]
            )
            
            if distance < min_door_distance:
                min_door_distance = distance
                door_pos = perimeter_pos
        
        # Create a path from the door to the closest path
        connect_door_to_path(paths, door_pos, closest_path, water_positions, path_positions, grid_size, tile_size)


def create_direct_path(paths, start_pos, end_pos, water_positions, path_positions, grid_size, tile_size):
    """
    Create a direct path from start to end, avoiding water if possible.
    
    Args:
        paths: List of path dictionaries to append new paths to
        start_pos: Starting position for the path
        end_pos: Ending position for the path
        water_positions: Set of water positions to avoid
        path_positions: Set of existing path positions
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
    """
    start_x, start_y = start_pos
    end_x, end_y = end_pos
    
    # Determine if we should go horizontally or vertically first
    dx = end_x - start_x
    dy = end_y - start_y
    
    # Start with the current position
    current_x, current_y = start_x, start_y
    
    # Try horizontal movement first if horizontal distance is greater, otherwise vertical
    horizontal_first = abs(dx) > abs(dy)
    
    # Follow a L-shaped path: first in one direction, then in the other
    if horizontal_first:
        # Move horizontally first
        step_x = tile_size if dx > 0 else -tile_size if dx < 0 else 0
        
        while current_x != end_x:
            current_x += step_x
            
            # Ensure we don't go past the end point
            if (step_x > 0 and current_x > end_x) or (step_x < 0 and current_x < end_x):
                current_x = end_x
            
            # Skip if out of bounds
            if not utils.is_in_bounds(current_x, current_y, grid_size):
                break
            
            # Skip or detour around water
            if (current_x, current_y) in water_positions:
                # Try to go around
                found_detour = False
                for detour_y in [current_y + tile_size, current_y - tile_size]:
                    if utils.is_in_bounds(current_x, detour_y, grid_size) and (current_x, detour_y) not in water_positions:
                        # Found a detour
                        found_detour = True
                        
                        # Add path to the detour
                        if (current_x, detour_y) not in path_positions:
                            paths.append({
                                'position': (current_x, detour_y),
                                'variant': 1  # Dirt path
                            })
                            path_positions.add((current_x, detour_y))
                        
                        # Update current position
                        current_y = detour_y
                        break
                
                if not found_detour:
                    # Skip and continue from next position
                    continue
            
            # Add path if not already a path
            if (current_x, current_y) not in path_positions:
                paths.append({
                    'position': (current_x, current_y),
                    'variant': 1  # Dirt path
                })
                path_positions.add((current_x, current_y))
        
        # Now move vertically to the end
        step_y = tile_size if dy > 0 else -tile_size if dy < 0 else 0
        
        while current_y != end_y:
            current_y += step_y
            
            # Ensure we don't go past the end point
            if (step_y > 0 and current_y > end_y) or (step_y < 0 and current_y < end_y):
                current_y = end_y
            
            # Skip if out of bounds
            if not utils.is_in_bounds(current_x, current_y, grid_size):
                break
            
            # Skip or detour around water
            if (current_x, current_y) in water_positions:
                # Try to go around
                found_detour = False
                for detour_x in [current_x + tile_size, current_x - tile_size]:
                    if utils.is_in_bounds(detour_x, current_y, grid_size) and (detour_x, current_y) not in water_positions:
                        # Found a detour
                        found_detour = True
                        
                        # Add path to the detour
                        if (detour_x, current_y) not in path_positions:
                            paths.append({
                                'position': (detour_x, current_y),
                                'variant': 1  # Dirt path
                            })
                            path_positions.add((detour_x, current_y))
                        
                        # Update current position
                        current_x = detour_x
                        break
                
                if not found_detour:
                    # Skip and continue from next position
                    continue
            
            # Add path if not already a path
            if (current_x, current_y) not in path_positions:
                paths.append({
                    'position': (current_x, current_y),
                    'variant': 1  # Dirt path
                })
                path_positions.add((current_x, current_y))
    else:
        # Move vertically first
        step_y = tile_size if dy > 0 else -tile_size if dy < 0 else 0
        
        while current_y != end_y:
            current_y += step_y
            
            # Ensure we don't go past the end point
            if (step_y > 0 and current_y > end_y) or (step_y < 0 and current_y < end_y):
                current_y = end_y
            
            # Skip if out of bounds
            if not utils.is_in_bounds(current_x, current_y, grid_size):
                break
            
            # Skip or detour around water
            if (current_x, current_y) in water_positions:
                # Try to go around
                found_detour = False
                for detour_x in [current_x + tile_size, current_x - tile_size]:
                    if utils.is_in_bounds(detour_x, current_y, grid_size) and (detour_x, current_y) not in water_positions:
                        # Found a detour
                        found_detour = True
                        
                        # Add path to the detour
                        if (detour_x, current_y) not in path_positions:
                            paths.append({
                                'position': (detour_x, current_y),
                                'variant': 1  # Dirt path
                            })
                            path_positions.add((detour_x, current_y))
                        
                        # Update current position
                        current_x = detour_x
                        break
                
                if not found_detour:
                    # Skip and continue from next position
                    continue
            
            # Add path if not already a path
            if (current_x, current_y) not in path_positions:
                paths.append({
                    'position': (current_x, current_y),
                    'variant': 1  # Dirt path
                })
                path_positions.add((current_x, current_y))
        
        # Now move horizontally to the end
        step_x = tile_size if dx > 0 else -tile_size if dx < 0 else 0
        
        while current_x != end_x:
            current_x += step_x
            
            # Ensure we don't go past the end point
            if (step_x > 0 and current_x > end_x) or (step_x < 0 and current_x < end_x):
                current_x = end_x
            
            # Skip if out of bounds
            if not utils.is_in_bounds(current_x, current_y, grid_size):
                break
            
            # Skip or detour around water
            if (current_x, current_y) in water_positions:
                # Try to go around
                found_detour = False
                for detour_y in [current_y + tile_size, current_y - tile_size]:
                    if utils.is_in_bounds(current_x, detour_y, grid_size) and (current_x, detour_y) not in water_positions:
                        # Found a detour
                        found_detour = True
                        
                        # Add path to the detour
                        if (current_x, detour_y) not in path_positions:
                            paths.append({
                                'position': (current_x, detour_y),
                                'variant': 1  # Dirt path
                            })
                            path_positions.add((current_x, detour_y))
                        
                        # Update current position
                        current_y = detour_y
                        break
                
                if not found_detour:
                    # Skip and continue from next position
                    continue
            
            # Add path if not already a path
            if (current_x, current_y) not in path_positions:
                paths.append({
                    'position': (current_x, current_y),
                    'variant': 1  # Dirt path
                })
                path_positions.add((current_x, current_y))

def ensure_path_adjacency(paths, grid_size, tile_size):
    """Fix disconnected paths by ensuring all path tiles have proper adjacency."""
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    fixed_paths = paths.copy()
    new_paths = []
    
    # First pass: identify problematic paths (those with only diagonal connections)
    for path in paths:
        x, y = path['position']
        # Check cardinal directions (N, E, S, W)
        cardinal_neighbors = [
            (x, y - tile_size),  # North
            (x + tile_size, y),  # East
            (x, y + tile_size),  # South
            (x - tile_size, y)   # West
        ]
        
        # Count adjacent paths in cardinal directions
        cardinal_adjacent = sum(1 for pos in cardinal_neighbors if pos in path_positions)
        
        # If no cardinal adjacency but has diagonal neighbors, add connecting paths
        if cardinal_adjacent == 0:
            # Check diagonal directions
            diagonal_neighbors = [
                (x - tile_size, y - tile_size),  # NW
                (x + tile_size, y - tile_size),  # NE
                (x - tile_size, y + tile_size),  # SW
                (x + tile_size, y + tile_size)   # SE
            ]
            
            for i, diag_pos in enumerate(diagonal_neighbors):
                if diag_pos in path_positions:
                    # Add a connecting path in one of the cardinal directions
                    # Based on which diagonal has a path
                    if i == 0:  # NW diagonal
                        # Try north first, then west
                        if (x, y - tile_size) not in path_positions and utils.is_in_bounds(x, y - tile_size, grid_size):
                            new_paths.append({
                                'position': (x, y - tile_size),
                                'variant': path['variant']
                            })
                            path_positions.add((x, y - tile_size))
                        elif (x - tile_size, y) not in path_positions and utils.is_in_bounds(x - tile_size, y, grid_size):
                            new_paths.append({
                                'position': (x - tile_size, y),
                                'variant': path['variant']
                            })
                            path_positions.add((x - tile_size, y))
                    elif i == 1:  # NE diagonal
                        # Try north first, then east
                        if (x, y - tile_size) not in path_positions and utils.is_in_bounds(x, y - tile_size, grid_size):
                            new_paths.append({
                                'position': (x, y - tile_size),
                                'variant': path['variant']
                            })
                            path_positions.add((x, y - tile_size))
                        elif (x + tile_size, y) not in path_positions and utils.is_in_bounds(x + tile_size, y, grid_size):
                            new_paths.append({
                                'position': (x + tile_size, y),
                                'variant': path['variant']
                            })
                            path_positions.add((x + tile_size, y))
                    elif i == 2:  # SW diagonal
                        # Try south first, then west
                        if (x, y + tile_size) not in path_positions and utils.is_in_bounds(x, y + tile_size, grid_size):
                            new_paths.append({
                                'position': (x, y + tile_size),
                                'variant': path['variant']
                            })
                            path_positions.add((x, y + tile_size))
                        elif (x - tile_size, y) not in path_positions and utils.is_in_bounds(x - tile_size, y, grid_size):
                            new_paths.append({
                                'position': (x - tile_size, y),
                                'variant': path['variant']
                            })
                            path_positions.add((x - tile_size, y))
                    else:  # SE diagonal
                        # Try south first, then east
                        if (x, y + tile_size) not in path_positions and utils.is_in_bounds(x, y + tile_size, grid_size):
                            new_paths.append({
                                'position': (x, y + tile_size),
                                'variant': path['variant']
                            })
                            path_positions.add((x, y + tile_size))
                        elif (x + tile_size, y) not in path_positions and utils.is_in_bounds(x + tile_size, y, grid_size):
                            new_paths.append({
                                'position': (x + tile_size, y),
                                'variant': path['variant']
                            })
                            path_positions.add((x + tile_size, y))
    
    # Add all new connecting paths
    fixed_paths.extend(new_paths)
    return fixed_paths

def remove_isolated_paths(paths, grid_size, tile_size):
    """Remove path tiles that have fewer than two cardinal neighbors and aren't connected to buildings."""
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    result_paths = []
    removed_positions = set()
    
    # First, identify isolated path tiles (fewer than 2 cardinal neighbors)
    for path in paths:
        x, y = path['position']
        # Check cardinal directions
        cardinal_neighbors = [
            (x, y - tile_size),  # North
            (x + tile_size, y),  # East
            (x, y + tile_size),  # South
            (x - tile_size, y)   # West
        ]
        
        # Count adjacent paths in cardinal directions
        adjacent_paths = sum(1 for pos in cardinal_neighbors if pos in path_positions)
        
        # Keep paths with at least two adjacent paths
        if adjacent_paths >= 2:
            result_paths.append(path)
        else:
            # Mark for potential removal
            removed_positions.add((x, y))
    
    # Second pass: preserve paths that are at map edges or connect to buildings
    for path in paths:
        x, y = path['position']
        pos = (x, y)
        if pos in removed_positions:
            # Check if at map edge
            if x == 0 or y == 0 or x == grid_size - tile_size or y == grid_size - tile_size:
                result_paths.append(path)
                removed_positions.discard(pos)  # Use discard instead of remove
                continue
            
            # Check all 8 surrounding tiles for buildings
            has_potential_building = False
            for dx in [-tile_size, 0, tile_size]:
                for dy in [-tile_size, 0, tile_size]:
                    if dx == 0 and dy == 0:
                        continue  # Skip self
                        
                    # Check if there's a building at this position
                    # This is a simple proxy since we don't have the actual building positions here
                    # We're checking if this position has no paths and is not at the map edge
                    check_x = x + dx
                    check_y = y + dy
                    check_pos = (check_x, check_y)
                    
                    if (check_pos not in path_positions and
                       utils.is_in_bounds(check_x, check_y, grid_size)):
                        # Assume this might be a building - keep the path
                        has_potential_building = True
                        break
                        
                if has_potential_building:
                    break
            
            if has_potential_building:
                result_paths.append(path)
                removed_positions.discard(pos)  # Use discard instead of remove
    
    return result_paths

def fix_grass_around_water(terrain, water_positions, grid_size, tile_size):
    """Ensure grass tiles around water are properly set to type 2."""
    # Reset all grass variants near water
    for water_pos in water_positions:
        x, y = water_pos
        
        # Check 8 neighboring tiles
        for dx in [-tile_size, 0, tile_size]:
            for dy in [-tile_size, 0, tile_size]:
                if dx == 0 and dy == 0:
                    continue  # Skip self
                    
                neighbor_pos = (x + dx, y + dy)
                
                # Skip if out of bounds
                if not utils.is_in_bounds(neighbor_pos[0], neighbor_pos[1], grid_size):
                    continue
                
                # If neighbor is a grass tile, update to type 2
                if neighbor_pos in terrain and terrain[neighbor_pos]['type'] == 'grass':
                    terrain[neighbor_pos]['variant'] = 2


def find_village_center(center_x, center_y, water_positions, grid_size, tile_size):
    """Find the best location for village center (near map center but not on water)."""
    # If center is not on water, use it
    if (center_x, center_y) not in water_positions:
        return center_x, center_y
    
    # Otherwise, search outward in spiral pattern to find closest non-water point
    for radius in range(1, grid_size // 4, tile_size):
        for angle in range(0, 360, 15):  # Check every 15 degrees
            angle_rad = math.radians(angle)
            x, y = utils.polar_to_cartesian(center_x, center_y, angle_rad, radius)
            
            # Align to grid
            x, y = utils.align_to_grid(x, y, tile_size)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(x, y, grid_size):
                continue
                
            # If this point is not water, use it
            if (x, y) not in water_positions:
                return x, y
    
    # Fallback: just use a point 1/4 of the way from top-left
    return grid_size // 4, grid_size // 4

def create_central_plaza(paths, village_center_x, village_center_y, grid_size, tile_size, water_positions):
    """Create a central plaza in the village."""
    plaza_radius = grid_size // 16
    
    # Generate positions in a circular area
    for x in range(village_center_x - plaza_radius, village_center_x + plaza_radius, tile_size):
        for y in range(village_center_y - plaza_radius, village_center_y + plaza_radius, tile_size):
            # Skip if out of bounds or water
            if not utils.is_in_bounds(x, y, grid_size) or (x, y) in water_positions:
                continue
                
            # Create circular village center            
            distance = utils.calculate_distance(x, y, village_center_x, village_center_y)
            if distance < plaza_radius:
                # Central plaza with stone path
                paths.append({
                    'position': (x, y),
                    'variant': 2  # Stone path
                })

def create_waterfront_path(paths, water_positions, grid_size, tile_size):
    """Create a path along the waterfront."""
    # Identify water edge tiles (land tiles adjacent to water)
    water_edge = set()
    for water_pos in water_positions:
        # Check neighbors for non-water tiles
        for neighbor_pos in utils.get_neighbors(water_pos[0], water_pos[1], tile_size):
            # Skip if out of bounds
            if not utils.is_in_bounds(neighbor_pos[0], neighbor_pos[1], grid_size):
                continue
            
            # If neighbor is not water, it's a potential edge tile
            if neighbor_pos not in water_positions:
                water_edge.add(neighbor_pos)
    
    # Process edges to selectively create paths
    # Don't place paths on every edge tile - make it more natural
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Sort edge tiles for more consistent results
    sorted_edges = sorted(water_edge)
    
    # Add paths to every 3rd edge tile
    for i, edge_pos in enumerate(sorted_edges):
        if edge_pos not in path_positions and i % 3 == 0:
            paths.append({
                'position': edge_pos,
                'variant': 1  # Dirt path
            })
            path_positions.add(edge_pos)

def create_road_from_center(paths, water_positions, center_x, center_y, angle, grid_size, tile_size):
    """Create a road from village center outward in a specific direction, avoiding water."""
    angle_rad = math.radians(angle)
    road_length = grid_size // 2 + random.randint(0, grid_size // 4)
    
    # Starting position is the village center
    current_x = center_x
    current_y = center_y
    
    # Convert existing paths to a set for quick checking
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    for dist in range(0, road_length, tile_size):
        # Calculate next position along the angle
        next_x, next_y = utils.polar_to_cartesian(center_x, center_y, angle_rad, dist)
        
        # Align to grid
        next_x, next_y = utils.align_to_grid(next_x, next_y, tile_size)
        
        # Skip if out of bounds
        if not utils.is_in_bounds(next_x, next_y, grid_size):
            break
        
        # If we hit water, try to route around it
        if (next_x, next_y) in water_positions:
            # Find a route around water
            detour_pos = find_detour_around_water(current_x, current_y, angle, water_positions, grid_size, tile_size)
            
            if detour_pos:
                # Add path segment to detour point
                detour_x, detour_y = detour_pos
                if (detour_x, detour_y) not in path_positions:
                    paths.append({
                        'position': (detour_x, detour_y),
                        'variant': 1  # Dirt path
                    })
                    path_positions.add((detour_x, detour_y))
                
                # Update current position to continue from detour
                current_x = detour_x
                current_y = detour_y
            else:
                # If no detour found, stop this road
                break
        else:
            # No water here, add path segment if needed
            if (next_x, next_y) not in path_positions:
                paths.append({
                    'position': (next_x, next_y),
                    'variant': 1  # Dirt path
                })
                path_positions.add((next_x, next_y))
            
            # Update current position for next segment
            current_x = next_x
            current_y = next_y

def find_detour_around_water(current_x, current_y, angle, water_positions, grid_size, tile_size):
    """Find a detour around water."""
    # Try different angles to detour around water
    for detour_angle_offset in [-30, -15, 15, 30, -45, 45, -60, 60]:
        detour_angle = angle + detour_angle_offset
        detour_angle_rad = math.radians(detour_angle)
        
        # Try different distances for detour
        for detour_dist in range(tile_size, 5 * tile_size, tile_size):
            detour_x, detour_y = utils.polar_to_cartesian(current_x, current_y, detour_angle_rad, detour_dist)
            
            # Align to grid
            detour_x, detour_y = utils.align_to_grid(detour_x, detour_y, tile_size)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(detour_x, detour_y, grid_size):
                continue
            
            # If this point is not water, use it to detour
            if (detour_x, detour_y) not in water_positions:
                return detour_x, detour_y
    
    # No detour found
    return None

def add_connecting_paths_around_center(paths, path_positions, water_positions, center_x, center_y, grid_size, tile_size):
    """Add connecting paths between main roads around the village center."""
    # Create rings of paths at different distances from center
    ring_distances = [
        grid_size // 10,   # Inner ring
        grid_size // 5,    # Middle ring
        grid_size // 3     # Outer ring
    ]
    
    for ring_radius in ring_distances:
        create_ring_path(paths, path_positions, water_positions, center_x, center_y, ring_radius, grid_size, tile_size)

def create_ring_path(paths, path_positions, water_positions, center_x, center_y, ring_radius, grid_size, tile_size):
    """Create a ring of paths around the center."""
    # Number of segments for this ring
    num_segments = max(8, int(ring_radius / 20))
    angle_step = 2 * math.pi / num_segments
    
    # Place path segments around the ring
    for i in range(num_segments):
        angle = i * angle_step
        
        # Start and end points of this segment
        start_angle = angle
        end_angle = angle + angle_step
        
        # Generate multiple points along this segment
        for t in range(10):  # 10 steps per segment
            segment_angle = start_angle + (end_angle - start_angle) * (t / 10)
            
            # Calculate position on ring
            x, y = utils.polar_to_cartesian(center_x, center_y, segment_angle, ring_radius)
            
            # Align to grid
            x, y = utils.align_to_grid(x, y, tile_size)
            
            # Skip if out of bounds, on water, or already a path
            if not utils.is_in_bounds(x, y, grid_size):
                continue
                
            if (x, y) in water_positions or (x, y) in path_positions:
                continue
            
            # Add path segment
            paths.append({
                'position': (x, y),
                'variant': 1  # Dirt path
            })
            path_positions.add((x, y))

def place_buildings_by_zones(buildings, paths, water_positions, path_positions, 
                            grid_size, tile_size, assets, building_sizes, target_building_count, terrain):
    """Place buildings in different zones: waterfront, center, and outskirts."""
    # Track occupied spaces for better building placement
    occupied_spaces = set()
    
    # Identify village center
    center_x, center_y = grid_size // 2, grid_size // 2
    village_center_x, village_center_y = find_village_center(center_x, center_y, water_positions, grid_size, tile_size)
    
    # Create zones
    waterfront_zone, center_zone, outskirts_zone = create_village_zones(
        path_positions, water_positions, village_center_x, village_center_y, grid_size, tile_size)
    
    # Distribute target building count across zones
    waterfront_count = int(target_building_count * 0.3)  # 30% near water
    center_count = int(target_building_count * 0.4)     # 40% in town center
    outskirts_count = int(target_building_count * 0.3)  # 30% in outskirts
    
    # Adjust if necessary to ensure total is correct
    total = waterfront_count + center_count + outskirts_count
    if total < target_building_count:
        center_count += target_building_count - total
    
    # Convert zones to lists for random selection
    waterfront_paths = list(waterfront_zone)
    center_paths = list(center_zone)
    outskirts_paths = list(outskirts_zone)
    
    # Place buildings in each zone
    place_zone_buildings(buildings, waterfront_paths, water_positions, path_positions, 
                         occupied_spaces, grid_size, tile_size, assets, building_sizes, 
                         waterfront_count, zone_type="waterfront")
    
    place_zone_buildings(buildings, center_paths, water_positions, path_positions, 
                         occupied_spaces, grid_size, tile_size, assets, building_sizes, 
                         center_count, zone_type="center")
    
    place_zone_buildings(buildings, outskirts_paths, water_positions, path_positions, 
                         occupied_spaces, grid_size, tile_size, assets, building_sizes, 
                         outskirts_count, zone_type="outskirts")

def create_village_zones(path_positions, water_positions, village_center_x, village_center_y, grid_size, tile_size):
    """Create different zones in the village (waterfront, center, outskirts)."""
    waterfront_zone = set()  # Near water
    center_zone = set()      # Near village center
    outskirts_zone = set()   # Further out
    
    # Define zone distances
    center_radius = grid_size // 8
    outskirts_radius = grid_size // 3
    
    # Identify waterfront paths (paths adjacent to water)
    for path_pos in path_positions:
        # Check if this path is near water
        is_waterfront = is_near_water(path_pos[0], path_pos[1], water_positions, tile_size)
        
        if is_waterfront:
            waterfront_zone.add(path_pos)
            continue
            
        # Check if path is in center zone
        dist_to_center = utils.calculate_distance(path_pos[0], path_pos[1], village_center_x, village_center_y)
        if dist_to_center < center_radius:
            center_zone.add(path_pos)
        elif dist_to_center < outskirts_radius:
            outskirts_zone.add(path_pos)
            
    return waterfront_zone, center_zone, outskirts_zone

def is_near_water(x, y, water_positions, tile_size):
    """Check if a position is near water."""
    for neighbor_pos in utils.get_neighbors(x, y, tile_size):
        if neighbor_pos in water_positions:
            return True
    return False

def place_zone_buildings(buildings, zone_paths, water_positions, path_positions, 
                        occupied_spaces, grid_size, tile_size, assets, building_sizes, 
                        target_count, zone_type):
    """Place buildings in a specific zone."""
    # Skip if no valid paths in this zone
    if not zone_paths:
        return
        
    # Determine building sizes and types based on zone
    size_weights, type_weights = get_zone_building_distributions(zone_type)
    
    # Place buildings
    for _ in range(target_count):
        if not zone_paths:  # Stop if we run out of valid paths
            break
            
        # Pick a random path
        path_idx = random.randrange(len(zone_paths))
        path_pos = zone_paths[path_idx]
        
        # Try to place a building
        if try_place_building(buildings, path_pos, water_positions, path_positions, 
                             occupied_spaces, grid_size, tile_size, assets, 
                             building_sizes, size_weights, type_weights):
            # Remove used path to avoid placing multiple buildings at same spot
            zone_paths.pop(path_idx)

def get_zone_building_distributions(zone_type):
    """Get building size and type distributions for a zone."""
    # Building size weights by zone
    if zone_type == "waterfront":
        # Waterfront: mostly small buildings, some medium
        size_weights = {"small": 70, "medium": 30, "large": 0}
        type_weights = {
            "Cottage": 30, "House": 20, "Workshop": 10, 
            "Inn": 20, "Tavern": 10, "Smithy": 0, 
            "Store": 10, "Market": 0, "Bakery": 0
        }
    elif zone_type == "center":
        # Center: mix of sizes, important buildings
        size_weights = {"small": 30, "medium": 50, "large": 20}
        type_weights = {
            "House": 10, "Workshop": 15, "Store": 20,
            "Inn": 10, "Tavern": 10, "Smithy": 10,
            "Market": 10, "Town Hall": 5, "Bakery": 10
        }
    else:  # outskirts
        # Outskirts: mostly small residential
        size_weights = {"small": 80, "medium": 20, "large": 0}
        type_weights = {
            "House": 40, "Cottage": 30, "Workshop": 10,
            "Store": 10, "Storage": 10
        }
        
    return size_weights, type_weights


def is_footprint_valid(building_x, building_y, footprint_tiles, tile_size,
                      water_positions, path_positions, occupied_spaces):
    """Check if a building footprint is valid."""
    # Check all tiles in the building footprint
    for pos in utils.iterate_area(building_x, building_y, footprint_tiles * tile_size, footprint_tiles * tile_size, tile_size):
        if (pos in water_positions or pos in path_positions or pos in occupied_spaces):
            return False
                
    return True

def is_buffer_valid(building_x, building_y, footprint_tiles, buffer_tiles, tile_size,
                   grid_size, occupied_spaces, path_positions):
    """Check if the buffer zone around a building is valid."""
    # Check buffer zone around the building (excluding the building itself)
    for dx in range(-buffer_tiles, footprint_tiles + buffer_tiles):
        for dy in range(-buffer_tiles, footprint_tiles + buffer_tiles):
            # Skip checking the actual building footprint
            if 0 <= dx < footprint_tiles and 0 <= dy < footprint_tiles:
                continue
                
            check_x = building_x + dx * tile_size
            check_y = building_y + dy * tile_size
            
            # Skip if out of bounds
            if not utils.is_in_bounds(check_x, check_y, grid_size):
                continue
            
            check_pos = (check_x, check_y)
            
            # Allow buffer to overlap with paths (buildings can be near paths)
            # But don't allow overlap with other buildings' occupied spaces
            if check_pos in occupied_spaces and check_pos not in path_positions:
                return False
                
    return True

    """Update grass terrain near building entrances to type 3."""
    for building in buildings:
        # Get building properties
        building_pos = building['position']
        building_size_px = building_sizes[building['size']]
        
        # Determine likely door position - usually at the bottom center of the building
        door_x = building_pos[0] + building_size_px // 2
        door_y = building_pos[1] + building_size_px  # Bottom center
        
        # Check if the bottom of the building is near water
        # If so, likely the door is on one of the other sides
        bottom_water = False
        for dx in range(-tile_size, tile_size * 2, tile_size):
            check_pos = (door_x + dx, door_y)
            if check_pos in water_positions:
                bottom_water = True
                break
                
        if bottom_water:
            # Try other sides - left, right, then top
            left_side_valid = True
            for dy in range(-tile_size, tile_size * 2, tile_size):
                check_pos = (building_pos[0], building_pos[1] + building_size_px // 2 + dy)
                if check_pos in water_positions:
                    left_side_valid = False
                    break
                    
            if left_side_valid:
                # Door likely on left side
                door_x = building_pos[0]
                door_y = building_pos[1] + building_size_px // 2
            else:
                # Check right side
                right_side_valid = True
                for dy in range(-tile_size, tile_size * 2, tile_size):
                    check_pos = (building_pos[0] + building_size_px, building_pos[1] + building_size_px // 2 + dy)
                    if check_pos in water_positions:
                        right_side_valid = False
                        break
                        
                if right_side_valid:
                    # Door likely on right side
                    door_x = building_pos[0] + building_size_px
                    door_y = building_pos[1] + building_size_px // 2
                else:
                    # Door likely on top side
                    door_x = building_pos[0] + building_size_px // 2
                    door_y = building_pos[1]
        
        # For path-adjacent buildings, place door near path
        door_placed = False
        for offset_x in range(-1, 2):
            for offset_y in range(-1, 2):
                check_x = door_x + offset_x * tile_size
                check_y = door_y + offset_y * tile_size
                
                if (check_x, check_y) in path_positions:
                    # Update door position to be near path
                    door_x = check_x
                    door_y = check_y
                    door_placed = True
                    break
            if door_placed:
                break
        
        # Update grass tiles around the door to variant 3
        for neighbor_pos in utils.get_neighbors(door_x, door_y, tile_size, include_self=True):
            # Skip if out of bounds
            if not utils.is_in_bounds(neighbor_pos[0], neighbor_pos[1], grid_size):
                continue
            
            # Skip if not grass, a path, or water
            if (neighbor_pos not in terrain or 
                terrain[neighbor_pos]['type'] != 'grass' or 
                neighbor_pos in path_positions or 
                neighbor_pos in water_positions):
                continue
            
            # Update grass to variant 3
            terrain[neighbor_pos]['variant'] = 3  # Building entrance grass                    

            """
Refactored functions from village_generator.py to better utilize utils.py
"""
import random
import math
import utils


def try_place_building(buildings, path_pos, water_positions, path_positions, 
                      occupied_spaces, grid_size, tile_size, assets, 
                      building_sizes, size_weights, type_weights):
    """Try to place a building near a path."""
    # Determine building size
    sizes = list(size_weights.keys())
    weights = [size_weights[s] for s in sizes]
    building_size = random.choices(sizes, weights=weights)[0]
    
    # Get building type based on weights
    types = list(type_weights.keys())
    weights = [type_weights[t] for t in types]
    building_type = random.choices(types, weights=weights)[0]
    
    # Get actual building size in pixels
    building_size_px = building_sizes[building_size]
    
    # Calculate building footprint size in tiles
    footprint_tiles = building_size_px // tile_size
    
    # Define search directions (8 directions around the path)
    directions = [
        (-1, -1), (0, -1), (1, -1),
        (-1, 0),           (1, 0),
        (-1, 1),  (0, 1),  (1, 1)
    ]
    
    # Shuffle directions for variety
    random.shuffle(directions)
    
    # Try each direction
    path_x, path_y = path_pos
    
    for dir_x, dir_y in directions:
        # Calculate potential building position
        # Move further out for larger buildings to ensure they don't overlap the path
        distance = max(1, footprint_tiles // 2 + 1)
        building_x = path_x + dir_x * tile_size * distance
        building_y = path_y + dir_y * tile_size * distance
        
        # Align to grid
        building_x, building_y = utils.align_to_grid(building_x, building_y, tile_size)
        
        # Skip if out of bounds
        if not utils.is_in_bounds(building_x, building_y, grid_size) or \
           building_x + building_size_px > grid_size or \
           building_y + building_size_px > grid_size:
            continue
        
        # Check if the footprint is valid (not on water, paths, or other buildings)
        excluded_sets = [water_positions, path_positions, occupied_spaces]
        if utils.is_footprint_valid(building_x, building_y, footprint_tiles, tile_size,
                                   excluded_sets, grid_size):
            
            # Check if there's enough buffer space around the building
            buffer_tiles = 1 if building_size == "small" else 2
            if is_buffer_valid(building_x, building_y, footprint_tiles, buffer_tiles, tile_size,
                              grid_size, occupied_spaces, path_positions):
                
                # Get available building variants
                available_variants = [k for k in assets['buildings'].keys() 
                                    if k.startswith(building_size) and k != 'roofs']
                
                variant = ""
                if available_variants:
                    variant = random.choice(available_variants)
                
                # Add the building
                buildings.append({
                    'position': (building_x, building_y),
                    'type': variant,
                    'size': building_size,
                    'building_type': building_type
                })
                
                # Mark the space as occupied (both the building footprint and its buffer zone)
                for pos in utils.iterate_area(building_x, building_y, 
                                           footprint_tiles * tile_size, 
                                           footprint_tiles * tile_size, 
                                           tile_size):
                    occupied_spaces.add(pos)
                
                # Add buffer zone around building
                for pos in utils.get_buffer_positions(building_x, building_y, buffer_tiles, tile_size):
                    if utils.is_in_bounds(pos[0], pos[1], grid_size):
                        occupied_spaces.add(pos)
                
                # Successfully placed a building
                return True
    
    # Could not place a building
    return False


def update_grass_near_building_entrances(terrain, buildings, building_sizes, grid_size, 
                                        tile_size, water_positions, path_positions):
    """Update grass terrain near building entrances to type 3, but only if connected to paths."""
    for building in buildings:
        # Get building properties
        building_pos = building['position']
        building_size_px = building_sizes[building['size']]
        
        # Determine likely door position - usually at the bottom center of the building
        door_x = building_pos[0] + building_size_px // 2
        door_y = building_pos[1] + building_size_px  # Bottom center
        
        # Check if the bottom of the building is near water
        # If so, likely the door is on one of the other sides
        bottom_water = False
        for dx in range(-tile_size, tile_size * 2, tile_size):
            check_pos = (door_x + dx, door_y)
            if check_pos in water_positions:
                bottom_water = True
                break
                
        if bottom_water:
            # Try other sides - left, right, then top
            left_side_valid = True
            for dy in range(-tile_size, tile_size * 2, tile_size):
                check_pos = (building_pos[0], building_pos[1] + building_size_px // 2 + dy)
                if check_pos in water_positions:
                    left_side_valid = False
                    break
                    
            if left_side_valid:
                # Door likely on left side
                door_x = building_pos[0]
                door_y = building_pos[1] + building_size_px // 2
            else:
                # Check right side
                right_side_valid = True
                for dy in range(-tile_size, tile_size * 2, tile_size):
                    check_pos = (building_pos[0] + building_size_px, building_pos[1] + building_size_px // 2 + dy)
                    if check_pos in water_positions:
                        right_side_valid = False
                        break
                        
                if right_side_valid:
                    # Door likely on right side
                    door_x = building_pos[0] + building_size_px
                    door_y = building_pos[1] + building_size_px // 2
                else:
                    # Door likely on top side
                    door_x = building_pos[0] + building_size_px // 2
                    door_y = building_pos[1]
        
        # FIX: Look for adjacent paths to place the door near
        door_placed = False
        
        # Only check cardinal directions (not diagonals)
        for neighbor_pos in utils.get_neighbors(door_x, door_y, tile_size, include_self=False):
            if neighbor_pos in path_positions:
                # Update door position to be near path
                door_x, door_y = neighbor_pos
                door_placed = True
                break
        
        # FIX: Only update grass tiles if they're connected to a path
        has_adjacent_path = False
        for neighbor_pos in utils.get_neighbors(door_x, door_y, tile_size, include_self=False):
            if neighbor_pos in path_positions:
                has_adjacent_path = True
                break
                
        if not has_adjacent_path:
            continue  # Skip this door if it doesn't connect to a path
        
        # Update grass tiles around the door to variant 3
        for neighbor_pos in utils.get_neighbors(door_x, door_y, tile_size, include_self=True):
            # Skip if out of bounds
            if not utils.is_in_bounds(neighbor_pos[0], neighbor_pos[1], grid_size):
                continue
            
            # Skip if not grass, a path, or water
            if (neighbor_pos not in terrain or 
                terrain[neighbor_pos]['type'] != 'grass' or 
                neighbor_pos in path_positions or 
                neighbor_pos in water_positions):
                continue
            
            # Update grass to variant 3
            terrain[neighbor_pos]['variant'] = 3  # Building entrance grass


def connect_door_to_path(paths, door_pos, closest_path, water_positions, path_positions, grid_size, tile_size):
    """
    Create a path connecting a building door to the nearest existing path.
    Ensures all path connections have proper adjacency (no diagonal-only connections).
    
    Args:
        paths: List of path dictionaries to append new paths to
        door_pos: Position of the building door/entrance
        closest_path: Position of the nearest existing path
        water_positions: Set of water positions to avoid
        path_positions: Set of existing path positions
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
    """
    # Queue for breadth-first search - prioritize cardinal directions first
    # Each item is (position, path_so_far, is_diagonal_move)
    queue = [(door_pos, [], False)]
    visited = {door_pos}
    
    # Define directions - CARDINAL FIRST for more natural-looking paths
    # This ordering is important to prioritize non-diagonal connections
    directions = [
        (0, -tile_size),  # North
        (tile_size, 0),   # East
        (0, tile_size),   # South
        (-tile_size, 0),  # West
        # Only consider diagonals if no cardinal direction works
        (tile_size, -tile_size),  # Northeast
        (tile_size, tile_size),   # Southeast
        (-tile_size, tile_size),  # Southwest
        (-tile_size, -tile_size)  # Northwest
    ]
    
    while queue:
        (x, y), path_so_far, is_diagonal = queue.pop(0)
        current_pos = (x, y)
        
        # Check if we reached an existing path that's not the door
        if current_pos in path_positions and current_pos != door_pos:
            # If we made a diagonal move in the last step and this is not a cardinal connection
            # to the existing path, add an extra path tile to ensure proper adjacency
            if is_diagonal:
                # Check if we need to add an extra path to ensure cardinal adjacency
                needs_adjacency_fix = True
                
                # Check if current position has cardinal adjacency to the previous position
                prev_pos = path_so_far[-1] if path_so_far else door_pos
                
                # If previous position is cardinally adjacent, no fix needed
                if (prev_pos[0] == x and abs(prev_pos[1] - y) == tile_size) or \
                   (prev_pos[1] == y and abs(prev_pos[0] - x) == tile_size):
                    needs_adjacency_fix = False
                
                if needs_adjacency_fix and path_so_far:
                    # Insert an additional path to ensure cardinal adjacency
                    # We have two options: either go horizontal first, then vertical,
                    # or vertical first, then horizontal
                    prev_pos = path_so_far[-1]
                    
                    # Try horizontal first
                    horizontal_pos = (x, prev_pos[1])
                    if horizontal_pos not in water_positions and horizontal_pos not in visited:
                        path_so_far.append(horizontal_pos)
                    else:
                        # Try vertical first
                        vertical_pos = (prev_pos[0], y)
                        if vertical_pos not in water_positions and vertical_pos not in visited:
                            path_so_far.append(vertical_pos)
            
            # Add all positions along the path to the path list
            for pos in path_so_far:
                if pos not in path_positions:
                    paths.append({
                        'position': pos,
                        'variant': 1  # Dirt path
                    })
                    path_positions.add(pos)
            return True
        
        # Try each direction - cardinal directions first
        for i, (dx, dy) in enumerate(directions):
            next_x, next_y = x + dx, y + dy
            next_pos = (next_x, next_y)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(next_x, next_y, grid_size):
                continue
            
            # Skip if it's water
            if next_pos in water_positions:
                continue
            
            # Skip if already visited in this search
            if next_pos in visited:
                continue
            
            # Mark as diagonal if using diagonal directions (last 4 in our list)
            is_diagonal_move = i >= 4
            
            # Add to queue
            visited.add(next_pos)
            new_path = path_so_far + [next_pos]
            queue.append((next_pos, new_path, is_diagonal_move))
    
    # If BFS failed, fall back to a simple L-shaped path
    create_direct_path_with_cardinal_adjacency(paths, door_pos, closest_path, water_positions, path_positions, grid_size, tile_size)
    return False


# 2. New helper function for creating L-shaped paths with guaranteed cardinal adjacency

def create_direct_path_with_cardinal_adjacency(paths, start_pos, end_pos, water_positions, path_positions, grid_size, tile_size):
    """
    Create a direct L-shaped path from start to end, avoiding water and ensuring cardinal adjacency.
    
    Args:
        paths: List of path dictionaries to append new paths to
        start_pos: Starting position for the path
        end_pos: Ending position for the path
        water_positions: Set of water positions to avoid
        path_positions: Set of existing path positions
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
    """
    start_x, start_y = start_pos
    end_x, end_y = end_pos
    
    # Determine if we should go horizontally or vertically first
    # This is a design choice - you could implement different strategies
    horizontal_first = random.choice([True, False])
    
    # Add current position to the path if not already a path
    if start_pos not in path_positions:
        paths.append({
            'position': start_pos,
            'variant': 1  # Dirt path
        })
        path_positions.add(start_pos)
    
    # Create path using L-shape (always with cardinal connections)
    current_x, current_y = start_x, start_y
    
    if horizontal_first:
        # Move horizontally first
        dx = tile_size if end_x > current_x else -tile_size if end_x < current_x else 0
        
        while current_x != end_x and dx != 0:
            next_x = current_x + dx
            next_pos = (next_x, current_y)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(next_x, current_y, grid_size):
                break
            
            # Skip water or find detour
            if next_pos in water_positions:
                # Try to find a detour around water
                detour_found = False
                for detour_offset in [tile_size, -tile_size]:
                    detour_y = current_y + detour_offset
                    detour_pos = (current_x, detour_y)
                    next_detour_pos = (next_x, detour_y)
                    
                    # Check if detour is valid
                    if (utils.is_in_bounds(current_x, detour_y, grid_size) and 
                        utils.is_in_bounds(next_x, detour_y, grid_size) and
                        detour_pos not in water_positions and 
                        next_detour_pos not in water_positions):
                        
                        # Add detour path
                        if detour_pos not in path_positions:
                            paths.append({
                                'position': detour_pos,
                                'variant': 1  # Dirt path
                            })
                            path_positions.add(detour_pos)
                        
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
            if next_pos not in path_positions:
                paths.append({
                    'position': next_pos,
                    'variant': 1  # Dirt path
                })
                path_positions.add(next_pos)
        
        # Then move vertically
        dy = tile_size if end_y > current_y else -tile_size if end_y < current_y else 0
        
        while current_y != end_y and dy != 0:
            next_y = current_y + dy
            next_pos = (current_x, next_y)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(current_x, next_y, grid_size):
                break
            
            # Skip water or find detour
            if next_pos in water_positions:
                # Try to find a detour around water
                detour_found = False
                for detour_offset in [tile_size, -tile_size]:
                    detour_x = current_x + detour_offset
                    detour_pos = (detour_x, current_y)
                    next_detour_pos = (detour_x, next_y)
                    
                    # Check if detour is valid
                    if (utils.is_in_bounds(detour_x, current_y, grid_size) and 
                        utils.is_in_bounds(detour_x, next_y, grid_size) and
                        detour_pos not in water_positions and 
                        next_detour_pos not in water_positions):
                        
                        # Add detour path
                        if detour_pos not in path_positions:
                            paths.append({
                                'position': detour_pos,
                                'variant': 1  # Dirt path
                            })
                            path_positions.add(detour_pos)
                        
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
            if next_pos not in path_positions:
                paths.append({
                    'position': next_pos,
                    'variant': 1  # Dirt path
                })
                path_positions.add(next_pos)
    else:
        # Move vertically first, then horizontally
        # (Implementation similar to above but with directions reversed)
        dy = tile_size if end_y > current_y else -tile_size if end_y < current_y else 0
        
        while current_y != end_y and dy != 0:
            next_y = current_y + dy
            next_pos = (current_x, next_y)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(current_x, next_y, grid_size):
                break
            
            # Skip water or find detour
            if next_pos in water_positions:
                # Try to find a detour around water
                detour_found = False
                for detour_offset in [tile_size, -tile_size]:
                    detour_x = current_x + detour_offset
                    detour_pos = (detour_x, current_y)
                    next_detour_pos = (detour_x, next_y)
                    
                    # Check if detour is valid
                    if (utils.is_in_bounds(detour_x, current_y, grid_size) and 
                        utils.is_in_bounds(detour_x, next_y, grid_size) and
                        detour_pos not in water_positions and 
                        next_detour_pos not in water_positions):
                        
                        # Add detour path
                        if detour_pos not in path_positions:
                            paths.append({
                                'position': detour_pos,
                                'variant': 1  # Dirt path
                            })
                            path_positions.add(detour_pos)
                        
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
            if next_pos not in path_positions:
                paths.append({
                    'position': next_pos,
                    'variant': 1  # Dirt path
                })
                path_positions.add(next_pos)
        
        # Then move horizontally
        dx = tile_size if end_x > current_x else -tile_size if end_x < current_x else 0
        
        while current_x != end_x and dx != 0:
            next_x = current_x + dx
            next_pos = (next_x, current_y)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(next_x, current_y, grid_size):
                break
            
            # Skip water or find detour
            if next_pos in water_positions:
                # Try to find a detour around water
                detour_found = False
                for detour_offset in [tile_size, -tile_size]:
                    detour_y = current_y + detour_offset
                    detour_pos = (current_x, detour_y)
                    next_detour_pos = (next_x, detour_y)
                    
                    # Check if detour is valid
                    if (utils.is_in_bounds(current_x, detour_y, grid_size) and 
                        utils.is_in_bounds(next_x, detour_y, grid_size) and
                        detour_pos not in water_positions and 
                        next_detour_pos not in water_positions):
                        
                        # Add detour path
                        if detour_pos not in path_positions:
                            paths.append({
                                'position': detour_pos,
                                'variant': 1  # Dirt path
                            })
                            path_positions.add(detour_pos)
                        
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
            if next_pos not in path_positions:
                paths.append({
                    'position': next_pos,
                    'variant': 1  # Dirt path
                })
                path_positions.add(next_pos)


# 3. Improved path validation function to enforce cardinal adjacency

def validate_path_adjacency(paths, grid_size, tile_size):
    """
    Validate and fix path adjacency, ensuring all paths have proper cardinal connections.
    
    Args:
        paths: List of path dictionaries
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        
    Returns:
        List of validated paths
    """
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    result_paths = list(paths)  # Make a copy to avoid modifying during iteration
    new_paths = []
    
    # First pass: identify any paths with only diagonal connections
    for path in paths:
        x, y = path['position']
        
        # Check cardinal directions (N, E, S, W)
        cardinal_neighbors = [
            (x, y - tile_size),  # North
            (x + tile_size, y),  # East
            (x, y + tile_size),  # South
            (x - tile_size, y)   # West
        ]
        
        # Count adjacent paths in cardinal directions
        cardinal_adjacent = sum(1 for pos in cardinal_neighbors if pos in path_positions)
        
        # If no cardinal connections but has diagonal neighbors, add connecting paths
        if cardinal_adjacent == 0:
            # Check diagonal directions
            diagonal_neighbors = [
                (x - tile_size, y - tile_size),  # NW
                (x + tile_size, y - tile_size),  # NE
                (x - tile_size, y + tile_size),  # SW
                (x + tile_size, y + tile_size)   # SE
            ]
            
            diagonal_connections = []
            for i, diag_pos in enumerate(diagonal_neighbors):
                if diag_pos in path_positions:
                    diagonal_connections.append((i, diag_pos))
            
            # Fix each diagonal connection by adding a cardinal connection
            for i, diag_pos in diagonal_connections:
                if i == 0:  # NW diagonal
                    # Try north first, then west
                    if (x, y - tile_size) not in path_positions and utils.is_in_bounds(x, y - tile_size, grid_size):
                        new_paths.append({
                            'position': (x, y - tile_size),
                            'variant': path['variant']
                        })
                        path_positions.add((x, y - tile_size))
                    elif (x - tile_size, y) not in path_positions and utils.is_in_bounds(x - tile_size, y, grid_size):
                        new_paths.append({
                            'position': (x - tile_size, y),
                            'variant': path['variant']
                        })
                        path_positions.add((x - tile_size, y))
                elif i == 1:  # NE diagonal
                    # Try north first, then east
                    if (x, y - tile_size) not in path_positions and utils.is_in_bounds(x, y - tile_size, grid_size):
                        new_paths.append({
                            'position': (x, y - tile_size),
                            'variant': path['variant']
                        })
                        path_positions.add((x, y - tile_size))
                    elif (x + tile_size, y) not in path_positions and utils.is_in_bounds(x + tile_size, y, grid_size):
                        new_paths.append({
                            'position': (x + tile_size, y),
                            'variant': path['variant']
                        })
                        path_positions.add((x + tile_size, y))
                elif i == 2:  # SW diagonal
                    # Try south first, then west
                    if (x, y + tile_size) not in path_positions and utils.is_in_bounds(x, y + tile_size, grid_size):
                        new_paths.append({
                            'position': (x, y + tile_size),
                            'variant': path['variant']
                        })
                        path_positions.add((x, y + tile_size))
                    elif (x - tile_size, y) not in path_positions and utils.is_in_bounds(x - tile_size, y, grid_size):
                        new_paths.append({
                            'position': (x - tile_size, y),
                            'variant': path['variant']
                        })
                        path_positions.add((x - tile_size, y))
                else:  # SE diagonal
                    # Try south first, then east
                    if (x, y + tile_size) not in path_positions and utils.is_in_bounds(x, y + tile_size, grid_size):
                        new_paths.append({
                            'position': (x, y + tile_size),
                            'variant': path['variant']
                        })
                        path_positions.add((x, y + tile_size))
                    elif (x + tile_size, y) not in path_positions and utils.is_in_bounds(x + tile_size, y, grid_size):
                        new_paths.append({
                            'position': (x + tile_size, y),
                            'variant': path['variant']
                        })
                        path_positions.add((x + tile_size, y))
    
    # Add all new connecting paths
    result_paths.extend(new_paths)
    
    # Second pass: verify all paths now have proper adjacency
    # Optionally, add checks to ensure the final path network looks good
    
    return result_paths


# 4. Modified generate_village function to use the improved path validation

def generate_village(size, assets, tile_size=32):
    """Generate a procedural village with buildings, roads, and paths.
    
    Args:
        size: Base size parameter (will be scaled up)
        assets: Dictionary of game assets
        tile_size: Size of each tile in pixels
        
    Returns:
        Dictionary containing complete village data
    """
    # First, generate the landscape
    landscape = landscape_generator.generate_landscape(size, tile_size)
    
    # Extract landscape components
    grid_size = landscape['size']
    terrain = landscape['terrain']
    water = landscape['water']
    water_positions = landscape['water_positions']
    trees = landscape['trees']
    
    # Create additional village components
    bridges = []
    buildings = []
    paths = []
    
    print(f"Building village on landscape with size {grid_size}x{grid_size} pixels...")
    
    # Create a village layout based on the water feature
    # First, plan the main roads and paths around the water
    create_village_layout(paths, water_positions, grid_size, tile_size)
    
    # Convert path positions to a set for quick checking
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Place buildings with appropriate types based on proximity to water and village center
    target_building_count = int(size * 0.5)  # Scale with village size
    
    # Define building sizes for lookup
    building_sizes = {
        "large": 3 * tile_size,  # 3 tiles
        "medium": 2 * tile_size, # 2 tiles
        "small": 1 * tile_size   # 1 tile
    }
    
    place_buildings_by_zones(buildings, paths, water_positions, path_positions, 
                            grid_size, tile_size, assets, building_sizes, target_building_count, terrain)
    
    # Connect buildings to paths with proper adjacency
    connect_buildings_to_paths(buildings, paths, water_positions, grid_size, tile_size)
    
    # NEW: Validate all paths to ensure proper adjacency
    paths = validate_path_adjacency(paths, grid_size, tile_size)
    
    # FIX 1: Ensure path adjacency (no diagonal-only connections)
    paths = ensure_path_adjacency(paths, grid_size, tile_size)
    
    # FIX 2: Remove isolated paths (paths with fewer than 2 adjacent path neighbors)
    paths = remove_isolated_paths(paths, grid_size, tile_size)
    
    # Update path_positions after fixing paths
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Update grass near building entrances and ensure they connect to paths
    update_grass_near_building_entrances(terrain, buildings, building_sizes, grid_size, 
                                        tile_size, water_positions, path_positions)
    
    # FIX 3: Ensure grass type 2 is properly around water
    fix_grass_around_water(terrain, water_positions, grid_size, tile_size)
    
    # Add bridges where paths cross water
    bridges = landscape_generator.add_bridges_at_path_water_intersections(terrain, water, paths, grid_size, tile_size, assets)
    
    # Print some stats about the village
    print(f"Village generation complete! {len(buildings)} buildings, {len(paths)} path tiles, {len(bridges)} bridges")
    
    paths = fix_path_issues(paths, buildings, grid_size, tile_size, water_positions)
    # Return the complete village data
    return {
        'size': grid_size,
        'terrain': terrain,
        'buildings': buildings,
        'trees': trees,
        'paths': paths,
        'water': water,
        'bridges': bridges
    }            

def scanmap(grid_size, tile_size, pattern_check_fn, fix_fn):
    """
    Scan the entire map for a specific 2x2 pattern and apply a fix function when found.
    
    Args:
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        pattern_check_fn: Function that checks if a 2x2 pattern matches. 
                         Takes (x, y, items) where items is a dict with keys 'tl', 'tr', 'bl', 'br'
        fix_fn: Function to call when pattern is found. Takes (x, y, items) and returns any modifications.
    
    Returns:
        Number of fixes applied
    """
    fixes_applied = 0
    
    # Scan the entire map in tile-sized steps
    for y in range(0, grid_size - tile_size, tile_size):
        for x in range(0, grid_size - tile_size, tile_size):
            # Extract the 2x2 grid at this position
            items = {
                'tl': (x, y),                    # Top-left
                'tr': (x + tile_size, y),        # Top-right
                'bl': (x, y + tile_size),        # Bottom-left
                'br': (x + tile_size, y + tile_size)  # Bottom-right
            }
            
            # Check if this pattern matches
            if pattern_check_fn(x, y, items):
                # Apply fix if pattern matches
                if fix_fn(x, y, items):
                    fixes_applied += 1
    
    return fixes_applied


def replace_diagonal(paths, path_positions, new_position, variant=1):
    """
    Replace a diagonal path connection with a proper cardinal connection.
    
    Args:
        paths: List of path dictionaries to modify
        path_positions: Set of existing path positions
        new_position: Position to add a new path tile
        variant: Path variant to use (default: 1)
        
    Returns:
        Boolean indicating if a path was added
    """
    # Check if position already has a path
    if new_position in path_positions:
        return False
    
    # Add the new path
    paths.append({
        'position': new_position,
        'variant': variant
    })
    path_positions.add(new_position)
    return True


def fix_diagonal_paths(paths, grid_size, tile_size, water_positions=None):
    """
    Fix all diagonal path connections in the map by ensuring they have proper cardinal adjacency.
    
    Args:
        paths: List of path dictionaries to modify
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        water_positions: Set of water positions to avoid (optional)
    
    Returns:
        Updated paths list
    """
    # Create a set of path positions for quick lookup
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Keep track of total fixes
    total_fixes = 0
    
    # Run multiple scans for different diagonal patterns
    # We'll do this in multiple passes until no more fixes are needed or max passes reached
    max_passes = 3  # Limit to prevent infinite loop
    current_pass = 0
    fixes_in_pass = 1  # Initialize to enter the loop
    
    while fixes_in_pass > 0 and current_pass < max_passes:
        current_pass += 1
        fixes_in_pass = 0
        
        # Pattern 1: Path in top-left and bottom-right, but not top-right or bottom-left
        # [P][_]
        # [_][P]
        def pattern1_check(x, y, items):
            tl, tr, bl, br = items['tl'], items['tr'], items['bl'], items['br']
            return (tl in path_positions and br in path_positions and 
                   tr not in path_positions and bl not in path_positions)
        
        def pattern1_fix(x, y, items):
            # Choose which cardinal connection to add based on water
            tl, tr, bl, br = items['tl'], items['tr'], items['bl'], items['br']
            
            # Prefer top-right if not water, otherwise bottom-left
            if water_positions is None or tr not in water_positions:
                return replace_diagonal(paths, path_positions, tr)
            elif bl not in water_positions:
                return replace_diagonal(paths, path_positions, bl)
            # If both are water, don't add a path
            return False
        
        # Pattern 2: Path in top-right and bottom-left, but not top-left or bottom-right
        # [_][P]
        # [P][_]
        def pattern2_check(x, y, items):
            tl, tr, bl, br = items['tl'], items['tr'], items['bl'], items['br']
            return (tr in path_positions and bl in path_positions and 
                   tl not in path_positions and br not in path_positions)
        
        def pattern2_fix(x, y, items):
            # Choose which cardinal connection to add based on water
            tl, tr, bl, br = items['tl'], items['tr'], items['bl'], items['br']
            
            # Prefer top-left if not water, otherwise bottom-right
            if water_positions is None or tl not in water_positions:
                return replace_diagonal(paths, path_positions, tl)
            elif br not in water_positions:
                return replace_diagonal(paths, path_positions, br)
            # If both are water, don't add a path
            return False
        
        # Scan for both patterns
        fixes_in_pattern1 = scanmap(grid_size, tile_size, pattern1_check, pattern1_fix)
        fixes_in_pattern2 = scanmap(grid_size, tile_size, pattern2_check, pattern2_fix)
        
        fixes_in_pass = fixes_in_pattern1 + fixes_in_pattern2
        
        # Update total fixes
        total_fixes += fixes_in_pass
        
        print(f"Pass {current_pass}: Fixed {fixes_in_pass} diagonal path connections")
    
    print(f"Total diagonal path fixes: {total_fixes}")
    return paths


def ensure_building_path_connections(buildings, paths, grid_size, tile_size, water_positions=None):
    """
    Ensure all buildings have at least one cardinal path connection.
    
    Args:
        buildings: List of building dictionaries
        paths: List of path dictionaries
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        water_positions: Set of water positions to avoid (optional)
    
    Returns:
        Updated paths list
    """
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    buildings_connected = 0
    
    for building in buildings:
        building_pos = building['position']
        building_size_name = building['size']
        
        # Convert size name to pixel size
        building_size_px = 3 * tile_size if building_size_name == 'large' else (
                          2 * tile_size if building_size_name == 'medium' else tile_size)
        
        # Calculate footprint size in tiles
        footprint_tiles = building_size_px // tile_size
        
        # Check if building already has a cardinal path connection
        has_cardinal_connection = False
        
        # Check all sides of the building
        for x in range(footprint_tiles):
            # Check top edge
            if (building_pos[0] + x * tile_size, building_pos[1] - tile_size) in path_positions:
                has_cardinal_connection = True
                break
                
            # Check bottom edge
            if (building_pos[0] + x * tile_size, building_pos[1] + footprint_tiles * tile_size) in path_positions:
                has_cardinal_connection = True
                break
        
        for y in range(footprint_tiles):
            # Check left edge
            if (building_pos[0] - tile_size, building_pos[1] + y * tile_size) in path_positions:
                has_cardinal_connection = True
                break
                
            # Check right edge
            if (building_pos[0] + footprint_tiles * tile_size, building_pos[1] + y * tile_size) in path_positions:
                has_cardinal_connection = True
                break
        
        # If no cardinal connection, add one
        if not has_cardinal_connection:
            # Find the nearest path
            nearest_path = None
            min_distance = float('inf')
            
            for path in paths:
                path_pos = path['position']
                dx = path_pos[0] - (building_pos[0] + building_size_px // 2)
                dy = path_pos[1] - (building_pos[1] + building_size_px // 2)
                distance = dx*dx + dy*dy  # Use square distance to avoid sqrt
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_path = path_pos
            
            if nearest_path:
                # Determine which side of the building to connect from
                center_x = building_pos[0] + building_size_px // 2
                center_y = building_pos[1] + building_size_px // 2
                
                # Calculate which side is closest to the nearest path
                distances = [
                    (abs(center_y - (building_pos[1] + building_size_px) - nearest_path[1]), 'bottom'),
                    (abs(center_x - (building_pos[0] + building_size_px) - nearest_path[0]), 'right'),
                    (abs(center_y - building_pos[1] - nearest_path[1]), 'top'),
                    (abs(center_x - building_pos[0] - nearest_path[0]), 'left')
                ]
                
                # Sort by distance (closest first)
                distances.sort()
                
                # Try sides in order of closest to nearest path
                for _, side in distances:
                    if side == 'bottom':
                        door_pos = (center_x, building_pos[1] + building_size_px)
                    elif side == 'right':
                        door_pos = (building_pos[0] + building_size_px, center_y)
                    elif side == 'top':
                        door_pos = (center_x, building_pos[1] - tile_size)
                    else:  # left
                        door_pos = (building_pos[0] - tile_size, center_y)
                    
                    # Skip if door position is in water
                    if water_positions and door_pos in water_positions:
                        continue
                    
                    # Create a cardinal path from door to nearest path
                    create_cardinal_path(paths, path_positions, door_pos, nearest_path, grid_size, tile_size, water_positions)
                    buildings_connected += 1
                    break
    
    print(f"Connected {buildings_connected} buildings to path network")
    return paths


def create_cardinal_path(paths, path_positions, start_pos, end_pos, grid_size, tile_size, water_positions=None):
    """
    Create a path between two points using strictly cardinal connections.
    
    Args:
        paths: List of path dictionaries to modify
        path_positions: Set of existing path positions
        start_pos: Starting position of the path
        end_pos: Ending position of the path
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        water_positions: Set of water positions to avoid (optional)
    """
    # Add starting position if it's not already a path
    if start_pos not in path_positions:
        paths.append({
            'position': start_pos,
            'variant': 1
        })
        path_positions.add(start_pos)
    
    # If end_pos is already connected to start_pos (through other paths),
    # no need to create a new path
    if start_pos == end_pos:
        return
    
    # Get starting and ending coordinates
    start_x, start_y = start_pos
    end_x, end_y = end_pos
    
    # Current position
    current_x, current_y = start_x, start_y
    
    # Use a hybrid L-shaped approach: go horizontally first, then vertically
    # We'll limit the maximum number of steps to prevent infinite loops
    max_steps = int((grid_size / tile_size) * 2)  # Should be more than enough
    steps_taken = 0
    
    # Step horizontally until we're aligned with the target on x-axis
    while current_x != end_x and steps_taken < max_steps:
        steps_taken += 1
        step_x = tile_size if end_x > current_x else -tile_size
        next_x = current_x + step_x
        next_pos = (next_x, current_y)
        
        # Skip if out of bounds
        if not (0 <= next_x < grid_size):
            break
        
        # Skip if water and we care about water
        if water_positions and next_pos in water_positions:
            # Try going around vertically
            detour_found = False
            
            # Try up and down
            for detour_offset in [tile_size, -tile_size]:
                detour_y = current_y + detour_offset
                detour_pos = (current_x, detour_y)
                
                if (0 <= detour_y < grid_size and 
                    (water_positions is None or detour_pos not in water_positions)):
                    
                    # Add detour path if needed
                    if detour_pos not in path_positions:
                        paths.append({
                            'position': detour_pos,
                            'variant': 1
                        })
                        path_positions.add(detour_pos)
                    
                    # Update current position
                    current_y = detour_y
                    detour_found = True
                    break
            
            # If both detours fail, give up on horizontal movement
            if not detour_found:
                break
        else:
            # Add path at next position if needed
            if next_pos not in path_positions:
                paths.append({
                    'position': next_pos,
                    'variant': 1
                })
                path_positions.add(next_pos)
            
            # Update current position
            current_x = next_x
    
    # Now move vertically until we reach the target y-axis
    while current_y != end_y and steps_taken < max_steps:
        steps_taken += 1
        step_y = tile_size if end_y > current_y else -tile_size
        next_y = current_y + step_y
        next_pos = (current_x, next_y)
        
        # Skip if out of bounds
        if not (0 <= next_y < grid_size):
            break
        
        # Skip if water and we care about water
        if water_positions and next_pos in water_positions:
            # Try going around horizontally
            detour_found = False
            
            # Try left and right
            for detour_offset in [tile_size, -tile_size]:
                detour_x = current_x + detour_offset
                detour_pos = (detour_x, current_y)
                
                if (0 <= detour_x < grid_size and 
                    (water_positions is None or detour_pos not in water_positions)):
                    
                    # Add detour path if needed
                    if detour_pos not in path_positions:
                        paths.append({
                            'position': detour_pos,
                            'variant': 1
                        })
                        path_positions.add(detour_pos)
                    
                    # Update current position
                    current_x = detour_x
                    detour_found = True
                    break
            
            # If both detours fail, give up on vertical movement
            if not detour_found:
                break
        else:
            # Add path at next position if needed
            if next_pos not in path_positions:
                paths.append({
                    'position': next_pos,
                    'variant': 1
                })
                path_positions.add(next_pos)
            
            # Update current position
            current_y = next_y


def fix_path_issues(paths, buildings, grid_size, tile_size, water_positions=None):
    """
    Fix all path issues in one go - diagonal paths and disconnected buildings.
    
    Args:
        paths: List of path dictionaries
        buildings: List of building dictionaries
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        water_positions: Set of water positions to avoid (optional)
        
    Returns:
        Updated paths with all issues fixed
    """
    print("Fixing path issues...")
    
    # First, ensure all buildings have path connections
    paths = ensure_building_path_connections(buildings, paths, grid_size, tile_size, water_positions)
    
    # Then, fix any diagonal-only path connections
    paths = fix_diagonal_paths(paths, grid_size, tile_size, water_positions)
    
    # Finally, do a final verification pass to make sure we haven't introduced any new issues
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Verify all paths have at least one cardinal neighbor
    isolated_paths = []
    
    for path in paths:
        x, y = path['position']
        cardinal_neighbors = [
            (x, y - tile_size),      # North
            (x + tile_size, y),      # East
            (x, y + tile_size),      # South
            (x - tile_size, y)       # West
        ]
        
        # Count cardinal neighbors that are paths
        cardinal_count = sum(1 for pos in cardinal_neighbors if pos in path_positions)
        
        # If no cardinal neighbors, mark for removal
        if cardinal_count == 0:
            isolated_paths.append(path)
    
    # Remove truly isolated paths
    for path in isolated_paths:
        paths.remove(path)
    
    if isolated_paths:
        print(f"Removed {len(isolated_paths)} isolated paths")
    
    return paths