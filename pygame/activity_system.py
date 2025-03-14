import json
import random
import math
import os
from copy import deepcopy


class ActivitySystem:
    """
    A flexible activity system for villagers that uses JSON configuration and can be
    dynamically modified based on events, individual preferences, and environmental factors.
    """
    
    def __init__(self, villager=None, job=None, custom_config=None):
        """
        Initialize the activity system.
        
        Args:
            villager: The villager this system belongs to (optional)
            job: The villager's job (optional, can be derived from villager)
            custom_config: Path to a custom configuration file (optional)
        """
        self.villager = villager
        self.job = job if job else (villager.job if villager else "Default")
        
        # Load default configuration
        self.config = self._load_config(custom_config)
        
        # Villager-specific overrides
        self.custom_activities = []
        self.custom_time_ranges = {}
        self.active_conditions = set()  # Set of active condition modifiers (e.g., "raining")
        
        # Current activity state
        self.current_activity_name = None
        self.current_activity_data = None
        self.activity_start_time = 0
        self.activity_duration = 0
    
    def _load_config(self, custom_config=None):
        """
        Load the activity configuration from JSON.
        
        Args:
            custom_config: Path to a custom configuration file (optional)
            
        Returns:
            Dictionary with the configuration
        """
        # Start with default config
        default_config_path = "activity_config.json"
        
        # First try to load custom config if provided
        if custom_config and os.path.exists(custom_config):
            try:
                with open(custom_config, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading custom config: {e}")
        
        # Then try default config file
        if os.path.exists(default_config_path):
            try:
                with open(default_config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading default config: {e}")
        
        # If no config files are available, use minimal hardcoded defaults
        return {
            "time_periods": {
                "early_morning": {"start": 6, "end": 9, "priority": 1},
                "morning": {"start": 9, "end": 12, "priority": 2},
                "midday": {"start": 12, "end": 14, "priority": 3},
                "afternoon": {"start": 14, "end": 18, "priority": 2},
                "evening": {"start": 18, "end": 21, "priority": 1},
                "night": {"start": 21, "end": 24, "priority": 0}
            },
            "activity_pools": {
                "early_morning": ["Waking up", "Getting ready"],
                "morning": ["Working", "Running errands"],
                "midday": ["Having lunch", "Taking a break"],
                "afternoon": ["Working", "Running errands"],
                "evening": ["Heading home", "Having dinner"],
                "night": ["Preparing for bed", "Getting ready to sleep"]
            },
            "job_activities": {
                "Default": {
                    "morning": [{"name": "Working", "weight": 0.7}],
                    "afternoon": [{"name": "Working", "weight": 0.6}]
                }
            }
        }
    
    def save_config(self, filepath="villager_activity_config.json"):
        """
        Save the current configuration to a JSON file.
        Useful for debugging or for creating custom configurations.
        
        Args:
            filepath: Path to save the configuration
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get_time_period(self, current_hour):
        """
        Determine the current time period based on the hour.
        
        Args:
            current_hour: Current hour (0-24)
            
        Returns:
            String name of the current time period
        """
        # First check custom time ranges
        for period, (start, end) in self.custom_time_ranges.items():
            if start <= current_hour < end:
                return period
        
        # Then check config time periods
        for period, range_data in self.config["time_periods"].items():
            start = range_data["start"]
            end = range_data["end"]
            if start <= current_hour < end:
                return period
        
        # Default to night for hours outside defined ranges (midnight to 6 AM)
        return "night"
    
    def get_activity(self, current_hour, village_data=None):
        """
        Get an appropriate activity for the given hour.
        
        Args:
            current_hour: Current hour (0-24)
            village_data: Optional village data for location-aware activities
            
        Returns:
            Activity information (either a string or a dictionary with details)
        """
        # Get current time period
        time_period = self.get_time_period(current_hour)
        
        # 1. Check for active condition overrides (e.g., village is under attack)
        if self.active_conditions:
            override_activity = self._check_condition_overrides(time_period)
            if override_activity:
                return override_activity
        
        # 2. Check job-specific activities for this time period
        job_activity = self._get_job_activity(time_period)
        if job_activity:
            # If job activity has location requirements and village data is provided
            # make sure the location exists
            if isinstance(job_activity, dict) and village_data:
                # Verify location exists before returning job activity
                if self._verify_location_availability(job_activity, village_data):
                    return job_activity
            else:
                return job_activity
        
        # 3. Check location-specific activities if village data is provided
        if village_data:
            location_activity = self._get_location_activity(village_data)
            if location_activity:
                return location_activity
        
        # 4. Check custom activities (specific to this villager)
        if self.custom_activities:
            custom_activity = self._get_custom_activity(time_period)
            if custom_activity:
                return custom_activity
        
        # 5. Fall back to generic activities for this time period
        return self._get_generic_activity(time_period)
    
    def _check_condition_overrides(self, time_period):
        """
        Check if any active conditions override normal activities.
        
        Args:
            time_period: Current time period name
            
        Returns:
            Override activity or None
        """
        if "condition_modifiers" not in self.config:
            return None
            
        for condition in self.active_conditions:
            if condition in self.config["condition_modifiers"]:
                condition_data = self.config["condition_modifiers"][condition]
                
                # Check for complete overrides
                if "override_activities" in condition_data:
                    # Check for job-specific override
                    if self.job in condition_data["override_activities"]:
                        activities = condition_data["override_activities"][self.job]
                        if activities:
                            return random.choices(
                                activities, 
                                weights=[a.get("weight", 1.0) for a in activities],
                                k=1
                            )[0]
                    
                    # Check for default override
                    elif "Default" in condition_data["override_activities"]:
                        activities = condition_data["override_activities"]["Default"]
                        if activities:
                            return random.choices(
                                activities, 
                                weights=[a.get("weight", 1.0) for a in activities],
                                k=1
                            )[0]
        
        return None
    
    def _get_job_activity(self, time_period):
        """
        Get a job-specific activity for the current time period.
        
        Args:
            time_period: Current time period name
            
        Returns:
            Activity information or None
        """
        if "job_activities" not in self.config:
            return None
            
        # Check if job exists in config
        if self.job in self.config["job_activities"]:
            job_data = self.config["job_activities"][self.job]
            
            # Check if this time period has job-specific activities
            if time_period in job_data and job_data[time_period]:
                activities = job_data[time_period]
                
                # Apply personality modifiers
                if self.villager and hasattr(self.villager, 'personality'):
                    activities = self._apply_personality_modifiers(activities, "work_activities")
                
                # Select an activity based on weights
                return random.choices(
                    activities, 
                    weights=[a.get("weight", 1.0) for a in activities],
                    k=1
                )[0]
        
        # Check for default job activities
        if "Default" in self.config["job_activities"]:
            default_job_data = self.config["job_activities"]["Default"]
            
            if time_period in default_job_data and default_job_data[time_period]:
                activities = default_job_data[time_period]
                
                # Apply personality modifiers
                if self.villager and hasattr(self.villager, 'personality'):
                    activities = self._apply_personality_modifiers(activities, "work_activities")
                
                # Select an activity based on weights
                return random.choices(
                    activities, 
                    weights=[a.get("weight", 1.0) for a in activities],
                    k=1
                )[0]
        
        return None
    
    def _get_location_activity(self, village_data):
        """
        Get a location-based activity based on nearby features.
        
        Args:
            village_data: Village data dictionary
            
        Returns:
            Location-based activity or None
        """
        if not hasattr(self.villager, 'position') or "location_activities" not in self.config:
            return None
            
        # Get villager's current position
        x, y = self.villager.position.x, self.villager.position.y
        
        # Check for nearby water
        is_near_water = self._is_near_water(x, y, village_data)
        if is_near_water and "outdoors" in self.config["location_activities"]:
            if "water_adjacent" in self.config["location_activities"]["outdoors"]:
                activities = self.config["location_activities"]["outdoors"]["water_adjacent"]
                
                # Apply condition modifiers
                activities = self._apply_condition_modifiers(activities, "outdoors")
                
                # Apply personality modifiers
                if hasattr(self.villager, 'personality'):
                    activities = self._apply_personality_modifiers(activities, "outdoors")
                
                # Select an activity based on weights
                if activities:
                    return random.choices(
                        activities, 
                        weights=[a.get("weight", 1.0) for a in activities],
                        k=1
                    )[0]
        
        # Check for paths
        is_on_path = self._is_on_path(x, y, village_data)
        if is_on_path and "outdoors" in self.config["location_activities"]:
            if "path" in self.config["location_activities"]["outdoors"]:
                activities = self.config["location_activities"]["outdoors"]["path"]
                
                # Apply condition modifiers
                activities = self._apply_condition_modifiers(activities, "outdoors")
                
                # Apply personality modifiers
                if hasattr(self.villager, 'personality'):
                    activities = self._apply_personality_modifiers(activities, "outdoors")
                
                # Select an activity based on weights
                if activities:
                    return random.choices(
                        activities, 
                        weights=[a.get("weight", 1.0) for a in activities],
                        k=1
                    )[0]
        
        # Check if villager is at home
        is_at_home = self._is_at_home(x, y, village_data)
        if is_at_home and "home" in self.config["location_activities"]:
            if "generic" in self.config["location_activities"]["home"]:
                activities = self.config["location_activities"]["home"]["generic"]
                
                # Apply condition modifiers
                activities = self._apply_condition_modifiers(activities, "indoors")
                
                # Apply personality modifiers
                if hasattr(self.villager, 'personality'):
                    activities = self._apply_personality_modifiers(activities, "rest_activities")
                
                # Select an activity based on weights
                if activities:
                    return random.choices(
                        activities, 
                        weights=[a.get("weight", 1.0) for a in activities],
                        k=1
                    )[0]
        
        return None
    
    def _get_custom_activity(self, time_period):
        """
        Get a custom activity for this villager appropriate for the time period.
        
        Args:
            time_period: Current time period name
            
        Returns:
            Custom activity or None
        """
        if not self.custom_activities:
            return None
            
        # Filter activities that might be appropriate for this time period
        time_appropriate = []
        
        for activity in self.custom_activities:
            # If activity has time_period specified, check if it matches
            if isinstance(activity, dict) and "time_period" in activity:
                if activity["time_period"] == time_period:
                    time_appropriate.append(activity)
            # For string activities, check based on keywords
            elif isinstance(activity, str):
                if self._is_activity_appropriate_for_time(activity, time_period):
                    time_appropriate.append(activity)
            # For other dictionary activities without time_period, add them
            elif isinstance(activity, dict):
                time_appropriate.append(activity)
        
        if time_appropriate:
            # If activities are dictionaries with weights, use weighted selection
            if all(isinstance(a, dict) and "weight" in a for a in time_appropriate):
                return random.choices(
                    time_appropriate,
                    weights=[a["weight"] for a in time_appropriate],
                    k=1
                )[0]
            # Otherwise, select randomly
            return random.choice(time_appropriate)
        
        return None
    
    def _get_generic_activity(self, time_period):
        """
        Get a generic activity for the time period from the activity pools.
        
        Args:
            time_period: Current time period name
            
        Returns:
            Generic activity
        """
        if "activity_pools" in self.config and time_period in self.config["activity_pools"]:
            activities = self.config["activity_pools"][time_period]
            if activities:
                return random.choice(activities)
        
        # Fallback
        return "Wandering"
    
    def _is_activity_appropriate_for_time(self, activity, time_period):
        """
        Check if a string activity is appropriate for a time period based on keywords.
        
        Args:
            activity: Activity name
            time_period: Time period name
            
        Returns:
            Boolean indicating appropriateness
        """
        activity = activity.lower()
        
        # Early morning activities
        if time_period == "early_morning" and any(kw in activity for kw in 
                                                ["wake", "breakfast", "morning", "early"]):
            return True
            
        # Morning work activities
        elif time_period == "morning" and any(kw in activity for kw in 
                                             ["work", "duty", "craft", "make", "tend"]):
            return True
            
        # Midday activities
        elif time_period == "midday" and any(kw in activity for kw in 
                                            ["lunch", "break", "rest", "eat"]):
            return True
            
        # Afternoon activities
        elif time_period == "afternoon" and any(kw in activity for kw in 
                                              ["work", "errand", "visit", "collect"]):
            return True
            
        # Evening activities
        elif time_period == "evening" and any(kw in activity for kw in 
                                            ["dinner", "home", "relax", "tavern", "inn"]):
            return True
            
        # Night activities
        elif time_period == "night" and any(kw in activity for kw in 
                                          ["sleep", "bed", "rest", "night"]):
            return True
            
        return False
    
    def _is_near_water(self, x, y, village_data):
        """
        Check if a position is near water.
        
        Args:
            x, y: Position coordinates
            village_data: Village data dictionary
            
        Returns:
            Boolean indicating if the position is near water
        """
        if 'water' not in village_data:
            return False
            
        # Check if any water tile is within a threshold distance
        tile_size = 32  # Assuming TILE_SIZE is 32
        threshold = tile_size * 2  # Check within 2 tiles
        
        for water_tile in village_data['water']:
            water_x, water_y = water_tile['position']
            distance = math.sqrt((x - water_x)**2 + (y - water_y)**2)
            if distance <= threshold:
                return True
                
        return False
    
    def _is_on_path(self, x, y, village_data):
        """
        Check if a position is on a path.
        
        Args:
            x, y: Position coordinates
            village_data: Village data dictionary
            
        Returns:
            Boolean indicating if the position is on a path
        """
        if 'paths' not in village_data:
            return False
            
        # Check if the position is on a path
        tile_size = 32  # Assuming TILE_SIZE is 32
        threshold = tile_size / 2  # Position must be close to path center
        
        for path in village_data['paths']:
            path_x, path_y = path['position']
            distance = math.sqrt((x - path_x)**2 + (y - path_y)**2)
            if distance <= threshold:
                return True
                
        return False
    
    def _is_at_home(self, x, y, village_data):
        """
        Check if the villager is at their home.
        
        Args:
            x, y: Position coordinates
            village_data: Village data dictionary
            
        Returns:
            Boolean indicating if the villager is at their home
        """
        if not hasattr(self.villager, 'home') or not self.villager.home:
            return False
            
        home_id = self.villager.home.get('id', -1)
        if home_id < 0 or home_id >= len(village_data['buildings']):
            return False
            
        building = village_data['buildings'][home_id]
        bx, by = building['position']
        size_name = building['size']
        
        # Determine building size in pixels
        size_multiplier = 3 if size_name == 'large' else (2 if size_name == 'medium' else 1)
        size_px = size_multiplier * 32  # Assuming TILE_SIZE is 32
        
        # Check if villager is inside the building
        return (bx <= x < bx + size_px and by <= y < by + size_px)
    
    def _verify_location_availability(self, activity, village_data):
        """
        Verify that the location and interaction point required by an activity exists.
        
        Args:
            activity: Activity dictionary
            village_data: Village data dictionary
            
        Returns:
            Boolean indicating if the location is available
        """
        if not isinstance(activity, dict):
            return True  # No location requirements for string activities
            
        # Check if activity has location requirements
        if "location_type" not in activity:
            return True  # No location type specified
            
        location_type = activity["location_type"]
        
        # Handle outdoor
