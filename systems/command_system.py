"""
Command System - Handles console commands
"""
from ui import Interface

class CommandSystem:
    """Handles console commands and command registration."""
    
    def __init__(self, game_state, console_manager):
        """Initialize the command system.
        
        Args:
            game_state: Reference to the main game state
            console_manager: Reference to the console manager
        """
        self.game_state = game_state
        self.console_manager = console_manager
    
    def register_commands(self):
        """Register all console commands."""
        # Add commands to console
        self.console_manager.commands.update({
            "daytime": self._cmd_daytime,
            "timespeed": self._cmd_timespeed,
            "houses": self._cmd_houses,
            "assign": self._cmd_assign_housing,
            "interiors": self._cmd_interiors,
            "wake": self._cmd_wake,      # New command to wake villagers
            "sleep": self._cmd_sleep,    # New command to make villagers sleep
            "fix": self._cmd_fix         # New command to fix various issues
        })
    
    def _cmd_houses(self, args, game_state):
        """List all houses and their residents."""
        self.console_manager.add_output("Houses and Residents:")
        
        # Find houses with residents
        houses_with_residents = {}
        for villager in self.game_state.villagers:
            if hasattr(villager, 'home') and villager.home and 'id' in villager.home:
                house_id = villager.home['id']
                if house_id not in houses_with_residents:
                    houses_with_residents[house_id] = []
                houses_with_residents[house_id].append(villager)
        
        # Display houses
        for house_id, residents in houses_with_residents.items():
            if house_id < 0 or house_id >= len(self.game_state.village_data['buildings']):
                continue
                
            building = self.game_state.village_data['buildings'][house_id]
            house_name = building.get('name', f"House #{house_id}")
            house_type = building.get('building_type', 'Unknown')
            
            self.console_manager.add_output(f"{house_name} ({house_type}):")
            for resident in residents:
                self.console_manager.add_output(f"  - {resident.name} ({resident.job})")
        
        return True
    
    def _cmd_assign_housing(self, args, game_state):
        """Generate or regenerate housing assignments."""
        if not args:
            self.console_manager.add_output("Usage: assign <new|reload>")
            self.console_manager.add_output("  new - Generate new housing assignments")
            self.console_manager.add_output("  reload - Reload existing assignments from file")
            return
        
        command = args[0].lower()
        
        if command == "new":
            self.console_manager.add_output("Generating new housing assignments...")
            self.game_state.housing_manager.assign_housing(regenerate=True)
            self.console_manager.add_output("Housing assignments created and saved to village_assignments.json")
            return True
        
        elif command == "reload":
            self.console_manager.add_output("Reloading housing assignments from file...")
            self.game_state.housing_manager.assign_housing(regenerate=False)
            self.console_manager.add_output("Housing assignments loaded successfully")
            return True
        
        else:
            self.console_manager.add_output(f"Unknown option: '{command}'")
            self.console_manager.add_output("Use 'assign new' or 'assign reload'")
            return False
    
    def _cmd_interiors(self, args, game_state):
        """Toggle building interiors visibility."""
        if not args:
            current_state = getattr(self.game_state.renderer, 'show_interiors', False)
            self.console_manager.add_output(f"Building interiors are currently {'visible' if current_state else 'hidden'}.")
            self.console_manager.add_output("Use 'interiors on' or 'interiors off' to change.")
            return
        
        command = args[0].lower()
        
        if command == "on":
            if hasattr(self.game_state.renderer, 'toggle_interiors'):
                if not getattr(self.game_state.renderer, 'show_interiors', False):
                    self.game_state.renderer.toggle_interiors()
                self.console_manager.add_output("Building interiors turned ON.")
                return True
            else:
                self.console_manager.add_output("Interior toggle functionality not available.")
                return False
        elif command == "off":
            if hasattr(self.game_state.renderer, 'toggle_interiors'):
                if getattr(self.game_state.renderer, 'show_interiors', True):
                    self.game_state.renderer.toggle_interiors()
                self.console_manager.add_output("Building interiors turned OFF.")
                return True
            else:
                self.console_manager.add_output("Interior toggle functionality not available.")
                return False
        elif command == "toggle":
            if hasattr(self.game_state.renderer, 'toggle_interiors'):
                new_state = self.game_state.renderer.toggle_interiors()
                self.console_manager.add_output(f"Building interiors {'shown' if new_state else 'hidden'}.")
                return True
            else:
                self.console_manager.add_output("Interior toggle functionality not available.")
                return False
        else:
            self.console_manager.add_output(f"Unknown option: '{command}'")
            self.console_manager.add_output("Use 'interiors on', 'interiors off', or 'interiors toggle'.")
            return False
    
    def _cmd_wake(self, args, game_state):
        """Force villagers to wake up with proper state override."""
        if len(args) > 0 and args[0].lower() == "all":
            # Wake up all villagers
            count = self.game_state.villager_manager.wake_villager(force_all=True)
            self.console_manager.add_output(f"Forced {count} villagers to wake up")
            return count
        else:
            # Try to find villager by name
            name_query = " ".join(args) if args else ""
            
            if not name_query:
                self.console_manager.add_output("Please specify a villager name or use 'wake all'")
                return False
                
            count = self.game_state.villager_manager.wake_villager(villager_name=name_query)
            if count > 0:
                self.console_manager.add_output(f"Villager has been woken up")
                return True
            else:
                self.console_manager.add_output(f"Could not find villager: '{name_query}' or villager was already awake")
                return False
    
    def _cmd_sleep(self, args, game_state):
        """Force villagers to sleep."""
        if len(args) > 0 and args[0].lower() == "all":
            # Put all villagers to sleep
            count = self.game_state.villager_manager.sleep_villager(force_all=True)
            self.console_manager.add_output(f"Forced {count} villagers to sleep")
            return count
        else:
            # Try to find villager by name
            name_query = " ".join(args) if args else ""
            
            if not name_query:
                self.console_manager.add_output("Please specify a villager name or use 'sleep all'")
                return False
                
            count = self.game_state.villager_manager.sleep_villager(villager_name=name_query)
            if count > 0:
                self.console_manager.add_output(f"Villager has been put to sleep")
                return True
            else:
                self.console_manager.add_output(f"Could not find villager: '{name_query}' or villager was already sleeping")
                return False
    
    def _cmd_fix(self, args, game_state):
        """Fix common issues with villagers or game state."""
        if not args:
            self.console_manager.add_output("Available fixes:")
            self.console_manager.add_output("  fix sleepers - Force all villagers to follow correct sleep schedule")
            self.console_manager.add_output("  fix homes - Reset villagers to their home positions")
            self.console_manager.add_output("  fix all - Apply all fixes")
            return None
            
        fix_type = args[0].lower()
        
        if fix_type == "sleepers":
            # Fix villagers that are sleeping or waking at wrong times
            fixed_count = self.game_state.villager_manager.fix_villager_sleep_states()
            self.console_manager.add_output(f"Fixed sleep states for {fixed_count} villagers")
            return fixed_count
            
        elif fix_type == "homes":
            # Reset villagers to their homes
            self.game_state.housing_manager.force_villagers_to_homes()
            self.console_manager.add_output("Reset villagers to their home positions")
            return True
            
        elif fix_type == "all":
            # Apply all fixes
            self._cmd_fix(["sleepers"], self.game_state)
            self._cmd_fix(["homes"], self.game_state)
            self.console_manager.add_output("Applied all fixes")
            return True
            
        else:
            self.console_manager.add_output(f"Unknown fix type: '{fix_type}'")
            self.console_manager.add_output("Use 'fix sleepers', 'fix homes', or 'fix all'")
            return False
    
    def _cmd_daytime(self, args, game_state):
        """Get or set the time of day."""
        if not hasattr(self.game_state, 'time_manager'):
            self.console_manager.add_output("Time of day system is not enabled.")
            return False
            
        time_manager = self.game_state.time_manager
        
        if not args:
            # Display current time
            current_time = time_manager.get_time_string()
            self.console_manager.add_output(f"Current time: {current_time}")
            self.console_manager.add_output("Use 'daytime <hour>' to set time (0-24).")
            self.console_manager.add_output("Use 'daytime <hour:minute>' for precise time.")
            self.console_manager.add_output("Examples: 'daytime 12' for noon, 'daytime 18:30' for 6:30 PM")
            return None
            
        # Set time to specified hour
        try:
            if ':' in args[0]:
                # Format HH:MM
                hour_str, minute_str = args[0].split(':')
                hour = float(hour_str)
                minute = float(minute_str)
                if minute >= 60:
                    self.console_manager.add_output("Minutes must be between 0 and 59.")
                    return False
                    
                new_time = hour + (minute / 60.0)
            else:
                # Just hour
                new_time = float(args[0])
                
            if 0 <= new_time <= 24:
                old_time = time_manager.current_hour
                time_manager.set_time(new_time)
                
                old_time_str = f"{int(old_time)}:{int((old_time % 1) * 60):02d}"
                new_time_str = f"{int(new_time)}:{int((new_time % 1) * 60):02d}"
                
                self.console_manager.add_output(f"Time changed from {old_time_str} to {new_time_str}.")
                self.console_manager.add_output(f"Current time: {time_manager.get_time_string()}")
                
                # Notify through Interface
                Interface.on_time_changed(new_time, time_manager.get_time_name())
                return True
            else:
                self.console_manager.add_output("Time must be between 0 and 24 hours.")
                return False
        except ValueError:
            self.console_manager.add_output("Invalid time format. Use 'daytime <hour>' or 'daytime <hour:minute>'.")
            return False
    
    def _cmd_timespeed(self, args, game_state):
        """Get or set the day length."""
        if not hasattr(self.game_state, 'time_manager'):
            self.console_manager.add_output("Time of day system is not enabled.")
            return False
            
        time_manager = self.game_state.time_manager
        
        if not args:
            # Display current day length
            day_length = time_manager.day_length_seconds
            self.console_manager.add_output(f"Current day length: {day_length} seconds.")
            self.console_manager.add_output(f"({day_length/60:.1f} minutes per day)")
            self.console_manager.add_output("Use 'timespeed <seconds>' to set day length.")
            return None
            
        # Set day length
        try:
            day_length = float(args[0])
            if day_length < 60:
                self.console_manager.add_output("Day length must be at least 60 seconds.")
                return False
                
            old_length = time_manager.day_length_seconds
            time_manager.day_length_seconds = day_length
            
            self.console_manager.add_output(f"Day length changed from {old_length} to {day_length} seconds.")
            self.console_manager.add_output(f"({day_length/60:.1f} minutes per day)")
            return True
        except ValueError:
            self.console_manager.add_output("Invalid day length. Please provide a number of seconds.")
            return False