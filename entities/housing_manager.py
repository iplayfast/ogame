# entities/housing_manager.py
# [MODIFIED] Includes safety check for villager.rect in initialize_unique_bed_position

import random
import pygame # Added import

# Assume these imports work or replace with actual implementations if needed
try:
    from entities.villager_housing import assign_housing_and_jobs, load_assignments, update_game_with_assignments
except ImportError:
    # Dummy functions if villager_housing is missing
    def assign_housing_and_jobs(villagers, village_data): return {}
    def load_assignments(filename='village_assignments.json'): return {}
    def update_game_with_assignments(game_state, assignments): pass

# Assume Interface is available or add dummy class if needed
try:
    from ui import Interface
except ImportError:
    class Interface: # Dummy class
        @staticmethod
        def on_building_selected(building): pass
        # Add other methods if needed


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
                    print("Warning: initialize_unique_bed_position not found, using fallback positioning.")
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
                if hasattr(villager, 'name'): # Check if name attribute exists
                     print(f"Warning: {villager.name} has no home assigned")
                else:
                     print("Warning: Villager with no name has no home assigned")


        print(f"Villager home stats: {villagers_with_homes} with homes, {villagers_without_homes} without homes")
        return villagers_with_homes


    def _position_villager_in_home(self, villager):
        """Position a villager in their assigned home (Fallback method)."""
        if not hasattr(villager, 'home') or not villager.home or 'position' not in villager.home:
             print(f"Warning: Cannot position villager {getattr(villager, 'name', 'Unknown')} - home data missing.")
             return

        home_pos = villager.home['position']
        home_id = villager.home.get('id', -1)

        # Find the actual building
        if 0 <= home_id < len(self.game_state.village_data.get('buildings', [])):
            building = self.game_state.village_data['buildings'][home_id]
            building_pos = building['position']
            building_size_str = building.get('size', 'small')

            # Convert to pixel sizes
            size_multiplier = 3 if building_size_str == 'large' else (2 if building_size_str == 'medium' else 1)
            building_size_px = self.game_state.TILE_SIZE * size_multiplier

            # Calculate a position inside the house
            padding = self.game_state.TILE_SIZE // 2
            bed_x = building_pos[0] + random.randint(padding, max(padding, building_size_px - padding)) # Ensure range is valid
            bed_y = building_pos[1] + random.randint(padding, max(padding, building_size_px // 2)) # Top half

            # Set the villager's bed position
            villager.bed_position = (bed_x, bed_y)

            # Directly set position
            villager.position.x = bed_x
            villager.position.y = bed_y

            # Update rect (Check if rect exists first)
            if villager.rect:
                 villager.rect.center = (int(villager.position.x), int(villager.position.y))
            else:
                 print(f"Warning: Villager {getattr(villager, 'name', 'Unknown')} rect is None in _position_villager_in_home.")

            # Set sleep state
            villager.is_sleeping = True
            villager.current_activity = "Sleeping"

            # Clear any destination
            villager.destination = None
        else:
            print(f"Warning: {getattr(villager, 'name', 'Unknown')} has invalid home ID: {home_id}")

    def initialize_unique_bed_position(self, villager, occupied_bed_positions=None):
        """Initialize home position with a unique bed position for each villager."""
        if occupied_bed_positions is None:
            occupied_bed_positions = {}

        if not hasattr(villager, 'home') or not villager.home or 'position' not in villager.home:
            return # No home assigned, can't initialize

        home_pos = villager.home['position']
        home_id = villager.home.get('id', -1)

        # Find the actual building
        if 0 <= home_id < len(self.game_state.village_data.get('buildings', [])):
            building = self.game_state.village_data['buildings'][home_id]
            building_pos = building['position']
            building_size_str = building.get('size', 'small')

            # Convert to pixel sizes
            size_multiplier = 3 if building_size_str == 'large' else (2 if building_size_str == 'medium' else 1)
            building_size_px = self.game_state.TILE_SIZE * size_multiplier

            # Get the number of roommates to determine how to spread beds
            roommates = villager.home.get('roommates', [])
            num_roommates = len(roommates)

            # Default position (for safety)
            bed_x = building_pos[0] + building_size_px // 2
            bed_y = building_pos[1] + building_size_px // 2

            # Try to find an available position
            attempt_count = 0
            padding = self.game_state.TILE_SIZE // 3 #

            # Keep trying to find an unoccupied position
            while attempt_count < 10:  # Limit attempts to avoid infinite loops
                # Calculate positions based on number of roommates and building size
                if building_size_str == 'large':
                    row = attempt_count % 2
                    col = (attempt_count // 2) % 2
                    cell_size = max(1, (building_size_px - padding * 2) // 2) # Ensure > 0
                    bed_x = building_pos[0] + padding + col * cell_size + cell_size // 2
                    bed_y = building_pos[1] + padding + row * cell_size + cell_size // 2
                elif building_size_str == 'medium':
                    if num_roommates <= 1:
                        bed_x = building_pos[0] + building_size_px // 2
                        bed_y = building_pos[1] + building_size_px // 2
                    else:
                        col = attempt_count % 2
                        bed_width_space = max(self.game_state.TILE_SIZE, building_size_px - padding * 2 - self.game_state.TILE_SIZE)
                        bed_x = building_pos[0] + padding + col * bed_width_space
                        bed_y = building_pos[1] + building_size_px // 2
                else:  # small
                    if num_roommates <= 1:
                        bed_x = building_pos[0] + building_size_px // 2
                        bed_y = building_pos[1] + building_size_px // 2
                    else:
                        offset_x = (attempt_count % 3 - 1) * (self.game_state.TILE_SIZE // 3)
                        offset_y = (attempt_count // 3 - 1) * (self.game_state.TILE_SIZE // 3)
                        bed_x = building_pos[0] + building_size_px // 2 + offset_x
                        bed_y = building_pos[1] + building_size_px // 2 + offset_y

                # Check if this position is already occupied
                position_key = f"{int(bed_x)},{int(bed_y)}"
                if position_key not in occupied_bed_positions:
                    occupied_bed_positions[position_key] = villager.name
                    break # Found an unoccupied position

                attempt_count += 1 # Try another position

            # Add some randomness to avoid perfect alignment
            bed_x += random.randint(-3, 3)
            bed_y += random.randint(-3, 3)

            # Set the villager's bed position
            villager.bed_position = (bed_x, bed_y)

            # Move villager to bed
            villager.position.x = bed_x
            villager.position.y = bed_y

            # --- MODIFIED PART (Safety Check for villager.rect) ---
            if villager.rect is None: # Check if rect is None
                 print(f"  Warning: Villager {getattr(villager, 'name', 'Unknown')} rect was None in initialize_unique_bed_position. Attempting creation.")
                 # Try calling the villager's image update method first
                 if hasattr(villager, '_update_image'):
                      villager._update_image() # This should create/update rect if image exists

                 # If rect is still None after _update_image (maybe image is also None)
                 if villager.rect is None:
                     if villager.image: # If image exists, create rect from it
                         villager.rect = villager.image.get_rect(center=(int(villager.position.x), int(villager.position.y)))
                     else: # If no image either, create a default rect
                          # Try to use frame size if available, else default
                          default_width = getattr(villager, 'frame_width', 24)
                          default_height = getattr(villager, 'frame_height', 24)
                          default_width = default_width if default_width > 0 else 24
                          default_height = default_height if default_height > 0 else 24
                          villager.rect = pygame.Rect(0, 0, default_width, default_height)
                          villager.rect.center = (int(villager.position.x), int(villager.position.y))

            # Now it should be safe to update center
            if villager.rect: # Double-check it exists now
                 villager.rect.center = (int(villager.position.x), int(villager.position.y))
            else:
                 print(f"  ERROR: Failed to ensure rect exists for villager {getattr(villager, 'name', 'Unknown')} in initialize_unique_bed_position.")
            # --- END MODIFIED PART ---

            # Clear destination
            villager.destination = None
        else:
            print(f"Warning: {getattr(villager, 'name', 'Unknown')} has invalid home ID: {home_id}")


    def assign_building_types(self):
        """Assign building types to buildings (house, store, inn, etc.)."""
        building_types = {
            "small": ["House", "Cottage", "Workshop", "Storage"],
            "medium": ["Inn", "Store", "Tavern", "Smithy", "Bakery"],
            "large": ["Town Hall", "Market", "Temple", "Manor"]
        }

        for building in self.game_state.village_data.get('buildings', []):
            # Only assign if type is missing or empty
            if 'building_type' not in building or not building['building_type']:
                size = building.get('size', 'small')
                available_types = building_types.get(size, ["House"])
                building['building_type'] = random.choice(available_types)


    def get_building_info(self, building_id=None, building_type=None):
        """Get information about buildings."""
        results = []

        for idx, building in enumerate(self.game_state.village_data.get('buildings', [])):
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
                'size': building.get('size', 'small'),
                'position': building.get('position', (0,0)),
                'name': building.get('name', f"Building #{idx}")
            }

            # Add residents if applicable
            residents = []
            for villager in self.game_state.villagers:
                if hasattr(villager, 'home') and villager.home and 'id' in villager.home:
                    if villager.home['id'] == idx:
                        residents.append(getattr(villager, 'name', 'Unknown Villager'))

            if residents:
                info['residents'] = residents

            results.append(info)

            # Return early if specific ID requested
            if building_id is not None:
                return results

        return results