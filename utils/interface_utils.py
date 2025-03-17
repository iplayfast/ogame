"""
Interface integration utilities for village simulation.

This module provides helper functions to integrate the Interface module
with various game systems, making it easier to register callbacks and
notify about game events.
"""

import Interface

def setup_default_interface(game_state, enable_debug=False):
    """
    Initialize Interface with default callbacks for the game.
    
    Args:
        game_state: The main game state object
        enable_debug: Whether to enable debug logging for Interface events
    """
    # Register initial time update
    current_time = game_state.clock.get_ticks()
    Interface.update(current_time, 0)
    
    # Notify that game started
    Interface.on_game_started(game_state)
    
    # Set up default callbacks
    Interface.setup_default_callbacks(enable_debug=enable_debug)
    
    # Set up additional integrations if available
    if hasattr(Interface, 'setup_mouse_proximity_detection'):
        Interface.setup_mouse_proximity_detection(game_state)
        
    if hasattr(Interface, 'setup_villager_discussion_detection'):
        Interface.setup_villager_discussion_detection(game_state)
        
    if hasattr(Interface, 'setup_environment_change_detection'):
        Interface.setup_environment_change_detection(game_state)
        
    if hasattr(Interface, 'setup_unusual_event_detection'):
        Interface.setup_unusual_event_detection(game_state)

def notify_time_changed(time_manager, old_hour=None, old_time_name=None):
    """
    Notify Interface about time changes when they are significant.
    
    Args:
        time_manager: The time manager instance
        old_hour: Previous hour (if None, will skip notification)
        old_time_name: Previous time name (if None, will skip notification)
    """
    if old_hour is None or old_time_name is None:
        return
    
    new_hour = time_manager.current_hour
    new_time_name = time_manager.get_time_name()
    
    # Notify of time change if the hour changed by at least 0.25 or the time period changed
    if abs(new_hour - old_hour) >= 0.25 or new_time_name != old_time_name:
        Interface.on_time_changed(new_hour, new_time_name)
        
        # Also notify of environment change if time period changed
        if new_time_name != old_time_name:
            Interface.on_environment_changed(new_time_name, old_time_name, new_hour)

def notify_villager_state_changes(villager, old_position, old_activity, old_sleep_state):
    """
    Check for villager state changes and notify Interface when needed.
    
    Args:
        villager: The villager object
        old_position: Previous position tuple (x, y)
        old_activity: Previous activity string
        old_sleep_state: Previous sleep state boolean
    """
    # Check position change
    new_position = (villager.position.x, villager.position.y)
    if old_position != new_position:
        # Notify significant movements (more than 1 pixel)
        if ((new_position[0] - old_position[0])**2 + 
            (new_position[1] - old_position[1])**2) > 1:
            Interface.on_villager_moved(villager, old_position, new_position)
    
    # Check activity change
    new_activity = villager.current_activity if hasattr(villager, 'current_activity') else None
    if old_activity != new_activity and old_activity is not None and new_activity is not None:
        Interface.on_villager_activity_changed(villager, old_activity, new_activity)
    
    # Check sleep state change
    new_sleep_state = villager.is_sleeping if hasattr(villager, 'is_sleeping') else False
    if old_sleep_state != new_sleep_state:
        Interface.on_villager_sleep_state_changed(villager, new_sleep_state)

def notify_building_selected(building, old_building=None):
    """
    Notify Interface when a building is selected.
    
    Args:
        building: The newly selected building or None
        old_building: The previously selected building or None
    """
    if building is not None and building != old_building:
        Interface.on_building_selected(building)

def notify_villager_selected(villager, is_selected, old_villager=None):
    """
    Notify Interface when a villager is selected or deselected.
    
    Args:
        villager: The villager being selected/deselected
        is_selected: Whether the villager is now selected
        old_villager: The previously selected villager (if any)
    """
    if villager is not None:
        Interface.on_villager_selected(villager, is_selected)
        
    # Also notify about deselection of previous villager
    if old_villager is not None and old_villager != villager:
        Interface.on_villager_selected(old_villager, False)

def notify_villager_interaction(villager1, villager2, interaction_type="conversation"):
    """
    Notify Interface when villagers interact with each other.
    
    Args:
        villager1: First villager in the interaction
        villager2: Second villager in the interaction
        interaction_type: Type of interaction (default: "conversation")
    """
    Interface.on_villager_interaction(villager1, villager2, interaction_type)

def notify_camera_moved(old_position, new_position):
    """
    Notify Interface when the camera position changes.
    
    Args:
        old_position: Previous camera position tuple (x, y)
        new_position: New camera position tuple (x, y)
    """
    if old_position != new_position:
        Interface.on_camera_moved(old_position, new_position)

def notify_game_paused(is_paused):
    """
    Notify Interface when the game is paused or unpaused.
    
    Args:
        is_paused: Whether the game is now paused
    """
    Interface.on_game_paused(is_paused)

def notify_debug_toggled(is_enabled):
    """
    Notify Interface when debug display is toggled.
    
    Args:
        is_enabled: Whether debug display is now enabled
    """
    Interface.on_debug_toggled(is_enabled)

def notify_ui_panel_toggled(panel_name, is_visible):
    """
    Notify Interface when a UI panel is shown or hidden.
    
    Args:
        panel_name: Name of the UI panel (e.g., "building_interiors")
        is_visible: Whether the panel is now visible
    """
    Interface.on_ui_panel_toggled(panel_name, is_visible)

def register_unusual_event(event_type, details, severity=3):
    """
    Register an unusual event with Interface.
    
    Args:
        event_type: Type of unusual event (e.g., "missed_work", "sleeping_outside")
        details: Dictionary with details about the event
        severity: Severity level (1-5, where 5 is most severe)
    """
    Interface.on_unusual_event(event_type, details, severity)
