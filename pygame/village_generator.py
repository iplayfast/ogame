import random
import math

def generate_village(size, assets, tile_size=32):
    """Generate a procedural village with buildings, paths, trees, and water features.
    
    Args:
        size: Base size parameter (will be scaled up)
        assets: Dictionary of game assets
        tile_size: Size of each tile in pixels (grass tiles are this size)
        
    Returns:
        Dictionary containing village data
    """
    # Scale up the village size to accommodate larger buildings
    size = size * 2  # Double the original size parameter
    
    print(f"Generating village with expanded size {size}x{size} tiles...")
    
    # Define asset sizes
    building_sizes = {
        "large": 256,    # 8 tiles (256x256)
        "medium": 192,   # 6 tiles (192x192)
        "small": 128     # 4 tiles (128x128)
    }
    character_size = 48  # 1.5 tiles (48x48)
    grass_size = tile_size  # 1 tile (32x32)
    
    # Create grid with grass base
    grid_size = size * tile_size
    terrain = {}
    buildings = []
    trees = []
    paths = []
    water = []
    
    # Place grass everywhere as base
    for x in range(0, grid_size, tile_size):
        for y in range(0, grid_size, tile_size):
            terrain[(x, y)] = {
                'type': 'grass',
                'variant': random.randint(1, 3)
            }
    
    # Create a central area with paths
    center_x, center_y = grid_size // 2, grid_size // 2
    
    # Add water features first, so we can avoid placing paths over them
    _add_water_features(water, grid_size, tile_size, size)
    
    # Convert water positions to a set for quick checking
    water_positions = {(w['position'][0], w['position'][1]) for w in water}
    
    # Create a circular town center with paths
    town_center_radius = grid_size // 8  # Larger central area
    for x in range(0, grid_size, tile_size):
        for y in range(0, grid_size, tile_size):
            # Check if position has water
            if (x, y) in water_positions:
                continue
                
            # Calculate distance from center
            dx = x - center_x
            dy = y - center_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Create circular town center
            if distance < town_center_radius:
                # Central plaza with stone path
                paths.append({
                    'position': (x, y),
                    'variant': 2  # Stone path
                })
    
    # Create more roads extending from center (12 directions instead of 8)
    for angle in range(0, 360, 30):  # 12 directions
        # FIX: Convert float to int for randint
        road_length = random.randint(grid_size // 3, int(grid_size // 1.5))  # Longer roads
        angle_rad = math.radians(angle)
        
        # Create a path in this direction, routing around water
        current_x = center_x
        current_y = center_y
        
        for dist in range(0, road_length, tile_size):
            # Calculate next position
            next_x = center_x + int(math.cos(angle_rad) * dist)
            next_y = center_y + int(math.sin(angle_rad) * dist)
            
            # Align to grid
            next_x = (next_x // tile_size) * tile_size
            next_y = (next_y // tile_size) * tile_size
            
            # Skip if out of bounds
            if not (0 <= next_x < grid_size and 0 <= next_y < grid_size):
                break
                
            # Check if next position has water
            if (next_x, next_y) in water_positions:
                # Try to route around the water
                directions = [
                    (tile_size, 0),      # Right
                    (0, tile_size),      # Down
                    (-tile_size, 0),     # Left
                    (0, -tile_size),     # Up
                    (tile_size, tile_size),    # Down-right
                    (-tile_size, tile_size),   # Down-left
                    (tile_size, -tile_size),   # Up-right
                    (-tile_size, -tile_size)   # Up-left
                ]
                
                # Shuffle directions to avoid bias
                random.shuffle(directions)
                
                routed = False
                for dx, dy in directions:
                    alt_x = next_x + dx
                    alt_y = next_y + dy
                    
                    # Check if the alternative position is valid
                    if (0 <= alt_x < grid_size and 0 <= alt_y < grid_size and
                        (alt_x, alt_y) not in water_positions):
                        # Add this alternative path segment
                        if not any(p['position'] == (alt_x, alt_y) for p in paths):
                            paths.append({
                                'position': (alt_x, alt_y),
                                'variant': 1  # Dirt path
                            })
                        next_x = alt_x
                        next_y = alt_y
                        routed = True
                        break
                
                # If we couldn't route around, stop this path
                if not routed:
                    break
            else:
                # Add this path segment if it doesn't already exist
                if not any(p['position'] == (next_x, next_y) for p in paths):
                    paths.append({
                        'position': (next_x, next_y),
                        'variant': 1  # Dirt path
                    })
    
    # Add some secondary connecting paths between radial roads
    _add_connecting_paths(paths, water_positions, grid_size, tile_size)
    
    # Convert path positions to a set for quick checking
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Place buildings along paths with improved spacing, taking into account the actual building sizes
    # Increase building target count to fill the larger village
    target_building_count = int(size * 0.5)  # Scale with village size
    _place_buildings_improved(buildings, paths, water_positions, path_positions, 
                            grid_size, tile_size, assets, building_sizes, target_building_count)
    
    # Convert building positions to a set for quick checking (include their full footprint)
    building_positions = set()
    for building in buildings:
        x, y = building['position']
        building_size_px = building_sizes[building['size']]
        footprint_tiles = building_size_px // tile_size
        
        for dx in range(footprint_tiles):
            for dy in range(footprint_tiles):
                bx = x + dx * tile_size
                by = y + dy * tile_size
                
                # Skip if out of bounds
                if 0 <= bx < grid_size and 0 <= by < grid_size:
                    building_positions.add((bx, by))
                    
                    # Add buffer zone around buildings to prevent trees from being too close
                    for buffer_x in range(-1, 2):
                        for buffer_y in range(-1, 2):
                            buffer_pos = (bx + buffer_x * tile_size, by + buffer_y * tile_size)
                            if 0 <= buffer_pos[0] < grid_size and 0 <= buffer_pos[1] < grid_size:
                                building_positions.add(buffer_pos)
    
    # Place trees (avoid paths, buildings, and water)
    tree_target = int(size * size * 0.03)  # Reduced density slightly for performance
    _place_trees_improved(trees, path_positions, building_positions, water_positions, grid_size, tile_size, size, tree_target)
    
    print(f"Village generation complete! {len(buildings)} buildings, {len(trees)} trees, {len(paths)} path tiles, {len(water)} water tiles")
    return {
        'size': grid_size,
        'terrain': terrain,
        'buildings': buildings,
        'trees': trees,
        'paths': paths,
        'water': water
    }

def _add_connecting_paths(paths, water_positions, grid_size, tile_size):
    """Add connecting paths between the radial roads."""
    # Convert existing paths to a set for quick checking
    path_set = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Create rings of paths at different distances from center
    center_x, center_y = grid_size // 2, grid_size // 2
    
    # Define 2-3 rings at different distances
    ring_distances = [
        grid_size // 6,   # Inner ring
        grid_size // 3,   # Middle ring
        grid_size // 2    # Outer ring (optional)
    ]
    
    # Only use the outer ring sometimes
    if random.random() < 0.7:
        ring_distances = ring_distances[:2]
        
    for ring_radius in ring_distances:
        # Number of segments for this ring (more segments for outer rings)
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
                x = center_x + int(math.cos(segment_angle) * ring_radius)
                y = center_y + int(math.sin(segment_angle) * ring_radius)
                
                # Align to grid
                x = (x // tile_size) * tile_size
                y = (y // tile_size) * tile_size
                
                # Skip if out of bounds or on water or already a path
                if not (0 <= x < grid_size and 0 <= y < grid_size):
                    continue
                    
                if (x, y) in water_positions or (x, y) in path_set:
                    continue
                
                # Add path segment
                paths.append({
                    'position': (x, y),
                    'variant': 1  # Dirt path
                })
                path_set.add((x, y))

def _place_buildings_improved(buildings, paths, water_positions, path_positions, 
                            grid_size, tile_size, assets, building_sizes, target_building_count):
    """Place buildings along paths with improved spacing logic, taking into account actual building sizes."""
    # Track occupied spaces for better building placement
    occupied_spaces = set()
    
    # Sort paths to prioritize those near the center
    center = grid_size // 2
    sorted_paths = sorted(paths, 
                         key=lambda p: abs(p['position'][0] - center) + abs(p['position'][1] - center))
    
    # First pass: place larger buildings near center
    for path in sorted_paths[:len(sorted_paths)//4]:  # Use first quarter of paths (closer to center)
        if random.random() < 0.25:  # 25% chance for each path near center
            _try_place_building(buildings, path, water_positions, path_positions, 
                              occupied_spaces, grid_size, tile_size, assets, building_sizes,
                              preferred_sizes=["medium", "large"])
            
            # Check if we've reached our target for larger buildings
            large_medium_count = sum(1 for b in buildings if b['size'] in ["medium", "large"])
            if large_medium_count >= target_building_count // 4:  # Limit larger buildings to 25% of total
                break
    
    # Second pass: place remaining buildings along all paths
    building_attempts = 0
    max_attempts = target_building_count * 5  # Limit attempts to avoid infinite loops
    
    while len(buildings) < target_building_count and building_attempts < max_attempts:
        building_attempts += 1
        
        # Pick a random path
        path = random.choice(paths)
        
        # Try to place a building
        _try_place_building(buildings, path, water_positions, path_positions, 
                          occupied_spaces, grid_size, tile_size, assets, building_sizes)

def _try_place_building(buildings, path, water_positions, path_positions, 
                      occupied_spaces, grid_size, tile_size, assets, building_sizes,
                      preferred_sizes=None):
    """Try to place a building near a path with proper spacing."""
    # Determine building size
    if preferred_sizes:
        size_weights = {size: 80 if size in preferred_sizes else 20 for size in ["small", "medium", "large"]}
    else:
        size_weights = {"small": 70, "medium": 25, "large": 5}
    
    sizes = list(size_weights.keys())
    weights = [size_weights[s] for s in sizes]
    building_size = random.choices(sizes, weights=weights)[0]
    
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
    path_x, path_y = path['position']
    
    for dir_x, dir_y in directions:
        # Calculate potential building position
        # Move further out for larger buildings to ensure they don't overlap the path
        distance = max(1, footprint_tiles // 2 + 1)
        building_x = path_x + dir_x * tile_size * distance
        building_y = path_y + dir_y * tile_size * distance
        
        # Align to grid
        building_x = (building_x // tile_size) * tile_size
        building_y = (building_y // tile_size) * tile_size
        
        # Skip if out of bounds
        if (building_x < 0 or building_x + building_size_px > grid_size or
            building_y < 0 or building_y + building_size_px > grid_size):
            continue
        
        # Check if the footprint is valid (not on water, paths, or other buildings)
        footprint_valid = True
        
        for dx in range(footprint_tiles):
            for dy in range(footprint_tiles):
                check_x = building_x + dx * tile_size
                check_y = building_y + dy * tile_size
                check_pos = (check_x, check_y)
                
                if (check_pos in water_positions or 
                    check_pos in path_positions or 
                    check_pos in occupied_spaces):
                    footprint_valid = False
                    break
                    
            if not footprint_valid:
                break
        
        if not footprint_valid:
            continue
        
        # Check if there's enough buffer space around the building (prevent crowding)
        buffer_valid = True
        
        # Buffer size based on building size (smaller buffer for smaller buildings)
        buffer_tiles = 1 if building_size == "small" else 2
        
        # Check the buffer zone around the building (including diagonals)
        for dx in range(-buffer_tiles, footprint_tiles + buffer_tiles):
            for dy in range(-buffer_tiles, footprint_tiles + buffer_tiles):
                # Skip checking the actual building footprint
                if 0 <= dx < footprint_tiles and 0 <= dy < footprint_tiles:
                    continue
                    
                check_x = building_x + dx * tile_size
                check_y = building_y + dy * tile_size
                
                # Skip if out of bounds
                if not (0 <= check_x < grid_size and 0 <= check_y < grid_size):
                    continue
                
                check_pos = (check_x, check_y)
                
                # Allow buffer to overlap with paths (buildings can be near paths)
                # But don't allow overlap with other buildings' occupied spaces
                if check_pos in occupied_spaces and check_pos not in path_positions:
                    buffer_valid = False
                    break
            
            if not buffer_valid:
                break
        
        if not buffer_valid:
            continue
        
        # If we're here, we found a valid spot!
        
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
            'building_type': _get_random_building_type(building_size)  # Add a building type
        })
        
        # Mark the space as occupied (both the building footprint and its buffer zone)
        for dx in range(-buffer_tiles, footprint_tiles + buffer_tiles):
            for dy in range(-buffer_tiles, footprint_tiles + buffer_tiles):
                check_x = building_x + dx * tile_size
                check_y = building_y + dy * tile_size
                
                # Skip if out of bounds
                if not (0 <= check_x < grid_size and 0 <= check_y < grid_size):
                    continue
                
                occupied_spaces.add((check_x, check_y))
        
        # Successfully placed a building
        return True
    
    # Could not place a building
    return False

def _get_random_building_type(size):
    """Return a random building type appropriate for the size."""
    if size == "large":
        return random.choice(["Town Hall", "Market", "Temple", "Manor"])
    elif size == "medium":
        return random.choice(["Inn", "Store", "Tavern", "Smithy", "Bakery"])
    else:  # small
        return random.choice(["House", "Cottage", "Workshop", "Storage"])

def _place_trees_improved(trees, path_positions, building_positions, water_positions, grid_size, tile_size, size, target_tree_count):
    """Place trees with improved spacing logic to avoid buildings and roads."""
    # Track occupied tree positions
    tree_positions = set()
    
    # Different tree distribution zones
    forest_zones = []
    
    # Create 4-6 forest zones randomly placed around the map
    num_forests = random.randint(4, 6)
    for _ in range(num_forests):
        forest_x = random.randint(tile_size * 5, grid_size - tile_size * 5)
        forest_y = random.randint(tile_size * 5, grid_size - tile_size * 5)
        forest_radius = random.randint(grid_size // 12, grid_size // 8)
        forest_zones.append((forest_x, forest_y, forest_radius))
    
    # Track attempts to avoid infinite loops
    attempts = 0
    max_attempts = target_tree_count * 3
    
    # Place trees
    while len(trees) < target_tree_count and attempts < max_attempts:
        attempts += 1
        
        # Decide where to try placing a tree
        if random.random() < 0.7:  # 70% in forest zones
            # Select a random forest zone
            forest_x, forest_y, forest_radius = random.choice(forest_zones)
            
            # Place within this forest with random distribution
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, forest_radius)
            
            x = forest_x + int(math.cos(angle) * distance)
            y = forest_y + int(math.sin(angle) * distance)
            
            # Align to grid
            x = (x // tile_size) * tile_size
            y = (y // tile_size) * tile_size
        else:
            # Random position anywhere
            x = random.randint(0, grid_size - tile_size)
            y = random.randint(0, grid_size - tile_size)
            
            # Align to grid
            x = (x // tile_size) * tile_size
            y = (y // tile_size) * tile_size
        
        # Skip if out of bounds
        if not (0 <= x < grid_size and 0 <= y < grid_size):
            continue
            
        tree_pos = (x, y)
        
        # Check if position is valid
        if (tree_pos in path_positions or
            tree_pos in building_positions or
            tree_pos in water_positions or
            tree_pos in tree_positions):
            continue
            
        # Add spacing between trees (less dense in some areas)
        too_close = False
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                near_pos = (x + dx * tile_size, y + dy * tile_size)
                if near_pos in tree_positions:
                    too_close = True
                    break
            if too_close:
                break
                
        if too_close:
            continue
            
        # Add the tree
        tree_variant = random.randint(1, 5)  # 5 tree variants
        trees.append({
            'position': (x, y),
            'variant': tree_variant
        })
        
        # Mark position as occupied
        tree_positions.add(tree_pos)

def _add_water_features(water, grid_size, tile_size, size):
    """Add ponds and lakes to the village."""
    num_water = int(size * 0.7)  # Scale with village size
    
    # Create larger ponds/lakes
    for _ in range(num_water):
        x = random.randint(tile_size * 5, grid_size - tile_size * 5)
        y = random.randint(tile_size * 5, grid_size - tile_size * 5)
        
        # Align to grid
        x = (x // tile_size) * tile_size
        y = (y // tile_size) * tile_size
        
        # Create small to medium ponds (3x3 to 8x8)
        pond_size = random.randint(3, 8)
        for dx in range(pond_size):
            for dy in range(pond_size):
                pond_x = x + dx * tile_size
                pond_y = y + dy * tile_size
                
                # Keep within grid
                if 0 <= pond_x < grid_size and 0 <= pond_y < grid_size:
                    # Make pond more irregular (circular-ish)
                    dist_from_center = math.sqrt((dx - pond_size/2)**2 + (dy - pond_size/2)**2)
                    if dist_from_center <= pond_size/2:
                        water.append({
                            'position': (pond_x, pond_y),
                            'frame': 0  # Start with first frame
                        })
