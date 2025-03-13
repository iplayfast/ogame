import pygame
import random
import math
import os
from PIL import Image

def create_directories(base_dirs=None):
    """Create standard directory structure for assets.
    
    Args:
        base_dirs: List of additional directories to create
    """
    directories = [
        "assets",
        "assets/characters",
        "assets/buildings",
        "assets/buildings/roofs",
        "assets/environment",
        "assets/ui"
    ]
    
    # Add any additional directories
    if base_dirs:
        directories.extend(base_dirs)
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def vary_color(base_color, range_r=15, range_g=15, range_b=15):
    """Create a slight variation of a base color.
    
    Args:
        base_color: Base RGB color tuple (r, g, b)
        range_r: Range of red variation
        range_g: Range of green variation
        range_b: Range of blue variation
        
    Returns:
        Tuple with varied RGB color
    """
    return (
        max(0, min(255, base_color[0] + random.randint(-range_r, range_r))),
        max(0, min(255, base_color[1] + random.randint(-range_g, range_g))),
        max(0, min(255, base_color[2] + random.randint(-range_b, range_b)))
    )

def darken_color(color, amount):
    """Darken a color by a specified amount.
    
    Args:
        color: RGB color tuple
        amount: Amount to darken each component
        
    Returns:
        Darkened RGB color tuple
    """
    return (
        max(0, color[0] - amount),
        max(0, color[1] - amount),
        max(0, color[2] - amount)
    )

def lighten_color(color, amount):
    """Lighten a color by a specified amount.
    
    Args:
        color: RGB color tuple
        amount: Amount to lighten each component
        
    Returns:
        Lightened RGB color tuple
    """
    return (
        min(255, color[0] + amount),
        min(255, color[1] + amount),
        min(255, color[2] + amount)
    )

def add_texture(draw, rect, base_color, density=100, skip_areas=None):
    """Add texture to a rectangular area, skipping specified areas.
    
    Args:
        draw: PIL ImageDraw instance
        rect: Rectangle coordinates (x1, y1, x2, y2)
        base_color: Base color to vary for texture
        density: Number of texture points to add
        skip_areas: List of areas to skip [(x1, y1, x2, y2), ...]
    """
    x1, y1, x2, y2 = rect
    for _ in range(density):
        px = random.randint(x1, x2)
        py = random.randint(y1, y2)
        
        # Skip areas if specified
        if skip_areas:
            skip = False
            for area in skip_areas:
                ax1, ay1, ax2, ay2 = area
                if ax1 <= px <= ax2 and ay1 <= py <= ay2:
                    skip = True
                    break
            if skip:
                continue
        
        # Slightly vary the color for texture
        texture_color = vary_color(base_color)
        draw.point((px, py), fill=texture_color)

def rounded_rect(draw, rect, color, radius):
    """Draw a rectangle with rounded corners.
    
    Args:
        draw: PIL ImageDraw instance
        rect: Rectangle coordinates (x1, y1, x2, y2)
        color: Fill color
        radius: Corner radius
    """
    x1, y1, x2, y2 = rect
    
    # Draw the middle rectangle
    draw.rectangle((x1, y1 + radius, x2, y2 - radius), fill=color)
    draw.rectangle((x1 + radius, y1, x2 - radius, y2), fill=color)
    
    # Draw the four corner circles
    draw.ellipse((x1, y1, x1 + radius * 2, y1 + radius * 2), fill=color)
    draw.ellipse((x1, y2 - radius * 2, x1 + radius * 2, y2), fill=color)
    draw.ellipse((x2 - radius * 2, y1, x2, y1 + radius * 2), fill=color)
    draw.ellipse((x2 - radius * 2, y2 - radius * 2, x2, y2), fill=color)

def draw_ellipse_with_outline(draw, rect, fill_color, outline_color=None, width=1):
    """Draw an ellipse with optional outline.
    
    Args:
        draw: PIL ImageDraw instance
        rect: Rectangle coordinates (x1, y1, x2, y2)
        fill_color: Fill color for ellipse
        outline_color: Outline color (None for no outline)
        width: Outline width
    """
    draw.ellipse(rect, fill=fill_color)
    if outline_color:
        draw.ellipse(rect, outline=outline_color, width=width)

def generate_sine_wave(frequency, duration, sample_rate=44100):
    """Generate a simple sine wave sound for testing.
    
    Args:
        frequency: Frequency of the sound in Hz
        duration: Duration of the sound in seconds
        sample_rate: Sample rate in samples per second
        
    Returns:
        bytearray containing the sound data
    """
    num_samples = int(duration * sample_rate)
    buf = bytearray(num_samples)
    
    for i in range(num_samples):
        t = i / sample_rate
        buf[i] = int(127 + 127 * math.sin(frequency * t * 2 * math.pi))
    
    return buf

def is_overlapping(rect, occupied_spaces):
    """Check if a rectangle overlaps with any occupied spaces.
    
    Args:
        rect: Rectangle coordinates (x1, y1, x2, y2)
        occupied_spaces: List of occupied rectangles [(x1, y1, x2, y2), ...]
        
    Returns:
        True if overlapping, False otherwise
    """
    x1, y1, x2, y2 = rect
    
    for space in occupied_spaces:
        sx1, sy1, sx2, sy2 = space
        
        # Check if rectangles overlap
        if (x1 < sx2 and x2 > sx1 and y1 < sy2 and y2 > sy1):
            return True
    
    return False

def is_blocking_doors(rect, doors):
    """Check if a rectangle blocks any doors.
    
    Args:
        rect: Rectangle coordinates (x1, y1, x2, y2)
        doors: List of door dictionaries with x1, y1, x2, y2 keys
        
    Returns:
        True if blocking a door, False otherwise
    """
    x1, y1, x2, y2 = rect
    
    for door in doors:
        dx1, dy1, dx2, dy2 = door["x1"], door["y1"], door["x2"], door["y2"]
        
        # Check if rectangles overlap
        if (x1 < dx2 and x2 > dx1 and y1 < dy2 and y2 > dy1):
            return True
    
    return False

def distance(point1, point2):
    """Calculate Euclidean distance between two points.
    
    Args:
        point1: First point (x, y)
        point2: Second point (x, y)
        
    Returns:
        Float distance
    """
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def manhattan_distance(point1, point2):
    """Calculate Manhattan distance between two points.
    
    Args:
        point1: First point (x, y)
        point2: Second point (x, y)
        
    Returns:
        Integer Manhattan distance
    """
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

def align_to_grid(x, y, tile_size):
    """Align coordinates to the nearest grid point.
    
    Args:
        x: X coordinate
        y: Y coordinate
        tile_size: Size of a grid tile
        
    Returns:
        Tuple of aligned (x, y) coordinates
    """
    return ((x // tile_size) * tile_size, (y // tile_size) * tile_size)

def generate_name():
    """Generate a random NPC name.
    
    Returns:
        String with first and last name
    """
    first_names = [
        "Aiden", "Bela", "Clara", "Doran", "Eliza", "Finn", "Greta", "Hilda", 
        "Ivan", "Julia", "Kai", "Lily", "Milo", "Nina", "Otto", "Petra", 
        "Quinn", "Rosa", "Sven", "Tilly", "Ulric", "Vera", "Wren", "Xander", 
        "Yara", "Zeke"
    ]
    
    last_names = [
        "Smith", "Miller", "Fisher", "Baker", "Cooper", "Fletcher", "Thatcher",
        "Wood", "Stone", "Field", "Hill", "Brook", "River", "Dale", "Ford",
        "Green", "White", "Black", "Brown", "Gray", "Reed", "Swift", "Strong"
    ]
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def get_random_building_type(size):
    """Return a random building type appropriate for the size.
    
    Args:
        size: Building size ("small", "medium", "large")
        
    Returns:
        String building type
    """
    if size == "large":
        return random.choice(["Town Hall", "Market", "Temple", "Manor"])
    elif size == "medium":
        return random.choice(["Inn", "Store", "Tavern", "Smithy", "Bakery"])
    else:  # small
        return random.choice(["House", "Cottage", "Workshop", "Storage"])

def create_color_palettes():
    """Create color palettes for various game elements.
    
    Returns:
        Dictionary containing color palettes
    """
    return {
        "character_skin": [(255, 220, 178), (255, 213, 164), (255, 200, 159), 
                          (240, 184, 135), (222, 165, 118), (198, 134, 66),
                          (172, 112, 61), (147, 85, 45)],
        "character_hair": [(43, 29, 14), (67, 44, 13), (113, 65, 25), 
                          (143, 89, 30), (175, 136, 74), (211, 188, 141),
                          (70, 35, 10), (30, 20, 10), (120, 80, 30)],
        "character_clothes": [(45, 49, 66), (86, 90, 105), (152, 93, 93), 
                             (65, 90, 119), (102, 141, 60), (222, 110, 75),
                             (241, 175, 78), (31, 138, 112), (180, 50, 50),
                             (50, 100, 150), (100, 60, 120), (160, 130, 50)],
        "building_walls": [(240, 217, 181), (219, 182, 151), (236, 229, 206),
                          (204, 174, 145), (176, 166, 147), (157, 132, 109),
                          (220, 200, 180), (200, 185, 160), (180, 160, 140),
                          (160, 145, 120), (240, 230, 215), (230, 210, 180),
                          (210, 190, 170), (190, 170, 150), (170, 150, 130)],
        "building_roofs": [(172, 89, 74), (140, 76, 54), (92, 62, 42),
                          (109, 79, 51), (140, 118, 84), (160, 100, 80),
                          (130, 65, 50), (100, 70, 45), (80, 55, 35),
                          (120, 85, 55), (150, 125, 90), (170, 110, 90),
                          (80, 50, 40), (110, 80, 60), (60, 40, 30)],
        "environment_green": [(62, 137, 72), (94, 153, 84), (138, 178, 125),
                             (49, 135, 118), (83, 160, 121), (30, 100, 50),
                             (70, 140, 60), (110, 170, 90), (35, 120, 70),
                             (60, 130, 100), (90, 150, 70), (40, 110, 60)],
        "decorations": [(180, 120, 70),  # Wood
                       (200, 200, 210),  # Metal
                       (160, 40, 30),    # Rust
                       (220, 220, 180),  # Cream
                       (160, 180, 200),  # Light blue
                       (190, 150, 110),  # Tan
                       (150, 70, 50)],   # Terracotta
        "floor_wood": [(180, 140, 100), (170, 130, 90), (160, 120, 80),
                      (150, 110, 70), (140, 100, 60), (130, 90, 50)],
        "floor_stone": [(180, 180, 180), (170, 170, 170), (160, 160, 160),
                       (150, 150, 150), (140, 140, 140), (130, 130, 130)],
        "floor_carpet": [(180, 120, 120), (120, 180, 120), (120, 120, 180),
                        (180, 180, 120), (180, 120, 180), (120, 180, 180)],
        "furniture_wood": [(150, 100, 50), (140, 90, 40), (130, 80, 30),
                          (120, 70, 20), (110, 60, 10), (100, 50, 0)],
        "furniture_upholstery": [(200, 150, 150), (150, 200, 150), (150, 150, 200),
                                (200, 200, 150), (200, 150, 200), (150, 200, 200)],
        "furniture_metal": [(200, 200, 200), (190, 190, 190), (180, 180, 180),
                           (170, 170, 170), (160, 160, 160), (150, 150, 150)]
    }

def get_job_activities():
    """Get activity lists for different jobs.
    
    Returns:
        Dictionary mapping job titles to lists of activities
    """
    return {
        "Baker": [
            "Wake up early", 
            "Prepare dough", 
            "Bake bread", 
            "Sell goods to customers", 
            "Clean bakery",
            "Chat with customers",
            "Return home"
        ],
        "Blacksmith": [
            "Get materials ready", 
            "Forge tools and weapons", 
            "Repair items", 
            "Work on special orders", 
            "Sell wares",
            "Return home"
        ],
        "Merchant": [
            "Open shop", 
            "Arrange merchandise", 
            "Bargain with customers", 
            "Restock inventory", 
            "Close shop",
            "Count earnings",
            "Return home"
        ],
        "Innkeeper": [
            "Prepare breakfast for guests", 
            "Clean rooms", 
            "Welcome new travelers", 
            "Serve food and drinks", 
            "Manage staff",
            "Close up for the night"
        ],
        "Farmer": [
            "Tend to crops", 
            "Feed animals", 
            "Repair fences", 
            "Take produce to market", 
            "Plant new seeds",
            "Return home"
        ],
        "Tailor": [
            "Cut fabric", 
            "Sew garments", 
            "Meet with clients", 
            "Design new styles", 
            "Make alterations",
            "Return home"
        ],
        "Carpenter": [
            "Select wood", 
            "Cut lumber", 
            "Build furniture", 
            "Make repairs around village", 
            "Finish projects",
            "Return home"
        ],
        "Miner": [
            "Travel to mines", 
            "Dig for ore", 
            "Sort materials", 
            "Sell findings", 
            "Repair tools",
            "Return home"
        ],
        "Hunter": [
            "Check traps", 
            "Track animals", 
            "Hunt for game", 
            "Prepare hides", 
            "Sell meat at market",
            "Return home"
        ],
        "Guard": [
            "Patrol village", 
            "Check on merchants", 
            "Stand watch at gate", 
            "Train with weapons", 
            "Report to captain",
            "Return home"
        ]
    }

def get_common_activities():
    """Get common activities that all NPCs might do.
    
    Returns:
        List of common activities
    """
    return [
        "Visit the market",
        "Chat with neighbors",
        "Eat at the Inn",
        "Relax at home",
        "Attend town gathering",
        "Go for a walk",
        "Collect water from well"
    ]

def get_job_workplace_mapping():
    """Get mapping of jobs to workplace building types.
    
    Returns:
        Dictionary mapping job titles to workplace building types
    """
    return {
        "Baker": "Bakery",
        "Blacksmith": "Smithy",
        "Merchant": "Store",
        "Innkeeper": "Inn", 
        "Farmer": "Farm",
        "Tailor": "Workshop",
        "Carpenter": "Workshop",
        "Miner": None,  # Works outside village
        "Hunter": None,  # Works outside village
        "Guard": "Town Hall"
    }

# Pathfinding utilities
def a_star_pathfind(start, goal, is_valid_position_fn, heuristic_fn=None):
    """A* pathfinding algorithm.
    
    Args:
        start: Start position (x, y)
        goal: Goal position (x, y)
        is_valid_position_fn: Function that takes (x, y) and returns True if the position is valid
        heuristic_fn: Function that takes (current, goal) and returns estimated cost
        
    Returns:
        List of positions from start to goal, or empty list if no path found
    """
    import heapq
    
    if start == goal:
        return [start]
    
    if heuristic_fn is None:
        heuristic_fn = manhattan_distance
    
    # Initialize
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic_fn(start, goal)}
    open_set_hash = {start}
    
    # Directions (8-way movement)
    directions = [
        (0, 1), (1, 0), (0, -1), (-1, 0),  # Cardinal
        (1, 1), (1, -1), (-1, 1), (-1, -1)  # Diagonal
    ]
    
    while open_set:
        current = heapq.heappop(open_set)[1]
        open_set_hash.remove(current)
        
        if current == goal:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path
        
        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            
            # Skip if not valid
            if not is_valid_position_fn(neighbor):
                continue
            
            # Calculate cost (diagonal moves cost more)
            move_cost = 1.414 if dx != 0 and dy != 0 else 1.0
            tentative_g = g_score[current] + move_cost
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                # This path is better
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic_fn(neighbor, goal)
                
                if neighbor not in open_set_hash:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    open_set_hash.add(neighbor)
    
    # No path found
    return []
def polar_to_cartesian(center_x, center_y, angle, distance):
    """Convert polar coordinates to Cartesian.
    
    Args:
        center_x, center_y: Center coordinates
        angle: Angle in radians
        distance: Distance from center
        
    Returns:
        Tuple of (x, y) coordinates
    """
    x = center_x + int(math.cos(angle) * distance)
    y = center_y + int(math.sin(angle) * distance)
    return x, y

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

def calculate_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points.
    
    Args:
        x1, y1: Coordinates of first point
        x2, y2: Coordinates of second point
        
    Returns:
        Distance between the points
    """
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx*dx + dy*dy)

def add_to_set_if_in_bounds(element_set, pos, grid_size):
    """Add a position to a set if it's in bounds.
    
    Args:
        element_set: Set to add position to
        pos: Position to add (x, y)
        grid_size: Size of the grid in pixels
        
    Returns:
        True if added, False otherwise
    """
    if is_in_bounds(pos[0], pos[1], grid_size):
        element_set.add(pos)
        return True
    return False

def iterate_area(x, y, width, height, tile_size):
    """Generate positions within a rectangular area in grid-aligned steps.

    Args:
        x, y: Starting coordinates of the area
        width, height: Size of the area in pixels
        tile_size: Size of a tile in pixels

    Yields:
        Tuples of (x, y) coordinates for each grid position
    """
    for dx in range(0, width, tile_size):
        for dy in range(0, height, tile_size):
            yield (x + dx, y + dy)

def get_neighbors(x, y, tile_size, include_self=False):
    """Generate 8-way neighboring positions.

    Args:
        x, y: Center coordinates
        tile_size: Size of a tile in pixels
        include_self: Whether to include the center position

    Yields:
        Tuples of (x, y) coordinates for neighboring positions
    """
    for dx in [-tile_size, 0, tile_size]:
        for dy in [-tile_size, 0, tile_size]:
            if dx == 0 and dy == 0 and not include_self:
                continue
            yield (x + dx, y + dy)

def get_buffer_positions(center_x, center_y, radius, tile_size):
    """Get all positions within a buffer radius of center.

    Args:
        center_x, center_y: Center coordinates
        radius: Buffer radius in tile units
        tile_size: Size of a tile in pixels

    Yields:
        Tuples of (x, y) coordinates within the buffer
    """
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            yield (center_x + dx * tile_size, center_y + dy * tile_size)

def filter_valid_positions(positions, grid_size, water_positions=None, path_positions=None, building_positions=None):
    """Filter positions based on common validity criteria.

    Args:
        positions: Iterable of position tuples
        grid_size: Size of the grid in pixels
        water_positions: Set of water positions to avoid
        path_positions: Set of path positions to avoid
        building_positions: Set of building positions to avoid

    Yields:
        Valid position tuples
    """
    for pos in positions:
        x, y = pos
        if not utils.is_in_bounds(x, y, grid_size):
            continue
        if water_positions is not None and pos in water_positions:
            continue
        if path_positions is not None and pos in path_positions:
            continue
        if building_positions is not None and pos in building_positions:
            continue
        yield pos


def is_near_water(x, y, water_positions, tile_size):
    """Check if a position is near water."""
    for neighbor_pos in utils.get_neighbors(x, y, tile_size):
        if neighbor_pos in water_positions:
            return True
    return False

def is_footprint_valid(position_x, position_y, footprint_tiles, tile_size,
                      excluded_positions_sets, grid_size=None):
    """Check if a building footprint is valid.
    
    Args:
        position_x, position_y: Position to check
        footprint_tiles: Size of footprint in tiles
        tile_size: Size of a tile in pixels
        excluded_positions_sets: List of sets of positions to avoid
        grid_size: Optional size of the grid for bounds checking
    
    Returns:
        Boolean indicating if the footprint is valid
    """
    # Check all tiles in the footprint
    for pos in iterate_area(position_x, position_y, 
                                 footprint_tiles * tile_size, 
                                 footprint_tiles * tile_size, 
                                 tile_size):
        # Check if out of bounds if grid_size is provided
        if grid_size and not is_in_bounds(pos[0], pos[1], grid_size):
            return False
            
        # Check if position is in any excluded sets
        for excluded_set in excluded_positions_sets:
            if pos in excluded_set:
                return False
                
    return True


def generate_points_in_irregular_shape(center_x, center_y, base_radius, 
                                     irregularity, num_points=12):
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
        
        x, y = polar_to_cartesian(center_x, center_y, angle, radius)
        points.append((x, y))
    return points

def generate_points_in_irregular_shape(center_x, center_y, base_radius, 
                                     irregularity, num_points=12):
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
        
        x, y = polar_to_cartesian(center_x, center_y, angle, radius)
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
    
def find_path_between_points(start, end, obstacles, grid_size, tile_size, 
                            prefer_cardinal=True):
    """Find a path between two points avoiding obstacles.
    
    Args:
        start: Start position (x, y)
        end: End position (x, y)
        obstacles: Set of obstacle positions to avoid
        grid_size: Size of the grid in pixels
        tile_size: Size of a tile in pixels
        prefer_cardinal: Whether to prefer cardinal directions
        
    Returns:
        List of positions forming a path, or empty list if no path found
    """
    import heapq
    
    # Convert positions to grid coordinates if they aren't already
    start_grid = (start[0] // tile_size, start[1] // tile_size)
    end_grid = (end[0] // tile_size, end[1] // tile_size)
    
    # If start and goal are the same, return just the start point
    if start_grid == end_grid:
        return [start]
    
    # Helper function to check if a position is valid
    def is_valid_position(pos):
        x, y = pos
        
        # Check if in bounds
        if x < 0 or x >= grid_size // tile_size or y < 0 or y >= grid_size // tile_size:
            return False
            
        # Check if position is an obstacle
        grid_pos = (x * tile_size, y * tile_size)
        if grid_pos in obstacles:
            return False
            
        return True
    
    # Helper function to estimate cost to goal
    def heuristic(a, b):
        # Manhattan distance with slight preference for aligned moves
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        return dx + dy
    
    # Initialize A* search
    open_set = []
    heapq.heappush(open_set, (0, start_grid))
    came_from = {}
    g_score = {start_grid: 0}
    f_score = {start_grid: heuristic(start_grid, end_grid)}
    open_set_hash = {start_grid}
    
    # Define movement directions
    if prefer_cardinal:
        # Cardinal directions first (NESW), then diagonals
        directions = [
            (0, -1), (1, 0), (0, 1), (-1, 0),  # Cardinal (NESW)
            (1, -1), (1, 1), (-1, 1), (-1, -1)  # Diagonal (NE, SE, SW, NW)
        ]
    else:
        # All 8 directions
        directions = [
            (0, -1), (1, -1), (1, 0), (1, 1),
            (0, 1), (-1, 1), (-1, 0), (-1, -1)
        ]
    
    # A* search algorithm
    while open_set:
        _, current = heapq.heappop(open_set)
        open_set_hash.remove(current)
        
        if current == end_grid:
            # Goal reached, reconstruct path
            path = []
            while current in came_from:
                # Convert grid coordinates back to pixel positions
                path.append((current[0] * tile_size, current[1] * tile_size))
                current = came_from[current]
            
            path.append((start_grid[0] * tile_size, start_grid[1] * tile_size))
            path.reverse()
            return path
        
        for i, (dx, dy) in enumerate(directions):
            neighbor = (current[0] + dx, current[1] + dy)
            
            # Skip if not valid
            if not is_valid_position(neighbor):
                continue
            
            # Calculate movement cost (diagonal moves cost more)
            is_diagonal = i >= 4 if prefer_cardinal else (dx != 0 and dy != 0)
            move_cost = 1.414 if is_diagonal else 1.0
            
            tentative_g = g_score[current] + move_cost
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                # This path is better
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, end_grid)
                
                if neighbor not in open_set_hash:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    open_set_hash.add(neighbor)
    
    # No path found
    return []
import math
import random

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

def is_in_bounds(x, y, grid_size):
    """Check if a position is within the grid bounds.
    
    Args:
        x, y: Position coordinates
        grid_size: Size of the grid in pixels
        
    Returns:
        Boolean indicating if the position is in bounds
    """
    return 0 <= x < grid_size and 0 <= y < grid_size

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

def get_neighbors(x, y, tile_size, include_self=False):
    """Get neighboring positions (8-way).
    
    Args:
        x, y: Position coordinates
        tile_size: Size of a tile in pixels
        include_self: Whether to include the position itself
        
    Returns:
        List of neighboring positions
    """
    neighbors = []
    
    for dx in [-tile_size, 0, tile_size]:
        for dy in [-tile_size, 0, tile_size]:
            if dx == 0 and dy == 0 and not include_self:
                continue
            neighbors.append((x + dx, y + dy))
    
    return neighbors

def generate_points_in_irregular_shape(center_x, center_y, base_radius, irregularity):
    """Generate points that define an irregular shape.
    
    Args:
        center_x, center_y: Center of the shape
        base_radius: Base radius of the shape
        irregularity: Factor for irregularity (0.0-1.0)
        
    Returns:
        List of points defining the shape perimeter
    """
    # Number of points based on size
    num_points = max(8, int(base_radius / 10))
    
    # Angle step between points
    angle_step = 2 * math.pi / num_points
    
    # Generate perimeter points
    perimeter_points = []
    for i in range(num_points):
        angle = i * angle_step
        
        # Random radius variation
        radius_variation = random.uniform(1.0 - irregularity, 1.0 + irregularity)
        radius = base_radius * radius_variation
        
        # Calculate point position
        x = center_x + math.cos(angle) * radius
        y = center_y + math.sin(angle) * radius
        
        perimeter_points.append((x, y))
    
    return perimeter_points

def is_point_in_shape(px, py, shape_points, center_x, center_y):
    """Check if a point is inside a shape defined by perimeter points.
    
    Args:
        px, py: Point coordinates
        shape_points: List of points defining the shape perimeter
        center_x, center_y: Center of the shape
        
    Returns:
        Boolean indicating if the point is inside the shape
    """
    # Special case: if the shape has no points
    if not shape_points:
        return False
        
    # Check if the point is close to the center
    if calculate_distance(px, py, center_x, center_y) < 10:
        return True
    
    # Ray casting algorithm
    inside = False
    j = len(shape_points) - 1
    
    for i in range(len(shape_points)):
        xi, yi = shape_points[i]
        xj, yj = shape_points[j]
        
        intersect = ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi)
        if intersect:
            inside = not inside
        
        j = i
    
    return inside

def iterate_area(x, y, width, height, tile_size):
    """Iterate over all tiles in an area.
    
    Args:
        x, y: Top-left corner coordinates
        width, height: Size of the area in pixels
        tile_size: Size of a tile in pixels
        
    Returns:
        Generator yielding tile positions
    """
    x_start, y_start = align_to_grid(x, y, tile_size)
    x_end = x_start + width
    y_end = y_start + height
    
    for tile_y in range(y_start, y_end, tile_size):
        for tile_x in range(x_start, x_end, tile_size):
            yield (tile_x, tile_y)

def get_buffer_positions(x, y, buffer_tiles, tile_size):
    """Get all positions in a buffer zone around a position.
    
    Args:
        x, y: Position coordinates
        buffer_tiles: Size of buffer in tiles
        tile_size: Size of a tile in pixels
        
    Returns:
        Generator yielding buffer positions
    """
    for dx in range(-buffer_tiles, buffer_tiles + 1):
        for dy in range(-buffer_tiles, buffer_tiles + 1):
            # Skip the center tile
            if dx == 0 and dy == 0:
                continue
                
            yield (x + dx * tile_size, y + dy * tile_size)

def is_footprint_valid(x, y, footprint_tiles, tile_size, excluded_sets, grid_size):
    """Check if a building footprint is valid.
    
    Args:
        x, y: Top-left corner coordinates
        footprint_tiles: Size of footprint in tiles
        tile_size: Size of a tile in pixels
        excluded_sets: List of sets with positions to exclude
        grid_size: Size of the grid in pixels
        
    Returns:
        Boolean indicating if the footprint is valid
    """
    # Check all tiles in the building footprint
    for tile_x, tile_y in iterate_area(x, y, footprint_tiles * tile_size, footprint_tiles * tile_size, tile_size):
        # Skip if out of bounds
        if not is_in_bounds(tile_x, tile_y, grid_size):
            return False
            
        # Check if position is in any excluded set
        pos = (tile_x, tile_y)
        for excluded_set in excluded_sets:
            if pos in excluded_set:
                return False
                
    return True

def get_direction_name(dx, dy):
    """Get the name of a direction from delta coordinates.
    
    Args:
        dx, dy: Delta coordinates
        
    Returns:
        Direction name (N, NE, E, SE, S, SW, W, NW)
    """
    if dx == 0 and dy < 0:
        return "N"
    elif dx > 0 and dy < 0:
        return "NE"
    elif dx > 0 and dy == 0:
        return "E"
    elif dx > 0 and dy > 0:
        return "SE"
    elif dx == 0 and dy > 0:
        return "S"
    elif dx < 0 and dy > 0:
        return "SW"
    elif dx < 0 and dy == 0:
        return "W"
    elif dx < 0 and dy < 0:
        return "NW"
    else:
        return ""

def get_angle_between_points(x1, y1, x2, y2):
    """Get the angle between two points in radians.
    
    Args:
        x1, y1: First point coordinates
        x2, y2: Second point coordinates
        
    Returns:
        Angle in radians
    """
    dx = x2 - x1
    dy = y2 - y1
    return math.atan2(dy, dx)

def perlin_noise_2d(x, y, seed=0):
    """Simple 2D Perlin noise implementation.
    
    Args:
        x, y: Coordinates
        seed: Random seed
        
    Returns:
        Noise value between -1 and 1
    """
    # Initialize the permutation table
    random.seed(seed)
    p = list(range(256))
    random.shuffle(p)
    p += p
    
    # Coordinates of the unit cube
    xi, yi = int(x) & 255, int(y) & 255
    xf, yf = x - int(x), y - int(y)
    
    # Fade curves
    u, v = fade(xf), fade(yf)
    
    # Hash coordinates of the 4 cube corners
    a = p[p[xi] + yi]
    b = p[p[xi + 1] + yi]
    c = p[p[xi] + yi + 1]
    d = p[p[xi + 1] + yi + 1]
    
    # And add blended results from the 4 corners
    return lerp(v, 
                lerp(u, grad(a, xf, yf), grad(b, xf - 1, yf)),
                lerp(u, grad(c, xf, yf - 1), grad(d, xf - 1, yf - 1)))

def fade(t):
    """Fade function for Perlin noise."""
    return t * t * t * (t * (t * 6 - 15) + 10)

def lerp(t, a, b):
    """Linear interpolation."""
    return a + t * (b - a)

def grad(hash, x, y):
    """Gradient function for Perlin noise."""
    h = hash & 15
    u = x if h < 8 else y
    v = y if h < 4 else (x if h == 12 or h == 14 else 0)
    return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

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
    
    # Align to tile grid and convert to integers
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
            if pos in village.terrain:
                cell_data['terrain'] = village.terrain[pos]
            if pos in village.water_positions:
                cell_data['water'] = True
            if pos in village.path_positions:
                cell_data['path'] = True
            if pos in village.building_positions:
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
    left = (left // village.tile_size) * village.tile_size
    top = (top // village.tile_size) * village.tile_size
    right = (right // village.tile_size) * village.tile_size
    bottom = (bottom // village.tile_size) * village.tile_size
    
    # Scan territory
    for y in range(top, bottom, village.tile_size):
        for x in range(left, right, village.tile_size):
            pos = (x, y)
            cell_data = {}
            
            # Gather data about this position
            if pos in village.terrain:
                cell_data['terrain'] = village.terrain[pos]
            if pos in village.water_positions:
                cell_data['water'] = True
            if pos in village.path_positions:
                cell_data['path'] = True
            if pos in village.building_positions:
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