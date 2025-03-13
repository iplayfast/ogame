import pygame
import random
import re
import Interface

class ConsoleManager:
    def __init__(self, screen, assets, screen_width, screen_height):
        """Initialize the console manager.
        
        Args:
            screen: Pygame screen object
            assets: Dictionary of game assets
            screen_width: Width of the game screen
            screen_height: Height of the game screen
        """
        self.screen = screen
        self.assets = assets
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Console dimensions and position
        self.console_height = 200
        self.console_width = screen_width
        self.console_x = 0
        self.console_y = screen_height - self.console_height
        
        # Input field dimensions
        self.input_height = 30
        self.input_width = screen_width - 20
        self.input_x = 10
        self.input_y = screen_height - 40
        
        # Visual properties
        self.console_bg_color = (0, 0, 0, 180)  # Semi-transparent black
        self.console_border_color = (200, 200, 200)
        self.text_color = (255, 255, 255)
        self.input_bg_color = (30, 30, 30)
        self.input_active_color = (50, 50, 50)
        self.input_border_color = (150, 150, 150)
        self.cursor_color = (255, 255, 255)
        
        # Text properties
        self.font = pygame.font.SysFont(None, 24)
        self.command_font = pygame.font.SysFont(None, 24)
        
        # Input state
        self.active = False
        self.input_text = ""
        self.cursor_visible = True
        self.cursor_blink_timer = 0
        self.cursor_blink_speed = 500  # ms
        
        # Command history
        self.command_history = []
        self.history_index = -1
        
        # Console output
        self.console_output = []
        self.max_lines = 10
        
        # Toggle debounce timer to prevent flashing
        self.toggle_debounce = 0
        self.debounce_time = 300  # ms
        
        # Command registry
        self.commands = {
            "help": self._cmd_help,
            "clear": self._cmd_clear,
            "list": self._cmd_list,
            "info": self._cmd_info,
            "teleport": self._cmd_teleport,
            "spawn": self._cmd_spawn,
            "stats": self._cmd_stats,
            "time": self._cmd_time
        }
        
        # Add intro message
        self.add_output("Console activated. Type 'help' for available commands.")
    
    def toggle(self):
        """Toggle console visibility."""
        # Check debounce timer to prevent rapid toggling
        current_time = pygame.time.get_ticks()
        if current_time - self.toggle_debounce < self.debounce_time:
            return
            
        self.toggle_debounce = current_time
        self.active = not self.active
        
        if self.active:
            self.add_output("Console opened.")
        
    def is_active(self):
        """Return whether the console is active."""
        return self.active
    
    def add_output(self, text):
        """Add text to the console output."""
        # Split long lines to fit the console width
        lines = []
        max_chars_per_line = self.console_width // 10  # Approximate char width
        
        # Split the text by newlines first
        for line in text.split('\n'):
            if len(line) <= max_chars_per_line:
                lines.append(line)
            else:
                # Split long lines
                words = line.split(' ')
                current_line = ""
                
                for word in words:
                    if len(current_line) + len(word) + 1 <= max_chars_per_line:
                        if current_line:
                            current_line += ' ' + word
                        else:
                            current_line = word
                    else:
                        lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
        
        # Add all resulting lines to the output
        for line in lines:
            self.console_output.append(line)
        
        # Trim old lines
        if len(self.console_output) > self.max_lines:
            self.console_output = self.console_output[-self.max_lines:]
    
    def handle_event(self, event, game_state):
        """Handle keyboard events."""
        if not self.active:
            # Only check for the toggle key if not active
            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:  # Backtick/tilde key
                self.toggle()
                # Consume the event to prevent it from being processed elsewhere
                return True
            return False
        
        # Handle events when console is active
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.toggle()
                return True
                
            elif event.key == pygame.K_BACKQUOTE:
                # Don't toggle immediately when console is already active
                # Just consume the event
                return True
            
            elif event.key == pygame.K_RETURN:
                if self.input_text:
                    self.process_command(self.input_text, game_state)
                    self.command_history.append(self.input_text)
                    self.input_text = ""
                    self.history_index = -1
                return True
            
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return True
            
            elif event.key == pygame.K_UP:
                # Navigate command history (up)
                if self.command_history and self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.input_text = self.command_history[-(self.history_index + 1)]
                return True
            
            elif event.key == pygame.K_DOWN:
                # Navigate command history (down)
                if self.history_index > 0:
                    self.history_index -= 1
                    self.input_text = self.command_history[-(self.history_index + 1)]
                elif self.history_index == 0:
                    self.history_index = -1
                    self.input_text = ""
                return True
            
            elif event.key == pygame.K_TAB:
                # Auto-complete
                return self.autocomplete(game_state)
            
            else:
                # Add printable characters to input text
                if event.unicode and event.unicode.isprintable():
                    self.input_text += event.unicode
                return True
                
        # Consume mouse events when console is active to prevent clicks passing through
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return True
        
        # If we get here, we didn't handle the event
        return False
    
    def autocomplete(self, game_state):
        """Attempt to autocomplete the current command or arguments."""
        if not self.input_text:
            return True
        
        parts = self.input_text.split()
        
        if len(parts) == 1:
            # Autocomplete command name
            cmd_part = parts[0].lower()
            matching_commands = [cmd for cmd in self.commands.keys() if cmd.startswith(cmd_part)]
            
            if len(matching_commands) == 1:
                self.input_text = matching_commands[0] + " "
            elif len(matching_commands) > 1:
                self.add_output("Possible commands: " + ", ".join(matching_commands))
        
        elif len(parts) >= 2:
            # Autocomplete command arguments
            cmd = parts[0].lower()
            
            if cmd == "info" or cmd == "teleport":
                # Autocomplete entity names
                arg_part = parts[-1].lower()
                
                # Get possible entity names based on villagers
                if hasattr(game_state, 'villagers'):
                    villager_names = []
                    for villager in game_state.villagers:
                        name = villager.name.lower()
                        if name.startswith(arg_part):
                            villager_names.append(villager.name)
                    
                    if len(villager_names) == 1:
                        self.input_text = " ".join(parts[:-1]) + " " + villager_names[0]
                    elif len(villager_names) > 1:
                        self.add_output("Possible names: " + ", ".join(villager_names))
        
        return True
    
    def process_command(self, text, game_state):
        """Process a console command."""
        # Add input to console output with prefix
        self.add_output("> " + text)
        
        # Parse the command
        parts = text.split()
        if not parts:
            return
        
        command = parts[0].lower()
        args = parts[1:]
        
        # Execute the command if it exists
        if command in self.commands:
            try:
                self.commands[command](args, game_state)
            except Exception as e:
                self.add_output(f"Error executing command: {e}")
        else:
            self.add_output(f"Unknown command: '{command}'. Type 'help' for available commands.")
    
    def update(self, dt):
        """Update console state (cursor blink, etc.)."""
        if not self.active:
            return
            
        # Update cursor blink timer
        self.cursor_blink_timer += dt
        if self.cursor_blink_timer >= self.cursor_blink_speed:
            self.cursor_blink_timer = 0
            self.cursor_visible = not self.cursor_visible
# Add these methods to the ConsoleManager class
    
    def _cmd_time(self, args, game_state):
        """Get or set game time speed."""
        if not args:
            if hasattr(game_state, 'time_scale'):
                self.add_output(f"Current time scale: {game_state.time_scale:.1f}x")
            else:
                self.add_output("Time scale: 1.0x (default)")
            return
        
        try:
            time_scale = float(args[0])
            if time_scale < 0.1 or time_scale > 10.0:
                self.add_output("Time scale must be between 0.1 and 10.0.")
                return
            
            # Set the time scale
            if hasattr(game_state, 'time_scale'):
                old_scale = game_state.time_scale
                game_state.time_scale = time_scale
                self.add_output(f"Time scale changed from {old_scale:.1f}x to {time_scale:.1f}x.")
            else:
                # Add time_scale attribute if it doesn't exist
                game_state.time_scale = time_scale
                self.add_output(f"Time scale set to {time_scale:.1f}x.")
        except ValueError:
            self.add_output("Invalid time scale. Please provide a number between 0.1 and 10.0.")
    
    def _cmd_daytime(self, args, game_state):
        """Get or set the time of day."""
        if not hasattr(game_state, 'time_manager'):
            self.add_output("Time of day system is not enabled.")
            return
            
        time_manager = game_state.time_manager
        
        if not args:
            # Display current time
            current_time = time_manager.get_time_string()
            self.add_output(f"Current time: {current_time}")
            self.add_output("Use 'daytime <hour>' to set time (0-24).")
            self.add_output("Use 'daytime <hour:minute>' for precise time.")
            self.add_output("Examples: 'daytime 12' for noon, 'daytime 18:30' for 6:30 PM")
            return
            
        # Set time to specified hour
        try:
            if ':' in args[0]:
                # Format HH:MM
                hour_str, minute_str = args[0].split(':')
                hour = float(hour_str)
                minute = float(minute_str)
                if minute >= 60:
                    self.add_output("Minutes must be between 0 and 59.")
                    return
                    
                new_time = hour + (minute / 60.0)
            else:
                # Just hour
                new_time = float(args[0])
                
            if 0 <= new_time <= 24:
                old_time = time_manager.current_hour
                time_manager.set_time(new_time)
                
                old_time_str = f"{int(old_time)}:{int((old_time % 1) * 60):02d}"
                new_time_str = f"{int(new_time)}:{int((new_time % 1) * 60):02d}"
                
                self.add_output(f"Time changed from {old_time_str} to {new_time_str}.")
                self.add_output(f"Current time: {time_manager.get_time_string()}")
            else:
                self.add_output("Time must be between 0 and 24 hours.")
        except ValueError:
            self.add_output("Invalid time format. Use 'daytime <hour>' or 'daytime <hour:minute>'.")
    
    def _cmd_timespeed(self, args, game_state):
        """Get or set the day length."""
        if not hasattr(game_state, 'time_manager'):
            self.add_output("Time of day system is not enabled.")
            return
            
        time_manager = game_state.time_manager
        
        if not args:
            # Display current day length
            day_length = time_manager.day_length_seconds
            self.add_output(f"Current day length: {day_length} seconds.")
            self.add_output(f"({day_length/60:.1f} minutes per day)")
            self.add_output("Use 'timespeed <seconds>' to set day length.")
            return
            
        # Set day length
        try:
            day_length = float(args[0])
            if day_length < 60:
                self.add_output("Day length must be at least 60 seconds.")
                return
                
            old_length = time_manager.day_length_seconds
            time_manager.day_length_seconds = day_length
            
            self.add_output(f"Day length changed from {old_length} to {day_length} seconds.")
            self.add_output(f"({day_length/60:.1f} minutes per day)")
        except ValueError:
            self.add_output("Invalid day length. Please provide a number of seconds.")

    def draw(self):
        """Draw the console if active."""
        if not self.active:
            return
            
        # Create a semi-transparent surface
        console_surface = pygame.Surface((self.console_width, self.console_height), pygame.SRCALPHA)
        console_surface.fill(self.console_bg_color)
        
        # Draw console background
        self.screen.blit(console_surface, (self.console_x, self.console_y))
        pygame.draw.rect(self.screen, self.console_border_color, 
                       (self.console_x, self.console_y, self.console_width, self.console_height), 1)
        
        # Draw console output
        y_offset = self.console_y + 10
        for line in self.console_output:
            text_surface = self.font.render(line, True, self.text_color)
            self.screen.blit(text_surface, (self.console_x + 10, y_offset))
            y_offset += 25
        
        # Draw input field background
        pygame.draw.rect(self.screen, self.input_bg_color, 
                       (self.input_x, self.input_y, self.input_width, self.input_height))
        pygame.draw.rect(self.screen, self.input_border_color, 
                       (self.input_x, self.input_y, self.input_width, self.input_height), 1)
        
        # Draw input text
        if self.input_text:
            text_surface = self.command_font.render(self.input_text, True, self.text_color)
            self.screen.blit(text_surface, (self.input_x + 5, self.input_y + 5))
            
            # Draw cursor (if visible)
            if self.cursor_visible:
                text_width = self.command_font.size(self.input_text)[0]
                pygame.draw.rect(self.screen, self.cursor_color, 
                               (self.input_x + 5 + text_width, self.input_y + 5, 2, 20))
        else:
            # Draw just the cursor if no text
            if self.cursor_visible:
                pygame.draw.rect(self.screen, self.cursor_color, 
                               (self.input_x + 5, self.input_y + 5, 2, 20))
    
    # Command implementations
    def _cmd_help(self, args, game_state):
        """Display help information."""
        if not args:
            self.add_output("Available commands:")
            self.add_output("  help [command] - Display help information")
            self.add_output("  clear - Clear the console output")
            self.add_output("  list [villagers|buildings] - List entities")
            self.add_output("  info <name|id> - Display information about an entity")
            self.add_output("  teleport <name|id> <x> <y> - Teleport an entity")
            self.add_output("  spawn <type> [x] [y] - Spawn a new entity")
            self.add_output("  stats - Show game statistics")
            self.add_output("  time [speed] - Get or set game time speed")
            self.add_output("Type 'help <command>' for more information on a specific command.")
        else:
            command = args[0].lower()
            if command == "help":
                self.add_output("help [command] - Display help information")
                self.add_output("If a command is specified, shows detailed help for that command.")
            elif command == "clear":
                self.add_output("clear - Clear the console output")
                self.add_output("Removes all previous output from the console.")
            elif command == "list":
                self.add_output("list [villagers|buildings] - List entities")
                self.add_output("Displays a list of entities in the game.")
                self.add_output("Options:")
                self.add_output("  villagers - List all villagers")
                self.add_output("  buildings - List all buildings")
            elif command == "info":
                self.add_output("info <name|id> - Display information about an entity")
                self.add_output("Shows detailed information about a specific entity.")
            elif command == "teleport":
                self.add_output("teleport <name|id> <x> <y> - Teleport an entity")
                self.add_output("Moves the specified entity to the given coordinates.")
            elif command == "spawn":
                self.add_output("spawn <type> [x] [y] - Spawn a new entity")
                self.add_output("Creates a new entity of the specified type.")
                self.add_output("If x and y are not provided, spawns at a random location.")
            elif command == "stats":
                self.add_output("stats - Show game statistics")
                self.add_output("Displays various statistics about the current game state.")
            elif command == "time":
                self.add_output("time [speed] - Get or set game time speed")
                self.add_output("With no arguments, shows the current time speed.")
                self.add_output("With a speed argument (0.1-10.0), sets the game time speed.")
            else:
                self.add_output(f"No help available for '{command}'.")
    
    def _cmd_clear(self, args, game_state):
        """Clear the console output."""
        self.console_output = []
        self.add_output("Console cleared.")
    
    def _cmd_list(self, args, game_state):
        """List entities in the game."""
        if not args:
            self.add_output("Please specify what to list: 'villagers' or 'buildings'")
            return
        
        list_type = args[0].lower()
        
        if list_type == "villagers":
            if hasattr(game_state, 'villagers'):
                villager_count = len(game_state.villagers)
                self.add_output(f"There are {villager_count} villagers:")
                
                for i, villager in enumerate(game_state.villagers):
                    if i < 10:  # Limit to 10 villagers to avoid spamming
                        self.add_output(f"  {i+1}. {villager.name} ({villager.job})")
                
                if villager_count > 10:
                    self.add_output(f"  ... and {villager_count - 10} more.")
            else:
                self.add_output("No villagers found.")
        
        elif list_type == "buildings":
            if hasattr(game_state, 'village_data') and 'buildings' in game_state.village_data:
                buildings = game_state.village_data['buildings']
                building_count = len(buildings)
                self.add_output(f"There are {building_count} buildings:")
                
                for i, building in enumerate(buildings):
                    if i < 10:  # Limit to 10 buildings
                        building_type = building.get('building_type', 'Unknown')
                        x, y = building['position']
                        self.add_output(f"  {i+1}. {building_type} at ({x}, {y})")
                
                if building_count > 10:
                    self.add_output(f"  ... and {building_count - 10} more.")
            else:
                self.add_output("No buildings found.")
        
        else:
            self.add_output(f"Unknown list type: '{list_type}'. Use 'villagers' or 'buildings'.")
    
    def _cmd_info(self, args, game_state):
        """Display information about an entity."""
        if not args:
            self.add_output("Please specify an entity name or ID.")
            return
        
        entity_id = " ".join(args)
        
        # Try to find a villager with matching name
        if hasattr(game_state, 'villagers'):
            for villager in game_state.villagers:
                if entity_id.lower() in villager.name.lower():
                    status = villager.get_status()
                    self.add_output(f"Villager: {status['Name']}")
                    self.add_output(f"  Job: {status['Job']}")
                    self.add_output(f"  Position: ({int(villager.position.x)}, {int(villager.position.y)})")
                    self.add_output(f"  Health: {status['Health']}, Energy: {status['Energy']}")
                    self.add_output(f"  Mood: {status['Mood']}, Money: {status['Money']}")
                    self.add_output(f"  Activity: {status['Activity']}")
                    return
        
        # Try to find a building with matching ID
        if hasattr(game_state, 'village_data') and 'buildings' in game_state.village_data:
            try:
                # Check if entity_id is a number (building index)
                index = int(entity_id) - 1
                if 0 <= index < len(game_state.village_data['buildings']):
                    building = game_state.village_data['buildings'][index]
                    building_type = building.get('building_type', 'Unknown')
                    x, y = building['position']
                    size = building['size']
                    self.add_output(f"Building: {building_type}")
                    self.add_output(f"  Position: ({x}, {y})")
                    self.add_output(f"  Size: {size}")
                    return
            except ValueError:
                # Not a number, continue searching
                pass
                
            # Search by building type
            for i, building in enumerate(game_state.village_data['buildings']):
                building_type = building.get('building_type', 'Unknown')
                if entity_id.lower() in building_type.lower():
                    x, y = building['position']
                    size = building['size']
                    self.add_output(f"Building {i+1}: {building_type}")
                    self.add_output(f"  Position: ({x}, {y})")
                    self.add_output(f"  Size: {size}")
                    return
        
        self.add_output(f"Could not find entity: '{entity_id}'")
    
    def _cmd_teleport(self, args, game_state):
        """Teleport an entity to specific coordinates."""
        if len(args) < 3:
            self.add_output("Usage: teleport <name|id> <x> <y>")
            return
        
        entity_id = args[0]
        try:
            target_x = int(args[1])
            target_y = int(args[2])
        except ValueError:
            self.add_output("Coordinates must be integers.")
            return
        
        # Check if coordinates are within village bounds
        if hasattr(game_state, 'village_data') and 'size' in game_state.village_data:
            village_size = game_state.village_data['size']
            if target_x < 0 or target_x >= village_size or target_y < 0 or target_y >= village_size:
                self.add_output(f"Coordinates out of bounds. Village size is {village_size}x{village_size}.")
                return
        
        # Try to find and teleport a villager
        if hasattr(game_state, 'villagers'):
            for villager in game_state.villagers:
                if entity_id.lower() in villager.name.lower():
                    old_pos = (int(villager.position.x), int(villager.position.y))
                    
                    # Update position
                    villager.position.x = target_x
                    villager.position.y = target_y
                    villager.rect.x = target_x - villager.rect.width // 2
                    villager.rect.y = target_y - villager.rect.height // 2
                    
                    # Clear destination to prevent immediate movement
                    villager.destination = None
                    
                    self.add_output(f"Teleported {villager.name} from {old_pos} to ({target_x}, {target_y}).")
                    return
        
        self.add_output(f"Could not find entity: '{entity_id}'")
    
    def _cmd_spawn(self, args, game_state):
        """Spawn a new entity."""
        if not args:
            self.add_output("Usage: spawn <type> [x] [y]")
            return
        
        entity_type = args[0].lower()
        
        # Determine spawn position
        if len(args) >= 3:
            try:
                spawn_x = int(args[1])
                spawn_y = int(args[2])
            except ValueError:
                self.add_output("Coordinates must be integers.")
                return
        else:
            # Random position within village bounds
            if hasattr(game_state, 'village_data') and 'size' in game_state.village_data:
                village_size = game_state.village_data['size']
                padding = 100  # Keep away from edges
                spawn_x = random.randint(padding, village_size - padding)
                spawn_y = random.randint(padding, village_size - padding)
            else:
                self.add_output("Cannot determine spawn position. Please specify coordinates.")
                return
        
        # Spawn the requested entity type
        if entity_type == "villager":
            if hasattr(game_state, 'villagers') and hasattr(game_state, 'assets'):
                try:
                    from villager import Villager
                    new_villager = Villager(spawn_x, spawn_y, game_state.assets, game_state.TILE_SIZE)
                    game_state.villagers.add(new_villager)
                    self.add_output(f"Spawned new villager: {new_villager.name} at ({spawn_x}, {spawn_y}).")
                except Exception as e:
                    self.add_output(f"Error spawning villager: {e}")
            else:
                self.add_output("Cannot spawn villager: missing game state components.")
        else:
            self.add_output(f"Unknown entity type: '{entity_type}'. Try 'villager'.")
    
    def _cmd_stats(self, args, game_state):
        """Show game statistics."""
        stats = []
        
        # Villager stats
        if hasattr(game_state, 'villagers'):
            villager_count = len(game_state.villagers)
            stats.append(f"Villagers: {villager_count}")
            
            # Count villagers by job
            jobs = {}
            for villager in game_state.villagers:
                jobs[villager.job] = jobs.get(villager.job, 0) + 1
            
            stats.append("Jobs:")
            for job, count in sorted(jobs.items(), key=lambda x: x[1], reverse=True):
                stats.append(f"  {job}: {count}")
        
        # Building stats
        if hasattr(game_state, 'village_data') and 'buildings' in game_state.village_data:
            building_count = len(game_state.village_data['buildings'])
            stats.append(f"Buildings: {building_count}")
            
            # Count buildings by type
            building_types = {}
            for building in game_state.village_data['buildings']:
                building_type = building.get('building_type', 'Unknown')
                building_types[building_type] = building_types.get(building_type, 0) + 1
            
            stats.append("Building types:")
            for building_type, count in sorted(building_types.items(), key=lambda x: x[1], reverse=True):
                stats.append(f"  {building_type}: {count}")
        
        # FPS and other performance stats
        if hasattr(game_state, 'clock'):
            fps = game_state.clock.get_fps()
            stats.append(f"FPS: {fps:.1f}")
        
        # Village size
        if hasattr(game_state, 'village_data') and 'size' in game_state.village_data:
            village_size = game_state.village_data['size']
            stats.append(f"Village size: {village_size}x{village_size} pixels")
        
        # Camera position
        if hasattr(game_state, 'camera_x') and hasattr(game_state, 'camera_y'):
            stats.append(f"Camera position: ({game_state.camera_x}, {game_state.camera_y})")
        
        # Output all stats
        if stats:
            for stat in stats:
                self.add_output(stat)
        else:
            self.add_output("No statistics available.")
    
    def _cmd_time(self, args, game_state):
        """Get or set game time speed."""
        if not args:
            if hasattr(game_state, 'time_scale'):
                self.add_output(f"Current time scale: {game_state.time_scale:.1f}x")
            else:
                self.add_output("Time scale: 1.0x (default)")
            return
        
        try:
            time_scale = float(args[0])
            if time_scale < 0.1 or time_scale > 10.0:
                self.add_output("Time scale must be between 0.1 and 10.0.")
                return
            
            # Set the time scale
            if hasattr(game_state, 'time_scale'):
                old_scale = game_state.time_scale
                game_state.time_scale = time_scale
                self.add_output(f"Time scale changed from {old_scale:.1f}x to {time_scale:.1f}x.")
            else:
                # Add time_scale attribute if it doesn't exist
                game_state.time_scale = time_scale
                self.add_output(f"Time scale set to {time_scale:.1f}x.")
        except ValueError:
            self.add_output("Invalid time scale. Please provide a number between 0.1 and 10.0.")
    def process_command_with_interface(self, text, game_state):
        """Process a console command with Interface notification."""
        # Add input to console output with prefix
        self.add_output("> " + text)
        
        # Parse the command
        parts = text.split()
        if not parts:
            return
        
        command = parts[0].lower()
        args = parts[1:]
        
        # Result storage for Interface notification
        result = None
        
        # Execute the command if it exists
        if command in self.commands:
            try:
                result = self.commands[command](args, game_state)
                
                # If result is None (the default for most commands), set it to True
                # to indicate success
                if result is None:
                    result = True
            except Exception as e:
                self.add_output(f"Error executing command: {e}")
                result = False
        else:
            self.add_output(f"Unknown command: '{command}'. Type 'help' for available commands.")
            result = False
        
        # Notify Interface
        Interface.on_console_command(command, args, result)
        
        return result

    # --- MODIFY specific command implementations ---

    # Example: Modify _cmd_time to return a result
    def _cmd_time_with_interface(self, args, game_state):
        """Get or set game time speed."""
        if not args:
            if hasattr(game_state, 'time_scale'):
                self.add_output(f"Current time scale: {game_state.time_scale:.1f}x")
            else:
                self.add_output("Time scale: 1.0x (default)")
            return None  # No change
        
        try:
            time_scale = float(args[0])
            if time_scale < 0.1 or time_scale > 10.0:
                self.add_output("Time scale must be between 0.1 and 10.0.")
                return False  # Failed
            
            # Set the time scale
            if hasattr(game_state, 'time_scale'):
                old_scale = game_state.time_scale
                game_state.time_scale = time_scale
                self.add_output(f"Time scale changed from {old_scale:.1f}x to {time_scale:.1f}x.")
            else:
                # Add time_scale attribute if it doesn't exist
                game_state.time_scale = time_scale
                self.add_output(f"Time scale set to {time_scale:.1f}x.")
            
            return time_scale  # Return the new time scale
        except ValueError:
            self.add_output("Invalid time scale. Please provide a number between 0.1 and 10.0.")
            return False  # Failed

    # --- ADD NEW COMMANDS that interact with Interface ---

    def _cmd_listen(self, args, game_state):
        """Enable or disable Interface event logging."""
        if not args:
            self.add_output("Usage: listen <on|off> [event_type]")
            self.add_output("Event types: villager, building, environment, game, ui, all")
            return False
        
        mode = args[0].lower()
        event_type = args[1].lower() if len(args) > 1 else "all"
        
        if mode not in ["on", "off"]:
            self.add_output("Mode must be 'on' or 'off'")
            return False
        
        enabled = (mode == "on")
        
        # Set up a logging function
        def log_event(event_name, **kwargs):
            args_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            self.add_output(f"[EVENT] {event_name}({args_str})")
        
        # Register or unregister callbacks based on event type
        if event_type == "all" or event_type == "villager":
            # Villager events
            events = [
                "villager_moved", "villager_activity_changed", 
                "villager_sleep_state_changed", "villager_selected"
            ]
            for event in events:
                if enabled:
                    Interface._register_callback(event, log_event)
                # Unregistering would need a reference to the specific function
        
        # Similar for other event types...
        
        # Enable debug mode in Interface itself
        Interface.set_debug(enabled)
        
        self.add_output(f"Event listening turned {mode} for {event_type} events")
        return enabled

    def _cmd_interface(self, args, game_state):
        """Control Interface module settings."""
        if not args:
            self.add_output("Usage: interface <debug|stats> [on|off]")
            return False
        
        subcommand = args[0].lower()
        
        if subcommand == "debug":
            # Handle debug mode
            if len(args) < 2:
                current_debug = Interface._debug_mode
                self.add_output(f"Interface debug mode is currently {'ON' if current_debug else 'OFF'}")
                return current_debug
            
            mode = args[1].lower() == "on"
            Interface.set_debug(mode)
            self.add_output(f"Interface debug mode turned {'ON' if mode else 'OFF'}")
            return mode
            
        elif subcommand == "stats":
            # Retrieve and display stats about registered callbacks
            villager_count = sum(len(cbs) for cbs in Interface._villager_callbacks.values())
            building_count = sum(len(cbs) for cbs in Interface._building_callbacks.values())
            environment_count = sum(len(cbs) for cbs in Interface._environment_callbacks.values())
            game_count = sum(len(cbs) for cbs in Interface._game_event_callbacks.values())
            ui_count = sum(len(cbs) for cbs in Interface._ui_callbacks.values())
            time_count = len(Interface._time_callbacks)
            
            total = villager_count + building_count + environment_count + game_count + ui_count + time_count
            
            self.add_output(f"Interface Callback Statistics:")
            self.add_output(f"- Time callbacks: {time_count}")
            self.add_output(f"- Villager callbacks: {villager_count}")
            self.add_output(f"- Building callbacks: {building_count}")
            self.add_output(f"- Environment callbacks: {environment_count}")
            self.add_output(f"- Game callbacks: {game_count}")
            self.add_output(f"- UI callbacks: {ui_count}")
            self.add_output(f"- Total callbacks: {total}")
            
            return total
        
        else:
            self.add_output(f"Unknown subcommand: {subcommand}")
            return False

    # --- MAKE SURE TO UPDATE THE commands DICTIONARY ---

    # In the ConsoleManager.__init__ method, add the new commands:
    # self.commands.update({
    #     "listen": self._cmd_listen,
    #     "interface": self._cmd_interface
    # })

    # And replace the existing command with the enhanced version:
    # self.commands["time"] = self._cmd_time_with_interface