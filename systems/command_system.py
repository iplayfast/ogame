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
        self.game_state = game_state #
        self.console_manager = console_manager #

    # --- Start of Added/Modified Methods ---

    def register_additional_command(self, name, func):
        """Register an additional command after initialization."""
        if hasattr(self, 'console_manager') and hasattr(self.console_manager, 'commands'):
            self.console_manager.commands[name] = func
            print(f"Registered additional command: {name}")
        else:
            print(f"Error: Cannot register additional command '{name}', console manager or commands dict missing.")


    def register_commands(self):
        """Register all console commands."""
        # (Keep existing commands like "daytime", "houses", etc.)
        self.console_manager.commands.update({
            "daytime": self._cmd_daytime, #
            "timespeed": self._cmd_timespeed, #
            "houses": self._cmd_houses, #
            "assign": self._cmd_assign_housing, #
            "interiors": self._cmd_interiors, #
            "wake": self._cmd_wake, #
            "sleep": self._cmd_sleep, #
            "fix": self._cmd_fix, #
            # Add the new save/load commands
            "save": self._cmd_save, #
            "load": self._cmd_load, #
            # Add existing commands back if they were moved inside ConsoleManager previously
             "help": self._cmd_help, # Use self._cmd_help from this class
             "clear": self.console_manager._cmd_clear, #
             "list": self.console_manager._cmd_list, #
             "info": self.console_manager._cmd_info, #
             "teleport": self.console_manager._cmd_teleport, #
             "spawn": self.console_manager._cmd_spawn, #
             "stats": self.console_manager._cmd_stats, #
             "time": self.console_manager._cmd_time, # Or use the enhanced one if you implemented it
             # REMOVED "config": config_command
        })
        # Make sure help and clear are handled if they were moved inside ConsoleManager previously
        # (This logic might need adjustment depending on your exact ConsoleManager implementation)
        if hasattr(self.console_manager, '_cmd_clear') and "clear" not in self.console_manager.commands: #
             self.console_manager.commands["clear"] = self.console_manager._cmd_clear #

    # --- End of Added/Modified Methods ---


    def _cmd_help(self, args, game_state):
        """Display help information."""
        # Using self.add_output which should now exist if ConsoleManager was initialized correctly
        add_output_func = getattr(self.console_manager, 'add_output', print)

        if not args:
            add_output_func("Available commands:") #
            # List all commands registered, including the new ones
            for cmd in sorted(self.console_manager.commands.keys()): #
                 # Simple description (can be expanded later)
                 if cmd == "save": #
                     add_output_func(f"  {cmd} [filename] - Save the current game state.") #
                 elif cmd == "load": #
                     add_output_func(f"  {cmd} [filename] - Load game state from a file.") #
                 elif cmd == "help": #
                     add_output_func(f"  {cmd} [command] - Display help information.") #
                 elif cmd == "clear": #
                      add_output_func(f"  {cmd} - Clear the console output.") #
                 elif cmd == "list": #
                      add_output_func(f"  {cmd} [villagers|buildings] - List entities.") #
                 elif cmd == "info": #
                      add_output_func(f"  {cmd} <name|id> - Display info about an entity.") #
                 elif cmd == "teleport": #
                      add_output_func(f"  {cmd} <name|id> <x> <y> - Teleport an entity.") #
                 elif cmd == "spawn": #
                      add_output_func(f"  {cmd} <type> [x] [y] - Spawn an entity.") #
                 elif cmd == "stats": #
                      add_output_func(f"  {cmd} - Show game statistics.") #
                 elif cmd == "time": #
                      add_output_func(f"  {cmd} [speed] - Get or set game time speed.") #
                 elif cmd == "daytime": #
                      add_output_func(f"  {cmd} <hour[:minute]> - View or set time of day.") #
                 elif cmd == "timespeed": #
                      add_output_func(f"  {cmd} <seconds> - Set day length in seconds.") #
                 elif cmd == "houses": #
                      add_output_func(f"  {cmd} - List houses and residents.") #
                 elif cmd == "assign": #
                      add_output_func(f"  {cmd} <new|reload> - Manage housing assignments.") #
                 elif cmd == "interiors": #
                      add_output_func(f"  {cmd} <on|off|toggle> - Control interior visibility.") #
                 elif cmd == "wake": #
                      add_output_func(f"  {cmd} <name|all> - Wake up villager(s).") #
                 elif cmd == "sleep": #
                      add_output_func(f"  {cmd} <name|all> - Force villager(s) to sleep.") #
                 elif cmd == "fix": #
                      add_output_func(f"  {cmd} <sleepers|homes|all> - Fix game issues.") #
                 elif cmd == "config": #
                      add_output_func(f"  {cmd} [section key value] - View or modify config.") #
                 else: #
                      # Fallback for any other commands
                      add_output_func(f"  {cmd} - (No description available)") #

            add_output_func("") #
            add_output_func("Type 'help <command>' for more details.") #
        else: #
            # --- Keep the detailed help section mostly as is ---
            # You might want to add detailed descriptions for save/load here too
            command = args[0].lower() #
            if command == "save": #
                add_output_func("save [filename] - Save the current game state.") #
                add_output_func("  Saves the game to the specified file (e.g., 'mysave.json').") #
                add_output_func("  If no filename is given, defaults to 'savegame.json'.") #
            elif command == "load": #
                add_output_func("load [filename] - Load game state from a file.") #
                add_output_func("  Loads the game from the specified file (e.g., 'mysave.json').") #
                add_output_func("  If no filename is given, defaults to 'savegame.json'.") #
                add_output_func("  WARNING: Loading will overwrite the current game state.") #
            # (Include the detailed help for other existing commands as before)
            elif command == "help": #
                add_output_func("help [command] - Display help information") #
                add_output_func("  If a command is specified, shows detailed help for that command.") #
            elif command == "clear": #
                add_output_func("clear - Clear the console output") #
                add_output_func("  Removes all previous output from the console.") #
            # ... (add elif for other commands as in the original _cmd_help) ...
            # Example for 'houses':
            elif command == "houses":
                add_output_func("houses - List all houses and their residents.")
            # Example for 'assign':
            elif command == "assign":
                add_output_func("assign <new|reload> - Manage housing assignments.")
                add_output_func("  new: Generates new assignments and saves them.")
                add_output_func("  reload: Loads assignments from village_assignments.json.")
            # Add detailed help for wake, sleep, fix, interiors etc. here
            else: #
                add_output_func(f"No detailed help available for '{command}'.") #

    def _cmd_save(self, args, game_state):
        """Save the current game state."""
        filename = args[0] if args else "savegame.json" #
        if not filename.lower().endswith(".json"): #
            filename += ".json" #

        if hasattr(game_state, 'save_game'): #
            game_state.save_game(filename) #
            # Console output is handled within save_game
            return True #
        else: #
             self.console_manager.add_output("Error: Save function not found in game state.") #
             return False #

    def _cmd_load(self, args, game_state):
        """Load a game state from a file."""
        filename = args[0] if args else "savegame.json" #
        if not filename.lower().endswith(".json"): #
            filename += ".json" #

        if hasattr(game_state, 'load_game'): #
             # Pausing during load might prevent visual glitches/updates
             was_paused = game_state.paused #
             game_state.paused = True #
             success = game_state.load_game(filename) #
             game_state.paused = was_paused if not success else False # Unpause on success #
             # Console output is handled within load_game
             return success #
        else: #
            self.console_manager.add_output("Error: Load function not found in game state.") #
            return False #

    # --- Keep existing command methods (_cmd_houses, _cmd_assign_housing, etc.) ---
    # They should already use self.console_manager.add_output

    def _cmd_houses(self, args, game_state): #
        """List all houses and their residents."""
        self.console_manager.add_output("Houses and Residents:") #

        # Find houses with residents
        houses_with_residents = {} #
        for villager in self.game_state.villagers: #
            if hasattr(villager, 'home') and villager.home and 'id' in villager.home: #
                house_id = villager.home['id'] #
                if house_id not in houses_with_residents: #
                    houses_with_residents[house_id] = [] #
                houses_with_residents[house_id].append(villager) #

        # Display houses
        for house_id, residents in houses_with_residents.items(): #
            if house_id < 0 or house_id >= len(self.game_state.village_data['buildings']): #
                continue #

            building = self.game_state.village_data['buildings'][house_id] #
            house_name = building.get('name', f"House #{house_id}") #
            house_type = building.get('building_type', 'Unknown') #

            self.console_manager.add_output(f"{house_name} ({house_type}):") #
            for resident in residents: #
                self.console_manager.add_output(f"  - {resident.name} ({resident.job})") #

        return True #

    def _cmd_assign_housing(self, args, game_state): #
        """Generate or regenerate housing assignments."""
        if not args: #
            self.console_manager.add_output("Usage: assign <new|reload>") #
            self.console_manager.add_output("  new - Generate new housing assignments") #
            self.console_manager.add_output("  reload - Reload existing assignments from file") #
            return # False? Or None? Let's return False for consistency

        command = args[0].lower() #

        if command == "new": #
            self.console_manager.add_output("Generating new housing assignments...") #
            self.game_state.housing_manager.assign_housing(regenerate=True) #
            self.console_manager.add_output("Housing assignments created and saved to village_assignments.json") #
            return True #

        elif command == "reload": #
            self.console_manager.add_output("Reloading housing assignments from file...") #
            self.game_state.housing_manager.assign_housing(regenerate=False) #
            self.console_manager.add_output("Housing assignments loaded successfully") #
            return True #

        else: #
            self.console_manager.add_output(f"Unknown option: '{command}'") #
            self.console_manager.add_output("Use 'assign new' or 'assign reload'") #
            return False #

    def _cmd_interiors(self, args, game_state): #
        """Toggle building interiors visibility."""
        if not args: #
            current_state = getattr(self.game_state.renderer, 'show_interiors', False) #
            self.console_manager.add_output(f"Building interiors are currently {'visible' if current_state else 'hidden'}.") #
            self.console_manager.add_output("Use 'interiors on' or 'interiors off' to change.") #
            return # False? Let's return False for consistency

        command = args[0].lower() #

        if command == "on": #
            if hasattr(self.game_state.renderer, 'toggle_interiors'): #
                # Call toggle only if currently off to set it to on
                if not getattr(self.game_state.renderer, 'show_interiors', False): #
                    self.game_state.renderer.toggle_interiors() #
                self.console_manager.add_output("Building interiors turned ON.") #
                return True #
            else: #
                 self.console_manager.add_output("Interior toggle functionality not available.") #
                 return False #
        elif command == "off": #
            if hasattr(self.game_state.renderer, 'toggle_interiors'): #
                # Call toggle only if currently on to set it to off
                if getattr(self.game_state.renderer, 'show_interiors', False): # Check if True before toggling
                    self.game_state.renderer.toggle_interiors() #
                self.console_manager.add_output("Building interiors turned OFF.") #
                return True #
            else: #
                 self.console_manager.add_output("Interior toggle functionality not available.") #
                 return False #
        elif command == "toggle": #
            if hasattr(self.game_state.renderer, 'toggle_interiors'): #
                new_state = self.game_state.renderer.toggle_interiors() #
                self.console_manager.add_output(f"Building interiors {'shown' if new_state else 'hidden'}.") #
                return True #
            else: #
                self.console_manager.add_output("Interior toggle functionality not available.") #
                return False #
        else: #
            self.console_manager.add_output(f"Unknown option: '{command}'") #
            self.console_manager.add_output("Use 'interiors on', 'interiors off', or 'interiors toggle'.") #
            return False #

    def _cmd_wake(self, args, game_state): #
        """Force villagers to wake up with proper state override."""
        if len(args) > 0 and args[0].lower() == "all": #
            # Wake up all villagers
            count = self.game_state.villager_manager.wake_villager(force_all=True) #
            self.console_manager.add_output(f"Forced {count} villagers to wake up") #
            return count > 0 # Return True if any were woken
        else: #
            # Try to find villager by name
            name_query = " ".join(args) if args else "" #

            if not name_query: #
                self.console_manager.add_output("Please specify a villager name or use 'wake all'") #
                return False #

            count = self.game_state.villager_manager.wake_villager(villager_name=name_query) #
            if count > 0: #
                self.console_manager.add_output(f"Villager has been woken up") #
                return True #
            else: #
                self.console_manager.add_output(f"Could not find villager: '{name_query}' or villager was already awake") #
                return False #

    def _cmd_sleep(self, args, game_state): #
        """Force villagers to sleep."""
        if len(args) > 0 and args[0].lower() == "all": #
            # Put all villagers to sleep
            count = self.game_state.villager_manager.sleep_villager(force_all=True) #
            self.console_manager.add_output(f"Forced {count} villagers to sleep") #
            return count > 0 # Return True if any were put to sleep
        else: #
            # Try to find villager by name
            name_query = " ".join(args) if args else "" #

            if not name_query: #
                self.console_manager.add_output("Please specify a villager name or use 'sleep all'") #
                return False #

            count = self.game_state.villager_manager.sleep_villager(villager_name=name_query) #
            if count > 0: #
                self.console_manager.add_output(f"Villager has been put to sleep") #
                return True #
            else: #
                self.console_manager.add_output(f"Could not find villager: '{name_query}' or villager was already sleeping") #
                return False #

    def _cmd_fix(self, args, game_state): #
        """Fix common issues with villagers or game state."""
        if not args: #
            self.console_manager.add_output("Available fixes:") #
            self.console_manager.add_output("  fix sleepers - Force all villagers to follow correct sleep schedule") #
            self.console_manager.add_output("  fix homes - Reset villagers to their home positions") #
            self.console_manager.add_output("  fix all - Apply all fixes") #
            return # False? Let's return False

        fix_type = args[0].lower() #

        if fix_type == "sleepers": #
            # Fix villagers that are sleeping or waking at wrong times
            fixed_count = self.game_state.villager_manager.fix_villager_sleep_states() #
            self.console_manager.add_output(f"Fixed sleep states for {fixed_count} villagers") #
            return fixed_count > 0 # Return True if any were fixed

        elif fix_type == "homes": #
            # Reset villagers to their homes
            self.game_state.housing_manager.force_villagers_to_homes() #
            self.console_manager.add_output("Reset villagers to their home positions") #
            return True #

        elif fix_type == "all": #
            # Apply all fixes
            sleep_fixed = self._cmd_fix(["sleepers"], self.game_state) #
            home_fixed = self._cmd_fix(["homes"], self.game_state) #
            self.console_manager.add_output("Applied all fixes") #
            return sleep_fixed or home_fixed # Return True if any fix did something

        else: #
            self.console_manager.add_output(f"Unknown fix type: '{fix_type}'") #
            self.console_manager.add_output("Use 'fix sleepers', 'fix homes', or 'fix all'") #
            return False #

    def _cmd_daytime(self, args, game_state): #
        """Get or set the time of day."""
        if not hasattr(self.game_state, 'time_manager'): #
            self.console_manager.add_output("Time of day system is not enabled.") #
            return False #

        time_manager = self.game_state.time_manager #

        if not args: #
            # Display current time
            current_time = time_manager.get_time_string() #
            self.console_manager.add_output(f"Current time: {current_time}") #
            self.console_manager.add_output("Use 'daytime <hour>' to set time (0-24).") #
            self.console_manager.add_output("Use 'daytime <hour:minute>' for precise time.") #
            self.console_manager.add_output("Examples: 'daytime 12' for noon, 'daytime 18:30' for 6:30 PM") #
            return # False? Let's return False

        # Set time to specified hour
        try: #
            if ':' in args[0]: #
                # Format HH:MM
                hour_str, minute_str = args[0].split(':') #
                hour = float(hour_str) #
                minute = float(minute_str) #
                if minute >= 60: #
                    self.console_manager.add_output("Minutes must be between 0 and 59.") #
                    return False #

                new_time = hour + (minute / 60.0) #
            else: #
                # Just hour
                new_time = float(args[0]) #

            if 0 <= new_time <= 24: #
                old_time = time_manager.current_hour #
                time_manager.set_time(new_time) #

                old_time_str = f"{int(old_time)}:{int((old_time % 1) * 60):02d}" #
                new_time_str = f"{int(new_time)}:{int((new_time % 1) * 60):02d}" #

                self.console_manager.add_output(f"Time changed from {old_time_str} to {new_time_str}.") #
                self.console_manager.add_output(f"Current time: {time_manager.get_time_string()}") #

                # Notify through Interface
                Interface.on_time_changed(new_time, time_manager.get_time_name()) #
                return True #
            else: #
                 self.console_manager.add_output("Time must be between 0 and 24 hours.") #
                 return False #
        except ValueError: #
            self.console_manager.add_output("Invalid time format. Use 'daytime <hour>' or 'daytime <hour:minute>'.") #
            return False #

    def _cmd_timespeed(self, args, game_state): #
        """Get or set the day length."""
        if not hasattr(self.game_state, 'time_manager'): #
            self.console_manager.add_output("Time of day system is not enabled.") #
            return False #

        time_manager = self.game_state.time_manager #

        if not args: #
            # Display current day length
            day_length = time_manager.day_length_seconds #
            self.console_manager.add_output(f"Current day length: {day_length} seconds.") #
            self.console_manager.add_output(f"({day_length/60:.1f} minutes per day)") #
            self.console_manager.add_output("Use 'timespeed <seconds>' to set day length.") #
            return # False? Let's return False

        # Set day length
        try: #
            day_length = float(args[0]) #
            if day_length < 60: #
                self.console_manager.add_output("Day length must be at least 60 seconds.") #
                return False #

            old_length = time_manager.day_length_seconds #
            time_manager.day_length_seconds = day_length #

            self.console_manager.add_output(f"Day length changed from {old_length} to {day_length} seconds.") #
            self.console_manager.add_output(f"({day_length/60:.1f} minutes per day)") #
            return True #
        except ValueError: #
            self.console_manager.add_output("Invalid day length. Please provide a number of seconds.") #
            return False #