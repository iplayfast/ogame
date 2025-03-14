import random
import math
import heapq
import utils

# Define terrain types as constants
EMPTY = 0
GRASS_1 = 1
GRASS_2 = 2
GRASS_3 = 3
WATER = 10
PATH_1 = 20
PATH_2 = 21
TREE_1 = 30
TREE_2 = 31
TREE_3 = 32
TREE_4 = 33
TREE_5 = 34
BUILDING = 40  # Base value - building_id gets added to this

# Helper functions for terrain types
def is_grass(token):
    return 1 <= token <= 9
    
def is_water(token):
    return token == WATER
    
def is_path(token):
    return 20 <= token <= 29
    
def is_tree(token):
    return 30 <= token <= 39
    
def is_building(token):
    return token >= BUILDING
    
def get_building_id(token):
    return token - BUILDING if is_building(token) else -1

def is_passable(token):
    return (is_grass(token) or 
            is_path(token) or 
            token == EMPTY)

def get_variant(token):
    if is_grass(token):
        return token
    elif is_path(token):
        return token - PATH_1 + 1
    elif is_tree(token):
        return token - TREE_1 + 1
    return 1

class Village:
    """A class representing a procedurally generated village with buildings, roads, and natural features.
    
    The Village class encapsulates all the functionality to generate and manage a
    complete village environment, including terrain, water features, paths, buildings,
    and other elements that make up a coherent settlement.
    """
    
    def __init__(self, size, assets, tile_size=32):
        """Initialize and generate a new village.
        
        Args:
            size: Base size parameter (will be scaled up)
            assets: Dictionary of game assets
            tile_size: Size of each tile in pixels
        """
        # Basic properties
        self.size = size * 2  # Double the original size parameter
        self.grid_size = self.size * tile_size
        self.tile_size = tile_size
        self.assets = assets
        
        # Grid dimensions
        self.grid_width = self.grid_size // tile_size
        self.grid_height = self.grid_size // tile_size
        
        # New terrain grid with default grass
        self.terrain_grid = [[GRASS_1 for x in range(self.grid_width)] 
                            for y in range(self.grid_height)]
        
        # Position sets for fast iteration (these are now just views into the grid)
        self.water_positions = set()
        self.path_positions = set()
        self.tree_positions = set()
        self.building_positions = set()
        
        # Store building objects separately since they span multiple cells
        self.buildings = []
        self.bridges = []
        self.interaction_points = []
        
        # For optimization
        self.path_cache = {}
        
        # Village center - will be computed during generation
        self.village_center_x = None
        self.village_center_y = None
        
        # For compatibility with existing code
        self.terrain = {}  # Legacy terrain dictionary
        self.water = []    # Legacy water list
        self.paths = []    # Legacy paths list
        self.trees = []    # Legacy trees list
        
        # Village data dictionary for legacy compatibility
        self.village_data = {
            'size': self.grid_size,
            'terrain': self.terrain,
            'buildings': self.buildings,
            'trees': self.trees,
            'paths': self.paths,
            'water': self.water,
            'bridges': self.bridges,
            'interaction_points': self.interaction_points,
            'water_positions': self.water_positions,
            'path_positions': self.path_positions
        }
        
        print(f"Generating village with size {self.grid_size}x{self.grid_size} pixels...")
        
        # Generate the village
        self._generate()
    
    def _generate(self):
        """Generate the entire village structure in a single process."""
        # Step 1: Generate landscape (terrain and water)
        self._generate_landscape()
        
        # Step 2: Create village layout (paths and roads)
        self._create_village_layout()
        
        # Step 3: Place trees densely throughout all grassy areas
        self._place_trees()
        
        # Step 4: Remove trees from paths (buildings handle their own tree removal)
        self._remove_trees_from_paths()
        
        # Step 5: Place buildings (they'll remove trees as they're placed)
        self._place_buildings()
        
        # Step 6: Connect buildings to paths
        self._connect_buildings_to_paths()
        
        # Step 7: Fix path issues
        self._fix_path_issues()
        
        # Step 8: Add bridges at water crossings
        self._add_bridges()
        
        # Step 9: Update legacy data structures for compatibility
        self._update_legacy_structures()
        
        # Step 10: Analyze interaction points
        self._analyze_interaction_points()
        
        # Update village_data
        self.village_data.update({
            'size': self.grid_size,
            'terrain': self.terrain,
            'buildings': self.buildings,
            'trees': self.trees,
            'paths': self.paths,
            'water': self.water,
            'bridges': self.bridges,
            'interaction_points': self.interaction_points,
            'water_positions': self.water_positions,
            'path_positions': self.path_positions
        })
    
    def set_terrain(self, x, y, token):
        """Set terrain at pixel coordinates.
        
        Args:
            x, y: Pixel coordinates
            token: Terrain token to set
        """
        grid_x, grid_y = x // self.tile_size, y // self.tile_size
        
        # Check bounds
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            # Remove from old sets if necessary
            old_token = self.terrain_grid[grid_y][grid_x]
            self._remove_from_position_sets(grid_x, grid_y, old_token)
            
            # Set new terrain
            self.terrain_grid[grid_y][grid_x] = token
            
            # Add to appropriate position set
            self._add_to_position_sets(grid_x, grid_y, token)
    
    def get_terrain(self, x, y):
        """Get terrain at pixel coordinates.
        
        Args:
            x, y: Pixel coordinates
            
        Returns:
            Terrain token at the specified location
        """
        grid_x, grid_y = x // self.tile_size, y // self.tile_size
        
        # Check bounds
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return self.terrain_grid[grid_y][grid_x]
        return EMPTY
    
    def is_passable(self, x, y):
        """Check if a position is passable for pathfinding.
        
        Args:
            x, y: Pixel coordinates
            
        Returns:
            Boolean indicating if the position is passable
        """
        token = self.get_terrain(x, y)
        return is_passable(token)
    
    def _remove_from_position_sets(self, grid_x, grid_y, token):
        """Remove a position from the appropriate set based on its token.
        
        Args:
            grid_x, grid_y: Grid coordinates
            token: The terrain token being removed
        """
        pos = (grid_x * self.tile_size, grid_y * self.tile_size)
        
        if is_water(token):
            self.water_positions.discard(pos)
        elif is_path(token):
            self.path_positions.discard(pos)
        elif is_tree(token):
            self.tree_positions.discard(pos)
        elif is_building(token):
            self.building_positions.discard(pos)
    
    def _add_to_position_sets(self, grid_x, grid_y, token):
        """Add a position to the appropriate set based on its token.
        
        Args:
            grid_x, grid_y: Grid coordinates
            token: The terrain token being added
        """
        pos = (grid_x * self.tile_size, grid_y * self.tile_size)
        
        if is_water(token):
            self.water_positions.add(pos)
        elif is_path(token):
            self.path_positions.add(pos)
        elif is_tree(token):
            self.tree_positions.add(pos)
        elif is_building(token):
            self.building_positions.add(pos)
    
    def _rebuild_position_sets(self):
        """Rebuild all position sets from the terrain grid."""
        self.water_positions.clear()
        self.path_positions.clear()
        self.tree_positions.clear()
        self.building_positions.clear()
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                token = self.terrain_grid[y][x]
                pos = (x * self.tile_size, y * self.tile_size)
                
                if is_water(token):
                    self.water_positions.add(pos)
                elif is_path(token):
                    self.path_positions.add(pos)
                elif is_tree(token):
                    self.tree_positions.add(pos)
                elif is_building(token):
                    self.building_positions.add(pos)
    
    def _remove_trees_from_paths(self):
        """Update terrain grid to remove trees that overlap with paths."""
        count = 0
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                token = self.terrain_grid[y][x]
                
                # If this is a tree and there's a path nearby, remove the tree
                if is_tree(token):
                    # Check surrounding positions for paths
                    has_adjacent_path = False
                    for dx in range(-1, 2):
                        for dy in range(-1, 2):
                            nx, ny = x + dx, y + dy
                            
                            # Skip if out of bounds
                            if not (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                                continue
                                
                            if is_path(self.terrain_grid[ny][nx]):
                                has_adjacent_path = True
                                break
                        
                        if has_adjacent_path:
                            break
                    
                    # If there's a path nearby, replace the tree with grass
                    if has_adjacent_path:
                        self.terrain_grid[y][x] = GRASS_1
                        pos = (x * self.tile_size, y * self.tile_size)
                        self.tree_positions.discard(pos)
                        count += 1
        
        print(f"Removed {count} trees that were directly on paths")
        return count
    
    def _update_legacy_structures(self):
        """Update legacy data structures for backwards compatibility."""
        # Clear old structures
        self.terrain = {}
        self.water = []
        self.paths = []
        self.trees = []
        
        # Rebuild from terrain grid
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                token = self.terrain_grid[y][x]
                pos = (x * self.tile_size, y * self.tile_size)
                
                # Update terrain dictionary
                if is_grass(token):
                    variant = get_variant(token)
                    self.terrain[pos] = {
                        'type': 'grass',
                        'variant': variant
                    }
                
                # Update water list
                if is_water(token):
                    self.water.append({
                        'position': pos,
                        'frame': 0
                    })
                
                # Update paths list
                if is_path(token):
                    variant = get_variant(token)
                    self.paths.append({
                        'position': pos,
                        'variant': variant
                    })
                
                # Update trees list
                if is_tree(token):
                    variant = get_variant(token)
                    self.trees.append({
                        'position': pos,
                        'variant': variant
                    })
        
        print("Updated legacy data structures for compatibility")
    
    def find_path(self, start, goal, heuristic=None):
        """Find a path between two points using A* pathfinding.
        
        Args:
            start: Starting position in pixel coordinates (x, y)
            goal: Goal position in pixel coordinates (x, y)
            heuristic: Optional heuristic function for A* algorithm
            
        Returns:
            List of positions forming a path, or empty list if no path found
        """
        # Check path cache first
        cache_key = (start, goal)
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]
            
        # Convert positions to grid coordinates
        if isinstance(start, tuple):
            start_x, start_y = start
        else:
            # Handle pygame Vector2 or similar
            start_x, start_y = start.x, start.y
            
        if isinstance(goal, tuple):
            goal_x, goal_y = goal
        else:
            goal_x, goal_y = goal.x, goal.y
            
        # Align to grid
        start_x, start_y = utils.align_to_grid(start_x, start_y, self.tile_size)
        goal_x, goal_y = utils.align_to_grid(goal_x, goal_y, self.tile_size)
        
        # Convert to grid indices
        start_grid = (int(start_x // self.tile_size), int(start_y // self.tile_size))
        goal_grid = (int(goal_x // self.tile_size), int(goal_y // self.tile_size))
        
        # If start and goal are the same, return just the start point
        if start_grid == goal_grid:
            return [start]
            
        # Default heuristic is Manhattan distance
        if heuristic is None:
            def heuristic(a, b):
                return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
        # A* implementation
        path = self._a_star_pathfind(start_grid, goal_grid, heuristic)
        
        # Convert grid indices back to pixel coordinates
        pixel_path = [(x * self.tile_size + self.tile_size // 2, 
                       y * self.tile_size + self.tile_size // 2) for x, y in path]
        
        # Cache the result
        self.path_cache[cache_key] = pixel_path
        
        return pixel_path

    def _a_star_pathfind(self, start, goal, heuristic_fn):
        """A* pathfinding algorithm.
        
        Args:
            start: Start position in grid coordinates (x, y)
            goal: Goal position in grid coordinates (x, y)
            heuristic_fn: Heuristic function for A*
            
        Returns:
            List of grid positions from start to goal, or empty list if no path found
        """
        # Ensure start and goal are tuples of integers
        start = (int(start[0]), int(start[1]))
        goal = (int(goal[0]), int(goal[1]))
        
        # Helper function to check if a position is valid
        def is_valid_position(pos):
            x, y = int(pos[0]), int(pos[1])
            
            # Check if in bounds
            if not (0 <= x < self.grid_width and 0 <= y < self.grid_height):
                return False
                
            # Check if position is passable
            token = self.terrain_grid[y][x]
            return is_passable(token)
        
        # Helper function to get movement cost between positions
        def movement_cost(current, neighbor):
            curr_x, curr_y = current
            next_x, next_y = neighbor
            
            # If moving diagonally, cost is higher
            if curr_x != next_x and curr_y != next_y:
                cost = 1.414  # sqrt(2)
            else:
                cost = 1.0
                
            # Reduce cost for paths (prefer them)
            token = self.terrain_grid[next_y][next_x]
            if is_path(token):
                cost *= 0.8
                
            return cost
            
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
                if not is_valid_position(neighbor):
                    continue
                
                # Calculate cost
                tentative_g = g_score[current] + movement_cost(current, neighbor)
                
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
    
    # Methods for importing generators from separate modules
    def _generate_landscape(self):
        """Generate the terrain and water features."""
        # Import and call the landscape generation method
        # This will be implemented to use the new terrain system
        from village_landscape import generate_landscape
        landscape_data = generate_landscape(self)
        self.__dict__.update(landscape_data)
    
    def _create_village_layout(self):
        """Create the paths and road layout."""
        from village_paths import create_village_layout
        paths_data = create_village_layout(self)
        self.__dict__.update(paths_data)
    
    def _place_buildings(self):
        """Place buildings throughout the village."""
        from village_buildings import place_buildings
        buildings_data = place_buildings(self)
        if buildings_data:  # Only update dict if buildings_data is not None
            self.__dict__.update(buildings_data)
    
    def _connect_buildings_to_paths(self):
        """Ensure all buildings are connected to the path network."""
        from village_buildings import connect_buildings_to_paths
        connect_buildings_to_paths(self)
    
    def _fix_path_issues(self):
        """Fix issues with paths like diagonal-only connections."""
        from village_paths import fix_path_issues
        fix_path_issues(self)
    
    def _place_trees(self):
        """Place trees throughout the village."""
        from village_landscape import place_trees
        place_trees(self)
    
    def _add_bridges(self):
        """Add bridges at points where paths cross water."""
        from village_paths import add_bridges
        add_bridges(self)
    
    def _analyze_interaction_points(self):
        """Identify interaction points throughout the village."""
        from village_interaction import analyze_interaction_points
        analyze_interaction_points(self)
