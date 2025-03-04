extends CanvasLayer

# References to UI elements - using null checks to prevent errors
@onready var minimap = $Minimap
var villager_panel = null 
var building_panel = null
var debug_panel = null
var time_label = null

# Minimap properties
var minimap_scale = 0.1  # Scale factor for minimap (village coords to minimap pixels)
var following_villager = null
var debug_text = ""

func _ready():
	print("UI script is running")
	print("Minimap node exists: ", is_instance_valid(minimap))
	
	# Initialize panels safely
	if has_node("VillagerInfoPanel"):
		villager_panel = $VillagerInfoPanel
	if has_node("BuildingInfoPanel"):
		building_panel = $BuildingInfoPanel
	if has_node("DebugPanel"):
		debug_panel = $DebugPanel
	if has_node("TimeDisplay"):
		time_label = $TimeDisplay
	
	# Create timer manually for minimap updates
	var timer = Timer.new()
	timer.name = "MinimapUpdateTimer"
	timer.wait_time = 0.5
	timer.autostart = true
	add_child(timer)
	timer.timeout.connect(_on_minimap_update_timer_timeout)
	
	# Force an immediate update
	call_deferred("_on_minimap_update_timer_timeout")

func hide_all_panels():
	# Safely hide panels if they exist
	if villager_panel:
		villager_panel.visible = false
	if building_panel:
		building_panel.visible = false

# Simplify these functions to just return without errors if panels don't exist
func show_villager_info(villager):
	if not villager_panel:
		return

func show_building_info(building):
	if not building_panel:
		return

func _on_follow_button_pressed():
	if not villager_panel:
		return

func _on_minimap_update_timer_timeout():
	# Skip if minimap not available
	if not is_instance_valid(minimap):
		print("Minimap node is null or invalid")
		return
		
	print("Creating minimap image")
	
	# Create a new image for the minimap
	var img = Image.create(200, 200, false, Image.FORMAT_RGBA8)
	
	# Fill with background color (green for grass)
	img.fill(Color(0.2, 0.5, 0.2))
	
	# Get the village node
	var village_node = get_parent()
	if not village_node:
		print("Cannot find village node")
		return
		
	# Draw buildings (brown squares)
	if "buildings" in village_node:
		for building in village_node.buildings:
			var mini_x = int(building.position.x * minimap_scale)
			var mini_y = int(building.position.y * minimap_scale)
			
			# Different colors for different building types
			var color = Color(0.6, 0.4, 0.2)  # Brown for houses
			if "Shop" in building.name:
				color = Color(0.2, 0.4, 0.6)  # Blue for shops
				
			# Draw a 4x4 square
			for x in range(max(0, mini_x-2), min(200, mini_x+2)):
				for y in range(max(0, mini_y-2), min(200, mini_y+2)):
					if x >= 0 and x < 200 and y >= 0 and y < 200:
						img.set_pixel(x, y, color)
	
	# Draw villagers (white dots)
	if "villagers" in village_node:
		for villager in village_node.villagers:
			var mini_x = int(villager.position.x * minimap_scale)
			var mini_y = int(villager.position.y * minimap_scale)
			
			# Make sure coordinates are within bounds
			if mini_x >= 0 and mini_x < 200 and mini_y >= 0 and mini_y < 200:
				img.set_pixel(mini_x, mini_y, Color(1, 1, 1))
	
	# Draw camera viewport (yellow rectangle)
	var camera = village_node.get_node_or_null("Camera2D")
	if camera:
		var camera_pos = camera.position
		var viewport_size = get_viewport().get_visible_rect().size * camera.zoom
		
		var mini_camera_x = int(camera_pos.x * minimap_scale)
		var mini_camera_y = int(camera_pos.y * minimap_scale)
		var mini_width = int(viewport_size.x * minimap_scale * 0.5)
		var mini_height = int(viewport_size.y * minimap_scale * 0.5)
		
		# Draw the outline of the camera view
		for x in range(max(0, mini_camera_x-mini_width), min(200, mini_camera_x+mini_width)):
			if x >= 0 and x < 200:
				if mini_camera_y-mini_height >= 0 and mini_camera_y-mini_height < 200:
					img.set_pixel(x, mini_camera_y-mini_height, Color(1, 1, 0))
				if mini_camera_y+mini_height >= 0 and mini_camera_y+mini_height < 200:
					img.set_pixel(x, mini_camera_y+mini_height, Color(1, 1, 0))
					
		for y in range(max(0, mini_camera_y-mini_height), min(200, mini_camera_y+mini_height)):
			if y >= 0 and y < 200:
				if mini_camera_x-mini_width >= 0 and mini_camera_x-mini_width < 200:
					img.set_pixel(mini_camera_x-mini_width, y, Color(1, 1, 0))
				if mini_camera_x+mini_width >= 0 and mini_camera_x+mini_width < 200:
					img.set_pixel(mini_camera_x+mini_width, y, Color(1, 1, 0))
	
	print("Converting image to texture")
	# Convert the image to a texture for Godot 4.3
	var texture = ImageTexture.create_from_image(img)
	minimap.texture = texture
	print("Minimap texture assigned")

# Empty implementation to avoid errors
func _on_debug_update_timer_timeout():
	pass

func toggle_debug_panel():
	pass
