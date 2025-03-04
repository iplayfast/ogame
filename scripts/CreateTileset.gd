# CreateTileset.gd - Script to create a proper tileset from the terrain sprite
extends Node

func _ready():
	# This script creates a TileSet from the terrain.png file and saves it as a resource
	print("Creating tileset...")
	
	# Create a new TileSet
	var tileset = TileSet.new()
	
	# Load the terrain texture
	var terrain_texture = load("res://assets/sprites/terrain.png")
	if not terrain_texture:
		print("ERROR: Could not load terrain texture!")
		return
	
	# Create a new TileSetSource using atlas
	var source_id = 0
	var source = TileSetAtlasSource.new()
	
	# Set the texture
	source.texture = terrain_texture
	
	# Define tile size (based on your terrain.png layout)
	var tile_size = Vector2i(64, 64)
	source.texture_region_size = tile_size
	
	# Add all tiles from the 2x2 grid in terrain.png
	# Top-left: Grass (0,0)
	source.create_tile(Vector2i(0, 0))
	
	# Top-right: Water (1,0)
	source.create_tile(Vector2i(1, 0))
	
	# Bottom-left: Path (0,1)
	source.create_tile(Vector2i(0, 1))
	
	# Bottom-right: Stone (1,1)
	source.create_tile(Vector2i(1, 1))
	
	# Add the source to the tileset
	tileset.add_source(source, source_id)
	
	# Add physics layers (optional)
	tileset.add_physics_layer(0)
	
	# Add navigation layers (optional)
	tileset.add_navigation_layer(0)
	
	# Save the tileset as a resource
	var err = ResourceSaver.save(tileset, "res://assets/sprites/Terrain_tileset.tres")
	if err != OK:
		print("ERROR: Could not save tileset! Error code: ", err)
		return
	
	print("Tileset created successfully at 'res://assets/sprites/Terrain_tileset.tres'")
	print("Now you can use this tileset in your TileMap node.")
	
	# Notify user to restart Godot to see the tileset in the editor
	print("NOTE: You may need to restart Godot to see the tileset in the editor.")

# This function can be called manually if needed
func create_tileset():
	_ready()
