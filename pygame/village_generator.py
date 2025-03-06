import random
import math

def generate_village(size, assets, tile_size=32):
    """Generate a procedural village with buildings, paths, trees, and water features.
    
    Args:
        size: Size of the village in tiles (increased to 40 from 30)
        assets: Dictionary of game assets
        tile_size: Size of each tile in pixels
        
    Returns:
        Dictionary containing village data
    """
    print("Generating village...")
    
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
            if distance < grid_size // 6:
                # Central plaza with stone path
                paths.append({
                    'position': (x, y),
                    'variant': 2  # Stone path
                })
    
    # Create roads extending from center
    for angle in range(0, 360, 45):  # 8 directions
        road_length = random.randint(grid_size // 4, grid_size // 2)
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
    
    # Place buildings along paths
    _place_buildings(buildings, paths, water_positions, grid_size, tile_size, assets)
    
    # Place trees (avoid paths and buildings)
    _place_trees(trees, paths, buildings, water_positions, grid_size, tile_size, size)
    
    print(f"Village generation complete! {len(buildings)} buildings, {len(trees)} trees, {len(paths)} path tiles, {len(water)} water tiles")
    return {
        'size': grid_size,
        'terrain': terrain,
        'buildings': buildings,
        'trees': trees,
        'paths': paths,
        'water': water
    }

def _place_buildings(buildings, paths, water_positions, grid_size, tile_size, assets):
    """Place buildings along paths, avoiding water."""
    # Increase building density for larger villages
    path_building_chance = 0.15  
    
    for path in paths:
        if random.random() < path_building_chance:  # 15% chance for a building near a path
            # Find a spot near the path but not on it or on water
            for _ in range(10):  # Try 10 times to find a good spot
                offset_x = random.randint(-2, 2) * tile_size
                offset_y = random.randint(-2, 2) * tile_size
                
                building_x = path['position'][0] + offset_x
                building_y = path['position'][1] + offset_y
                
                # Check if position is within grid, not on a path, and not on water
                if (0 <= building_x < grid_size and 
                    0 <= building_y < grid_size and 
                    not any(p['position'] == (building_x, building_y) for p in paths) and
                    (building_x, building_y) not in water_positions):
                    
                    # Determine building size
                    size_weights = {"small": 70, "medium": 25, "large": 5}
                    sizes = list(size_weights.keys())
                    weights = list(size_weights.values())
                    building_size = random.choices(sizes, weights=weights)[0]
                    
                    # Check if the entire building footprint is valid (not on water)
                    footprint_size = 3 if building_size == 'large' else (2 if building_size == 'medium' else 1)
                    footprint_valid = True
                    
                    for dx in range(footprint_size):
                        for dy in range(footprint_size):
                            check_x = building_x + dx * tile_size
                            check_y = building_y + dy * tile_size
                            if (check_x, check_y) in water_positions:
                                footprint_valid = False
                                break
                        if not footprint_valid:
                            break
                    
                    if not footprint_valid:
                        continue
                    
                    # Get available building variants
                    available_variants = [k for k in assets['buildings'].keys() 
                                       if k.startswith(building_size) and k != 'roofs']
                    
                    if available_variants:
                        variant = random.choice(available_variants)
                        
                        # Check if there's already a building too close
                        too_close = False
                        min_distance = tile_size * 3  # Increased spacing between buildings
                        
                        for existing_building in buildings:
                            ex, ey = existing_building['position']
                            distance = math.sqrt((ex - building_x)**2 + (ey - building_y)**2)
                            if distance < min_distance:
                                too_close = True
                                break
                        
                        if not too_close:
                            buildings.append({
                                'position': (building_x, building_y),
                                'type': variant,
                                'size': building_size
                            })
                            break

def _place_trees(trees, paths, buildings, water_positions, grid_size, tile_size, size):
    """Place trees, avoiding paths, buildings, and water."""
    num_trees = int(size * size * 0.04)  # 5% tree coverage
    for _ in range(num_trees):
        for attempt in range(10):  # Try 10 times to place each tree
            x = random.randint(0, grid_size - tile_size)
            y = random.randint(0, grid_size - tile_size)
            
            # Align to grid
            x = (x // tile_size) * tile_size
            y = (y // tile_size) * tile_size
            
            # Make trees more likely around the edges
            distance_from_center = math.sqrt((x - grid_size/2)**2 + (y - grid_size/2)**2)
            if distance_from_center < grid_size/4 and random.random() < 0.7:
                continue  # 70% chance to skip trees near the center
            
            # Check if position is valid (not on path, building, or water)
            pos_valid = (
                not any(p['position'] == (x, y) for p in paths) and
                not any(abs(b['position'][0] - x) < tile_size * 2 and 
                        abs(b['position'][1] - y) < tile_size * 2 for b in buildings) and
                (x, y) not in water_positions
            )
            
            if pos_valid:
                tree_variant = random.randint(1, 5)  # 5 tree variants
                trees.append({
                    'position': (x, y),
                    'variant': tree_variant
                })
                break

def _add_water_features(water, grid_size, tile_size, size):
    """Add ponds and lakes to the village."""
    num_water = int(size * size * 0.01)  # 1% water coverage
    
    # Create larger ponds/lakes
    for _ in range(num_water):
        x = random.randint(tile_size * 3, grid_size - tile_size * 8)
        y = random.randint(tile_size * 3, grid_size - tile_size * 8)
        
        # Align to grid
        x = (x // tile_size) * tile_size
        y = (y // tile_size) * tile_size
        
        # Create small to medium ponds (3x3 to 7x7)
        pond_size = random.randint(3, 7)  # Increased max size
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
