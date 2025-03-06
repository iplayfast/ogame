import random
import math
import utils

# ================ VILLAGE GENERATION FUNCTIONS ================

def generate_village(size, assets, tile_size=32):
    """Generate a procedural village with a central water feature and realistic layout.
    
    Args:
        size: Base size parameter (will be scaled up)
        assets: Dictionary of game assets
        tile_size: Size of each tile in pixels (grass tiles are this size)
        
    Returns:
        Dictionary containing village data
    """
    # Scale up the village size to accommodate larger buildings
    size = size * 2  # Double the original size parameter
    
    print(f"Generating waterfront village with expanded size {size}x{size} tiles...")
    
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
    
    # Add a single large water feature (lake, river, or lake with river)
    water_type = random.choice(["lake", "river", "lake_with_river"])
    water_positions = create_water_feature(water, grid_size, tile_size, water_type)
    
    # Create a village layout based on the water feature
    # First, plan the main roads and paths around the water
    create_village_layout(paths, water_positions, grid_size, tile_size, water_type)
    
    # Convert path positions to a set for quick checking
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Place buildings with appropriate types based on proximity to water and village center
    target_building_count = int(size * 0.5)  # Scale with village size
    place_buildings_by_zones(buildings, paths, water_positions, path_positions, 
                             grid_size, tile_size, assets, building_sizes, target_building_count)
    
    # Convert building positions to a set for quick checking (include their full footprint)
    building_positions = get_building_footprints(buildings, building_sizes, tile_size, grid_size)
    
    # Place trees (avoid paths, buildings, and water)
    tree_target = int(size * size * 0.03)  # Reduced density slightly for performance
    place_trees_improved(trees, path_positions, building_positions, water_positions, grid_size, tile_size, size, tree_target)
    
    print(f"Village generation complete! {len(buildings)} buildings, {len(trees)} trees, {len(paths)} path tiles, {len(water)} water tiles")
    return {
        'size': grid_size,
        'terrain': terrain,
        'buildings': buildings,
        'trees': trees,
        'paths': paths,
        'water': water
    }

def get_building_footprints(buildings, building_sizes, tile_size, grid_size):
    """Get the footprint of all buildings including buffer zones.
    
    Args:
        buildings: List of building dictionaries
        building_sizes: Dictionary of building sizes
        tile_size: Size of a tile in pixels
        grid_size: Size of the grid in pixels
        
    Returns:
        Set of positions occupied by buildings and their buffer zones
    """
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
                if utils.is_in_bounds(bx, by, grid_size):
                    building_positions.add((bx, by))
                    
                    # Add buffer zone around buildings to prevent trees from being too close
                    for buffer_x in range(-1, 2):
                        for buffer_y in range(-1, 2):
                            buffer_pos = (bx + buffer_x * tile_size, by + buffer_y * tile_size)
                            utils.add_to_set_if_in_bounds(building_positions, buffer_pos, grid_size)
    
    return building_positions

def create_water_feature(water, grid_size, tile_size, water_type):
    """Create a single large water feature (lake, river, or both).
    
    Args:
        water: List to add water tiles to
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        water_type: Type of water feature ("lake", "river", or "lake_with_river")
        
    Returns:
        Set of water positions
    """
    water_positions = set()
    center_x, center_y = grid_size // 2, grid_size // 2
    
    if water_type == "lake" or water_type == "lake_with_river":
        # Create a large lake near the center
        lake_center_x = center_x + random.randint(-grid_size//10, grid_size//10)
        lake_center_y = center_y + random.randint(-grid_size//10, grid_size//10)
        
        # Larger, more irregular lake
        lake_radius = grid_size // 8
        irregularity = 0.3  # 0.0 = perfect circle, 1.0 = very irregular
        
        # Generate the lake with a jagged, natural shoreline
        generate_natural_lake(water, lake_center_x, lake_center_y, lake_radius, irregularity, grid_size, tile_size)
        
        # Update water positions
        water_positions = {(w['position'][0], w['position'][1]) for w in water}
    
    if water_type == "river" or water_type == "lake_with_river":
        # Create a winding river
        river_width = random.randint(3, 5)  # tiles
        
        if water_type == "river":
            # River crossing the whole map
            start_x = 0
            start_y = random.randint(grid_size//4, 3*grid_size//4)
            end_x = grid_size
            end_y = random.randint(grid_size//4, 3*grid_size//4)
            
            generate_winding_river(water, water_positions, start_x, start_y, end_x, end_y, 
                                   river_width, grid_size, tile_size)
        else:
            # River flowing into the lake
            # Decide river direction (into the lake)
            edge_options = ["top", "right", "bottom", "left"]
            river_edge = random.choice(edge_options)
            
            # Set river start and end points based on edge
            river_endpoints = get_river_endpoints(river_edge, grid_size, lake_center_x, lake_center_y, lake_radius)
            start_x, start_y, end_x, end_y = river_endpoints
            
            generate_winding_river(water, water_positions, start_x, start_y, end_x, end_y, 
                                   river_width, grid_size, tile_size)
    
    # Update water positions after adding all water elements
    water_positions = {(w['position'][0], w['position'][1]) for w in water}
    return water_positions

def get_river_endpoints(river_edge, grid_size, lake_center_x, lake_center_y, lake_radius):
    """Get the endpoints for a river based on the edge it flows from.
    
    Args:
        river_edge: Edge the river flows from ("top", "right", "bottom", "left")
        grid_size: Size of the grid in pixels
        lake_center_x, lake_center_y: Center of the lake
        lake_radius: Radius of the lake
        
    Returns:
        Tuple of (start_x, start_y, end_x, end_y)
    """
    if river_edge == "top":
        start_x = random.randint(grid_size//4, 3*grid_size//4)
        start_y = 0
        end_x = lake_center_x
        end_y = lake_center_y - lake_radius
    elif river_edge == "right":
        start_x = grid_size
        start_y = random.randint(grid_size//4, 3*grid_size//4)
        end_x = lake_center_x + lake_radius
        end_y = lake_center_y
    elif river_edge == "bottom":
        start_x = random.randint(grid_size//4, 3*grid_size//4)
        start_y = grid_size
        end_x = lake_center_x
        end_y = lake_center_y + lake_radius
    else:  # left
        start_x = 0
        start_y = random.randint(grid_size//4, 3*grid_size//4)
        end_x = lake_center_x - lake_radius
        end_y = lake_center_y
        
    return start_x, start_y, end_x, end_y

def generate_natural_lake(water, center_x, center_y, base_radius, irregularity, grid_size, tile_size):
    """Generate a natural-looking lake with an irregular shoreline."""
    # Create multiple "wobbles" around the circle to make the lake look natural
    num_wobbles = 12
    wobble_points = []
    
    for i in range(num_wobbles):
        angle = i * (2 * math.pi / num_wobbles)
        # Vary the radius at this angle to create irregularity
        radius_modifier = 1.0 - irregularity/2 + random.random() * irregularity
        radius = base_radius * radius_modifier
        
        x, y = utils.polar_to_cartesian(center_x, center_y, angle, radius)
        wobble_points.append((x, y))
    
    # Fill the lake
    min_x = min(p[0] for p in wobble_points)
    max_x = max(p[0] for p in wobble_points)
    min_y = min(p[1] for p in wobble_points)
    max_y = max(p[1] for p in wobble_points)
    
    # Create a slightly larger bounding box to ensure we fill all lake areas
    padding = tile_size
    for x in range(min_x - padding, max_x + padding, tile_size):
        for y in range(min_y - padding, max_y + padding, tile_size):
            # Skip if out of bounds
            if not utils.is_in_bounds(x, y, grid_size):
                continue
                
            # Align to grid
            grid_x, grid_y = utils.align_to_grid(x, y, tile_size)
            
            # Calculate if this point is inside our irregular lake shape
            # Use point-in-polygon algorithm with our wobble points
            if is_point_in_lake(grid_x + tile_size//2, grid_y + tile_size//2, center_x, center_y, wobble_points):
                water.append({
                    'position': (grid_x, grid_y),
                    'frame': 0
                })

def is_point_in_lake(x, y, center_x, center_y, wobble_points):
    """Determine if a point is inside the irregular lake shape using a distance-based approach."""
    # Calculate angle from center to point
    angle = math.atan2(y - center_y, x - center_x)
    if angle < 0:
        angle += 2 * math.pi
    
    # Find which wobble sector this angle falls into
    sector = int(angle / (2 * math.pi) * len(wobble_points))
    if sector >= len(wobble_points):
        sector = 0
    
    p1 = wobble_points[sector]
    p2 = wobble_points[(sector + 1) % len(wobble_points)]
    
    # Calculate how far along the sector this angle is
    sector_start_angle = sector * (2 * math.pi / len(wobble_points))
    sector_angle_range = 2 * math.pi / len(wobble_points)
    sector_progress = (angle - sector_start_angle) / sector_angle_range
    
    # Interpolate between the two wobble points
    edge_x = p1[0] + (p2[0] - p1[0]) * sector_progress
    edge_y = p1[1] + (p2[1] - p1[1]) * sector_progress
    
    # Calculate distance from center to edge and from center to point
    edge_distance = utils.calculate_distance(center_x, center_y, edge_x, edge_y)
    point_distance = utils.calculate_distance(center_x, center_y, x, y)
    
    # If point is closer to center than edge, it's inside the lake
    return point_distance <= edge_distance

def generate_winding_river(water, existing_water, start_x, start_y, end_x, end_y, width, grid_size, tile_size):
    """Generate a winding river from start to end point.
    
    Args:
        water: List to add water tiles to
        existing_water: Set of existing water positions
        start_x, start_y: Starting point of the river
        end_x, end_y: Ending point of the river
        width: Width of the river in tiles
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
    """
    # Calculate direct path length and direction
    distance = utils.calculate_distance(start_x, start_y, end_x, end_y)
    
    # Generate waypoints
    num_waypoints = max(3, int(distance / (grid_size / 10)))
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
        deviation = random.uniform(-0.5, 0.5) * grid_size / 6
        deviation *= math.sin(progress * math.pi)  # Maximum deviation in the middle
        
        x += int(perpendicular_x * deviation)
        y += int(perpendicular_y * deviation)
        
        # Add waypoint
        waypoints.append((x, y))
    
    # Add end point
    waypoints.append((end_x, end_y))
    
    # Now draw river along waypoints with specified width
    draw_river_segments(water, existing_water, waypoints, width, grid_size, tile_size)

def draw_river_segments(water, existing_water, waypoints, width, grid_size, tile_size):
    """Draw river segments between waypoints.
    
    Args:
        water: List to add water tiles to
        existing_water: Set of existing water positions
        waypoints: List of waypoint coordinates
        width: Width of the river in tiles
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
    """
    for i in range(len(waypoints) - 1):
        p1 = waypoints[i]
        p2 = waypoints[i+1]
        
        # Draw a line of water tiles along this segment
        segment_dx = p2[0] - p1[0]
        segment_dy = p2[1] - p1[1]
        segment_length = math.sqrt(segment_dx*segment_dx + segment_dy*segment_dy)
        
        if segment_length == 0:
            continue
            
        steps = int(segment_length / (tile_size / 2))  # Use half-tile steps for smoother river
        if steps == 0:
            steps = 1
            
        for step in range(steps + 1):
            # Position along line
            t = step / steps
            x = int(p1[0] + segment_dx * t)
            y = int(p1[1] + segment_dy * t)
            
            # Draw water tiles perpendicular to river direction
            if segment_length > 0:
                perpendicular_x = -segment_dy / segment_length
                perpendicular_y = segment_dx / segment_length
            else:
                perpendicular_x = 0
                perpendicular_y = 0
            
            # Place water tiles across the width of the river
            for w in range(-width//2, width//2 + 1):
                water_x = x + int(perpendicular_x * w * tile_size)
                water_y = y + int(perpendicular_y * w * tile_size)
                
                # Align to grid
                water_x, water_y = utils.align_to_grid(water_x, water_y, tile_size)
                
                # Skip if out of bounds
                if not utils.is_in_bounds(water_x, water_y, grid_size):
                    continue
                
                # Add water tile if not already water
                water_pos = (water_x, water_y)
                if water_pos not in existing_water:
                    water.append({
                        'position': water_pos,
                        'frame': 0
                    })
                    existing_water.add(water_pos)

def create_village_layout(paths, water_positions, grid_size, tile_size, water_type):
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

def create_central_plaza(paths, village_center_x, village_center_y, grid_size, tile_size, water_positions):
    """Create a central plaza in the village.
    
    Args:
        paths: List to add path tiles to
        village_center_x, village_center_y: Center coordinates of the village
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        water_positions: Set of water positions to avoid
    """
    plaza_radius = grid_size // 16
    for x in range(village_center_x - plaza_radius, village_center_x + plaza_radius, tile_size):
        for y in range(village_center_y - plaza_radius, village_center_y + plaza_radius, tile_size):
            # Skip if out of bounds or water
            if not utils.is_in_bounds(x, y, grid_size) or (x, y) in water_positions:
                continue
                
            # Create circular village center
            dx = x - village_center_x
            dy = y - village_center_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < plaza_radius:
                # Central plaza with stone path
                paths.append({
                    'position': (x, y),
                    'variant': 2  # Stone path
                })

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

def create_waterfront_path(paths, water_positions, grid_size, tile_size):
    """Create a path along the waterfront."""
    # Identify water edge tiles (land tiles adjacent to water)
    water_edge = set()
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
                
                # If neighbor is not water, it's a potential edge tile
                if neighbor_pos not in water_positions:
                    water_edge.add(neighbor_pos)
    
    # Process edges to selectively create paths
    # Don't place paths on every edge tile - make it more natural
    path_positions = {(p['position'][0], p['position'][1]) for p in paths}
    
    # Sort edge tiles for more consistent results
    sorted_edges = sorted(water_edge)
    
    for i, edge_pos in enumerate(sorted_edges):
        # Place a path on this edge if it's not already a path
        # Use spacing to make it look natural (not too dense)
        if edge_pos not in path_positions and i % 3 == 0:  # Every 3rd water edge tile
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
    """Find a detour around water.
    
    Args:
        current_x, current_y: Current position
        angle: Original direction angle in degrees
        water_positions: Set of water positions to avoid
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        
    Returns:
        Tuple of new (x, y) coordinates, or None if no detour found
    """
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
    """Create a ring of paths around the center.
    
    Args:
        paths: List to add path tiles to
        path_positions: Set of existing path positions
        water_positions: Set of water positions to avoid
        center_x, center_y: Center coordinates
        ring_radius: Radius of the ring
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
    """
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
            
            # Skip if out of bounds or on water or already a path
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
                            grid_size, tile_size, assets, building_sizes, target_building_count):
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
    """Create different zones in the village (waterfront, center, outskirts).
    
    Args:
        path_positions: Set of path positions
        water_positions: Set of water positions
        village_center_x, village_center_y: Center coordinates of the village
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        
    Returns:
        Tuple of (waterfront_zone, center_zone, outskirts_zone) sets
    """
    waterfront_zone = set()  # Near water
    center_zone = set()      # Near village center
    outskirts_zone = set()   # Further out
    
    # Define zone distances
    center_radius = grid_size // 8
    outskirts_radius = grid_size // 3
    
    # Identify waterfront paths (paths adjacent to water)
    for path_pos in path_positions:
        px, py = path_pos
        
        # Check if this path is near water
        is_waterfront = is_near_water(px, py, water_positions, tile_size)
        
        if is_waterfront:
            waterfront_zone.add(path_pos)
            continue
            
        # Check if path is in center zone
        dist_to_center = utils.calculate_distance(px, py, village_center_x, village_center_y)
        if dist_to_center < center_radius:
            center_zone.add(path_pos)
        elif dist_to_center < outskirts_radius:
            outskirts_zone.add(path_pos)
            
    return waterfront_zone, center_zone, outskirts_zone

def is_near_water(x, y, water_positions, tile_size):
    """Check if a position is near water.
    
    Args:
        x, y: Position coordinates
        water_positions: Set of water positions
        tile_size: Size of a tile in pixels
        
    Returns:
        Boolean indicating if the position is near water
    """
    for dx in [-tile_size, 0, tile_size]:
        for dy in [-tile_size, 0, tile_size]:
            if dx == 0 and dy == 0:
                continue  # Skip self
                
            check_pos = (x + dx, y + dy)
            if check_pos in water_positions:
                return True
                
    return False

def place_zone_buildings(buildings, zone_paths, water_positions, path_positions, 
                        occupied_spaces, grid_size, tile_size, assets, building_sizes, 
                        target_count, zone_type):
    """Place buildings in a specific zone.
    
    Args:
        buildings: List to add building data to
        zone_paths: List of path positions in this zone
        water_positions: Set of water positions
        path_positions: Set of all path positions
        occupied_spaces: Set of occupied positions to update
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        assets: Dictionary of game assets
        building_sizes: Dictionary of building sizes
        target_count: Target number of buildings for this zone
        zone_type: Type of zone ("waterfront", "center", "outskirts")
    """
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
    """Get building size and type distributions for a zone.
    
    Args:
        zone_type: Type of zone ("waterfront", "center", "outskirts")
        
    Returns:
        Tuple of (size_weights, type_weights) dictionaries
    """
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

def try_place_building(buildings, path_pos, water_positions, path_positions, 
                      occupied_spaces, grid_size, tile_size, assets, 
                      building_sizes, size_weights, type_weights):
    """Try to place a building near a path.
    
    Args:
        buildings: List to add building data to
        path_pos: Position of the path to place near
        water_positions: Set of water positions
        path_positions: Set of all path positions
        occupied_spaces: Set of occupied positions
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        assets: Dictionary of game assets
        building_sizes: Dictionary of building sizes
        size_weights: Dictionary of weights for building sizes
        type_weights: Dictionary of weights for building types
        
    Returns:
        Boolean indicating if building was successfully placed
    """
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
        if is_footprint_valid(building_x, building_y, footprint_tiles, tile_size, 
                             water_positions, path_positions, occupied_spaces):
            
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
                for dx in range(-buffer_tiles, footprint_tiles + buffer_tiles):
                    for dy in range(-buffer_tiles, footprint_tiles + buffer_tiles):
                        check_x = building_x + dx * tile_size
                        check_y = building_y + dy * tile_size
                        
                        # Skip if out of bounds
                        if utils.is_in_bounds(check_x, check_y, grid_size):
                            occupied_spaces.add((check_x, check_y))
                
                # Successfully placed a building
                return True
    
    # Could not place a building
    return False

def is_footprint_valid(building_x, building_y, footprint_tiles, tile_size,
                      water_positions, path_positions, occupied_spaces):
    """Check if a building footprint is valid.
    
    Args:
        building_x, building_y: Building position
        footprint_tiles: Size of building footprint in tiles
        tile_size: Size of a tile in pixels
        water_positions: Set of water positions
        path_positions: Set of path positions
        occupied_spaces: Set of occupied positions
        
    Returns:
        Boolean indicating if footprint is valid
    """
    for dx in range(footprint_tiles):
        for dy in range(footprint_tiles):
            check_x = building_x + dx * tile_size
            check_y = building_y + dy * tile_size
            check_pos = (check_x, check_y)
            
            if (check_pos in water_positions or 
                check_pos in path_positions or 
                check_pos in occupied_spaces):
                return False
                
    return True

def is_buffer_valid(building_x, building_y, footprint_tiles, buffer_tiles, tile_size,
                   grid_size, occupied_spaces, path_positions):
    """Check if the buffer zone around a building is valid.
    
    Args:
        building_x, building_y: Building position
        footprint_tiles: Size of building footprint in tiles
        buffer_tiles: Size of buffer in tiles
        tile_size: Size of a tile in pixels
        grid_size: Size of the grid in pixels
        occupied_spaces: Set of occupied positions
        path_positions: Set of path positions
        
    Returns:
        Boolean indicating if buffer is valid
    """
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

def place_trees_improved(trees, path_positions, building_positions, water_positions, grid_size, tile_size, size, target_tree_count):
    """Place trees with improved spacing logic to avoid buildings and roads."""
    # Track occupied tree positions
    tree_positions = set()
    
    # Different tree distribution zones
    forest_zones = create_forest_zones(grid_size, tile_size, size)
    
    # Track attempts to avoid infinite loops
    attempts = 0
    max_attempts = target_tree_count * 3
    
    # Place trees
    while len(trees) < target_tree_count and attempts < max_attempts:
        attempts += 1
        
        # Decide where to try placing a tree
        if random.random() < 0.7:  # 70% in forest zones
            tree_pos = place_tree_in_forest(forest_zones, grid_size, tile_size)
        else:
            # Random position anywhere
            tree_pos = place_tree_randomly(grid_size, tile_size)
        
        x, y = tree_pos
        
        # Skip if out of bounds
        if not utils.is_in_bounds(x, y, grid_size):
            continue
            
        # Check if position is valid
        if (tree_pos in path_positions or
            tree_pos in building_positions or
            tree_pos in water_positions or
            tree_pos in tree_positions):
            continue
            
        # Check for minimum spacing between trees
        if is_too_close_to_other_trees(tree_pos, tree_positions, tile_size):
            continue
            
        # Add the tree
        tree_variant = random.randint(1, 5)  # 5 tree variants
        trees.append({
            'position': (x, y),
            'variant': tree_variant
        })
        
        # Mark position as occupied
        tree_positions.add(tree_pos)

def create_forest_zones(grid_size, tile_size, size):
    """Create forest zones for tree placement.
    
    Args:
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        size: Size parameter
        
    Returns:
        List of (x, y, radius) tuples defining forest zones
    """
    forest_zones = []
    
    # Create 4-6 forest zones randomly placed around the map
    num_forests = random.randint(4, 6)
    for _ in range(num_forests):
        forest_x = random.randint(tile_size * 5, grid_size - tile_size * 5)
        forest_y = random.randint(tile_size * 5, grid_size - tile_size * 5)
        forest_radius = random.randint(grid_size // 12, grid_size // 8)
        forest_zones.append((forest_x, forest_y, forest_radius))
        
    return forest_zones

def place_tree_in_forest(forest_zones, grid_size, tile_size):
    """Place a tree within a forest zone.
    
    Args:
        forest_zones: List of (x, y, radius) tuples defining forest zones
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        
    Returns:
        Tuple of (x, y) coordinates
    """
    # Select a random forest zone
    forest_x, forest_y, forest_radius = random.choice(forest_zones)
    
    # Place within this forest with random distribution
    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(0, forest_radius)
    
    x, y = utils.polar_to_cartesian(forest_x, forest_y, angle, distance)
    
    # Align to grid
    return utils.align_to_grid(x, y, tile_size)

def place_tree_randomly(grid_size, tile_size):
    """Place a tree at a random position.
    
    Args:
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        
    Returns:
        Tuple of (x, y) coordinates
    """
    x = random.randint(0, grid_size - tile_size)
    y = random.randint(0, grid_size - tile_size)
    
    # Align to grid
    return utils.align_to_grid(x, y, tile_size)

def is_too_close_to_other_trees(tree_pos, tree_positions, tile_size):
    """Check if a position is too close to existing trees.
    
    Args:
        tree_pos: Position to check (x, y)
        tree_positions: Set of existing tree positions
        tile_size: Size of a tile in pixels
        
    Returns:
        Boolean indicating if position is too close
    """
    x, y = tree_pos
    
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            near_pos = (x + dx * tile_size, y + dy * tile_size)
            if near_pos in tree_positions:
                return True
                
    return False
