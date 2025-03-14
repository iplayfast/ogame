"""
Interface module for Village Simulation.

This module provides a flexible system of hooks and callbacks that can be registered
to respond to various game events without modifying the core game code.

Usage:
    1. Register callback functions using register_* methods
    2. The game will automatically call these functions when events occur
    3. Periodic updates will be called based on the game timer

Example:
    # Register a callback for villager movement
    def on_villager_moved(villager, old_position, new_position):
        print(f"{villager.name} moved from {old_position} to {new_position}")
    
    Interface.register_villager_moved_callback(on_villager_moved)
"""

import time
import inspect

# Global callback registries
_time_callbacks = []           # Periodic time-based callbacks
_villager_callbacks = {}       # Callbacks for villager events
_building_callbacks = {}       # Callbacks for building events
_environment_callbacks = {}    # Callbacks for environment events
_game_event_callbacks = {}     # General game event callbacks
_ui_callbacks = {}             # UI event callbacks

# Frequency settings for time-based callbacks (in milliseconds)
DEFAULT_UPDATE_FREQUENCY = 1000  # 1 second
_last_update_time = 0

# Settings
_debug_mode = False  # When True, log all event dispatches

def set_debug(mode=True):
    """Enable or disable debug logging for event dispatches."""
    global _debug_mode
    _debug_mode = mode
    if _debug_mode:
        print("Interface debug mode ENABLED")
    else:
        print("Interface debug mode DISABLED")

def _log_event(event_name, **kwargs):
    """Log event details if debug mode is enabled."""
    if _debug_mode:
        args_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"[INTERFACE EVENT] {event_name}({args_str})")

def _check_callback_signature(callback, required_params):
    """Verify that a callback function has the required parameters."""
    sig = inspect.signature(callback)
    callback_params = list(sig.parameters.keys())
    
    # Check if the callback has the required parameters
    for param in required_params:
        if param not in callback_params and not any(p for p in callback_params if p.startswith('**')):
            return False
    return True

# ----- TIME & UPDATE CALLBACKS -----

def register_time_callback(callback, frequency_ms=DEFAULT_UPDATE_FREQUENCY):
    """
    Register a function to be called periodically based on game time.
    
    Args:
        callback: Function to call, should accept (current_time, delta_time)
        frequency_ms: How often to call this function (in milliseconds)
    """
    if not _check_callback_signature(callback, ['current_time', 'delta_time']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (current_time, delta_time)")
    
    _time_callbacks.append({
        'function': callback,
        'frequency': frequency_ms,
        'last_called': 0
    })
    return callback  # Return the callback for decorator support

def update(current_time, delta_time):
    """
    Call all registered time callbacks based on their frequency.
    This should be called from the game's main update loop.
    
    Args:
        current_time: Current game time in milliseconds
        delta_time: Time since last update in milliseconds
    """
    global _last_update_time
    
    # Call time-based callbacks if their interval has elapsed
    for callback_data in _time_callbacks:
        time_since_last_call = current_time - callback_data['last_called']
        
        if time_since_last_call >= callback_data['frequency']:
            try:
                callback_data['function'](current_time, delta_time)
                callback_data['last_called'] = current_time
            except Exception as e:
                print(f"Error in time callback {callback_data['function'].__name__}: {e}")
    
    _last_update_time = current_time

# ----- VILLAGER CALLBACKS -----

def register_villager_moved_callback(callback):
    """Register a callback for when a villager moves."""
    if not _check_callback_signature(callback, ['villager', 'old_position', 'new_position']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager, old_position, new_position)")
    
    _register_callback('villager_moved', callback)
    return callback

def register_villager_activity_changed_callback(callback):
    """Register a callback for when a villager changes activity."""
    if not _check_callback_signature(callback, ['villager', 'old_activity', 'new_activity']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager, old_activity, new_activity)")
    
    _register_callback('villager_activity_changed', callback)
    return callback

def register_villager_created_callback(callback):
    """Register a callback for when a new villager is created."""
    if not _check_callback_signature(callback, ['villager']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager)")
    
    _register_callback('villager_created', callback)
    return callback

def register_villager_sleep_state_changed_callback(callback):
    """Register a callback for when a villager falls asleep or wakes up."""
    if not _check_callback_signature(callback, ['villager', 'is_sleeping']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager, is_sleeping)")
    
    _register_callback('villager_sleep_state_changed', callback)
    return callback

def register_villager_selected_callback(callback):
    """Register a callback for when a villager is selected by the player."""
    if not _check_callback_signature(callback, ['villager', 'is_selected']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager, is_selected)")
    
    _register_callback('villager_selected', callback)
    return callback

def register_villager_interaction_callback(callback):
    """Register a callback for when villagers interact with each other."""
    if not _check_callback_signature(callback, ['villager1', 'villager2', 'interaction_type']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager1, villager2, interaction_type)")
    
    _register_callback('villager_interaction', callback)
    return callback

# ----- BUILDING CALLBACKS -----

def register_building_created_callback(callback):
    """Register a callback for when a new building is created."""
    if not _check_callback_signature(callback, ['building']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (building)")
    
    _register_callback('building_created', callback)
    return callback

def register_building_selected_callback(callback):
    """Register a callback for when a building is selected by the player."""
    if not _check_callback_signature(callback, ['building']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (building)")
    
    _register_callback('building_selected', callback)
    return callback

def register_building_entered_callback(callback):
    """Register a callback for when a villager enters a building."""
    if not _check_callback_signature(callback, ['villager', 'building']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager, building)")
    
    _register_callback('building_entered', callback)
    return callback

def register_building_exited_callback(callback):
    """Register a callback for when a villager exits a building."""
    if not _check_callback_signature(callback, ['villager', 'building']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager, building)")
    
    _register_callback('building_exited', callback)
    return callback

def register_building_housing_assigned_callback(callback):
    """Register a callback for when housing/workplace is assigned to a villager."""
    if not _check_callback_signature(callback, ['villager', 'building', 'assignment_type']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager, building, assignment_type)")
    
    _register_callback('building_housing_assigned', callback)
    return callback

# ----- ENVIRONMENT CALLBACKS -----

def register_time_changed_callback(callback):
    """Register a callback for when the game time changes."""
    if not _check_callback_signature(callback, ['hour', 'time_name']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (hour, time_name)")
    
    _register_callback('time_changed', callback)
    return callback

def register_path_created_callback(callback):
    """Register a callback for when a new path is created."""
    if not _check_callback_signature(callback, ['path_position', 'path_type']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (path_position, path_type)")
    
    _register_callback('path_created', callback)
    return callback

def register_tree_created_callback(callback):
    """Register a callback for when a new tree is created."""
    if not _check_callback_signature(callback, ['tree_position', 'tree_variant']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (tree_position, tree_variant)")
    
    _register_callback('tree_created', callback)
    return callback

def register_bridge_created_callback(callback):
    """Register a callback for when a new bridge is created."""
    if not _check_callback_signature(callback, ['bridge_position', 'bridge_type']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (bridge_position, bridge_type)")
    
    _register_callback('bridge_created', callback)
    return callback

# ----- GAME EVENT CALLBACKS -----

def register_game_started_callback(callback):
    """Register a callback for when the game starts."""
    if not _check_callback_signature(callback, ['game_state']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (game_state)")
    
    _register_callback('game_started', callback)
    return callback

def register_game_paused_callback(callback):
    """Register a callback for when the game is paused/unpaused."""
    if not _check_callback_signature(callback, ['is_paused']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (is_paused)")
    
    _register_callback('game_paused', callback)
    return callback

def register_village_generated_callback(callback):
    """Register a callback for when the village is generated."""
    if not _check_callback_signature(callback, ['village_data']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (village_data)")
    
    _register_callback('village_generated', callback)
    return callback

def register_console_command_callback(callback):
    """Register a callback for when a console command is executed."""
    if not _check_callback_signature(callback, ['command', 'args', 'result']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (command, args, result)")
    
    _register_callback('console_command', callback)
    return callback

# ----- UI CALLBACKS -----

def register_camera_moved_callback(callback):
    """Register a callback for when the camera moves."""
    if not _check_callback_signature(callback, ['old_position', 'new_position']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (old_position, new_position)")
    
    _register_callback('camera_moved', callback)
    return callback

def register_debug_toggled_callback(callback):
    """Register a callback for when debug display is toggled."""
    if not _check_callback_signature(callback, ['is_enabled']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (is_enabled)")
    
    _register_callback('debug_toggled', callback)
    return callback

def register_minimap_clicked_callback(callback):
    """Register a callback for when the minimap is clicked."""
    if not _check_callback_signature(callback, ['screen_position', 'world_position']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (screen_position, world_position)")
    
    _register_callback('minimap_clicked', callback)
    return callback

def register_ui_panel_toggled_callback(callback):
    """Register a callback for when a UI panel is shown/hidden."""
    if not _check_callback_signature(callback, ['panel_name', 'is_visible']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (panel_name, is_visible)")
    
    _register_callback('ui_panel_toggled', callback)
    return callback

# ----- HELPER METHODS FOR REGISTRATION AND DISPATCH -----

def _register_callback(event_name, callback):
    """Register a callback for a specific event."""
    # Determine which registry to use based on event name
    if event_name.startswith('villager_'):
        registry = _villager_callbacks
    elif event_name.startswith('building_'):
        registry = _building_callbacks
    elif event_name in ['time_changed', 'path_created', 'tree_created', 'bridge_created']:
        registry = _environment_callbacks
    elif event_name.startswith('game_') or event_name == 'console_command' or event_name == 'village_generated':
        registry = _game_event_callbacks
    else:
        registry = _ui_callbacks
    
    # Initialize the event list if it doesn't exist
    if event_name not in registry:
        registry[event_name] = []
    
    # Add the callback
    registry[event_name].append(callback)

def _dispatch_event(event_name, registry, **kwargs):
    """Dispatch an event to all registered callbacks."""
    if event_name in registry:
        _log_event(event_name, **kwargs)
        for callback in registry[event_name]:
            try:
                callback(**kwargs)
            except Exception as e:
                print(f"Error in {event_name} callback {callback.__name__}: {e}")

# ----- EVENT DISPATCHERS -----
# These are called from the game code when events occur

def dispatch_villager_event(event_name, **kwargs):
    """Dispatch a villager-related event."""
    _dispatch_event(event_name, _villager_callbacks, **kwargs)

def dispatch_building_event(event_name, **kwargs):
    """Dispatch a building-related event."""
    _dispatch_event(event_name, _building_callbacks, **kwargs)

def dispatch_environment_event(event_name, **kwargs):
    """Dispatch an environment-related event."""
    _dispatch_event(event_name, _environment_callbacks, **kwargs)

def dispatch_game_event(event_name, **kwargs):
    """Dispatch a game-related event."""
    _dispatch_event(event_name, _game_event_callbacks, **kwargs)

def dispatch_ui_event(event_name, **kwargs):
    """Dispatch a UI-related event."""
    _dispatch_event(event_name, _ui_callbacks, **kwargs)

# ----- SPECIFIC EVENT DISPATCHERS -----
# These are convenience methods that dispatch specific events

# Villager events
def on_villager_moved(villager, old_position, new_position):
    """Notify when a villager moves."""
    dispatch_villager_event('villager_moved', villager=villager, old_position=old_position, new_position=new_position)

def on_villager_activity_changed(villager, old_activity, new_activity):
    """Notify when a villager changes activity."""
    dispatch_villager_event('villager_activity_changed', villager=villager, old_activity=old_activity, new_activity=new_activity)

def on_villager_created(villager):
    """Notify when a new villager is created."""
    dispatch_villager_event('villager_created', villager=villager)

def on_villager_sleep_state_changed(villager, is_sleeping):
    """Notify when a villager falls asleep or wakes up."""
    dispatch_villager_event('villager_sleep_state_changed', villager=villager, is_sleeping=is_sleeping)

def on_villager_selected(villager, is_selected):
    """Notify when a villager is selected by the player."""
    dispatch_villager_event('villager_selected', villager=villager, is_selected=is_selected)

def on_villager_interaction(villager1, villager2, interaction_type):
    """Notify when villagers interact with each other."""
    dispatch_villager_event('villager_interaction', villager1=villager1, villager2=villager2, interaction_type=interaction_type)

# Building events
def on_building_created(building):
    """Notify when a new building is created."""
    dispatch_building_event('building_created', building=building)

def on_building_selected(building):
    """Notify when a building is selected by the player."""
    dispatch_building_event('building_selected', building=building)

def on_building_entered(villager, building):
    """Notify when a villager enters a building."""
    dispatch_building_event('building_entered', villager=villager, building=building)

def on_building_exited(villager, building):
    """Notify when a villager exits a building."""
    dispatch_building_event('building_exited', villager=villager, building=building)

def on_building_housing_assigned(villager, building, assignment_type):
    """Notify when housing/workplace is assigned to a villager."""
    dispatch_building_event('building_housing_assigned', villager=villager, building=building, assignment_type=assignment_type)

# Environment events
def on_time_changed(hour, time_name):
    """Notify when the game time changes."""
    dispatch_environment_event('time_changed', hour=hour, time_name=time_name)

def on_path_created(path_position, path_type):
    """Notify when a new path is created."""
    dispatch_environment_event('path_created', path_position=path_position, path_type=path_type)

def on_tree_created(tree_position, tree_variant):
    """Notify when a new tree is created."""
    dispatch_environment_event('tree_created', tree_position=tree_position, tree_variant=tree_variant)

def on_bridge_created(bridge_position, bridge_type):
    """Notify when a new bridge is created."""
    dispatch_environment_event('bridge_created', bridge_position=bridge_position, bridge_type=bridge_type)

# Game events
def on_game_started(game_state):
    """Notify when the game starts."""
    dispatch_game_event('game_started', game_state=game_state)

def on_game_paused(is_paused):
    """Notify when the game is paused/unpaused."""
    dispatch_game_event('game_paused', is_paused=is_paused)

def on_village_generated(village_data):
    """Notify when the village is generated."""
    dispatch_game_event('village_generated', village_data=village_data)

def on_console_command(command, args, result):
    """Notify when a console command is executed."""
    dispatch_game_event('console_command', command=command, args=args, result=result)

# UI events
def on_camera_moved(old_position, new_position):
    """Notify when the camera moves."""
    dispatch_ui_event('camera_moved', old_position=old_position, new_position=new_position)

def on_debug_toggled(is_enabled):
    """Notify when debug display is toggled."""
    dispatch_ui_event('debug_toggled', is_enabled=is_enabled)

def on_minimap_clicked(screen_position, world_position):
    """Notify when the minimap is clicked."""
    dispatch_ui_event('minimap_clicked', screen_position=screen_position, world_position=world_position)

def on_ui_panel_toggled(panel_name, is_visible):
    """Notify when a UI panel is shown/hidden."""
    dispatch_ui_event('ui_panel_toggled', panel_name=panel_name, is_visible=is_visible)


# ----- BUILT-IN CALLBACK IMPLEMENTATIONS -----
# These can be used directly or as examples for custom implementations

def default_on_game_started(game_state):
    """Default handler when game starts."""
    print("Game started!")

def default_on_game_paused(is_paused):
    """Default handler when game is paused/resumed."""
    status = "PAUSED" if is_paused else "RESUMED"
    print(f"Game {status}")

def default_on_village_generated(village_data):
    """Default handler when village is generated."""
    print(f"Village generated with {len(village_data['buildings'])} buildings, " +
          f"{len(village_data['paths'])} path tiles, and {len(village_data['trees'])} trees")

def default_on_villager_created(villager):
    """Default handler when a new villager is created."""
    print(f"New villager created: {villager.name} the {villager.job}")

def default_on_villager_moved(villager, old_position, new_position):
    """Default handler when a villager moves."""
    # Only log significant movements (more than 5 pixels)
    distance = ((new_position[0] - old_position[0])**2 + 
                (new_position[1] - old_position[1])**2)**0.5
    if distance > 5:
        print(f"{villager.name} moved {distance:.1f} pixels")

def default_on_villager_activity_changed(villager, old_activity, new_activity):
    """Default handler when a villager changes activity."""
    print(f"{villager.name} changed activity: {old_activity} -> {new_activity}")

def default_on_villager_sleep_state_changed(villager, is_sleeping):
    """Default handler when a villager's sleep state changes."""
    if is_sleeping:
        print(f"{villager.name} has gone to sleep")
    else:
        print(f"{villager.name} has woken up")

def default_on_building_selected(building):
    """Default handler when a building is selected."""
    building_type = building.get('building_type', 'Building')
    print(f"Selected {building_type}")

def default_on_time_changed(hour, time_name):
    """Default handler when game time changes."""
    # Only log major time changes
    if time_name in ["Dawn", "Morning", "Noon", "Afternoon", "Evening", "Dusk", "Night"]:
        print(f"The time is now {hour:.1f} - {time_name}")

def default_periodic_status_update(current_time, delta_time):
    """Default periodic status update."""
    print(f"\n--- STATUS UPDATE @ {current_time/1000:.1f}s ---")
    print("--------------------------------\n")


def setup_default_callbacks(enable_debug=False):
    """
    Set up and register all default Interface callbacks.
    
    Args:
        enable_debug: If True, enables debug logging for all events
    """
    # Enable/disable debug mode
    set_debug(enable_debug)
    
    # Register game event callbacks
    register_game_started_callback(default_on_game_started)
    register_game_paused_callback(default_on_game_paused)
    register_village_generated_callback(default_on_village_generated)
    
    # Register villager callbacks
    register_villager_created_callback(default_on_villager_created)
    register_villager_moved_callback(default_on_villager_moved)
    register_villager_activity_changed_callback(default_on_villager_activity_changed)
    register_villager_sleep_state_changed_callback(default_on_villager_sleep_state_changed)
    
    # Register building callbacks
    register_building_selected_callback(default_on_building_selected)
    
    # Register time callbacks
    register_time_changed_callback(default_on_time_changed)
    
    # Register a periodic status update (every 10 seconds)
    register_time_callback(default_periodic_status_update, 10000)
