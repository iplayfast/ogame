import random
import math
import utils
from village_base import (
    EMPTY, GRASS_1, GRASS_2, GRASS_3, WATER, 
    PATH_1, PATH_2, TREE_1, TREE_2, TREE_3, TREE_4, TREE_5,
    BUILDING, is_water, is_path, is_tree, is_grass, is_building
)

def generate_landscape(village):
    """Generate the natural landscape: terrain, water features, etc.
    
    Args:
        village: Village instance
        
    Returns:
        Dictionary with updated landscape components
    """
    print("Generating landscape...")
    
    # Place grass type 1 everywhere as base
    for y in range(village.grid_height):
        for x in range(village.grid_width):
            village.terrain_grid[y][x] = GRASS_1
    
    # Add a water feature (lake, river, or lake with river)
    water_type = random.choice(["lake", "river", "lake_with_river"])
    
    # First, create grass type 2 around where water will be
    water_edge_positions = create_water_feature_edges(village, water_type)
    
    # Update terrain with grass type 2 around water
    for x, y in water_edge_positions:
        grid_x, grid_y = x // village.tile_size, y // village.tile_size
        # Only update if in bounds and not already water
        if (0 <= grid_x < village.grid_width and 
            0 <= grid_y < village.grid_height and
            not is_water(village.terrain_grid[grid_y][grid_x])):
            village.terrain_grid[grid_y][grid_x] = GRASS_2
    
    # Then create the actual water
    create_water_feature(village, water_type)
    
    # Ensure grass type 2 is properly around water
    update_grass_near_water(village)
    
    print(f"Landscape generation complete! {len(village.water_positions)} water tiles")
    
    # Return the updated components
    return {
        'water_positions': village.water_positions
    }

def create_water_feature_edges(village, water_type):
    """Create edges around where a water feature will be placed.
    
    Args:
        village: Village instance
        water_type: Type of water feature ("lake", "river", or "lake_with_river")
        
    Returns:
        Set of positions that should have grass type 2 (near water)
    """
    edge_positions = set()
    center_x, center_y = village.grid_size // 2, village.grid_size // 2
    
    # Lake variables that will be used for both lake and river, if needed
    lake_center_x, lake_center_y = center_x, center_y
    lake_radius = village.grid_size // 8
    
    # Handle lake creation
    if water_type in ["lake", "lake_with_river"]:
        # Create a large lake near the center
        lake_center_x = center_x + random.randint(-village.grid_size//10, village.grid_size//10)
        lake_center_y = center_y + random.randint(-village.grid_size//10, village.grid_size//10)
        
        # Larger, more irregular lake
        irregularity = 0.3  # 0.0 = perfect circle, 1.0 = very irregular
        
        # Generate wobble points for the irregular shape
        wobble_points = utils.generate_points_in_irregular_shape(
            lake_center_x, lake_center_y, 
            lake_radius + village.tile_size, 
            irregularity
        )
        
        # Find the bounds of the shape
        min_x = min(p[0] for p in wobble_points) - village.tile_size * 2
        max_x = max(p[0] for p in wobble_points) + village.tile_size * 2
        min_y = min(p[1] for p in wobble_points) - village.tile_size * 2
        max_y = max(p[1] for p in wobble_points) + village.tile_size * 2
        
        # Process grid positions within the bounding box
        for y in range(int(min_y), int(max_y), village.tile_size):
            for x in range(int(min_x), int(max_x), village.tile_size):
                # Align to grid
                grid_x, grid_y = utils.align_to_grid(x, y, village.tile_size)
                
                # Check if point is inside or near the lake shape
                center_x = grid_x + village.tile_size // 2
                center_y = grid_y + village.tile_size // 2
                
                if utils.is_point_in_shape(
                    center_x, center_y, 
                    wobble_points, lake_center_x, lake_center_y
                ):
                    # This will be water later, not adding to edge now
                    continue
                    
                # Check if this point is adjacent to the water shape
                is_adjacent = False
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue
                            
                        test_x = center_x + dx * village.tile_size
                        test_y = center_y + dy * village.tile_size
                        
                        if utils.is_point_in_shape(
                            test_x, test_y,
                            wobble_points, lake_center_x, lake_center_y
                        ):
                            is_adjacent = True
                            break
                    
                    if is_adjacent:
                        break
                
                if is_adjacent:
                    edge_positions.add((grid_x, grid_y))
    
    # Handle river creation
    if water_type in ["river", "lake_with_river"]:
        # Create a winding river
        river_width = random.randint(3, 5)  # tiles
        
        # Determine river endpoints
        if water_type == "river":
            # River crossing the whole map
            start_x = 0
            start_y = random.randint(village.grid_size//4, 3*village.grid_size//4)
            end_x = village.grid_size
            end_y = random.randint(village.grid_size//4, 3*village.grid_size//4)
        else:
            # River flowing into the lake
            # Decide river direction (into the lake)
            edge_options = ["top", "right", "bottom", "left"]
            river_edge = random.choice(edge_options)
            
            # Set river start and end points based on edge
            if river_edge == "top":
                start_x = random.randint(village.grid_size//4, 3*village.grid_size//4)
                start_y = 0
                end_x = lake_center_x
                end_y = lake_center_y - lake_radius
            elif river_edge == "right":
                start_x = village.grid_size
                start_y = random.randint(village.grid_size//4, 3*village.grid_size//4)
                end_x = lake_center_x + lake_radius
                end_y = lake_center_y
            elif river_edge == "bottom":
                start_x = random.randint(village.grid_size//4, 3*village.grid_size//4)
                start_y = village.grid_size
                end_x = lake_center_x
                end_y = lake_center_y + lake_radius
            else:  # left
                start_x = 0
                start_y = random.randint(village.grid_size//4, 3*village.grid_size//4)
                end_x = lake_center_x - lake_radius
                end_y = lake_center_y
        
        # Generate river waypoints for a natural look
        waypoints = generate_river_waypoints(village, start_x, start_y, end_x, end_y)
        
        # Process river segments between waypoints
        for i in range(len(waypoints) - 1):
            p1 = waypoints[i]
            p2 = waypoints[i+1]
            
            # Calculate segment properties
            segment_dx = p2[0] - p1[0]
            segment_dy = p2[1] - p1[1]
            segment_length = utils.calculate_distance(p1[0], p1[1], p2[0], p2[1])
            
            if segment_length == 0:
                continue
                
            # Use half-tile steps for smoother river
            steps = int(segment_length / (village.tile_size / 2))
            steps = max(1, steps)  # Ensure at least one step
            
            for step in range(steps + 1):
                # Position along line
                t = step / steps
                x = int(p1[0] + segment_dx * t)
                y = int(p1[1] + segment_dy * t)
                
                # Define perpendicular vector
                if segment_length > 0:
                    perpendicular_x = -segment_dy / segment_length
                    perpendicular_y = segment_dx / segment_length
                else:
                    perpendicular_x, perpendicular_y = 0, 0
                
                # Width to use for edges
                edge_width = river_width + 1
                
                # Place edge tiles across the width of the river
                for w in range(-edge_width//2, edge_width//2 + 1):
                    # Skip the river itself (which will be water later)
                    if -river_width//2 <= w <= river_width//2:
                        continue
                        
                    pos_x = x + int(perpendicular_x * w * village.tile_size)
                    pos_y = y + int(perpendicular_y * w * village.tile_size)
                    
                    # Align to grid
                    grid_x, grid_y = utils.align_to_grid(pos_x, pos_y, village.tile_size)
                    
                    # Skip if out of bounds
                    if not utils.is_in_bounds(grid_x, grid_y, village.grid_size):
                        continue
                    
                    # Add position to edge set
                    edge_positions.add((grid_x, grid_y))
    
    return edge_positions

def create_water_feature(village, water_type):
    """Create a water feature like lake or river.
    
    Args:
        village: Village instance
        water_type: Type of water feature ("lake", "river", or "lake_with_river")
    """
    center_x, center_y = village.grid_size // 2, village.grid_size // 2
    
    # Lake variables that will be used for both lake and river, if needed
    lake_center_x, lake_center_y = center_x, center_y
    lake_radius = village.grid_size // 8
    
    # Handle lake creation
    if water_type in ["lake", "lake_with_river"]:
        # Create a large lake near the center
        lake_center_x = center_x + random.randint(-village.grid_size//10, village.grid_size//10)
        lake_center_y = center_y + random.randint(-village.grid_size//10, village.grid_size//10)
        
        # Larger, more irregular lake
        irregularity = 0.3  # 0.0 = perfect circle, 1.0 = very irregular
        
        # Generate wobble points for the irregular shape
        wobble_points = utils.generate_points_in_irregular_shape(
            lake_center_x, lake_center_y, 
            lake_radius, 
            irregularity
        )
        
        # Find the bounds of the shape
        min_x = min(p[0] for p in wobble_points) - village.tile_size * 2
        max_x = max(p[0] for p in wobble_points) + village.tile_size * 2
        min_y = min(p[1] for p in wobble_points) - village.tile_size * 2
        max_y = max(p[1] for p in wobble_points) + village.tile_size * 2
        
        # Process grid positions within the bounding box
        for y in range(int(min_y), int(max_y), village.tile_size):
            for x in range(int(min_x), int(max_x), village.tile_size):
                # Align to grid
                grid_x, grid_y = utils.align_to_grid(x, y, village.tile_size)
                
                # Convert to grid indices
                idx_x, idx_y = grid_x // village.tile_size, grid_y // village.tile_size
                
                # Skip if out of bounds
                if not (0 <= idx_x < village.grid_width and 0 <= idx_y < village.grid_height):
                    continue
                
                # Check if point is inside the lake shape
                center_x = grid_x + village.tile_size // 2
                center_y = grid_y + village.tile_size // 2
                
                if utils.is_point_in_shape(
                    center_x, center_y, 
                    wobble_points, lake_center_x, lake_center_y
                ):
                    # Set as water in terrain grid
                    village.terrain_grid[idx_y][idx_x] = WATER
    
    # Handle river creation
    if water_type in ["river", "lake_with_river"]:
        # Create a winding river
        river_width = random.randint(3, 5)  # tiles
        
        # Determine river endpoints
        if water_type == "river":
            # River crossing the whole map
            start_x = 0
            start_y = random.randint(village.grid_size//4, 3*village.grid_size//4)
            end_x = village.grid_size
            end_y = random.randint(village.grid_size//4, 3*village.grid_size//4)
        else:
            # River flowing into the lake
            # Decide river direction (into the lake)
            edge_options = ["top", "right", "bottom", "left"]
            river_edge = random.choice(edge_options)
            
            # Set river start and end points based on edge
            if river_edge == "top":
                start_x = random.randint(village.grid_size//4, 3*village.grid_size//4)
                start_y = 0
                end_x = lake_center_x
                end_y = lake_center_y - lake_radius
            elif river_edge == "right":
                start_x = village.grid_size
                start_y = random.randint(village.grid_size//4, 3*village.grid_size//4)
                end_x = lake_center_x + lake_radius
                end_y = lake_center_y
            elif river_edge == "bottom":
                start_x = random.randint(village.grid_size//4, 3*village.grid_size//4)
                start_y = village.grid_size
                end_x = lake_center_x
                end_y = lake_center_y + lake_radius
            else:  # left
                start_x = 0
                start_y = random.randint(village.grid_size//4, 3*village.grid_size//4)
                end_x = lake_center_x - lake_radius
                end_y = lake_center_y
        
        # Generate river waypoints for a natural look
        waypoints = generate_river_waypoints(village, start_x, start_y, end_x, end_y)
        
        # Process river segments between waypoints
        for i in range(len(waypoints) - 1):
            p1 = waypoints[i]
            p2 = waypoints[i+1]
            
            # Calculate segment properties
            segment_dx = p2[0] - p1[0]
            segment_dy = p2[1] - p1[1]
            segment_length = utils.calculate_distance(p1[0], p1[1], p2[0], p2[1])
            
            if segment_length == 0:
                continue
                
            # Use half-tile steps for smoother river
            steps = int(segment_length / (village.tile_size / 2))
            steps = max(1, steps)  # Ensure at least one step
            
            for step in range(steps + 1):
                # Position along line
                t = step / steps
                x = int(p1[0] + segment_dx * t)
                y = int(p1[1] + segment_dy * t)
                
                # Define perpendicular vector
                if segment_length > 0:
                    perpendicular_x = -segment_dy / segment_length
                    perpendicular_y = segment_dx / segment_length
                else:
                    perpendicular_x, perpendicular_y = 0, 0
                
                # Place water tiles across the width of the river
                for w in range(-river_width//2, river_width//2 + 1):
                    pos_x = x + int(perpendicular_x * w * village.tile_size)
                    pos_y = y + int(perpendicular_y * w * village.tile_size)
                    
                    # Align to grid
                    grid_x, grid_y = utils.align_to_grid(pos_x, pos_y, village.tile_size)
                    
                    # Convert to grid indices
                    idx_x, idx_y = grid_x // village.tile_size, grid_y // village.tile_size
                    
                    # Skip if out of bounds
                    if not (0 <= idx_x < village.grid_width and 0 <= idx_y < village.grid_height):
                        continue
                        
                    # Set as water in terrain grid
                    village.terrain_grid[idx_y][idx_x] = WATER

def generate_river_waypoints(village, start_x, start_y, end_x, end_y):
    """Generate waypoints for a winding river with random deviations.
    
    Args:
        village: Village instance
        start_x, start_y: Starting position
        end_x, end_y: Ending position
        
    Returns:
        List of waypoint coordinates
    """
    # Calculate distance
    distance = utils.calculate_distance(start_x, start_y, end_x, end_y)
    
    # Generate waypoints
    num_waypoints = max(3, int(distance / (village.grid_size / 10)))
    waypoints = [(start_x, start_y)]
    
    # Create waypoints with random deviation from straight line
    for i in range(1, num_waypoints):
        progress = i / num_waypoints
        
        # Base point along straight line
        x = int(start_x + (end_x - start_x) * progress)
        y = int(start_y + (end_y - start_y) * progress)
        
        # Add random deviation perpendicular to path direction
        dx = end_x - start_x
        dy = end_y - start_y
        perpendicular_x = -dy
        perpendicular_y = dx
        
        # Normalize perpendicular vector
        perp_length = math.sqrt(perpendicular_x*perpendicular_x + perpendicular_y*perpendicular_y)
        if perp_length > 0:
            perpendicular_x /= perp_length
            perpendicular_y /= perp_length
        
        # Add random deviation, larger in the middle of the river
        deviation = random.uniform(-0.5, 0.5) * village.grid_size / 6
        deviation *= math.sin(progress * math.pi)  # Maximum deviation in the middle
        
        x += int(perpendicular_x * deviation)
        y += int(perpendicular_y * deviation)
        
        # Add waypoint
        waypoints.append((x, y))
    
    # Add end point
    waypoints.append((end_x, end_y))
    
    return waypoints

def update_grass_near_water(village):
    """Update grass terrain near water to type 2."""
    # Identify grass tiles adjacent to water
    for y in range(village.grid_height):
        for x in range(village.grid_width):
            # Skip if this isn't grass or is already grass type 2 or 3
            if not is_grass(village.terrain_grid[y][x]) or village.terrain_grid[y][x] != GRASS_1:
                continue
                
            # Check if adjacent to water
            is_adjacent_to_water = False
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    nx, ny = x + dx, y + dy
                    
                    # Skip if out of bounds
                    if not (0 <= nx < village.grid_width and 0 <= ny < village.grid_height):
                        continue
                        
                    if is_water(village.terrain_grid[ny][nx]):
                        is_adjacent_to_water = True
                        break
                
                if is_adjacent_to_water:
                    break
            
            # Update to grass type 2 if adjacent to water
            if is_adjacent_to_water:
                village.terrain_grid[y][x] = GRASS_2

def create_forest_zones(village):
    """Create forest zones for tree placement.
    
    Args:
        village: Village instance
        
    Returns:
        List of (x, y, radius) tuples defining forest zones
    """
    forest_zones = []
    
    # Create 4-6 forest zones randomly placed around the map
    num_forests = random.randint(4, 6)
    
    # Define village center and minimum distance from center for forests
    center_x, center_y = village.grid_size // 2, village.grid_size // 2
    min_distance_from_center = village.grid_size // 4
    
    for _ in range(num_forests):
        # Try up to 10 times to place a forest zone away from center
        for attempt in range(10):
            forest_x = random.randint(village.tile_size * 5, village.grid_size - village.tile_size * 5)
            forest_y = random.randint(village.tile_size * 5, village.grid_size - village.tile_size * 5)
            
            # Calculate distance from center
            dx = forest_x - center_x
            dy = forest_y - center_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # If far enough from center, add this forest zone
            if distance >= min_distance_from_center:
                # Create random radius for forest
                forest_radius = random.randint(village.grid_size // 15, village.grid_size // 8)
                forest_zones.append((forest_x, forest_y, forest_radius))
                break
    
    return forest_zones

def place_trees(village):
    """Place trees in the village, avoiding water, buildings, paths, and their surroundings.
    
    Args:
        village: Village instance
    """
    print("Placing trees...")
    
    # Create forest zones
    forest_zones = create_forest_zones(village)
    tree_count = 0
    
    # Calculate tree target count based on village size
    tree_target = int(village.grid_size * village.grid_size * 0.0003)  # 0.03% of tiles as trees
    print(f"Target: {tree_target} trees")

    # First try forest zones for the bulk of trees
    for zone in forest_zones:
        forest_x, forest_y, forest_radius = zone
        
        # Define bounds around the forest zone
        min_x = max(0, int((forest_x - forest_radius) // village.tile_size))
        min_y = max(0, int((forest_y - forest_radius) // village.tile_size))
        max_x = min(village.grid_width, int((forest_x + forest_radius) // village.tile_size))
        max_y = min(village.grid_height, int((forest_y + forest_radius) // village.tile_size))
        
        # Try to place trees within this zone
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                # Skip if we've reached our target
                if tree_count >= tree_target:
                    break
                    
                # Skip if already occupied by water, path, tree, or building
                token = village.terrain_grid[y][x]
                if not is_grass(token):
                    continue
                
                # Calculate distance from forest center
                pixel_x = x * village.tile_size + village.tile_size // 2
                pixel_y = y * village.tile_size + village.tile_size // 2
                distance = utils.calculate_distance(pixel_x, pixel_y, forest_x, forest_y)
                
                if distance > forest_radius:
                    continue
                
                # Calculate probability based on distance from center
                probability = 1.0 - (distance / forest_radius)
                
                # Higher chance near center, lower at edges
                if random.random() > probability * 0.8:
                    continue
                
                # Check if too close to existing trees
                too_close = False
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        
                        # Skip if out of bounds
                        if not (0 <= nx < village.grid_width and 0 <= ny < village.grid_height):
                            continue
                            
                        # Skip if this is us
                        if nx == x and ny == y:
                            continue
                            
                        if is_tree(village.terrain_grid[ny][nx]):
                            too_close = True
                            break
                    
                    if too_close:
                        break
                
                if too_close:
                    continue
                
                # Check if near a path - avoid placing trees too close to paths
                near_path = False
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        
                        # Skip if out of bounds
                        if not (0 <= nx < village.grid_width and 0 <= ny < village.grid_height):
                            continue
                            
                        if is_path(village.terrain_grid[ny][nx]):
                            near_path = True
                            break
                    
                    if near_path:
                        break
                
                if near_path:
                    continue
                
                # Place a tree here
                tree_variant = random.randint(1, 5)  # 5 tree variants
                tree_token = TREE_1 + tree_variant - 1
                village.terrain_grid[y][x] = tree_token
                tree_count += 1
            
            if tree_count >= tree_target:
                break
    
    # If we still need more trees, add them near paths
    if tree_count < tree_target:
        # Find path-adjacent positions
        for y in range(village.grid_height):
            for x in range(village.grid_width):
                # Skip if we've reached our target
                if tree_count >= tree_target:
                    break
                    
                # Skip if not grass
                if not is_grass(village.terrain_grid[y][x]):
                    continue
                
                # Check if near but not adjacent to a path
                near_path = False
                for distance in range(2, 4):  # Check within 2-3 tiles
                    if near_path:
                        break
                        
                    for dx in range(-distance, distance + 1):
                        for dy in range(-distance, distance + 1):
                            # Only check at the specified distance
                            if abs(dx) != distance and abs(dy) != distance:
                                continue
                                
                            nx, ny = x + dx, y + dy
                            
                            # Skip if out of bounds
                            if not (0 <= nx < village.grid_width and 0 <= ny < village.grid_height):
                                continue
                                
                            if is_path(village.terrain_grid[ny][nx]):
                                near_path = True
                                break
                        
                        if near_path:
                            break
                
                if not near_path:
                    continue
                
                # Check for too close trees
                too_close = False
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        
                        # Skip if out of bounds
                        if not (0 <= nx < village.grid_width and 0 <= ny < village.grid_height):
                            continue
                            
                        if is_tree(village.terrain_grid[ny][nx]):
                            too_close = True
                            break
                    
                    if too_close:
                        break
                
                if too_close:
                    continue
                
                # Place a tree here
                tree_variant = random.randint(1, 5)  # 5 tree variants
                tree_token = TREE_1 + tree_variant - 1
                village.terrain_grid[y][x] = tree_token
                tree_count += 1
            
            if tree_count >= tree_target:
                break
    
    # Fill in the rest with random trees if needed
    remaining_trees = tree_target - tree_count
    if remaining_trees > 0:
        attempts = 0
        while tree_count < tree_target and attempts < tree_target * 3:
            attempts += 1
            
            # Choose a random position
            x = random.randint(0, village.grid_width - 1)
            y = random.randint(0, village.grid_height - 1)
            
            # Skip if not grass
            if not is_grass(village.terrain_grid[y][x]):
                continue
            
            # Check for too close trees
            too_close = False
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    nx, ny = x + dx, y + dy
                    
                    # Skip if out of bounds
                    if not (0 <= nx < village.grid_width and 0 <= ny < village.grid_height):
                        continue
                        
                    if is_tree(village.terrain_grid[ny][nx]):
                        too_close = True
                        break
                
                if too_close:
                    break
            
            if too_close:
                continue
            
            # Check if near water, path, or building - avoid these
            near_obstacle = False
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    nx, ny = x + dx, y + dy
                    
                    # Skip if out of bounds
                    if not (0 <= nx < village.grid_width and 0 <= ny < village.grid_height):
                        continue
                        
                    token = village.terrain_grid[ny][nx]
                    if is_water(token) or is_path(token) or is_building(token):
                        near_obstacle = True
                        break
                
                if near_obstacle:
                    break
            
            if near_obstacle:
                continue
            
            # Place a tree here
            tree_variant = random.randint(1, 5)  # 5 tree variants
            tree_token = TREE_1 + tree_variant - 1
            village.terrain_grid[y][x] = tree_token
            tree_count += 1
    
    # Update the tree_positions set
    village._rebuild_position_sets()
    
    print(f"Placed {tree_count}/{tree_target} trees")
    return tree_count