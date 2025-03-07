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

