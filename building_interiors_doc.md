# Building Interiors Feature

This feature adds detailed interiors to buildings in the village simulation. Buildings now contain furniture and fixtures appropriate to their type, allowing villagers to interact with specific objects based on their activities.

## Features

- Interior layouts with furniture specific to building types (houses, bakeries, inns, etc.)
- Render toggling with the "I" key or console commands
- Different furniture types: beds, tables, chairs, hearths, ovens, and more
- Building-specific interiors matching their function
- Visible furniture that villagers can interact with

## Building Types

Each building type has a unique interior layout:

### Houses and Cottages
- Beds for sleeping
- Tables and chairs
- Hearths for cooking and warmth
- Chests for storage (in larger houses)
- Bookshelves (in larger houses)

### Bakeries
- Ovens for baking
- Counters for serving customers
- Tables for dough preparation
- Barrels for storage

### Inns and Taverns
- Bar/counter for serving
- Multiple tables with chairs
- Barrels for drinks
- Hearths in larger inns

### Stores and Markets
- Counter for transactions
- Shelves along walls
- Storage items (barrels, chests)

### Workshops and Smithies
- Workbenches
- Forges and anvils (in smithies)
- Tables for crafting
- Storage shelves

## Controls

- **I key**: Toggle building interiors visibility
- Console commands:
  - `interiors`: View current status
  - `interiors on`: Show building interiors
  - `interiors off`: Hide building interiors
  - `interiors toggle`: Toggle visibility

## Technical Implementation

The interiors system is implemented through several components:

1. **BuildingInteriors class**: Generates and renders interior layouts
2. **Renderer Enhancement**: Integrates interiors with the existing rendering system
3. **Game Logic Integration**: Connects interiors to game events and commands

## Villager Interactions

Villagers can now interact with specific furniture based on their activities:
- Sleep in beds during night hours
- Work at appropriate stations (ovens, forges, counters)
- Sit at tables during meals
- Gather around hearths

## Future Enhancements

Possible future improvements include:
- More detailed furniture with animations (flickering fires, etc.)
- Day/night lighting effects inside buildings
- More unique furniture types
- Building customization options
- Improved villager interactions with furniture
