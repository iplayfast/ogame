import random
import math
import utils
from village.village_buildings import connect_buildings_to_paths
from village.village_landscape import generate_landscape
from village.village_buildings import place_buildings
from village.village_paths import fix_path_issues
from village.village_landscape import place_trees
from village.village_paths import add_bridges
from village.village_interaction import analyze_interaction_points
from village.village_paths import create_village_layout


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
        
        # Village components with optimized data structures
        self.terrain = {}
        self.water = []
        self.water_positions = set()
        self.paths = []
        self.path_positions = set()
        self.buildings = []
        self.building_positions = set()
        self.trees = []
        self.bridges = []
        self.interaction_points = []
        
        # For optimization
        self.village_grid = None
        self.path_cache = {}
        
        # Village center - will be computed during generation
        self.village_center_x = None
        self.village_center_y = None
        
        # For compatibility with existing code
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
        
        # Step 2: Place trees densely throughout all grassy areas
        self._place_trees()
        
        # Step 3: Create village layout (paths and roads)
        self._create_village_layout()
        
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
        
        # Step 9: Initialize village grid for pathfinding
        self._initialize_grid()
        
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

    def _remove_trees_from_paths(self):
        """Remove trees that are directly on paths."""
        original_count = len(self.trees)
        
        # Keep only trees not on paths
        self.trees = [tree for tree in self.trees if tree['position'] not in self.path_positions]
        
        removed_count = original_count - len(self.trees)
        print(f"Removed {removed_count} trees that were directly on paths")
        
        return removed_count
    def _remove_trees_under_buildings(self):
        """Remove trees that overlap with buildings or paths.
        
        Returns:
            Number of trees removed
        """
        original_count = len(self.trees)
        trees_to_keep = []
        trees_removed = []
        
        # Debug info
        print(f"Before removal: {original_count} trees, {len(self.building_positions)} building positions, {len(self.path_positions)} path positions")
        
        for tree in self.trees:
            tree_pos = tree['position']
            tree_x, tree_y = tree_pos
            
            # Check ONLY the exact tree position against paths
            on_path = tree_pos in self.path_positions
            
            # For buildings, check the entire building footprint
            in_building = False
            for building in self.buildings:
                bx, by = building['position']
                size = building['size']
                
                # Calculate building dimensions
                b_width = b_height = self.tile_size
                if size == 'medium':
                    b_width = b_height = self.tile_size * 2
                elif size == 'large':
                    b_width = b_height = self.tile_size * 3
                    
                # Check if tree is inside this building
                if (bx <= tree_x < bx + b_width and
                    by <= tree_y < by + b_height):
                    in_building = True
                    break
            
            # Only remove if the tree is directly on a path or inside a building
            if on_path or in_building:
                trees_removed.append(tree)
            else:
                trees_to_keep.append(tree)
        
        # Update the trees list
        self.trees = trees_to_keep
        removed_count = original_count - len(self.trees)
        
        # More detailed output
        print(f"Removed {removed_count} trees that were directly on paths or inside buildings")
        print(f"Kept {len(trees_to_keep)} trees")
        
        return removed_count
    def _initialize_grid(self):
        """
        Creates a unified 2D grid representation of the village for efficient pathfinding.
        This should be called once during village generation.
        """
        # Helper function for safe grid access
        def safe_grid_access(grid, y, x, value=None):
            grid_y, grid_x = int(y), int(x)
            grid_height = len(grid)
            grid_width = len(grid[0]) if grid_height > 0 else 0
            
            if 0 <= grid_y < grid_height and 0 <= grid_x < grid_width:
                if value is not None:
                    grid[grid_y][grid_x] = value
                    return True
                return grid[grid_y][grid_x]
            return False if value is not None else None

        grid_size = self.grid_size // self.tile_size
        grid = [[{'type': 'empty', 'passable': True} for _ in range(grid_size)] for _ in range(grid_size)]
        
        # Add terrain (grass types)
        for pos, terrain in self.terrain.items():
            x, y = pos
            grid_x, grid_y = x // self.tile_size, y // self.tile_size
            
            safe_grid_access(grid, grid_y, grid_x, {
                'type': 'terrain',
                'terrain_type': terrain['type'],
                'variant': terrain.get('variant', 1),
                'passable': True
            })
        
        # Add water (impassable)
        for water_pos in self.water_positions:
            x, y = water_pos
            grid_x, grid_y = x // self.tile_size, y // self.tile_size
            
            safe_grid_access(grid, grid_y, grid_x, {
                'type': 'water',
                'passable': False
            })
        
        # Add bridges (passable)
        for bridge in self.bridges:
            x, y = bridge['position']
            grid_x, grid_y = x // self.tile_size, y // self.tile_size
            
            safe_grid_access(grid, grid_y, grid_x, {
                'type': 'bridge',
                'bridge_type': bridge.get('type', 'bridge'),
                'passable': True,
                'preferred': True
            })
        
        # Add paths (passable, preferred)
        for path in self.paths:
            x, y = path['position']
            grid_x, grid_y = x // self.tile_size, y // self.tile_size
            
            safe_grid_access(grid, grid_y, grid_x, {
                'type': 'path',
                'variant': path.get('variant', 1),
                'passable': True,
                'preferred': True
            })
        
        # Add buildings
        for i, building in enumerate(self.buildings):
            pos = building['position']
            size_name = building['size']
            
            # Determine building size in tiles
            size_multiplier = 3 if size_name == 'large' else (
                            2 if size_name == 'medium' else 1)
            size_tiles = size_multiplier
            
            # Add building footprint to grid
            for dx in range(size_tiles):
                for dy in range(size_tiles):
                    pos_x, pos_y = pos
                    grid_x = (pos_x // self.tile_size) + dx
                    grid_y = (pos_y // self.tile_size) + dy
                    
                    safe_grid_access(grid, grid_y, grid_x, {
                        'type': 'building',
                        'building_id': i,
                        'building_type': building.get('building_type', 'Unknown'),
                        'passable': False,
                        'preferred': False
                    })
        
        # Store the grid in village_data
        self.village_grid = grid
        self.village_data['village_grid'] = grid
        print(f"Village grid initialized: {grid_size}x{grid_size}")
        
        # Create utility method for grid access that uses our safe access function
        def get_cell_at(x, y):
            """Get the grid cell at the given pixel coordinates."""
            grid_x = x // self.tile_size
            grid_y = y // self.tile_size
            return safe_grid_access(grid, grid_y, grid_x)
        
        self.village_data['get_cell_at'] = get_cell_at

    def _generate_landscape(self):
        """Import and call the landscape generation method."""
        #from village_landscape import generate_landscape
        landscape_data = generate_landscape(self)
        self.__dict__.update(landscape_data)
    
    def _create_village_layout(self):
        """Import and call the path creation method."""
        #from village_paths import create_village_layout
        paths_data = create_village_layout(self)
        self.__dict__.update(paths_data)
    
    def _place_buildings(self):
        """Import and call the building placement method."""
        #from village.village_buildings import place_buildings
        buildings_data = place_buildings(self)
        self.__dict__.update(buildings_data)
    
    def _connect_buildings_to_paths(self):
        """Import and call the building-path connection method."""
        #from village_buildings import connect_buildings_to_paths
        connect_buildings_to_paths(self)
    
    def _fix_path_issues(self):
        """Import and call the path fixing method."""
        #from village_paths import fix_path_issues
        fix_path_issues(self)
    
    def _place_trees(self):
        """Import and call the tree placement method."""
        #from village_landscape import place_trees
        place_trees(self)
    
    def _add_bridges(self):
        """Import and call the bridge addition method."""
        #from village_paths import add_bridges
        add_bridges(self)
    
    def _analyze_interaction_points(self):
        """Import and call the interaction point analysis method."""
        #from village_interaction import analyze_interaction_points
        analyze_interaction_points(self)

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
            
        # If no grid, we can't pathfind
        if not self.village_grid:
            return []
            
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
        pixel_path = [(x * self.tile_size, y * self.tile_size) for x, y in path]
        
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
        import heapq
        
        grid_size = len(self.village_grid[0])
        
        # Ensure start and goal are tuples of integers
        start = (int(start[0]), int(start[1]))
        goal = (int(goal[0]), int(goal[1]))
        
        # Helper function to check if a position is valid
        def is_valid_position(pos):
            x, y = int(pos[0]), int(pos[1])
            
            # Check if in bounds
            if x < 0 or x >= grid_size or y < 0 or y >= grid_size:
                return False
                
            # Check if position is passable
            cell = self.village_grid[y][x]
            return cell['passable'] if 'passable' in cell else True
        
        # Helper function to get movement cost between positions
        def movement_cost(current, neighbor):
            # If moving diagonally, cost is higher
            if current[0] != neighbor[0] and current[1] != neighbor[1]:
                return 1.414  # sqrt(2)
            return 1.0
            
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
            
            current_x, current_y = int(current[0]), int(current[1])
            
            for dx, dy in directions:
                # Make sure all coordinates are integers
                neighbor = (int(current_x + dx), int(current_y + dy))
                
                # Skip if not valid
                if not is_valid_position(neighbor):
                    continue
                
                # Calculate cost
                tentative_g = g_score[current] + movement_cost(current, neighbor)
                
                # Prefer paths if available
                neighbor_x, neighbor_y = neighbor
                if 0 <= neighbor_x < grid_size and 0 <= neighbor_y < grid_size:
                    cell = self.village_grid[neighbor_y][neighbor_x]
                    if 'preferred' in cell and cell['preferred']:
                        tentative_g *= 0.8  # Reduce cost for preferred paths (paths, bridges)
                
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
