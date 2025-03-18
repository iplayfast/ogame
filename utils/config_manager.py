#!/usr/bin/env python
"""
Village Simulation - Configuration Manager

This module handles loading and saving configuration settings from config.json.
"""

import os
import json
import copy

# Default configuration
DEFAULT_CONFIG = {
    "villagers": {
        "count": 10,
        "comments": "Number of villagers to create at game start"
    },
    "buildings": {
        "size_multiplier": 1.0,
        "comments": "Multiplier for building sizes (1.0 = default, 2.0 = double size, etc.)"
    },
    "system": {
        "debug_mode": False,
        "enable_console": True
    }
}

# Singleton config instance
_config = None

def get_config():
    """
    Get the current configuration.
    
    Returns:
        dict: Current configuration dictionary
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config

def load_config(config_path="config.json"):
    """
    Load configuration from the config file, or create default config if not found.
    
    Args:
        config_path (str): Path to the config.json file
        
    Returns:
        dict: Loaded configuration dictionary
    """
    config = copy.deepcopy(DEFAULT_CONFIG)
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                
            # Update default config with user values
            for section in user_config:
                if section in config:
                    if isinstance(config[section], dict) and isinstance(user_config[section], dict):
                        # For dict sections, only copy values that aren't comments
                        for key, value in user_config[section].items():
                            if not key.startswith("_") and key != "comments":
                                config[section][key] = value
                    else:
                        # For non-dict sections, replace entirely
                        config[section] = user_config[section]
                else:
                    # Add new sections from user config
                    config[section] = user_config[section]
                    
            print(f"Configuration loaded from {config_path}")
        else:
            # No config file found, create a default one
            save_config(config, config_path)
            print(f"Default configuration created at {config_path}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("Using default configuration instead")
    
    return config

def save_config(config=None, config_path="config.json"):
    """
    Save the current configuration to the config file.
    
    Args:
        config (dict, optional): Configuration to save. If None, save current global config.
        config_path (str): Path to the config file
        
    Returns:
        bool: True if successful, False otherwise
    """
    if config is None:
        config = get_config()
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False

def update_config(section, key, value):
    """
    Update a specific configuration value.
    
    Args:
        section (str): Configuration section (e.g., 'villagers', 'buildings')
        key (str): Configuration key within the section
        value: New value to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = get_config()
    
    if section not in config:
        config[section] = {}
    
    config[section][key] = value
    return save_config(config)

def apply_config_to_game(game_state):
    """
    Apply configuration settings to the game state.
    
    Args:
        game_state: The game state object
        
    Returns:
        bool: True if successful, False otherwise
    """
    config = get_config()
    
    try:
        # Apply building size multiplier if different from default
        building_multiplier = config["buildings"].get("size_multiplier", 1.0)
        if building_multiplier != 1.0:
            apply_building_size_multiplier(game_state, building_multiplier)
            
        # Set number of villagers to create
        # Note: This won't affect existing villagers, only newly created ones
        game_state.num_villagers = config["villagers"].get("count", 10)
        
        # Apply other settings as needed
        
        print(f"Applied configuration: {building_multiplier}x building size, {game_state.num_villagers} villagers")
        return True
    except Exception as e:
        print(f"Error applying configuration: {e}")
        return False

def apply_building_size_multiplier(game_state, multiplier):
    """
    Apply building size multiplier to the game.
    
    Args:
        game_state: The game state object
        multiplier: Building size multiplier
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not hasattr(game_state, 'renderer'):
        print("Warning: Could not find renderer in game state")
        return False
    
    try:
        # Keep track of the original render_buildings method if we haven't already
        if not hasattr(game_state.renderer, '_original_render_buildings'):
            game_state.renderer._original_render_buildings = game_state.renderer._render_buildings
        
        # Define a new render_buildings method that applies the multiplier
        def modified_render_buildings(self, village_data, visible_left, visible_right, 
                                    visible_top, visible_bottom, camera_x, camera_y, 
                                    ui_manager, selected_villager=None):
            # Make a shallow copy of the buildings list to avoid modifying original data
            original_buildings = village_data['buildings']
            copied_buildings = []
            
            # Create copies with adjusted sizes for rendering
            for building in original_buildings:
                building_copy = building.copy()
                
                # Store original size
                if 'original_size' not in building_copy:
                    building_copy['original_size'] = building_copy['size']
                
                # Apply size multiplier
                size_name = building_copy['original_size']
                if multiplier >= 3.0:
                    # If multiplier is very large, use large for all buildings
                    building_copy['size'] = 'large'
                elif multiplier >= 2.0:
                    # For medium multiplier, upgrade small to medium, keep others
                    if size_name == 'small':
                        building_copy['size'] = 'medium'
                # For smaller multipliers, keep original sizes
                
                copied_buildings.append(building_copy)
            
            # Temporarily replace buildings for rendering
            village_data['buildings'] = copied_buildings
            
            try:
                # Call original method with the modified data
                self._original_render_buildings(village_data, visible_left, visible_right,
                                            visible_top, visible_bottom, camera_x, camera_y,
                                            ui_manager, selected_villager)
            finally:
                # Restore original data
                village_data['buildings'] = original_buildings
        
        # Apply the modified method
        import types
        game_state.renderer._render_buildings = types.MethodType(modified_render_buildings, game_state.renderer)
        
        # Also update input handler for click detection on the larger buildings
        if hasattr(game_state, 'input_handler'):
            if not hasattr(game_state.input_handler, '_original_check_building_click'):
                game_state.input_handler._original_check_building_click = game_state.input_handler._check_building_click
            
            # Define a new building click check method with adjusted sizes
            def modified_check_building_click(self, world_x, world_y):
                for building_index, building in enumerate(self.game_state.village_data['buildings']):
                    x, y = building['position']
                    
                    # Determine size based on original size and multiplier
                    original_size = building.get('original_size', building['size'])
                    size_multiplier = 1
                    
                    if original_size == 'large':
                        size_multiplier = 3
                    elif original_size == 'medium':
                        size_multiplier = 2
                    # Else size_multiplier stays 1 for 'small'
                    
                    # Apply the global multiplier
                    size_multiplier = max(size_multiplier, int(multiplier))
                    
                    # Calculate building size in pixels
                    building_size = self.game_state.TILE_SIZE * size_multiplier
                    
                    if x <= world_x <= x + building_size and y <= world_y <= y + building_size:
                        # Add building index
                        building['id'] = building_index
                        self.game_state.housing_ui.set_selected_building(building)
                        
                        # Notify through Interface
                        import Interface
                        Interface.on_building_selected(building)
                        
                        print(f"Clicked on building: {building.get('building_type', 'house')}")
                        return True
                
                # Reset selected building if clicked elsewhere
                if hasattr(self.game_state.housing_ui, 'selected_building') and self.game_state.housing_ui.selected_building is not None:
                    self.game_state.housing_ui.set_selected_building(None)
                
                return False
            
            # Apply the modified method
            game_state.input_handler._check_building_click = types.MethodType(modified_check_building_click, game_state.input_handler)
        
        print(f"Applied building size multiplier: {multiplier}x")
        return True
    except Exception as e:
        print(f"Error applying building size multiplier: {e}")
        return False
