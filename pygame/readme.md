# Village Simulation with Console

This is a pygame-based village simulation game with a console interface for interacting with the game through text commands.

## Controls

- **WASD/Arrow Keys**: Move camera
- **Mouse Click**: Select villager or building
- **P**: Pause/resume game
- **D**: Toggle debug info
- **~ (Tilde/Backtick)**: Toggle console interface
- **ESC**: Quit game

## Console Commands

The console interface allows you to interact with the game through text commands. Press the tilde key (~) to open the console, and type your commands.

### Available Commands

- **help [command]**: Display help information
  - With no arguments, lists all available commands
  - With a command name, shows detailed help for that command

- **clear**: Clear the console output

- **list [villagers|buildings]**: List entities in the game
  - `list villagers`: List all villagers
  - `list buildings`: List all buildings

- **info <name|id>**: Display detailed information about an entity
  - Can use villager name or building ID
  - Examples: `info John Smith`, `info Tavern`, `info 1`

- **teleport <name|id> <x> <y>**: Teleport an entity to specified coordinates
  - Example: `teleport Jane Doe 500 500`

- **spawn <type> [x] [y]**: Spawn a new entity
  - Currently supports: `villager`
  - If coordinates are not provided, spawns at a random location
  - Example: `spawn villager 600 400`

- **stats**: Show game statistics
  - Displays counts of vi