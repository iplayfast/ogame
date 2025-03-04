# NavigationManager.gd - Handles village navigation regions
extends NavigationRegion2D

# Navigation variables
var obstacle_points = []
var village_size = Vector2(2000, 2000)

func _ready():
	# Get village size from parent if available
	var parent = get_parent()
	if parent and "village_width" in parent and "village_height" in parent:
		village_size = Vector2(parent.village_width, parent.village_height)
	
	# Initialize the navigation polygon
	create_navigation_polygon()
	
	# Connect to signals for updating navigation when buildings are added/removed
	if parent:
		if parent.has_signal("building_added"):
			parent.building_added.connect(_on_building_added)
		if parent.has_signal("building_removed"):
			parent.building_removed.connect(_on_building_removed)
	
	print("Navigation system initialized")

func create_navigation_polygon():
	# Create a navigation polygon for the entire village
	var nav_polygon = NavigationPolygon.new()
	
	# Add the outer boundary of the village
	var outer_boundary = PackedVector2Array([
		Vector2(0, 0),
		Vector2(village_size.x, 0),
		Vector2(village_size.x, village_size.y),
		Vector2(0, village_size.y)
	])
	
	nav_polygon.add_outline(outer_boundary)
	
	# Add obstacles for buildings
	var parent = get_parent()
	if parent and "buildings" in parent:
		for building in parent.buildings:
			add_building_obstacle(nav_polygon, building)
	
	# Make polygons from outlines
	nav_polygon.make_polygons_from_outlines()
	
	# Set the navigation polygon
	navigation_polygon = nav_polygon
	
	# Force the NavigationServer to update
	NavigationServer2D.map_force_update(get_world_2d().navigation_map)
	
	print("Navigation polygon updated with " + str(parent.buildings.size() if parent and "buildings" in parent else 0) + " obstacles")

func add_building_obstacle(nav_polygon, building):
	# Skip if building doesn't have a position
	if not building or not "position" in building:
		return
		
	# Determine building size - use sprite size if available
	var size = Vector2(40, 40)  # Default size
	
	if building.has_node("Sprite2D") and building.get_node("Sprite2D").texture:
		size = building.get_node("Sprite2D").texture.get_size() * building.get_node("Sprite2D").scale
	
	# Create obstacle outline
	var half_size = size / 2
	var obstacle = PackedVector2Array([
		building.position - half_size,
		Vector2(building.position.x + half_size.x, building.position.y - half_size.y),
		building.position + half_size,
		Vector2(building.position.x - half_size.x, building.position.y + half_size.y)
	])
	
	# Add to navigation polygon
	nav_polygon.add_outline(obstacle)
	
	# Store the obstacle points for later reference
	obstacle_points.append({
		"building": building.name,
		"points": obstacle
	})

func _on_building_added(building):
	# Update navigation when a new building is added
	update_navigation()
	print("Navigation updated - building added: " + building.name)

func _on_building_removed(building):
	# Find and remove the obstacle for this building
	for i in range(obstacle_points.size() - 1, -1, -1):
		if obstacle_points[i].building == building.name:
			obstacle_points.remove_at(i)
	
	# Update navigation
	update_navigation()

func update_navigation():
	# Recreate the navigation polygon
	create_navigation_polygon()

func is_position_navigable(position):
	# Check if a position is within any building obstacle
	for obstacle in obstacle_points:
		var points = obstacle.points
		if Geometry2D.is_point_in_polygon(position, points):
			return false
	
	# Check village boundaries
	if position.x < 0 or position.x > village_size.x or position.y < 0 or position.y > village_size.y:
		return false
	
	return true

func get_random_navigable_position():
	# Get a random position in the village that's not inside a building
	var max_attempts = 20
	var attempts = 0
	
	while attempts < max_attempts:
		var pos = Vector2(
			randf_range(50, village_size.x - 50),
			randf_range(50, village_size.y - 50)
		)
		
		if is_position_navigable(pos):
			return pos
			
		attempts += 1
	
	# Default position if all attempts fail
	return Vector2(village_size.x / 2, village_size.y / 2)