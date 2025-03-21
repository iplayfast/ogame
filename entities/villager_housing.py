import json
import random
import os
from ui import Interface
            
def assign_housing_and_jobs(villagers, village_data):
    """
    Assign villagers to houses and workplaces, creating a JSON file with their info.
    
    Args:
        villagers: List of villager objects
        village_data: Village data dictionary containing buildings
        
    Returns:
        Dictionary containing the villager assignments
    """
    # Categorize buildings by type
    buildings_by_type = {}
    for i, building in enumerate(village_data['buildings']):
        building_type = building.get('building_type', 'House')
        if building_type not in buildings_by_type:
            buildings_by_type[building_type] = []
        
        # Add building index to make it easier to reference
        building_with_id = building.copy()
        building_with_id['id'] = i
        buildings_by_type[building_type].append(building_with_id)
    
    # Get residential buildings
    residential_buildings = []
    for building_type in ['House', 'Cottage', 'Manor']:
        if building_type in buildings_by_type:
            residential_buildings.extend(buildings_by_type[building_type])
    
    # If no residential buildings, use any available buildings
    if not residential_buildings and village_data['buildings']:
        residential_buildings = [b.copy() for b in village_data['buildings']]
        for i, building in enumerate(residential_buildings):
            building['id'] = i
    
    # Make sure we have at least some buildings
    if not residential_buildings:
        print("Warning: No buildings found for housing villagers!")
        return {}
    
    # Create assignment data
    villager_data = []
    assigned_houses = {}  # Keep track of who is assigned to each house
    
    # First, assign special workplaces based on job
    job_to_workplace = {
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
    
    # Daily activities by job type
    job_activities = {
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
            "Prepare equipment", 
            "Travel to mines outside village", 
            "Dig for ore and minerals", 
            "Take breaks for meals",
            "Sort and clean findings", 
            "Return to village with materials",
            "Sell findings at market",
            "Return home"
        ],
        "Hunter": [
            "Check hunting equipment", 
            "Travel to hunting grounds", 
            "Track animals in the forest", 
            "Hunt for game", 
            "Process catches",
            "Return to village with game",
            "Sell meat and furs at market",
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
    
    # Common activities everyone might do
    common_activities = [
        "Visit the market",
        "Chat with neighbors",
        "Eat at the Inn",
        "Relax at home",
        "Attend town gathering",
        "Go for a walk",
        "Collect water from well"
    ]
    
    # Fix this line - use the villagers parameter that was passed in
    for villager in villagers:
        # Find workplace based on job
        workplace = None
        workplace_type = job_to_workplace.get(villager.job)
        
        if workplace_type and workplace_type in buildings_by_type and buildings_by_type[workplace_type]:
            # Try to assign a dedicated workplace if available
            for building in buildings_by_type[workplace_type]:
                # Check if this building is already assigned
                is_available = True
                for v_data in villager_data:
                    if v_data.get('workplace') and v_data['workplace']['id'] == building['id']:
                        # For some jobs, only one person should work there
                        if villager.job in ["Blacksmith", "Baker", "Innkeeper"]:
                            is_available = False
                            break
                
                if is_available:
                    workplace = {
                        'id': building['id'],
                        'type': workplace_type,
                        'position': building['position']
                    }
                    break
        
        # Assign home (try to match to workplace area if possible)
        house = None
        if workplace:
            # Try to find a house near the workplace
            workplace_pos = workplace['position']
            nearest_house = None
            nearest_distance = float('inf')
            
            for building in residential_buildings:
                # Skip if house is full (2 occupants max for a house/cottage, 4 for a manor)
                building_id = building['id']
                occupants = assigned_houses.get(building_id, [])
                max_occupants = 4 if building['size'] == 'large' else 2
                
                if len(occupants) >= max_occupants:
                    continue
                    
                # Calculate distance to workplace
                bpos = building['position']
                dx = bpos[0] - workplace_pos[0]
                dy = bpos[1] - workplace_pos[1]
                distance = (dx*dx + dy*dy) ** 0.5
                
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_house = building
            
            if nearest_house:
                house = nearest_house
        
        # If no house found near workplace, assign any available house
        if not house:
            for building in residential_buildings:
                building_id = building['id']
                occupants = assigned_houses.get(building_id, [])
                max_occupants = 4 if building['size'] == 'large' else 2
                
                if len(occupants) < max_occupants:
                    house = building
                    break
        
        # Last resort - assign to any house, even if "full"
        if not house and residential_buildings:
            house = random.choice(residential_buildings)
        
        # Track house occupancy
        if house:
            house_id = house['id']
            if house_id not in assigned_houses:
                assigned_houses[house_id] = []
            assigned_houses[house_id].append(villager.name)
        
        # Create the villager entry
        v_entry = {
            'name': villager.name,
            'job': villager.job,
            'home': {
                'id': house['id'] if house else -1,
                'type': house['building_type'] if house else "Unknown",
                'position': house['position'] if house else (0, 0),
                'roommates': assigned_houses.get(house['id'] if house else -1, [])
            }
        }
        
        # Add workplace if assigned
        if workplace:
            v_entry['workplace'] = workplace
        
        # Create a daily schedule
        job_specific = job_activities.get(villager.job, [])
        # Add 2-3 common activities
        additional = random.sample(common_activities, random.randint(2, 3))
        
        v_entry['daily_activities'] = job_specific + additional
        random.shuffle(v_entry['daily_activities'])  # Randomize order somewhat
        
        # Make sure "Return home" or "Relax at home" is at the end
        home_activities = [act for act in v_entry['daily_activities'] if "home" in act.lower()]
        if home_activities:
            for home_act in home_activities:
                v_entry['daily_activities'].remove(home_act)
            v_entry['daily_activities'].append(home_activities[0])
        
        villager_data.append(v_entry)
    
    # Special handling for miners and hunters who work outside the village
    for villager in villagers:
        if villager.job in ["Miner", "Hunter"] and not any(v['name'] == villager.name and 'workplace' in v for v in villager_data):
            # Create an "external" workplace at the edge of the village
            village_width = village_data.get('width', 1000)
            village_height = village_data.get('height', 1000)
            tile_size = 32  # Default tile size
            
            # Choose a direction (north, east, south, west)
            direction = random.choice(["north", "east", "south", "west"])
            
            if direction == "north":
                workplace_pos = (random.randint(100, village_width - 100), tile_size * 2)
            elif direction == "east":
                workplace_pos = (village_width - tile_size * 2, random.randint(100, village_height - 100))
            elif direction == "south":
                workplace_pos = (random.randint(100, village_width - 100), village_height - tile_size * 2)
            else:  # west
                workplace_pos = (tile_size * 2, random.randint(100, village_height - 100))
            
            # Create external workplace data
            workplace = {
                'id': -1,  # Special ID for external workplaces
                'type': f"{villager.job} Workplace",
                'position': workplace_pos,
                'external': True  # Mark as external
            }
            
            # Assign to villager
            v_entry = next((v for v in villager_data if v['name'] == villager.name), None)
            if v_entry:
                v_entry['workplace'] = workplace
                print(f"Assigned external workplace for {villager.name} ({villager.job})")
    
    # Name houses based on occupants
    house_names = {}
    for house_id, occupants in assigned_houses.items():
        if not occupants:
            continue
            
        if len(occupants) == 1:
            name = f"{occupants[0]}'s House"
        else:
            # Get last names of occupants
            last_names = [name.split()[-1] for name in occupants]
            if len(set(last_names)) == 1:
                # Same last name - probably a family
                name = f"The {last_names[0]} House"
            else:
                # Different last names
                if len(occupants) == 2:
                    name = f"{occupants[0]} and {occupants[1]}'s House"
                else:
                    name = f"{occupants[0]} and Others' House"
        
        house_names[house_id] = name
    
    # Add house names to buildings and villager data
    for i, building in enumerate(village_data['buildings']):
        if i in house_names:
            building['name'] = house_names[i]
    
    for v_entry in villager_data:
        home_id = v_entry['home']['id']
        if home_id in house_names:
            v_entry['home']['name'] = house_names[home_id]
    
    # Create the full data structure
    village_assignments = {
        'villagers': villager_data,
        'house_names': house_names
    }
    
    # Save to JSON file
    with open('village_assignments.json', 'w') as f:
        json.dump(village_assignments, f, indent=4)
    
    print(f"Saved villager assignments to village_assignments.json")
    return village_assignments

def load_assignments(filename='village_assignments.json'):
    """
    Load villager assignments from a JSON file.
    
    Args:
        filename: Path to the JSON file
        
    Returns:
        Dictionary containing the villager assignments
    """
    if not os.path.exists(filename):
        print(f"Warning: Assignment file {filename} not found!")
        return {}
    
    with open(filename, 'r') as f:
        return json.load(f)


def update_game_with_assignments(game_state, assignments):
    """
    Update the game state with the villager assignments.
    
    Args:
        game_state: Game state object
        assignments: Villager assignments dictionary
    """
    if not assignments or 'villagers' not in assignments:
        return
    
    # Update buildings with names
    if 'house_names' in assignments:
        for building in game_state.village_data['buildings']:
            building_id = game_state.village_data['buildings'].index(building)
            if str(building_id) in assignments['house_names']:
                building['name'] = assignments['house_names'][str(building_id)]
    
    # Update villagers with home and workplace info
    for villager in game_state.villagers:
        for v_data in assignments['villagers']:
            if villager.name == v_data['name']:
                # Add home and workplace references
                villager.home = v_data.get('home', {})
                villager.workplace = v_data.get('workplace', {})
                villager.daily_activities = v_data.get('daily_activities', [])
                villager.is_sleeping = True
                villager.current_activity = "Sleeping"

                # Update villager's AI to consider home and workplace
                if hasattr(villager, 'find_new_destination'):
                    # Store the original method
                    villager._original_find_destination = villager.find_new_destination
                    
                    # Replace with our enhanced method that considers home and workplace
                    def enhanced_find_destination(self, village_data):
                        # 40% chance to go to home or workplace, 60% chance for normal behavior
                        if random.random() < 0.4:
                            if hasattr(self, 'home') and hasattr(self, 'workplace'):
                                # Decide between home and workplace based on time of day
                                # For now we'll just randomly choose
                                if random.random() < 0.5 and self.workplace:
                                    # Go to workplace
                                    workplace_pos = self.workplace.get('position')
                                    if workplace_pos:
                                        offset_x = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
                                        offset_y = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
                                        self.destination = (
                                            workplace_pos[0] + offset_x,
                                            workplace_pos[1] + offset_y
                                        )
                                        self.current_activity = f"Working at {self.workplace.get('type', 'workplace')}"
                                        return
                                else:
                                    # Go home
                                    home_pos = self.home.get('position')
                                    if home_pos:
                                        offset_x = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
                                        offset_y = random.randint(-self.TILE_SIZE, self.TILE_SIZE)
                                        self.destination = (
                                            home_pos[0] + offset_x,
                                            home_pos[1] + offset_y
                                        )
                                        self.current_activity = "At home"
                                        return
                        
                        # Fall back to original behavior
                        self._original_find_destination(village_data)
                    
                    # Bind our enhanced method to the villager
                    import types
                    villager.find_new_destination = types.MethodType(enhanced_find_destination, villager)

def notify_housing_assignments(villagers, assignments):
    """Notify Interface of housing and workplace assignments."""
    if not assignments or 'villagers' not in assignments:
        return
        
    for villager in villagers:
        for v_data in assignments['villagers']:
            if villager.name == v_data['name']:
                # Find the home building
                if 'home' in v_data and 'id' in v_data['home'] and v_data['home']['id'] >= 0:
                    home_id = v_data['home']['id']
                    # Notify Interface
                    Interface.on_building_housing_assigned(villager, {'id': home_id}, 'home')
                
                # Find the workplace building
                if 'workplace' in v_data and 'id' in v_data['workplace']:
                    workplace_id = v_data['workplace']['id']
                    # Notify Interface
                    Interface.on_building_housing_assigned(villager, {'id': workplace_id}, 'workplace')
                    
    print("Interface notified of all housing and workplace assignments")