# CameraController.gd - Controls the camera for the village view
extends Camera2D

# Camera properties
@export var camera_speed = 400  # Speed when moving with keys
@export var zoom_speed = 0.1    # Zoom speed with mouse wheel
@export var min_zoom = 0.5      # Maximum zoom in
@export var max_zoom = 2.0      # Maximum zoom out
@export var pan_speed = 1.0     # Speed when panning with middle mouse

# Camera control flags
var dragging = false
var drag_start = Vector2.ZERO
var drag_current = Vector2.ZERO
var following = false
var target = null  # Node to follow

func _ready():
	# Enable processing for camera movement
	set_process(true)
	set_process_input(true)
	
	# Set initial camera limits from parent if available
	if get_parent():
		if get_parent().has_method("get_village_size"):
			var size = get_parent().get_village_size()
			limit_left = 0
			limit_top = 0
			limit_right = size.x
			limit_bottom = size.y
		elif "village_width" in get_parent() and "village_height" in get_parent():
			limit_left = 0
			limit_top = 0
			limit_right = get_parent().village_width
			limit_bottom = get_parent().village_height

func _process(delta):
	# Follow target if enabled
	if following and is_instance_valid(target):
		position = target.position
		# Update the parent's view_rect if it exists
		if get_parent() and "view_rect" in get_parent():
			var view_size = get_viewport_rect().size * zoom
			get_parent().view_rect = Rect2(
				position - view_size/2,
				view_size
			)
		return
	
	# Handle keyboard movement
	var input_dir = Vector2.ZERO
	
	if Input.is_action_pressed("ui_right"):
		input_dir.x += 1
	if Input.is_action_pressed("ui_left"):
		input_dir.x -= 1
	if Input.is_action_pressed("ui_down"):
		input_dir.y += 1
	if Input.is_action_pressed("ui_up"):
		input_dir.y -= 1
	
	# Move camera with keys
	if input_dir != Vector2.ZERO:
		following = false  # Stop following when manually moving
		position += input_dir.normalized() * camera_speed * delta * zoom.x
	
	# Handle dragging (for pan)
	if dragging:
		following = false  # Stop following when manually moving
		position = drag_start + (drag_start - drag_current) * pan_speed * zoom.x
		
	# Update the parent's view_rect if it exists
	if get_parent() and "view_rect" in get_parent():
		var view_size = get_viewport_rect().size * zoom
		get_parent().view_rect = Rect2(
			position - view_size/2,
			view_size
		)

func _input(event):
	# Handle mouse wheel for zoom
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			# Zoom in
			zoom = Vector2(max(min_zoom, zoom.x - zoom_speed), max(min_zoom, zoom.y - zoom_speed))
			get_tree().set_input_as_handled()
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			# Zoom out
			zoom = Vector2(min(max_zoom, zoom.x + zoom_speed), min(max_zoom, zoom.y + zoom_speed))
			get_tree().set_input_as_handled()
		elif event.button_index == MOUSE_BUTTON_MIDDLE:
			# Middle mouse button for pan
			if event.pressed:
				dragging = true
				drag_start = position
				drag_current = get_global_mouse_position()
			else:
				dragging = false
	
	# Update drag position
	elif event is InputEventMouseMotion and dragging:
		drag_current = get_global_mouse_position()
	
	# Handle key presses
	elif event is InputEventKey:
		if event.pressed:
			if event.keycode == KEY_SPACE:
				# Reset zoom
				zoom = Vector2.ONE
			elif event.keycode == KEY_ESCAPE:
				# Stop following
				following = false

# Function to focus on a specific position
func focus_on(pos):
	position = pos
	following = false

# Function to change zoom level
func set_zoom_level(level):
	zoom = Vector2(level, level)

# Function to follow a node
func follow(node):
	if node and is_instance_valid(node):
		target = node
		following = true
