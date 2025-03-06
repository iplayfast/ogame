# Main.gd - This handles game initialization and scene transitions
extends Node

var current_scene = null
var game_speed = 1.0
var paused = false

func _ready():
	# Set up randomization
	randomize()
	
	# Get the current scene
	var root = get_tree().root
	current_scene = get_tree().current_scene
	
	# Check if we need to load the village
	if current_scene.name != "Village":
		load_village()
	
	# Connect input for game speed control
	set_process_input(true)

func _input(event):
	# Game speed controls
	if event.is_action_pressed("game_pause"):
		toggle_pause()
	elif event.is_action_pressed("game_speed_up"):
		increase_game_speed()
	elif event.is_action_pressed("game_speed_down"):
		decrease_game_speed()

func toggle_pause():
	paused = !paused
	get_tree().paused = paused
	
	# Show pause indicator if implemented
	if has_node("UI/PauseIndicator"):
		get_node("UI/PauseIndicator").visible = paused

func increase_game_speed():
	game_speed = min(game_speed + 0.5, 3.0)
	update_game_speed()

func decrease_game_speed():
	game_speed = max(game_speed - 0.5, 0.5)
	update_game_speed()

func update_game_speed():
	# Update game speed - for our simulation we'll adjust the timer durations
	for villager in get_tree().get_nodes_in_group("villagers"):
		if villager.has_node("Timer"):
			villager.get_node("Timer").wait_time = 1.0 / game_speed
	
	# Show speed indicator if implemented
	if has_node("UI/SpeedIndicator"):
		get_node("UI/SpeedIndicator").text = "Speed: x" + str(game_speed)

func load_village():
	call_deferred("_deferred_load_village")

func _deferred_load_village():
	# Clean up the current scene
	if current_scene:
		current_scene.queue_free()

	# Load the village scene
	var village_scene = load("res://scenes/Village.tscn")
	current_scene = village_scene.instantiate()

	# Add it to the tree
	get_tree().root.add_child(current_scene)
	get_tree().current_scene = current_scene

	# Position the camera at the center of the village
	var camera = current_scene.get_node("Camera2D")
	if camera:
		camera.position = Vector2(current_scene.village_width/2, current_scene.village_height/2)
		print("Camera positioned at: ", camera.position)

	print("Village scene loaded successfully")

func restart_game():
	# For restart functionality
	load_village()

func save_game():
	# This is where you would implement save game functionality
	# For now, it's just a placeholder
	print("Save game functionality not yet implemented")

func load_game():
	# This is where you would implement load game functionality
	# For now, it's just a placeholder
	print("Load game functionality not yet implemented")
