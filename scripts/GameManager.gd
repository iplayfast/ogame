# GameManager.gd - Global manager for village simulation
extends Node

# Store references to important nodes
var village: Node = null
var tilemap: TileMap = null
var navigation: Node = null

# Signal when core systems are ready
signal systems_initialized

func _ready():
	print("GameManager: Initializing...")
	# Wait for the scene to be fully loaded
	await get_tree().process_frame
	# Find the village scene
	initialize_references()

func initialize_references():
	# Find the village scene
	village = get_tree().get_root().get_node_or_null("Village")
	if not village:
		print("GameManager: ERROR - Village scene not found! Waiting for scene change...")
		# Wait for the scene to change and try again
		await get_tree().process_frame
		initialize_references()
		return
	
	print("GameManager: Village scene found")
	
	# Set up the TileMap if needed
	initialize_tilemap()
	
	# Set up the Navigation system if needed
	initialize_navigation()
	
	# Emit signal that all systems are ready
	print("GameManager: All systems initialized")
	emit_signal("systems_initialized")

func initialize_tilemap():
	# Find the TileMap in the village scene
	tilemap = village.get_node_or_null("TileMap")
	
	if not tilemap:
		print("GameManager: TileMap not found, creating it...")
		
		# Create a new TileMap
		tilemap = TileMap.new()
		tilemap.name = "TileMap"
		
		# Set the tileset resource
		var tileset_path = "res://assets/sprites/Terrain_tilset.tres"
		if ResourceLoader.exists(tileset_path):
			var tileset = load(tileset_path)
			tilemap.tile_set = tileset
		else:
			print("GameManager: ERROR - TileSet resource not found!")
		
		# Add to the scene
		village.add_child(tilemap)
		tilemap.owner = village
		
		# Configure the tilemap
		populate_tilemap()
	else:
		print("GameManager: Found existing TileMap")
		# Check if tilemap has contents
		var has_cells = false
		# Only check layer 0 which is guaranteed to exist
		var used_cells = tilemap.get_used_cells(0)
		if used_cells.size() > 0:
			has_cells = true
		
		if not has_cells:
			print("GameManager: TileMap exists but is empty, populating it...")
			populate_tilemap()

func populate_tilemap():
	print("GameManager: Populating TileMap...")
	if not tilemap or not village:
		print("GameManager: ERROR - Cannot populate TileMap, references missing")
		return
	
	# Clear any existing tiles
	tilemap.clear()
	
	# Get village size
	var width = 2000
	var height = 2000
	if "village_width" in village and "village_height" in village:
		width = village.village_width
		height = village.village_height

	
	# Fill with grass (layer 0, source 0, atlas coords 0,0)
	print("GameManager: Adding grass tiles...")
	for x in range(int(width / 64) + 1):
		for y in range(int(height / 64) + 1):
			tilemap.set_cell(0, Vector2i(x, y), 0, Vector2i(0, 0))
	
	# Add some water pools (layer 0, source 0, atlas coords 1,0)
	print("GameManager: Adding water features...")
	var num_water_pools = 5
	for i in range(num_water_pools):
		var pool_x = randi() % int(width / 64)
		var pool_y = randi() % int(height / 64)
		var pool_size = randi() % 3 + 2
		
		for x in range(pool_size):
			for y in range(pool_size):
				if randf() > 0.3:  # Make pools irregular
					tilemap.set_cell(0, Vector2i(pool_x + x, pool_y + y), 0, Vector2i(1, 0))
	
	# Add some paths (layer 0, source 0, atlas coords 0,1)
	print("GameManager: Adding paths...")
	var num_paths = 8
	for i in range(num_paths):
		var path_length = randi() % 10 + 5
		var start_x = randi() % int(width / 64)
		var start_y = randi() % int(height / 64)
		var direction = randi() % 2  # 0 = horizontal, 1 = vertical
		
		for j in range(path_length):
			if direction == 0:  # horizontal
				tilemap.set_cell(0, Vector2i(start_x + j, start_y), 0, Vector2i(0, 1))
			else:  # vertical
				tilemap.set_cell(0, Vector2i(start_x, start_y + j), 0, Vector2i(0, 1))
	
	# Add some stone areas (layer 0, source 0, atlas coords 1,1)
	print("GameManager: Adding stone areas...")
	var num_stone_areas = 3
	for i in range(num_stone_areas):
		var stone_x = randi() % int(width / 64)
		var stone_y = randi() % int(height / 64)
		var stone_size = randi() % 3 + 1
		
		for x in range(stone_size):
			for y in range(stone_size):
				tilemap.set_cell(0, Vector2i(stone_x + x, stone_y + y), 0, Vector2i(1, 1))
	
	print("GameManager: TileMap population complete!")
	print("TileMap cells: ", tilemap.get_used_cells(0).size())

func initialize_navigation():
	# Find the Navigation node in the village scene
	navigation = village.get_node_or_null("NavigationRegion2D")
	
	if not navigation:
		print("GameManager: Navigation node not found, creating it...")
		
		# Create a new NavigationRegion2D node
		navigation = NavigationRegion2D.new()
		navigation.name = "NavigationRegion2D"
		
		# Set the navigation script if it exists - FIX THIS PART
		var navigation_script_path = "res://scripts/Navigation.gd"
		if ResourceLoader.exists(navigation_script_path):
			var script = load(navigation_script_path)
			navigation.set_script(script)
			print("GameManager: Navigation script loaded successfully")
		else:
			print("GameManager: WARNING - Navigation.gd script not found at " + navigation_script_path)
			
		# Add to the scene
		village.add_child(navigation)
		navigation.owner = village
		
		print("GameManager: Created Navigation node")
	else:
		print("GameManager: Found existing Navigation node")
		
		# Ensure the script is attached even on existing navigation node
		if not navigation.get_script():
			var navigation_script_path = "res://scripts/Navigation.gd"
			if ResourceLoader.exists(navigation_script_path):
				navigation.set_script(load(navigation_script_path))
				print("GameManager: Navigation script attached to existing node")

func get_tilemap():
	# Safe access to the TileMap
	if not tilemap and village:
		# Try to find it again
		tilemap = village.get_node_or_null("TileMap")
	return tilemap

func get_navigation():
	# Safe access to the Navigation node
	if not navigation and village:
		# Try to find it again
		navigation = village.get_node_or_null("Navigation")
	return navigation
