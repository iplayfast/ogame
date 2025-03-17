# Village Simulation Game

A simulation game where villagers live their lives in a procedurally generated village.

## Code Organization

The code has been refactored to follow a more modular structure:

```
village_simulation/
├── game.py                 # Main entry point
├── game_core/              # Core game functionality
│   ├── __init__.py
│   ├── game_state.py       # Main game state class
│   ├── input_handler.py    # Handles user input
│   ├── render_manager.py   # Handles rendering
│   └── update_manager.py   # Handles game updates
├── entities/               # Game entities
│   ├── __init__.py
│   ├── housing_manager.py  # Manages buildings and housing
│   └── villager_manager.py # Manages villagers
└── systems/                # Game systems
    ├── __init__.py
    ├── command_system.py   # Console commands
    ├── interaction_system.py # Villager interactions
    └── time_system.py      # Time management
```

## Running the Game

Run the game with:

```
python game.py
```

## Key Features

- Procedurally generated village with various building types
- Villagers with daily routines and jobs
- Day/night cycle
- Basic villager interactions
- Developer console (toggle with ~ key)
- Path visualization
- Building interiors
- Villager sleep patterns

## Controls

- WASD/Arrows: Move camera
- Mouse click: Select villager or building
- P: Pause/resume game
- D: Toggle debug info
- V: Toggle path visualization
- T: Advance time by 1 hour (test key)
- I: Toggle building interiors
- ~ (tilde/backtick): Toggle console
- ESC: Quit

## Console Commands

- `help`: Show available commands
- `daytime <hour>`: View or set time of day
- `timespeed <seconds>`: Set day length in seconds
- `houses`: List all houses and their residents
- `assign <new|reload>`: Manage housing assignments
- `interiors <on|off|toggle>`: Control building interior visibility
- `wake <name|all>`: Wake up a specific villager or all villagers
- `sleep <name|all>`: Force a specific villager or all villagers to sleep
- `fix <sleepers|homes|all>`: Fix various game issues

## Code Structure Explanation

### Main Game Entry Point (game.py)

The main entry point initializes pygame, creates the game instance, and runs the main game loop.

### Game State (game_core/game_state.py)

The `VillageGame` class is the central game state that:
- Initializes all game subsystems
- Holds references to all managers and game data
- Delegates operations to specialized managers

### Managers

- **InputHandler**: Processes all user input events
- **UpdateManager**: Handles game state updates
- **RenderManager**: Handles rendering the game
- **VillagerManager**: Manages villager creation and behavior
- **HousingManager**: Manages building types and housing assignments

### Systems

- **CommandSystem**: Handles console commands
- **InteractionSystem**: Manages interactions between villagers
- **TimeSystem**: Handles time-related events and effects
