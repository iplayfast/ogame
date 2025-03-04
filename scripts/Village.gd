# Village.gd - Controls the village simulation
extends Node2D

# Scene references
@export var house_scene: PackedScene
@export var shop_scene: PackedScene
@export var villager_scene: PackedScene

# Village properties
var village_width = 2000
var village_height = 2000
var time_of_day = 8.0  # Start at 8 AM
var day = 1
var time_scale = 1.0  # Time multiplier

# Village entities
var buildings = []
var villagers = []
var selected_villager = null

# Village environment
enum Weather { SUNNY, CLOUDY, RAINY, STORMY }
var current_weather = Weather.SUNNY
var view_rect = Rect2(0, 0, 2000, 2000)

# Configuration
var num_houses = 10
var num_shops = 5
var num_villagers = 15

# Signals
signal building_added(building)
signal building_removed(building)
signal villager_added(villager)
signal villager_removed(villager)
signal day_changed(day)
signal weather_changed(weather)

func _ready():
	# Initialize random number generator
	randomize()
	
	# Setup village
	# Wait for GameManager to initialize systems
	print("Village: Waiting for GameManager to initialize systems...")
	if not GameManager.village:
		GameManager.village = self
	
	# Connect to the systems_initialized signal if needed
	if not GameManager.is_connected("systems_initialized", Callable(self, "_on_systems_initialized")):
		GameManager.systems_initialized.connect(_on_systems_initialized)
	
	# If systems are already initialized, call the handler directly
	if GameManager.tilemap and GameManager.navigation:
		_on_systems_initialized()


	# Make sure navigation is properly initialized
	call_deferred("_setup_navigation")
	
	# Initialize timers
	$DayNightTimer.timeout.connect(_on_day_night_timer_timeout)
	$DayNightTimer.start(1.0)  # Update time every second
	
	$WeatherTimer.timeout.connect(_on_weather_timer_timeout)
	$WeatherTimer.start()
	
	# Setup input detection for selection
	set_process_input(true)


func _on_systems_initialized():
	print("Village: GameManager systems initialized, continuing setup...")
	# Now that systems are initialized, continue with village setup
	setup_village()
	
	# Generate buildings and villagers
	generate_buildings()
	generate_villagers()
	
	print("Village scene loaded successfully")

func _setup_navigation():
	# Wait for a frame to ensure all buildings and villagers are added
	await get_tree().process_frame
	
	# Get navigation region
	var nav_region = $NavigationRegion2D
	
	# Create navigation polygon
	var nav_poly = NavigationPolygon.new()
	if nav_region and nav_region.has_method("create_navigation_polygon"):
		print("Village: Calling Navigation.gd's create_navigation_polygon method")
		nav_region.create_navigation_polygon()
	else:
		print("Village: WARNING - Navigation script not properly attached or method not found")

	print("Village: Navigation setup completed")
	# Set up village boundaries
	var outline = PackedVector2Array([
		Vector2(0, 0),
		Vector2(village_width, 0),
		Vector2(village_width, village_height),
		Vector2(0, village_height)
	])
	
	nav_poly.add_outline(outline)
	
	# Add building obstacles
	for building in buildings:
		var size = Vector2(64, 64)
		if building.has_node("Sprite2D") and building.get_node("Sprite2D").texture:
			size = building.get_node("Sprite2D").texture.get_size()
		
		var pos = building.position
		var half_size = size/2
		
		var building_outline = PackedVector2Array([
			Vector2(pos.x - half_size.x, pos.y - half_size.y),
			Vector2(pos.x + half_size.x, pos.y - half_size.y),
			Vector2(pos.x + half_size.x, pos.y + half_size.y),
			Vector2(pos.x - half_size.x, pos.y + half_size.y)
		])
		
		nav_poly.add_outline(building_outline)
	
	# Build navigation mesh
	nav_poly.make_polygons_from_outlines()
	nav_region.navigation_polygon = nav_poly
	
	# Force navigation update
	NavigationServer2D.map_force_update(get_world_2d().navigation_map)
	
	print("Navigation mesh created successfully")
			
func _input(event):
	# Check for mouse click to select entities
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		var click_pos = get_global_mouse_position()
		
		# Check for villager selection
		var clicked_villager = find_villager_at_position(click_pos)
		if clicked_villager:
			selected_villager = clicked_villager
			clicked_villager.on_click()
			return
		
		# Check for building selection
		var clicked_building = find_building_at_position(click_pos)
		if clicked_building:
			clicked_building.on_click()
			return

func setup_village():
	# Generate buildings
	generate_buildings()
	
	# Generate villagers
	generate_villagers()

func generate_buildings():
	# Generate houses
	for i in range(num_houses):
		var house = house_scene.instantiate()
		var pos = find_valid_position(64)  # Assuming house size
		house.position = pos
		house.name = "House_" + str(i)
		add_child(house)
		buildings.append(house)
		emit_signal("building_added", house)
	
	# Generate shops
	for i in range(num_shops):
		var shop = shop_scene.instantiate()
		var pos = find_valid_position(64)  # Assuming shop size
		shop.position = pos
		shop.name = "Shop_" + str(i)
		add_child(shop)
		buildings.append(shop)
		emit_signal("building_added", shop)

func generate_villagers():
	for i in range(num_villagers):
		var villager = villager_scene.instantiate()
		var pos = find_valid_position(32)  # Assuming villager size
		
		# Assign a random home and workplace
		var homes = buildings.filter(func(b): return "House" in b.name)
		var shops = buildings.filter(func(b): return "Shop" in b.name)
		
		var home = homes[randi() % homes.size()] if homes.size() > 0 else null
		var workplace = shops[randi() % shops.size()] if shops.size() > 0 else null
		
		villager.position = pos
		villager.name = "Villager_" + str(i)
		add_child(villager)
		
		# Initialize the villager with home and workplace
		villager.initialize(home, workplace)
		
		villagers.append(villager)
		emit_signal("villager_added", villager)

func find_valid_position(size):
	# Find a position that doesn't overlap with existing buildings
	var max_attempts = 50
	var attempts = 0
	
	while attempts < max_attempts:
		var pos = Vector2(
			randf_range(size, village_width - size),
			randf_range(size, village_height - size)
		)
		
		var valid = true
		for building in buildings:
			if pos.distance_to(building.position) < size + 32:  # Add some spacing
				valid = false
				break
				
		if valid:
			return pos
			
		attempts += 1
	
	# If we couldn't find a valid position, return a default
	return Vector2(village_width / 2, village_height / 2)

func _on_day_night_timer_timeout():
	# Update time of day
	time_of_day += 0.1 * time_scale  # 6 minutes game time per second
	
	if time_of_day >= 24.0:
		time_of_day = 0.0
		day += 1
		emit_signal("day_changed", day)
	
	# Update UI time display
	var ui = get_node("UI")
	if ui and ui.has_node("TimeDisplay"):
		var hour = floor(time_of_day)
		var minute = floor((time_of_day - hour) * 60)
		ui.get_node("TimeDisplay").text = "Day %d - %02d:%02d" % [day, hour, minute]
	
	# Update lighting based on time of day
	update_lighting()

func update_lighting():
	# Adjust global lighting based on time
	var is_night = time_of_day < 6.0 or time_of_day > 18.0
	var is_dawn_dusk = (time_of_day > 5.0 and time_of_day < 7.0) or (time_of_day > 17.0 and time_of_day < 19.0)
	
	# Could add code here to adjust environment lighting if using WorldEnvironment

func _on_weather_timer_timeout():
	# Change weather randomly
	var new_weather = randi() % Weather.size()
	
	if new_weather != current_weather:
		current_weather = new_weather
		emit_signal("weather_changed", current_weather)
		
		# Update weather effects
		update_weather_effects()
		
		# Notify UI
		var ui = get_node("UI")
		if ui and ui.has_node("WeatherDisplay"):
			ui.get_node("WeatherDisplay").text = "Weather: " + weather_to_string(current_weather)

func update_weather_effects():
	# Show/hide weather effect nodes based on current weather
	if has_node("WeatherEffects/Rain"):
		$WeatherEffects/Rain.visible = current_weather == Weather.RAINY or current_weather == Weather.STORMY
	
	if has_node("WeatherEffects/Lightning"):
		$WeatherEffects/Lightning.visible = current_weather == Weather.STORMY
		
		# For stormy weather, add occasional lightning flashes
		if current_weather == Weather.STORMY:
			$WeatherTransitionTimer.timeout.connect(_on_lightning_flash_timeout)
			$WeatherTransitionTimer.start(randf_range(5.0, 15.0))

func _on_lightning_flash_timeout():
	if current_weather == Weather.STORMY and has_node("WeatherEffects/Lightning/FlashRect"):
		# Flash the lightning effect
		$WeatherEffects/Lightning/FlashRect.visible = true
		
		# Hide after a short delay
		await get_tree().create_timer(0.1).timeout
		$WeatherEffects/Lightning/FlashRect.visible = false
		
		# Schedule next flash if still stormy
		if current_weather == Weather.STORMY:
			$WeatherTransitionTimer.start(randf_range(5.0, 15.0))

func find_villager_at_position(pos):
	for villager in villagers:
		if villager.get_rect().has_point(pos):
			return villager
	return null

func find_building_at_position(pos):
	for building in buildings:
		if building.get_rect().has_point(pos):
			return building
	return null

func get_village_size():
	return Vector2(village_width, village_height)

func weather_to_string(weather_enum):
	match weather_enum:
		Weather.SUNNY: return "Sunny"
		Weather.CLOUDY: return "Cloudy"
		Weather.RAINY: return "Rainy"
		Weather.STORMY: return "Stormy"
		_: return "Unknown"

# API functions for external control

func add_villager(custom_name = ""):
	var villager = villager_scene.instantiate()
	var pos = find_valid_position(32)
	
	# Assign a random home and workplace
	var homes = buildings.filter(func(b): return "House" in b.name)
	var shops = buildings.filter(func(b): return "Shop" in b.name)
	
	var home = homes[randi() % homes.size()] if homes.size() > 0 else null
	var workplace = shops[randi() % shops.size()] if shops.size() > 0 else null
	
	villager.position = pos
	villager.name = "Villager_" + str(villagers.size())
	add_child(villager)
	
	# Initialize the villager with home and workplace
	villager.initialize(home, workplace)
	
	# Set custom name if provided
	if custom_name.length() > 0:
		villager.villager_name = custom_name
	
	villagers.append(villager)
	emit_signal("villager_added", villager)
	
	return villager

func remove_villager(villager):
	if villager in villagers:
		villagers.erase(villager)
