"""
Interface module for Village Simulation.

This module provides a flexible system of hooks and callbacks that can be registered
to respond to various game events without modifying the core game code.
All events are printed to the console when they occur.

Usage:
    1. Register callback functions using register_* methods
    2. The game will automatically call these functions when events occur
    3. All events will be printed to the console
    4. Periodic updates will be called based on the game timer

Example:
    # Register a callback for villager movement
    def on_villager_moved(villager, old_position, new_position):
        print(f"{villager.name} moved from {old_position} to {new_position}")
    
    Interface.register_villager_moved_callback(on_villager_moved)
"""

import time
import inspect
from datetime import datetime

# Global callback registries
_time_callbacks = []           # Periodic time-based callbacks
_villager_callbacks = {}       # Callbacks for villager events
_building_callbacks = {}       # Callbacks for building events
_environment_callbacks = {}    # Callbacks for environment events
_game_event_callbacks = {}     # General game event callbacks
_ui_callbacks = {}             # UI event callbacks
_proximity_callbacks = {}      # Proximity-based event callbacks
_unusual_event_callbacks = {}  # Unusual event callbacks

# Frequency settings for time-based callbacks (in milliseconds)
DEFAULT_UPDATE_FREQUENCY = 1000  # 1 second
_last_update_time = 0

# Settings
_debug_mode = True  # Always enabled by default
_event_log_file = None  # Optional file logging
_log_to_console = True  # Whether to print to console

# Configure text colors for console output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

# Map event categories to colors
EVENT_COLORS = {
    'villager': Colors.GREEN,
    'building': Colors.YELLOW,
    'environment': Colors.BLUE,
    'game': Colors.MAGENTA,
    'ui': Colors.CYAN,
    'proximity': Colors.RED,
    'unusual': Colors.BG_RED + Colors.WHITE
}

def set_debug(mode=True):
    """Enable or disable debug logging for event dispatches."""
    global _debug_mode
    _debug_mode = mode
    if _debug_mode:
        print("Interface debug mode ENABLED")
    else:
        print("Interface debug mode DISABLED")

def enable_file_logging(filename="event_log.txt"):
    """Enable logging events to a file."""
    global _event_log_file
    _event_log_file = open(filename, "a")
    _event_log_file.write(f"\n--- Event Log Started at {datetime.now()} ---\n\n")
    print(f"Event logging to {filename} enabled")

def disable_file_logging():
    """Disable logging events to a file."""
    global _event_log_file
    if _event_log_file:
        _event_log_file.write(f"\n--- Event Log Ended at {datetime.now()} ---\n\n")
        _event_log_file.close()
        _event_log_file = None
        print("Event file logging disabled")

def set_console_logging(enabled=True):
    """Enable or disable logging to console."""
    global _log_to_console
    _log_to_console = enabled
    print(f"Console logging {'enabled' if enabled else 'disabled'}")

def _get_event_category(event_name):
    """Get the category of an event based on its name."""
    if event_name.startswith('villager_'):
        return 'villager'
    elif event_name.startswith('building_'):
        return 'building'
    elif event_name in ['time_changed', 'environment_changed', 'path_created', 'tree_created', 'bridge_created']:
        return 'environment'
    elif event_name.startswith('game_') or event_name == 'console_command' or event_name == 'village_generated':
        return 'game'
    elif event_name.startswith('mouse_') or event_name.startswith('villager_proximity'):
        return 'proximity'
    elif event_name.startswith('unusual_'):
        return 'unusual'
    else:
        return 'ui'

def _log_event(event_name, **kwargs):
    """Log event details if debug mode is enabled."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    category = _get_event_category(event_name)
    color = EVENT_COLORS.get(category, '')
    
    # Format the event arguments
    args_str = ", ".join(f"{k}={v}" for k, v in kwargs.items() if k != 'details')
    
    # Create the event message
    event_message = f"[{timestamp}] {color}{category.upper()}: {event_name}{Colors.RESET} - {args_str}"
    
    # Print special handling for events with detailed information
    if 'details' in kwargs and isinstance(kwargs['details'], dict):
        details = kwargs['details']
        event_message += "\n  Details:"
        for k, v in details.items():
            event_message += f"\n    {k}: {v}"
    
    # Log to console
    if _log_to_console:
        print(event_message)
    
    # Log to file if enabled
    if _event_log_file:
        # Strip ANSI color codes for file output
        clean_message = event_message
        for color_code in vars(Colors).values():
            if isinstance(color_code, str) and color_code.startswith('\033'):
                clean_message = clean_message.replace(color_code, '')
        
        _event_log_file.write(clean_message + "\n")
        _event_log_file.flush()

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
def register_screen_resized_callback(callback):
    """Register a callback for when the screen is resized.
    
    Args:
        callback: Function to call when the screen is resized
    """
    if not _check_callback_signature(callback, ['old_size', 'new_size']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (old_size, new_size)")
    
    _register_callback('screen_resized', callback)
    return callback

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

def register_villager_decision_callback(callback):
    """Register a callback for when a villager needs to decide its next action."""
    if not _check_callback_signature(callback, ['villager', 'current_state', 'possible_actions']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager, current_state, possible_actions)")
    
    _register_callback('villager_decision', callback)
    return callback

def register_villager_discussion_callback(callback):
    """Register a callback for when two or more villagers are in a discussion."""
    if not _check_callback_signature(callback, ['villagers', 'location', 'discussion_type']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villagers, location, discussion_type)")
    
    _register_callback('villager_discussion', callback)
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

def register_environment_changed_callback(callback):
    """Register a callback for when the environment changes (morning, noon, night, etc.)."""
    if not _check_callback_signature(callback, ['time_period', 'previous_period', 'game_time']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (time_period, previous_period, game_time)")
    
    _register_callback('environment_changed', callback)
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

# ----- NEW PROXIMITY CALLBACKS -----

def register_mouse_proximity_callback(callback):
    """Register a callback for when the mouse moves close to a character."""
    if not _check_callback_signature(callback, ['villager', 'mouse_position', 'distance']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager, mouse_position, distance)")
    
    _register_callback('mouse_proximity', callback, registry=_proximity_callbacks)
    return callback

def register_villager_proximity_callback(callback):
    """Register a callback for when villagers come in proximity to each other."""
    if not _check_callback_signature(callback, ['villager1', 'villager2', 'distance']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager1, villager2, distance)")
    
    _register_callback('villager_proximity', callback, registry=_proximity_callbacks)
    return callback

def register_building_proximity_callback(callback):
    """Register a callback for when a villager comes in proximity to a building."""
    if not _check_callback_signature(callback, ['villager', 'building', 'distance']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (villager, building, distance)")
    
    _register_callback('building_proximity', callback, registry=_proximity_callbacks)
    return callback

# ----- UNUSUAL EVENT CALLBACKS -----

def register_unusual_event_callback(callback):
    """Register a callback for when anything unusual happens."""
    if not _check_callback_signature(callback, ['event_type', 'details', 'severity']):
        print(f"Warning: Callback {callback.__name__} missing required parameters (event_type, details, severity)")
    
    _register_callback('unusual_event', callback, registry=_unusual_event_callbacks)
    return callback

# ----- HELPER METHODS FOR REGISTRATION AND DISPATCH -----

def _register_callback(event_name, callback, registry=None):
    """Register a callback for a specific event in the appropriate registry."""
    # Determine which registry to use based on event name or explicit registry parameter
    if registry is not None:
        # Use explicitly specified registry
        pass
    elif event_name.startswith('villager_'):
        registry = _villager_callbacks
    elif event_name.startswith('building_'):
        registry = _building_callbacks
    elif event_name in ['time_changed', 'environment_changed', 'path_created', 'tree_created', 'bridge_created']:
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
    # Always log the event regardless of debug mode
    _log_event(event_name, **kwargs)
    
    # Call registered callbacks
    if event_name in registry:
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

def dispatch_proximity_event(event_name, **kwargs):
    """Dispatch a proximity-related event."""
    _dispatch_event(event_name, _proximity_callbacks, **kwargs)

def dispatch_unusual_event(event_name, **kwargs):
    """Dispatch an unusual event."""
    _dispatch_event(event_name, _unusual_event_callbacks, **kwargs)

# ----- SPECIFIC EVENT DISPATCHERS -----
# These are convenience methods that dispatch specific events

# Villager events
def on_villager_moved(villager, old_position, new_position):
    """Notify when a villager moves."""
    #dispatch_villager_event('villager_moved', villager=villager, old_position=old_position, new_position=new_position)

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

def on_villager_decision(villager, current_state, possible_actions):
    """Notify when a villager needs to decide its next action.
    
    Args:
        villager: The villager object making a decision
        current_state: Dictionary containing current state information like:
                      - location: Current coordinates
                      - activity: Current activity name
                      - energy: Current energy level
                      - time: Current game time
        possible_actions: List of possible actions the villager could take
    """
    dispatch_villager_event('villager_decision', villager=villager, 
                           current_state=current_state, possible_actions=possible_actions)

def on_villager_discussion(villagers, location, discussion_type):
    """Notify when two or more villagers are in a discussion.
    
    Args:
        villagers: List of villager objects in the discussion
        location: Coordinates where the discussion is taking place
        discussion_type: Type of discussion (e.g., "casual", "work", "gossip")
    """
    dispatch_villager_event('villager_discussion', villagers=villagers, 
                           location=location, discussion_type=discussion_type)

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

def on_environment_changed(time_period, previous_period, game_time):
    """Notify when the environment changes (morning, noon, night, etc.)
    
    Args:
        time_period: Current time period name (e.g., "morning", "noon", "night")
        previous_period: Previous time period name
        game_time: Current game time as a float (hours)
    """
    dispatch_environment_event('environment_changed', time_period=time_period, 
                             previous_period=previous_period, game_time=game_time)

def on_path_created(path_position, path_type):
    """Notify when a new path is created."""
    dispatch_environment_event('path_created', path_position=path_position, path_type=path_type)

def on_tree_created(tree_position, tree_variant):
    """Notify when a new tree is created."""
    dispatch_environment_event('tree_created', tree_position=tree_position, tree_variant=tree_variant)

def on_bridge_created(bridge_position, bridge_type):
    """Notify when a new bridge is created."""
    dispatch_environment_event('bridge_created', bridge_position=bridge_position, bridge_type=bridge_type)

def on_screen_resized(old_size, new_size):
    """Notify when the screen is resized.
    
    Args:
        old_size: Previous screen size (width, height)
        new_size: New screen size (width, height)
    """
    dispatch_ui_event('screen_resized', old_size=old_size, new_size=new_size)

# Game events
def on_game_started(game_state):
    """Notify when the game starts."""
    dispatch_game_event('game_started', game_state=game_state)

def on_game_paused(is_paused):
    """Notify when the game is paused/unpaused."""
    dispatch_game_event('game_paused', is_paused=is_paused)

def on_village_generated(village_data):
    """Notify when the village is generated."""
    #dispatch_game_event('village_generated', village_data=village_data)

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

# Proximity events
def on_mouse_proximity(villager, mouse_position, distance):
    """Notify when the mouse moves close to a character.
    
    Args:
        villager: The villager object that the mouse is near
        mouse_position: Mouse position in world coordinates
        distance: Distance between mouse and villager center
    """
    dispatch_proximity_event('mouse_proximity', villager=villager, 
                            mouse_position=mouse_position, distance=distance)

def on_villager_proximity(villager1, villager2, distance):
    """Notify when villagers come in proximity to each other.
    
    Args:
        villager1: First villager object
        villager2: Second villager object
        distance: Distance between the villagers
    """
    dispatch_proximity_event('villager_proximity', villager1=villager1, 
                            villager2=villager2, distance=distance)

def on_building_proximity(villager, building, distance):
    """Notify when a villager comes in proximity to a building.
    
    Args:
        villager: Villager object
        building: Building object
        distance: Distance between villager and building
    """
    dispatch_proximity_event('building_proximity', villager=villager, 
                            building=building, distance=distance)

# Unusual events
def on_unusual_event(event_type, details, severity):
    """Notify when anything unusual happens.
    
    Args:
        event_type: Type of unusual event (e.g., "sleep_outside", "missed_work")
        details: Dictionary with event details
        severity: Severity level (1-5, where 5 is most severe)
    """
    dispatch_unusual_event('unusual_event', event_type=event_type, 
                          details=details, severity=severity)

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

def default_on_villager_decision(villager, current_state, possible_actions):
    """Default handler when a villager needs to decide its next action."""
    print(f"{villager.name} is deciding next action: {possible_actions}")
    # Here you could implement custom decision logic
    
def default_on_villager_discussion(villagers, location, discussion_type):
    """Default handler when villagers are in a discussion."""
    villager_names = [v.name for v in villagers]
    print(f"Discussion between {', '.join(villager_names)} ({discussion_type}) at {location}")

def default_on_environment_changed(time_period, previous_period, game_time):
    """Default handler when the environment changes."""
    print(f"Environment changed from {previous_period} to {time_period} at {game_time:.2f} hours")

def default_on_mouse_proximity(villager, mouse_position, distance):
    """Default handler when mouse is near a villager."""
    if distance < 50:  # Only show tooltip for very close proximity
        print(f"Mouse hovering near {villager.name} (distance: {distance:.1f})")

def default_on_unusual_event(event_type, details, severity):
    """Default handler for unusual events."""
    print(f"UNUSUAL EVENT: {event_type} (Severity: {severity})")
    for key, value in details.items():
        print(f"  {key}: {value}")

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

def setup_default_callbacks(enable_debug=True):
    """
    Set up and register all default Interface callbacks.
    
    Args:
        enable_debug: If True, enables debug logging for all events
    """
    # Enable debug mode by default for this enhanced version
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
    register_villager_decision_callback(default_on_villager_decision)
    register_villager_discussion_callback(default_on_villager_discussion)
    
    # Register building callbacks
    register_building_selected_callback(default_on_building_selected)
    
    # Register time and environment callbacks
    register_time_changed_callback(default_on_time_changed)
    register_environment_changed_callback(default_on_environment_changed)
    
    # Register proximity callbacks
    register_mouse_proximity_callback(default_on_mouse_proximity)
    
    # Register unusual event callbacks
    register_unusual_event_callback(default_on_unusual_event)
    
    # Register a periodic status update (every 10 seconds)
    register_time_callback(default_periodic_status_update, 10000)
    
    print("Enhanced Interface with event logging initialized!")

# ----- INTEGRATION HELPERS -----
# Helper functions to easily integrate Interface with specific game components

def setup_mouse_proximity_detection(game_state, threshold=50):
    """
    Set up mouse proximity detection for all villagers.
    
    Args:
        game_state: Game state object containing villagers and mouse position
        threshold: Distance threshold for proximity detection (in pixels)
    
    Usage:
        # Call this once during game initialization
        Interface.setup_mouse_proximity_detection(game_state)
        
        # Make sure to update mouse_position in game_state during your event handling
        game_state.mouse_position = pygame.mouse.get_pos()
    """
    def check_mouse_proximity(current_time, delta_time):
        if not hasattr(game_state, 'mouse_position') or not hasattr(game_state, 'villagers'):
            return
            
        mouse_x, mouse_y = game_state.mouse_position
        # Add camera offset to get world coordinates
        if hasattr(game_state, 'camera_x') and hasattr(game_state, 'camera_y'):
            mouse_world_x = mouse_x + game_state.camera_x
            mouse_world_y = mouse_y + game_state.camera_y
        else:
            mouse_world_x, mouse_world_y = mouse_x, mouse_y
            
        for villager in game_state.villagers:
            villager_x, villager_y = villager.position.x, villager.position.y
            distance = ((villager_x - mouse_world_x)**2 + (villager_y - mouse_world_y)**2)**0.5
            
            if distance <= threshold:
                on_mouse_proximity(villager, (mouse_world_x, mouse_world_y), distance)
    
    # Register a high-frequency callback to check mouse proximity
    register_time_callback(check_mouse_proximity, 100)  # Check every 100ms

def setup_villager_discussion_detection(game_state, distance_threshold=50, talk_required=True):
    """
    Set up detection for discussions between two or more villagers.
    
    Args:
        game_state: Game state object containing villagers
        distance_threshold: Distance threshold for discussions (in pixels)
        talk_required: If True, both villagers must be in a 'talking' state
    
    Usage:
        # Call this once during game initialization
        Interface.setup_villager_discussion_detection(game_state)
    """
    def check_villager_discussions(current_time, delta_time):
        if not hasattr(game_state, 'villagers'):
            return
            
        # Track groups of villagers in discussions
        discussion_groups = []
        processed_villagers = set()
        
        for v1 in game_state.villagers:
            if v1 in processed_villagers:
                continue
                
            # Skip villagers that aren't talking if talk_required is True
            if talk_required and hasattr(v1, 'is_talking') and not v1.is_talking:
                continue
                
            # Find all villagers near this one
            group = [v1]
            for v2 in game_state.villagers:
                if v1 == v2 or v2 in processed_villagers:
                    continue
                    
                # Skip villagers that aren't talking if talk_required is True
                if talk_required and hasattr(v2, 'is_talking') and not v2.is_talking:
                    continue
                    
                # Calculate distance
                v1_pos = (v1.position.x, v1.position.y)
                v2_pos = (v2.position.x, v2.position.y)
                distance = ((v1_pos[0] - v2_pos[0])**2 + (v1_pos[1] - v2_pos[1])**2)**0.5
                
                # If in range, add to group
                if distance <= distance_threshold:
                    group.append(v2)
            
            # If we found a group of 2+ villagers
            if len(group) >= 2:
                discussion_groups.append(group)
                processed_villagers.update(group)
        
        # Notify about each discussion group
        for group in discussion_groups:
            # Calculate average position
            avg_x = sum(v.position.x for v in group) / len(group)
            avg_y = sum(v.position.y for v in group) / len(group)
            location = (avg_x, avg_y)
            
            # Determine discussion type based on jobs or activities
            if all(hasattr(v, 'job') for v in group):
                if len(set(v.job for v in group)) == 1:
                    discussion_type = "work"  # Same job
                else:
                    discussion_type = "casual"  # Different jobs
            else:
                discussion_type = "casual"
                
            on_villager_discussion(group, location, discussion_type)
    
    # Register a low-frequency callback to check for discussions
    register_time_callback(check_villager_discussions, 2000)  # Check every 2 seconds

def setup_environment_change_detection(game_state):
    """
    Set up detection for environment changes (time period transitions).
    
    Args:
        game_state: Game state object containing time_manager
    
    Usage:
        # Call this once during game initialization
        Interface.setup_environment_change_detection(game_state)
    """
    # Keep track of the previous time period
    previous_period = None
    
    def check_environment_changes(current_time, delta_time):
        nonlocal previous_period
        
        if not hasattr(game_state, 'time_manager'):
            return
            
        # Get current time period
        current_hour = game_state.time_manager.current_hour
        current_period = game_state.time_manager.get_time_name()
        
        # If this is the first check or period has changed
        if previous_period is None or current_period != previous_period:
            if previous_period is not None:  # Skip the initial setup
                on_environment_changed(current_period, previous_period, current_hour)
            previous_period = current_period
    
    # Register a medium-frequency callback to check for environment changes
    register_time_callback(check_environment_changes, 1000)  # Check every second

def setup_unusual_event_detection(game_state):
    """
    Set up detection for unusual events in the village.
    
    Args:
        game_state: Game state object
    
    Usage:
        # Call this once during game initialization
        Interface.setup_unusual_event_detection(game_state)
    """
    def check_for_unusual_events(current_time, delta_time):
        if not hasattr(game_state, 'villagers'):
            return
            
        # Example: Check for villagers sleeping outside
        for villager in game_state.villagers:
            if hasattr(villager, 'is_sleeping') and villager.is_sleeping:
                # Check if villager is far from their bed or home
                if hasattr(villager, 'home') and villager.home and 'position' in villager.home:
                    home_pos = villager.home['position']
                    v_pos = (villager.position.x, villager.position.y)
                    distance_from_home = ((v_pos[0] - home_pos[0])**2 + (v_pos[1] - home_pos[1])**2)**0.5
                    
                    if distance_from_home > 100:  # Arbitrary threshold
                        # Report unusual sleeping location
                        details = {
                            'villager': villager.name,
                            'sleep_position': v_pos,
                            'home_position': home_pos,
                            'distance': distance_from_home
                        }
                        on_unusual_event("sleeping_outside", details, severity=2)
        
        # Example: Check for missed work
        if hasattr(game_state, 'time_manager'):
            current_hour = game_state.time_manager.current_hour
            
            # Work hours check (9 AM to 5 PM)
            if 9 <= current_hour < 17:
                for villager in game_state.villagers:
                    if (hasattr(villager, 'workplace') and villager.workplace and
                        hasattr(villager, 'current_activity')):
                        
                        workplace_pos = villager.workplace.get('position')
                        if workplace_pos:
                            v_pos = (villager.position.x, villager.position.y)
                            distance_from_work = ((v_pos[0] - workplace_pos[0])**2 + 
                                                 (v_pos[1] - workplace_pos[1])**2)**0.5
                            
                            # If far from work during work hours and not engaged in work activity
                            if (distance_from_work > 200 and  # Arbitrary threshold
                                not "work" in villager.current_activity.lower()):
                                
                                details = {
                                    'villager': villager.name,
                                    'job': villager.job,
                                    'current_activity': villager.current_activity,
                                    'current_position': v_pos,
                                    'workplace_position': workplace_pos,
                                    'time': current_hour
                                }
                                on_unusual_event("missed_work", details, severity=3)
    
    # Register a low-frequency callback to check for unusual events
    register_time_callback(check_for_unusual_events, 5000)  # Check every 5 seconds