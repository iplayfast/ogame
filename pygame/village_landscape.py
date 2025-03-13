import random
import math
import utils

def generate_landscape(village):
    """Generate the natural landscape: terrain, water features, etc.
    
    Args:
        village: Village instance
        
    Returns:
        Dictionary with updated landscape components
    """
    print("Generating landscape...")
    
    # Place grass everywhere as base - default to type 1
    for x in range(0, village.grid_size, village.tile_size):
        for y in range(0, village.grid_size, village.tile_size):
            village.terrain[(x, y)] = {
                'type': 'grass',
                'variant': 1
            }
    
    # Add a water feature (lake, river, or lake with river)
    water_type = random.choice(["lake", "river", "lake_with_river"])
    
    # First, create grass type 2 around where water will be
    water_edge_positions = create_water_feature(village, water_type, create_edge=True)
    
    # Update terrain with grass type 2 around water
    for pos in water_edge_positions:
        if pos in village.terrain:
            village.terrain[pos]['variant'] = 2
    
    # Then create the actual water
    water_positions = create_water_feature(village, water_type, create_edge=False)
    
    # Ensure grass type 2 is properly around water
    update_grass_near_water(village)
    
    print(f"Landscape generation complete! {len(village.water)} water tiles")
    
    # Return the updated components
    return {
        'water_positions': village.water_positions
    }

def create_water_feature(village, water_type, create_edge=False):
    """Create a water feature like lake or river.
    
    Args:
        village: Village instance
        water_type: Type of water feature ("lake", "river", or "lake_with_river")
        create_edge: If True, create edge positions instead of water tiles
        
    Returns:
        Set of water positions or edge positions
    """
    # Initialize sets for results
    results = set()
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
        lake_radius = village.grid_size // 8
        irregularity = 0.3  # 0.0 = perfect circle, 1.0 = very irregular
        
        # Generate wobble points for the irregular shape
        wobble_points = utils.generate_points_in_irregular_shape(
            lake_center_x, lake_center_y, 
            lake_radius + (village.tile_size if create_edge else 0), 
            irregularity
        )
        
        # Find the bounds of the shape
        min_x = min(p[0] for p in wobble_points) - village.tile_size * 2
        max_x = max(p[0] for p in wobble_points) + village.tile_size * 2
        min_y = min(p[1] for p in wobble_points) - village.tile_size * 2
        max_y = max(p[1] for p in wobble_points) + village.tile_size * 2
        
        # Process grid positions within the bounding box
        def water_filter(x, y, cell_data):
            # Check if point is inside the lake shape
            grid_x, grid_y = utils.align_to_grid(x, y, village.tile_size)
            return utils.is_point_in_shape(
                grid_x + village.tile_size//2, 
                grid_y + village.tile_size//2, 
                wobble_points, lake_center_x, lake_center_y
            )
            
        def water_processor(x, y, cell_data):
            grid_x, grid_y = utils.align_to_grid(x, y, village.tile_size)
            pos = (grid_x, grid_y)
            
            if create_edge:
                # For edges, just add to results set
                results.add(pos)
            else:
                # For water, add to water list and update positions set
                village.water.append({
                    'position': pos,
                    'frame': 0
                })
                village.water_positions.add(pos)
            
            return pos
            
        # Define bounds for the lake
        bounds = (int(min_x), int(min_y), int(max_x), int(max_y))
        
        # Use scan_terrain to process the lake
        utils.scan_terrain(village, bounds, water_filter, water_processor)
    
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
        
        # Generate river using waypoints for a natural look
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
                
                # Width to use (wider for edges)
                width = river_width + (1 if create_edge else 0)
                
                # Place tiles across the width of the river
                for w in range(-width//2, width//2 + 1):
                    pos_x = x + int(perpendicular_x * w * village.tile_size)
                    pos_y = y + int(perpendicular_y * w * village.tile_size)
                    
                    # Align to grid
                    grid_x, grid_y = utils.align_to_grid(pos_x, pos_y, village.tile_size)
                    
                    # Skip if out of bounds
                    if not utils.is_in_bounds(grid_x, grid_y, village.grid_size):
                        continue
                    
                    # Add position to appropriate collection
                    river_pos = (grid_x, grid_y)
                    
                    if create_edge:
                        results.add(river_pos)
                    elif river_pos not in village.water_positions:  # Don't add twice
                        village.water.append({
                            'position': river_pos,
                            'frame': 0
                        })
                        village.water_positions.add(river_pos)
    
    # If we're creating edges, update terrain with grass type 2
    if create_edge:
        for pos in results:
            if pos in village.terrain:
                village.terrain[pos]['variant'] = 2
    
    # Return the appropriate set
    return results if create_edge else village.water_positions


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
    for water_pos in village.water_positions:
        # Check all neighboring tiles (including diagonals for more natural transitions)
        for neighbor_pos in utils.get_neighbors(water_pos[0], water_pos[1], village.tile_size, include_self=False):
            # Skip if out of bounds
            if not utils.is_in_bounds(neighbor_pos[0], neighbor_pos[1], village.grid_size):
                continue
            
            # If neighbor is a grass tile, update to type 2
            if neighbor_pos in village.terrain and village.terrain[neighbor_pos]['type'] == 'grass':
                village.terrain[neighbor_pos]['variant'] = 2

def place_trees(village):
    """Place trees in the village, avoiding water, buildings, paths, and their surroundings.
    
    Args:
        village: Village instance
        
    Returns:
        None (modifies village.trees directly)
    """
    print("Placing trees...")
    
    # Clear any existing trees
    village.trees = []
    
    # Create forest zones
    forest_zones = create_forest_zones(village)
    
    # Track occupied spaces - start with all water and path positions
    occupied_spaces = set()
    occupied_spaces.update(village.water_positions)
    occupied_spaces.update(village.path_positions)
    
    # Create an expanded building positions set that includes building surroundings
    # This is critical to prevent trees from appearing inside buildings or too close to them
    expanded_building_positions = set()
    
    for building in village.buildings:
        position = building['position']
        size_name = building['size']
        size_multiplier = 3 if size_name == 'large' else (2 if size_name == 'medium' else 1)
        
        # Calculate the building's footprint
        building_tiles = []
        for dx in range(size_multiplier):
            for dy in range(size_multiplier):
                building_tile = (position[0] + dx * village.tile_size, 
                                position[1] + dy * village.tile_size)
                building_tiles.append(building_tile)
                expanded_building_positions.add(building_tile)
        
        # Add buffer zone around building (2 tiles)
        buffer_size = 2  # Increased from 1 to 2 for extra safety
        for dx in range(-buffer_size, size_multiplier + buffer_size):
            for dy in range(-buffer_size, size_multiplier + buffer_size):
                # Skip the actual building footprint (already added)
                if 0 <= dx < size_multiplier and 0 <= dy < size_multiplier:
                    continue
                
                buffer_pos = (position[0] + dx * village.tile_size, 
                             position[1] + dy * village.tile_size)
                
                if utils.is_in_bounds(buffer_pos[0], buffer_pos[1], village.grid_size):
                    expanded_building_positions.add(buffer_pos)
    
    # Add all expanded building positions to occupied spaces
    occupied_spaces.update(expanded_building_positions)
    
    # Calculate tree target count based on village size
    tree_target = int(village.grid_size * village.grid_size * 0.0003)  # 0.03% of tiles as trees
    print(f"Target: {tree_target} trees")
    
    # Place trees with a mix of strategies
    trees_placed = 0
    
    # First try forest zones for the bulk of trees
    for zone in forest_zones:
        forest_x, forest_y, forest_radius = zone
        
        # Define filter function for scan_terrain
        def tree_filter(x, y, cell_data):
            # Position must not be occupied by water, path, or building
            pos = (x, y)
            if pos in occupied_spaces:
                return False
            
            # Extra check: make sure this position isn't in expanded_building_positions
            if pos in expanded_building_positions:
                return False
                
            # Check if in forest zone (with distance falloff)
            distance = utils.calculate_distance(x, y, forest_x, forest_y)
            if distance > forest_radius:
                return False
                
            # Calculate probability based on distance from center of forest
            # Higher chance near center, lower at edges
            probability = 1.0 - (distance / forest_radius)
            if random.random() > probability * 0.8:  # Adjust density here
                return False
                
            # Check if too close to existing trees (for spacing)
            for existing_tree in village.trees:
                existing_pos = existing_tree['position']
                if utils.calculate_distance(x, y, existing_pos[0], existing_pos[1]) < village.tile_size * 1.5:
                    return False
                    
            # Final safety check - ensure not on a path or in a building
            # by checking multiple points in the vicinity
            # This helps catch cases where paths and buildings might not be perfectly aligned
            for check_dx in range(-1, 2):
                for check_dy in range(-1, 2):
                    check_pos = (x + check_dx * village.tile_size // 2, 
                                y + check_dy * village.tile_size // 2)
                    
                    # Check if this position is inside any building's footprint
                    for building in village.buildings:
                        bx, by = building['position']
                        bsize = 3 if building['size'] == 'large' else (
                                2 if building['size'] == 'medium' else 1)
                        bwidth = bsize * village.tile_size
                        
                        if (bx <= check_pos[0] < bx + bwidth and 
                            by <= check_pos[1] < by + bwidth):
                            return False
            
            return True
        
        # Define processor function for scan_terrain
        def tree_processor(x, y, cell_data):
            nonlocal trees_placed
            
            # We've reached our target
            if trees_placed >= tree_target:
                return None
                
            pos = (x, y)
            
            # Final safety check - position isn't occupied
            if pos in occupied_spaces:
                return None
                
            # Add tree
            tree_variant = random.randint(1, 5)  # 5 tree variants
            new_tree = {
                'position': pos,
                'variant': tree_variant
            }
            village.trees.append(new_tree)
            
            # Mark position as occupied
            occupied_spaces.add(pos)
            
            # Update counter
            trees_placed += 1
            
            return new_tree
        
        # Set bounds around this forest zone
        bounds = (
            max(0, int(forest_x - forest_radius)),
            max(0, int(forest_y - forest_radius)),
            min(village.grid_size, int(forest_x + forest_radius)),
            min(village.grid_size, int(forest_y + forest_radius))
        )
        
        # Use scan_terrain for this forest zone
        utils.scan_terrain(village, bounds, tree_filter, tree_processor)
    
    # If we haven't placed enough trees, place some near paths
    if trees_placed < tree_target:
        # Define filter function for path-adjacent trees
        def path_adjacent_filter(x, y, cell_data):
            pos = (x, y)
            if pos in occupied_spaces:
                return False
            
            # Extra safety check - not in expanded building positions
            if pos in expanded_building_positions:
                return False
            
            # Check if near a path (but not too close)
            is_near_path = False
            for dx in range(-3, 4):  # Check within 3 tiles
                for dy in range(-3, 4):
                    check_pos = (x + dx * village.tile_size, y + dy * village.tile_size)
                    
                    # Want to be near a path, but not directly on it
                    if check_pos in village.path_positions:
                        # Calculate distance to path - want it to be at least 1 tile
                        path_distance = utils.calculate_distance(x, y, 
                                                              check_pos[0], check_pos[1])
                        if village.tile_size <= path_distance <= village.tile_size * 3:
                            is_near_path = True
                            break
                if is_near_path:
                    break
                    
            if not is_near_path:
                return False
                
            # Check if too close to existing trees
            for existing_tree in village.trees:
                existing_pos = existing_tree['position']
                if utils.calculate_distance(x, y, existing_pos[0], existing_pos[1]) < village.tile_size * 1.5:
                    return False
            
            # Final safety check - ensure not in a building by checking building footprints directly
            for building in village.buildings:
                bx, by = building['position']
                bsize = 3 if building['size'] == 'large' else (
                        2 if building['size'] == 'medium' else 1)
                bwidth = bsize * village.tile_size
                
                # Check if position is within building + buffer
                buffer = village.tile_size  # 1 tile buffer
                if (bx - buffer <= x < bx + bwidth + buffer and 
                    by - buffer <= y < by + bwidth + buffer):
                    return False
                    
            return True
        
        # Use scan_terrain with the path adjacent filter
        utils.scan_terrain(village, None, path_adjacent_filter, tree_processor)
    
    # Verify that no trees are inside buildings or on paths
    problem_trees = []
    for i, tree in enumerate(village.trees):
        tx, ty = tree['position']
        
        # Check if tree is on a path
        if (tx, ty) in village.path_positions:
            problem_trees.append(i)
            print(f"WARNING: Tree {i} at {tx}, {ty} is on a path!")
            continue
            
        # Check if tree is inside any building
        for building in village.buildings:
            bx, by = building['position']
            bsize = 3 if building['size'] == 'large' else (
                    2 if building['size'] == 'medium' else 1)
            bwidth = bsize * village.tile_size
            
            if bx <= tx < bx + bwidth and by <= ty < by + bwidth:
                problem_trees.append(i)
                print(f"WARNING: Tree {i} at {tx}, {ty} is inside building at {bx}, {by}!")
                break
    
    # Remove problem trees
    for i in sorted(problem_trees, reverse=True):
        tree = village.trees.pop(i)
        print(f"Removed problem tree at {tree['position']}")
    
    print(f"Placed {len(village.trees)} trees (removed {len(problem_trees)} problem trees)")


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
            
            # If far enough from center, accept this position
            if distance >= min_distance_from_center:
                forest_radius = random.randint(village.grid_size // 12, village.grid_size // 8)
                
                # Check if forest zone has too much overlap with buildings
                building_overlap = False
                # Count number of buildings in this forest zone
                buildings_in_zone = 0
                for building in village.buildings:
                    bx, by = building['position']
                    if utils.calculate_distance(forest_x, forest_y, bx, by) < forest_radius:
                        buildings_in_zone += 1
                        if buildings_in_zone > 2:  # Allow at most 2 buildings in a forest zone
                            building_overlap = True
                            break
                
                if not building_overlap:
                    forest_zones.append((forest_x, forest_y, forest_radius))
                    break
    
    return forest_zones

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
            
            # If far enough from center, accept this position
            if distance >= min_distance_from_center:
                forest_radius = random.randint(village.grid_size // 12, village.grid_size // 8)
                
                # Check if forest zone has too much overlap with buildings
                building_overlap = False
                # Count number of buildings in this forest zone
                buildings_in_zone = 0
                for building in village.buildings:
                    bx, by = building['position']
                    if utils.calculate_distance(forest_x, forest_y, bx, by) < forest_radius:
                        buildings_in_zone += 1
                        if buildings_in_zone > 2:  # Allow at most 2 buildings in a forest zone
                            building_overlap = True
                            break
                
                if not building_overlap:
                    forest_zones.append((forest_x, forest_y, forest_radius))
                    break
    
    return forest_zones


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
            
            # If far enough from center, accept this position
            if distance >= min_distance_from_center:
                forest_radius = random.randint(village.grid_size // 12, village.grid_size // 8)
                forest_zones.append((forest_x, forest_y, forest_radius))
                break
    
    return forest_zones

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
            
            # If far enough from center, accept this position
            if distance >= min_distance_from_center:
                forest_radius = random.randint(village.grid_size // 12, village.grid_size // 8)
                forest_zones.append((forest_x, forest_y, forest_radius))
                break
    
    return forest_zones

def place_tree_in_forest(village, forest_zones):
    """Place a tree within a forest zone.
    
    Args:
        village: Village instance
        forest_zones: List of (x, y, radius) tuples defining forest zones
        
    Returns:
        Tuple of (x, y) coordinates or None if placement failed
    """
    # Select a random forest zone
    if not forest_zones:
        return None
        
    forest_x, forest_y, forest_radius = random.choice(forest_zones)
    
    # Distribution is denser toward center of forest
    # Use random.triangular() for a triangular distribution
    distance = random.triangular(0, forest_radius, forest_radius * 0.7)
    angle = random.uniform(0, 2 * math.pi)
    
    x = forest_x + math.cos(angle) * distance
    y = forest_y + math.sin(angle) * distance
    
    # Align to grid
    return utils.align_to_grid(x, y, village.tile_size)

def place_tree_near_path(village, occupied_spaces):
    """Place a tree adjacent to a path but not on the path.
    
    Args:
        village: Village instance
        occupied_spaces: Set of occupied positions
        
    Returns:
        Tuple of (x, y) coordinates or None if placement failed
    """
    # If no paths, can't place near a path
    if not village.paths:
        return None
        
    # Choose a random path
    path = random.choice(village.paths)
    path_x, path_y = path['position']
    
    # Try adjacent positions (not diagonals for better aesthetics)
    adjacent_positions = [
        (path_x, path_y - village.tile_size),  # North
        (path_x + village.tile_size, path_y),  # East
        (path_x, path_y + village.tile_size),  # South
        (path_x - village.tile_size, path_y)   # West
    ]
    
    # Shuffle positions for variety
    random.shuffle(adjacent_positions)
    
    # Return first valid position
    for pos in adjacent_positions:
        # Skip if out of bounds
        if not utils.is_in_bounds(pos[0], pos[1], village.grid_size):
            continue
            
        # Skip if occupied
        if pos in occupied_spaces:
            continue
            
        return pos
        
    return None  # No valid position found

def place_tree_randomly(village):
    """Place a tree at a random position.
    
    Args:
        village: Village instance
        
    Returns:
        Tuple of (x, y) coordinates
    """
    padding = village.tile_size * 2
    x = random.randint(padding, village.grid_size - padding)
    y = random.randint(padding, village.grid_size - padding)
    
    # Align to grid
    return utils.align_to_grid(x, y, village.tile_size)