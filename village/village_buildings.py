import random
import math
import utils
from .village_paths import create_direct_path_with_cardinal_adjacency

def place_zone_buildings_scan(village, zone, target_count, zone_type, building_sizes, occupied_spaces):
    """Place buildings in a specific zone using the scan_terrain function.
    
    Args:
        village: Village instance
        zone: Set of path positions in the zone
        target_count: Target number of buildings to place
        zone_type: Zone type ("waterfront", "center", or "outskirts")
        building_sizes: Dictionary mapping size names to pixel sizes
        occupied_spaces: Set of occupied positions
    """
    # Skip if no valid paths in this zone
    if not zone or target_count <= 0:
        return
    
    # Determine building sizes and types based on zone
    size_weights, type_weights = get_zone_building_distributions(zone_type)
    
    # Convert zone positions to list for random selection
    zone_paths = list(zone)
    
    # Keep track of buildings placed
    total_buildings_placed = 0
    
    # Try to place buildings until we reach the target count or run out of attempts
    for attempt in range(target_count * 3):  # Allow up to 3x attempts than needed
        if total_buildings_placed >= target_count:
            break
            
        if not zone_paths:  # Stop if we run out of valid paths
            break
            
        # Pick a random path position as center point for scanning
        path_pos = random.choice(zone_paths)
        x, y = path_pos
        
        # Define bounds around this path position for scanning
        bounds = (
            x - village.tile_size * 5,  # 5 tiles radius around the path
            y - village.tile_size * 5,
            x + village.tile_size * 5,
            y + village.tile_size * 5
        )
        
        # Use nonlocal variable to track buildings placed within the processor
        buildings_placed_this_scan = 0
        
        # Define filter function for scan_terrain
        def building_filter(pos_x, pos_y, cell_data):
            # Skip water, existing paths, and occupied spaces
            pos = (pos_x, pos_y)
            if cell_data.get('water') or cell_data.get('path') or pos in occupied_spaces:
                return False
            
            # Check for zone membership - confirm it's close enough to a path in the zone
            if not any(utils.calculate_distance(pos_x, pos_y, 
                                                path[0], path[1]) < village.tile_size * 3 
                      for path in zone_paths):
                return False
            
            # Choose a random size based on zone weights (but don't place yet)
            size = random.choices(list(size_weights.keys()), 
                                 weights=list(size_weights.values()), k=1)[0]
            footprint_tiles = building_sizes[size] // village.tile_size
            
            # Check if the building footprint is valid here
            return is_footprint_valid(village, pos_x, pos_y, footprint_tiles, occupied_spaces)
        
        # In the place_zone_buildings_scan function, update the building_processor function:
        def building_processor(pos_x, pos_y, cell_data):
            nonlocal buildings_placed_this_scan
            
            # We've placed enough buildings in this scan
            if buildings_placed_this_scan >= 1:  # Only place one building per scan for better distribution
                return None
                
            # Choose building size based on weights
            size = random.choices(list(size_weights.keys()), 
                                weights=list(size_weights.values()), k=1)[0]
            footprint_tiles = building_sizes[size] // village.tile_size
            
            # Double check that this is still valid (things might have changed)
            if not is_footprint_valid(village, pos_x, pos_y, footprint_tiles, occupied_spaces):
                return None
                
            # Check if there's enough buffer space
            buffer_tiles = 1 if size == "small" else 2
            if not is_buffer_valid(village, pos_x, pos_y, footprint_tiles, buffer_tiles, occupied_spaces):
                return None
            
            # Choose building type based on zone
            building_type = random.choices(
                list(type_weights.keys()),
                weights=list(type_weights.values()),
                k=1
            )[0]
            
            # Create the building
            building = {
                'position': (pos_x, pos_y),
                'size': size,
                'building_type': building_type
            }
            
            # Add to village buildings list
            village.buildings.append(building)
            
            # Mark spaces as occupied
            # 1. The building footprint itself
            for dx in range(footprint_tiles):
                for dy in range(footprint_tiles):
                    occupied_spaces.add((pos_x + dx * village.tile_size, 
                                    pos_y + dy * village.tile_size))
            
            # 2. The buffer zone around building (but not building itself)
            for dx in range(-buffer_tiles, footprint_tiles + buffer_tiles):
                for dy in range(-buffer_tiles, footprint_tiles + buffer_tiles):
                    # Skip the actual building footprint
                    if 0 <= dx < footprint_tiles and 0 <= dy < footprint_tiles:
                        continue
                        
                    buffer_pos = (pos_x + dx * village.tile_size, 
                                pos_y + dy * village.tile_size)
                    if utils.is_in_bounds(buffer_pos[0], buffer_pos[1], village.grid_size):
                        occupied_spaces.add(buffer_pos)
            
            # Remove any trees that overlap with this building
            trees_to_remove = []
            for i, tree in enumerate(village.trees):
                tree_pos = tree['position']
                tree_x, tree_y = tree_pos
                # Check if tree is within building footprint
                if (pos_x <= tree_x < pos_x + footprint_tiles * village.tile_size and
                    pos_y <= tree_y < pos_y + footprint_tiles * village.tile_size):
                    trees_to_remove.append(i)
            
            # Remove trees in reverse order to maintain correct indices
            for i in sorted(trees_to_remove, reverse=True):
                del village.trees[i]
            
            if trees_to_remove:
                print(f"  Removed {len(trees_to_remove)} trees when placing {building_type}")
            
            # Successfully placed building
            buildings_placed_this_scan += 1
            return building
        # Use the scan_terrain function to try to place buildings
        placed_buildings = utils.scan_terrain(village, bounds, building_filter, building_processor)
        
        # Update total count
        if placed_buildings:
            total_buildings_placed += len(placed_buildings)
        
        # Remove used path to avoid concentrating buildings in one area
        if path_pos in zone_paths:
            zone_paths.remove(path_pos)
    
    print(f"  Placed {total_buildings_placed}/{target_count} buildings in {zone_type} zone")

def place_buildings(village):
    """Place buildings in the village in different zones.
    
    Args:
        village: Village instance
        
    Returns:
        Dictionary with updated village properties
    """
    print("Placing buildings...")
    
    # Define building sizes in pixels
    building_sizes = {
        "small": village.tile_size,
        "medium": village.tile_size * 2,
        "large": village.tile_size * 3
    }
    
    # Create a set to track occupied positions
    occupied_spaces = set()
    
    # Add water and path positions to occupied spaces
    occupied_spaces.update(village.water_positions)
    
    # Create village zones
    waterfront_zone, center_zone, outskirts_zone = create_village_zones(village)
    
    # Number of buildings to place in each zone
    # Scale building count with village size
    scale_factor = (village.grid_size / 1000) ** 2
    buildings_in_center = int(8 * scale_factor)
    buildings_in_waterfront = int(6 * scale_factor)
    buildings_in_outskirts = int(12 * scale_factor)
    
    print(f"Building targets: {buildings_in_center} center, {buildings_in_waterfront} waterfront, {buildings_in_outskirts} outskirts")
    
    # Place buildings in each zone
    place_zone_buildings_scan(village, center_zone, buildings_in_center, "center", building_sizes, occupied_spaces)
    place_zone_buildings_scan(village, waterfront_zone, buildings_in_waterfront, "waterfront", building_sizes, occupied_spaces)
    place_zone_buildings_scan(village, outskirts_zone, buildings_in_outskirts, "outskirts", building_sizes, occupied_spaces)
    
    # Ensure all buildings have a type
    assign_building_types(village)
    
    # Update building positions for quick lookup
    update_building_positions(village, building_sizes)
    
    # Remove trees that overlap with buildings
    village._remove_trees_under_buildings()
    
    print(f"Placed {len(village.buildings)} buildings")
    
    return {
        'buildings': village.buildings,
        'building_positions': village.building_positions
    }
def create_village_zones(village):
    """Create different zones in the village (waterfront, center, outskirts).
    
    Args:
        village: Village instance
        
    Returns:
        Tuple of (waterfront_zone, center_zone, outskirts_zone) sets
    """
    waterfront_zone = set()  # Near water
    center_zone = set()      # Near village center
    outskirts_zone = set()   # Further out
    
    # Define zone distances
    center_radius = village.grid_size // 8
    outskirts_radius = village.grid_size // 3
    
    # Identify zones based on paths
    for path_pos in village.path_positions:
        # Check if this path is near water
        is_waterfront = is_near_water(village, path_pos[0], path_pos[1])
        
        if is_waterfront:
            waterfront_zone.add(path_pos)
            continue
            
        # Check if path is in center or outskirts zone
        dist_to_center = utils.calculate_distance(
            path_pos[0], path_pos[1], 
            village.village_center_x, village.village_center_y
        )
        
        if dist_to_center < center_radius:
            center_zone.add(path_pos)
        elif dist_to_center < outskirts_radius:
            outskirts_zone.add(path_pos)
                
    return waterfront_zone, center_zone, outskirts_zone

def is_near_water(village, x, y):
    """Check if a position is near water.
    
    Args:
        village: Village instance
        x, y: Position coordinates
        
    Returns:
        Boolean indicating if the position is near water
    """
    for neighbor_pos in utils.get_neighbors(x, y, village.tile_size):
        if neighbor_pos in village.water_positions:
            return True
    return False

def get_zone_building_distributions(zone_type):
    """Get building size and type distributions for a zone.
    
    Args:
        zone_type: Zone type ("waterfront", "center", or "outskirts")
        
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

def is_footprint_valid(village, building_x, building_y, footprint_tiles, occupied_spaces):
    """Check if a building footprint is valid.
    
    Args:
        village: Village instance
        building_x, building_y: Building position
        footprint_tiles: Size of footprint in tiles
        occupied_spaces: Set of occupied positions
        
    Returns:
        Boolean indicating if the footprint is valid
    """
    # Check all tiles in the building footprint
    for dx in range(footprint_tiles):
        for dy in range(footprint_tiles):
            pos = (building_x + dx * village.tile_size, building_y + dy * village.tile_size)
            
            # Skip if out of bounds
            if not utils.is_in_bounds(pos[0], pos[1], village.grid_size):
                return False
            
            # Skip if position is water, path, or already occupied
            if (pos in village.water_positions or pos in village.path_positions or 
                pos in occupied_spaces or pos in village.building_positions):
                return False
                
    return True

def is_buffer_valid(village, building_x, building_y, footprint_tiles, buffer_tiles, occupied_spaces):
    """Check if the buffer zone around a building is valid.
    
    Args:
        village: Village instance
        building_x, building_y: Building position
        footprint_tiles: Size of footprint in tiles
        buffer_tiles: Size of buffer in tiles
        occupied_spaces: Set of occupied positions
        
    Returns:
        Boolean indicating if the buffer is valid
    """
    # Check buffer zone around the building (excluding the building itself)
    for dx in range(-buffer_tiles, footprint_tiles + buffer_tiles):
        for dy in range(-buffer_tiles, footprint_tiles + buffer_tiles):
            # Skip checking the actual building footprint
            if 0 <= dx < footprint_tiles and 0 <= dy < footprint_tiles:
                continue
                
            check_x = building_x + dx * village.tile_size
            check_y = building_y + dy * village.tile_size
            
            # Skip if out of bounds
            if not utils.is_in_bounds(check_x, check_y, village.grid_size):
                continue
            
            check_pos = (check_x, check_y)
            
            # Allow buffer to overlap with paths (buildings can be near paths)
            # But don't allow overlap with other buildings' occupied spaces
            if check_pos in occupied_spaces and check_pos not in village.path_positions:
                return False
                
    return True

def assign_building_types(village):
    """Assign building types to buildings (house, store, inn, etc.).
    
    Args:
        village: Village instance
    """
    # This should only be used for buildings that don't already have a type
    for building in village.buildings:
        if 'building_type' not in building or not building['building_type']:
            size = building['size']
            building_types = {
                "small": ["House", "Cottage", "Workshop", "Storage"],
                "medium": ["Inn", "Store", "Tavern", "Smithy", "Bakery"],
                "large": ["Town Hall", "Market", "Temple", "Manor"]
            }
            available_types = building_types.get(size, ["House"])
            building['building_type'] = random.choice(available_types)

def update_building_positions(village, building_sizes):
    """Update the building positions set with all tiles occupied by buildings.
    
    Args:
        village: Village instance
        building_sizes: Dictionary mapping size names to pixel sizes
    """
    village.building_positions = set()
    for building in village.buildings:
        position = building['position']
        size_name = building['size']
        size_px = building_sizes[size_name]
        footprint_tiles = size_px // village.tile_size
        
        # Add all tiles in the building footprint
        for dx in range(footprint_tiles):
            for dy in range(footprint_tiles):
                village.building_positions.add((position[0] + dx * village.tile_size, 
                                              position[1] + dy * village.tile_size))

def connect_buildings_to_paths(village):
    """Ensure that each building has a path connecting it to the existing path network.
    
    Args:
        village: Village instance
    """
    print("Connecting buildings to paths...")
    
    # Process each building
    for building in village.buildings:
        # Get building properties
        building_pos = building['position']
        building_size_name = building['size']
        
        # Convert size name to pixel size
        building_size_px = 3 * village.tile_size if building_size_name == 'large' else (
                          2 * village.tile_size if building_size_name == 'medium' else village.tile_size)
        
        # Calculate building footprint size in tiles
        footprint_tiles = building_size_px // village.tile_size
        
        # Generate building perimeter positions - these are possible door locations
        perimeter_positions = []
        
        # Focus on cardinal sides only for door placement (no corners)
        # Bottom side - priority for door position
        for x in range(0, footprint_tiles):
            perimeter_positions.append((
                building_pos[0] + x * village.tile_size,
                building_pos[1] + footprint_tiles * village.tile_size
            ))
        
        # Right side
        for y in range(0, footprint_tiles):
            perimeter_positions.append((
                building_pos[0] + footprint_tiles * village.tile_size,
                building_pos[1] + y * village.tile_size
            ))
        
        # Top side
        for x in range(0, footprint_tiles):
            perimeter_positions.append((
                building_pos[0] + x * village.tile_size,
                building_pos[1] - village.tile_size
            ))
        
        # Left side
        for y in range(0, footprint_tiles):
            perimeter_positions.append((
                building_pos[0] - village.tile_size,
                building_pos[1] + y * village.tile_size
            ))
        
        # Check if building already has a path adjacent to it
        has_adjacent_path = False
        
        for perimeter_pos in perimeter_positions:
            if perimeter_pos in village.path_positions:
                has_adjacent_path = True
                break
        
        # If building already has adjacent path, skip to next building
        if has_adjacent_path:
            continue
        
        # Find closest path to this building
        closest_path = None
        min_distance = float('inf')
        
        for path_pos in village.path_positions:
            distance = utils.calculate_distance(
                building_pos[0] + building_size_px // 2, 
                building_pos[1] + building_size_px // 2,
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
        create_direct_path_with_cardinal_adjacency(village, door_pos, closest_path)
