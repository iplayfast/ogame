"""
Housing Manager - Handles housing and building management
"""
import random
from entities.villager_housing import assign_housing_and_jobs, load_assignments, update_game_with_assignments

class HousingManager:
    """Manages housing assignments and building management."""
    
    def __init__(self, game_state):
        """Initialize the housing manager.
        
        Args:
            game_state: Reference to the main game state
        """
        self.game_state = game_state
    
    def assign_housing(self, regenerate=True):
        """Assign housing and jobs to villagers.
        
        Args:
            regenerate: If True, generate new assignments; if False, load from file
        """
        if regenerate:
            # Force creation of new housing assignments
            print("Creating new housing assignments...")
            assignments = assign_housing_and_jobs(self.game_state.villagers, self.game_state.village_data)
        else:
            # Load existing assignments
            print("Loading existing housing assignments...")
            assignments = load_assignments()
        
        # Apply the assignments
        update_game_with_assignments(self.game_state, assignments)
    
    # Improved function to force villagers to their homes at game start
# This should be in housing_manager.py

    def force_villagers_to_homes(self):
        """Force all villagers to be positioned in their assigned homes."""
        print("Forcing all villagers to their home positions...")
        villagers_with_homes = 0
        villagers_without_homes = 0
        
        # Track occupied bed positions to avoid overlap
        occupied_bed_positions = {}
        
        for villager in self.game_state.villagers:
            # Check if villager has a home assigned
            if hasattr(villager, 'home') and villager.home and 'position' in villager.home:
                villagers_with_homes += 1
                
                # Use the initialize_unique_bed_position method to avoid overlapping beds
                if hasattr(self, 'initialize_unique_bed_position'):
                    self.initialize_unique_bed_position(villager, occupied_bed_positions)
                else:
                    # Fallback to direct positioning if the method doesn't exist
                    self._position_villager_in_home(villager)
                
                # Ensure villager is in sleeping state
                villager.is_sleeping = True
                villager.current_activity = "Sleeping"
                
                # Clear any destination
                villager.destination = None
                villager.path = []
                if hasattr(villager, 'current_path_index'):
                    villager.current_path_index = 0
            else:
                villagers_without_homes += 1
                print(f"Warning: {villager.name} has no home assigned")
        
        print(f"Villager home stats: {villagers_with_homes} with homes, {villagers_without_homes} without homes")
        return villagers_with_homes

    

    def _position_villager_in_home(self, villager):
        """Position a villager in their assigned home.
        
        Args:
            villager: Villager to position
        """
        home_pos = villager.home['position']
        home_id = villager.home.get('id', -1)
        
        # Find the actual building
        if 0 <= home_id < len(self.game_state.village_data['buildings']):
            building = self.game_state.village_data['buildings'][home_id]
            building_pos = building['position']
            building_size = building['size']
            
            # Convert to pixel sizes
            size_multiplier = 3 if building_size == 'large' else (2 if building_size == 'medium' else 1)
            building_size_px = self.game_state.TILE_SIZE * size_multiplier
            
            # Calculate a position inside the house (near top area for bed)
            padding = self.game_state.TILE_SIZE // 2
            bed_x = building_pos[0] + random.randint(padding, building_size_px - padding)
            bed_y = building_pos[1] + random.randint(padding, building_size_px // 2)
            
            # Set the villager's bed position
            villager.bed_position = (bed_x, bed_y)
            
            # Directly set position
            villager.position.x = bed_x
            villager.position.y = bed_y
            
            # Update rect
            villager.rect.centerx = int(villager.position.x)
            villager.rect.centery = int(villager.position.y)
            
            # Set sleep state
            villager.is_sleeping = True
            villager.current_activity = "Sleeping"
            
            # Clear any destination
            villager.destination = None
        else:
            print(f"Warning: {villager.name} has invalid home ID: {home_id}")
    
    def initialize_unique_bed_position(self, villager, occupied_bed_positions=None):
        """Initialize home position with a unique bed position for each villager.
        
        Args:
            villager: Villager to position
            occupied_bed_positions: Dictionary of already occupied bed positions
        """
        if occupied_bed_positions is None:
            occupied_bed_positions = {}
            
        if not hasattr(villager, 'home') or not villager.home or 'position' not in villager.home:
            # No home assigned, can't initialize
            return
            
        home_pos = villager.home['position']
        home_id = villager.home.get('id', -1)
        
        # Find the actual building
        if 0 <= home_id < len(self.game_state.village_data['buildings']):
            building = self.game_state.village_data['buildings'][home_id]
            building_pos = building['position']
            building_size = building['size']
            
            # Convert to pixel sizes
            size_multiplier = 3 if building_size == 'large' else (2 if building_size == 'medium' else 1)
            building_size_px = self.game_state.TILE_SIZE * size_multiplier
            
            # Get the number of roommates to determine how to spread beds
            roommates = villager.home.get('roommates', [])
            num_roommates = len(roommates)
            
            # Default position (for safety)
            bed_x = building_pos[0] + building_size_px // 2
            bed_y = building_pos[1] + building_size_px // 2
            
            # Try to find an available position
            attempt_count = 0
            padding = self.game_state.TILE_SIZE // 3
            
            # Keep trying to find an unoccupied position
            while attempt_count < 10:  # Limit attempts to avoid infinite loops
                # Calculate positions based on number of roommates and building size
                if building_size == 'large':
                    # For large buildings (manor), we can have up to 4 beds in a grid pattern
                    row = attempt_count % 2
                    col = (attempt_count // 2) % 2
                    
                    # Divide the building interior into a 2x2 grid
                    cell_size = (building_size_px - padding * 2) // 2
                    bed_x = building_pos[0] + padding + col * cell_size + cell_size // 2
                    bed_y = building_pos[1] + padding + row * cell_size + cell_size // 2
                elif building_size == 'medium':
                    # For medium buildings, we can have up to 2 beds in a row
                    if num_roommates <= 1:
                        # Single occupant - place in center
                        bed_x = building_pos[0] + building_size_px // 2
                        bed_y = building_pos[1] + building_size_px // 2
                    else:
                        # Two occupants - place side by side
                        col = attempt_count % 2
                        bed_x = building_pos[0] + padding + col * (building_size_px - padding * 2 - self.game_state.TILE_SIZE)
                        bed_y = building_pos[1] + building_size_px // 2
                else:  # small
                    # For small buildings, we have limited space
                    if num_roommates <= 1:
                        # Single occupant - place in center
                        bed_x = building_pos[0] + building_size_px // 2
                        bed_y = building_pos[1] + building_size_px // 2
                    else:
                        # Multiple occupants - stagger positions slightly
                        offset_x = (attempt_count % 3 - 1) * (self.game_state.TILE_SIZE // 3)
                        offset_y = (attempt_count // 3 - 1) * (self.game_state.TILE_SIZE // 3)
                        bed_x = building_pos[0] + building_size_px // 2 + offset_x
                        bed_y = building_pos[1] + building_size_px // 2 + offset_y
                
                # Check if this position is already occupied
                position_key = f"{int(bed_x)},{int(bed_y)}"
                if position_key not in occupied_bed_positions:
                    # Found an unoccupied position
                    occupied_bed_positions[position_key] = villager.name
                    break
                    
                # Try another position
                attempt_count += 1
                
            # Add some randomness to avoid perfect alignment
            bed_x += random.randint(-3, 3)
            bed_y += random.randint(-3, 3)
            
            # Set the villager's bed position
            villager.bed_position = (bed_x, bed_y)
            
            # Move villager to bed
            villager.position.x = bed_x
            villager.position.y = bed_y
            
            # Update rect
            villager.rect.centerx = int(villager.position.x)
            villager.rect.centery = int(villager.position.y)
            
            # Clear destination
            villager.destination = None
        else:
            print(f"Warning: {villager.name} has invalid home ID: {home_id}")
    
    def assign_building_types(self):
        """Assign building types to buildings (house, store, inn, etc.)."""
        building_types = {
            "small": ["House", "Cottage", "Workshop", "Storage"],
            "medium": ["Inn", "Store", "Tavern", "Smithy", "Bakery"],
            "large": ["Town Hall", "Market", "Temple", "Manor"]
        }
        
        for building in self.game_state.village_data['buildings']:
            size = building['size']
            available_types = building_types.get(size, ["House"])
            building['building_type'] = random.choice(available_types)
    
    def get_building_info(self, building_id=None, building_type=None):
        """Get information about buildings.
        
        Args:
            building_id: Optional building ID to filter
            building_type: Optional building type to filter
            
        Returns:
            List of building information dictionaries
        """
        results = []
        
        for idx, building in enumerate(self.game_state.village_data['buildings']):
            # Skip if not matching ID filter
            if building_id is not None and idx != building_id:
                continue
                
            # Skip if not matching type filter
            if building_type is not None and building.get('building_type', '') != building_type:
                continue
                
            # Create info dictionary
            info = {
                'id': idx,
                'type': building.get('building_type', 'Unknown'),
                'size': building['size'],
                'position': building['position'],
                'name': building.get('name', f"Building #{idx}")
            }
            
            # Add residents if applicable
            residents = []
            for villager in self.game_state.villagers:
                if hasattr(villager, 'home') and villager.home and 'id' in villager.home:
                    if villager.home['id'] == idx:
                        residents.append(villager.name)
            
            if residents:
                info['residents'] = residents
                
            results.append(info)
            
            # Return early if specific ID requested
            if building_id is not None:
                return results
        
        return results
