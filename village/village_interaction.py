import random
import math
import utils

def analyze_interaction_points(village):
    """Analyze buildings and environment to identify interaction points.
    
    Args:
        village: Village instance
    """
    print("Analyzing interaction points...")
    
    # Analyze buildings for interaction points
    for building_id, building in enumerate(village.buildings):
        building_type = building.get('building_type', '')
        position = building['position']
        
        # Determine building size in pixels
        size_name = building['size']
        size_multiplier = 3 if size_name == 'large' else (2 if size_name == 'medium' else 1)
        size_px = size_multiplier * village.tile_size
        
        # Find door position (usually bottom center of building)
        door_pos = (position[0] + size_px // 2, position[1] + size_px)
        
        # Check if the bottom of the building is near water
        # If so, likely the door is on one of the other sides
        bottom_water = False
        for dx in range(-village.tile_size, village.tile_size * 2, village.tile_size):
            check_pos = (door_pos[0] + dx, door_pos[1])
            if check_pos in village.water_positions:
                bottom_water = True
                break
                
        if bottom_water:
            # Try other sides - left, right, then top
            left_side_valid = True
            for dy in range(-village.tile_size, village.tile_size * 2, village.tile_size):
                check_pos = (position[0], position[1] + size_px // 2 + dy)
                if check_pos in village.water_positions:
                    left_side_valid = False
                    break
                    
            if left_side_valid:
                # Door likely on left side
                door_pos = (position[0], position[1] + size_px // 2)
            else:
                # Check right side
                right_side_valid = True
                for dy in range(-village.tile_size, village.tile_size * 2, village.tile_size):
                    check_pos = (position[0] + size_px, position[1] + size_px // 2 + dy)
                    if check_pos in village.water_positions:
                        right_side_valid = False
                        break
                        
                if right_side_valid:
                    # Door likely on right side
                    door_pos = (position[0] + size_px, position[1] + size_px // 2)
                else:
                    # Door likely on top side
                    door_pos = (position[0] + size_px // 2, position[1])
        
        # For path-adjacent buildings, place door near path
        door_placed = False
        for offset_x in range(-1, 2):
            for offset_y in range(-1, 2):
                check_x = door_pos[0] + offset_x * village.tile_size
                check_y = door_pos[1] + offset_y * village.tile_size
                
                if (check_x, check_y) in village.path_positions:
                    # Update door position to be near path
                    door_pos = (check_x, check_y)
                    door_placed = True
                    break
            if door_placed:
                break
        
        # Add door interaction point
        door_point = {
            'type': 'door',
            'position': door_pos,
            'building_id': building_id,
            'properties': {'is_entrance': True}
        }
        
        # Add building-specific interaction points
        interior_points = generate_interior_points(
            building_type, position, size_px, building_id, village.tile_size)
        
        # Add to building and to global list
        building['interaction_points'] = [door_point] + interior_points
        village.interaction_points.extend([door_point] + interior_points)
    
    # Analyze natural features (water edges, bridges, etc.)
    find_water_interaction_points(village)
    
    print(f"Added {len(village.interaction_points)} interaction points")

def generate_interior_points(building_type, position, size_px, building_id, tile_size):
    """Generate interior interaction points based on building type.
    
    Args:
        building_type: Type of building (e.g., "House", "Inn", "Store")
        position: Building position (x, y)
        size_px: Building size in pixels
        building_id: Building identifier
        tile_size: Size of each tile in pixels
        
    Returns:
        List of interior interaction points
    """
    interior_points = []
    
    # Generate different interaction points based on building type
    if building_type == "House" or building_type == "Cottage":
        # Add bed
        bed_pos = (position[0] + size_px // 4, position[1] + size_px // 4)
        bed_point = {
            'type': 'furniture',
            'position': bed_pos,
            'building_id': building_id,
            'properties': {'furniture_type': 'bed'}
        }
        interior_points.append(bed_point)
        
        # Add table
        table_pos = (position[0] + size_px * 3 // 4, position[1] + size_px * 3 // 4)
        table_point = {
            'type': 'furniture',
            'position': table_pos,
            'building_id': building_id,
            'properties': {'furniture_type': 'table'}
        }
        interior_points.append(table_point)
    
    elif building_type == "Inn" or building_type == "Tavern":
        # Add multiple tables
        for i in range(2):
            for j in range(2):
                table_pos = (
                    position[0] + (i+1) * size_px // 3,
                    position[1] + (j+1) * size_px // 3
                )
                table_point = {
                    'type': 'furniture',
                    'position': table_pos,
                    'building_id': building_id,
                    'properties': {'furniture_type': 'table'}
                }
                interior_points.append(table_point)
    
    elif building_type == "Store" or building_type == "Market":
        # Add counter
        counter_pos = (position[0] + size_px // 2, position[1] + size_px * 3 // 4)
        counter_point = {
            'type': 'furniture',
            'position': counter_pos,
            'building_id': building_id,
            'properties': {'furniture_type': 'counter'}
        }
        interior_points.append(counter_point)
        
        # Add display shelves
        for i in range(2):
            shelf_pos = (
                position[0] + (i+1) * size_px // 3,
                position[1] + size_px // 4
            )
            shelf_point = {
                'type': 'furniture',
                'position': shelf_pos,
                'building_id': building_id,
                'properties': {'furniture_type': 'shelf'}
            }
            interior_points.append(shelf_point)
    
    elif building_type == "Smithy" or building_type == "Workshop":
        # Add workbench
        workbench_pos = (position[0] + size_px // 2, position[1] + size_px // 2)
        workbench_point = {
            'type': 'furniture',
            'position': workbench_pos,
            'building_id': building_id,
            'properties': {'furniture_type': 'workbench'}
        }
        interior_points.append(workbench_point)
        
        # Add anvil (for smithy)
        if building_type == "Smithy":
            anvil_pos = (position[0] + size_px * 3 // 4, position[1] + size_px // 4)
            anvil_point = {
                'type': 'furniture',
                'position': anvil_pos,
                'building_id': building_id,
                'properties': {'furniture_type': 'anvil'}
            }
            interior_points.append(anvil_point)
    
    elif building_type == "Bakery":
        # Add oven
        oven_pos = (position[0] + size_px // 4, position[1] + size_px // 4)
        oven_point = {
            'type': 'furniture',
            'position': oven_pos,
            'building_id': building_id,
            'properties': {'furniture_type': 'oven'}
        }
        interior_points.append(oven_point)
        
        # Add counter
        counter_pos = (position[0] + size_px * 3 // 4, position[1] + size_px * 3 // 4)
        counter_point = {
            'type': 'furniture',
            'position': counter_pos,
            'building_id': building_id,
            'properties': {'furniture_type': 'counter'}
        }
        interior_points.append(counter_point)
    
    elif building_type == "Town Hall":
        # Add desk
        desk_pos = (position[0] + size_px // 2, position[1] + size_px // 4)
        desk_point = {
            'type': 'furniture',
            'position': desk_pos,
            'building_id': building_id,
            'properties': {'furniture_type': 'desk'}
        }
        interior_points.append(desk_point)
        
        # Add meeting table
        table_pos = (position[0] + size_px // 2, position[1] + size_px * 3 // 4)
        table_point = {
            'type': 'furniture',
            'position': table_pos,
            'building_id': building_id,
            'properties': {'furniture_type': 'table'}
        }
        interior_points.append(table_point)
    
    # For any other building type, add a generic interaction point
    if not interior_points:
        generic_pos = (position[0] + size_px // 2, position[1] + size_px // 2)
        generic_point = {
            'type': 'furniture',
            'position': generic_pos,
            'building_id': building_id,
            'properties': {'furniture_type': 'generic'}
        }
        interior_points.append(generic_point)
    
    return interior_points

def find_water_interaction_points(village):
    def fishing_spot_filter(x, y, cell_data):
        # Position must be adjacent to water but not water itself
        pos = (x, y)
        if pos in village.water_positions:
            return False
            
        # Check if adjacent to water
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            if (x + dx * village.tile_size, y + dy * village.tile_size) in village.water_positions:
                return True
                
        return False
        
    def fishing_spot_processor(x, y, cell_data):
        pos = (x, y)
        # Classify water type
        water_type = classify_water_feature(pos, village)
        
        # Create properties
        properties = {
            'water_type': water_type,
            'elevated': False,
            'covered': False,
            'near_village': is_near_village_center(pos, village)
        }
        
        # Create interaction point
        fishing_spot = {
            'position': pos,
            'type': 'fishing_spot',
            'building_id': None,
            'properties': properties
        }
        
        village.interaction_points.append(fishing_spot)
        return fishing_spot
    
    return utils.scan_terrain(village, None, fishing_spot_filter, fishing_spot_processor)

def classify_water_feature(position, village):
    """Classify a water-adjacent position as being near a lake or river.
    
    Args:
        position: The position to classify
        village: Village instance
        
    Returns:
        String "lake" or "river" describing the water feature
    """
    # Count water tiles in increasing radius to determine feature type
    px, py = position
    water_counts = []
    
    # Check in concentric rings of increasing size
    for radius in range(1, 6):
        water_in_radius = 0
        total_in_radius = 0
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                # Only check positions exactly at this radius (ring)
                if max(abs(dx), abs(dy)) == radius:
                    check_pos = (px + dx * village.tile_size, py + dy * village.tile_size)
                    if check_pos in village.water_positions:
                        water_in_radius += 1
                    total_in_radius += 1
        
        # Store the ratio of water tiles to total tiles at this radius
        water_counts.append(water_in_radius / total_in_radius if total_in_radius > 0 else 0)
    
    # Lakes tend to have more water tiles in larger rings
    # Rivers tend to have fewer water tiles as radius increases
    
    # Simple heuristic:
    # - If water density stays high as radius increases, it's a lake
    # - If water density drops off quickly, it's a river
    if water_counts[3] > 0.3 and water_counts[4] > 0.25:
        return "lake"
    else:
        return "river"

def is_position_occupied(position, village):
    """Check if a position is occupied by buildings or other non-walkable features.
    
    Args:
        position: The (x, y) position to check
        village: Village instance
        
    Returns:
        Boolean indicating if the position is occupied
    """
    # Check if position is occupied by a building
    if position in village.building_positions:
        return True
    
    # If we have tree positions, check those too
    for tree in village.trees:
        tx, ty = tree['position']
        # Simple collision check for trees (assuming tree is 1 tile)
        if tx == position[0] and ty == position[1]:
            return True
    
    return False

def is_near_village_center(position, village):
    """Determine if a position is near the village center.
    
    Args:
        position: The (x, y) position to check
        village: Village instance
        
    Returns:
        Float value between 0.0 and 1.0 indicating proximity to village center
        (1.0 means at the center, 0.0 means furthest away)
    """
    # Calculate distance from center
    px, py = position
    distance = utils.calculate_distance(
        px, py, 
        village.village_center_x, village.village_center_y
    )
    
    # Normalize to a 0-1 scale (1 at center, 0 at max distance)
    max_distance = ((village.grid_size // 2) ** 2 + (village.grid_size // 2) ** 2) ** 0.5
    proximity = 1.0 - (distance / max_distance if max_distance > 0 else 0)
    
    return max(0.0, min(1.0, proximity))  # Clamp to 0-1 range
