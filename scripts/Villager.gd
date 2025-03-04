# Villager.gd - Controls villager behavior
extends CharacterBody2D

# Villager properties
var villager_name = "Unnamed"
var age = 25
var gender = "Male"
var health = 100
var energy = 100
var hunger = 0
var happiness = 100

# Home and work references
var home = null
var workplace = null
var current_destination = null

# Behavior state machine
enum State { IDLE, WALKING, WORKING, SHOPPING, SLEEPING, EATING }
var current_state = State.IDLE
var previous_state = State.IDLE

# Movement
var speed = 100
var path = []
var path_index = 0
var reached_destination = true

# Daily schedule
var wake_time = 6.0
var work_start_time = 8.0
var work_end_time = 17.0
var sleep_time = 22.0

# Inventory
var inventory = []
var money = 100

# Relationships
var friends = []
var family = []

# Signals
signal state_changed(old_state, new_state)
signal destination_reached()  # Renamed from reached_destination to avoid conflict

func _ready():
	# Set random properties
	randomize_appearance()
	
	# Initialize name
	villager_name = generate_name()
	
	# Initialize the villager's timer for periodic updates
	var timer = $Timer
	if timer:
		timer.connect("timeout", Callable(self, "_on_timer_timeout"))
		timer.start(1.0)
	else:
		print("ERROR: Timer node not found for " + name)
		
	# Add to villager group for easy access
	add_to_group("villagers")

func _process(delta):
	# Update villager state based on village time
	update_state_from_time()
	
	# Handle movement if we have a path
	if current_state == State.WALKING and path.size() > 0 and path_index < path.size():
		move_along_path(delta)

func initialize(home_building, work_building):
	# Set home and workplace
	home = home_building
	workplace = work_building
	
	# Add this villager to building occupants if applicable
	if home and home.has_method("add_occupant"):
		home.add_occupant(self)
	
	if workplace and workplace.has_method("add_employee"):
		workplace.add_employee(self)
	
	# Debug log
	print("Villager " + villager_name + " initialized with home: " + 
		(home.name if home else "None") + " and workplace: " + 
		(workplace.name if workplace else "None"))

func _on_timer_timeout():
	# This function is called every second to update the villager's state
	match current_state:
		State.IDLE:
			# Chance to wander
			if randf() < 0.2:  # 20% chance every second
				wander()
		
		State.WORKING:
			# Work actions
			if workplace and "income" in workplace:
				workplace.income += 1  # Generate income for the shop
				
			# Get tired from working
			energy = max(energy - 1, 0)
			
			# Get hungry from working
			hunger = min(hunger + 0.5, 100)
		
		State.SLEEPING:
			# Recover energy while sleeping
			energy = min(energy + 2, 100)
			
		State.EATING:
			# Reduce hunger
			hunger = max(hunger - 5, 0)
			
			# Finish eating after a short while
			if hunger <= 20:
				set_state(State.IDLE)
				
	# Update needs
	update_needs(0.1)  # Small changes each second

func randomize_appearance():
	# Randomize age
	age = randi() % 60 + 18  # 18-78 years old
	
	# Randomize gender
	if randf() < 0.5:
		gender = "Male"
	else:
		gender = "Female"

func generate_name():
	var male_names = ["John", "Michael", "William", "James", "Robert", "Thomas"]
	var female_names = ["Mary", "Elizabeth", "Susan", "Sarah", "Karen", "Lisa"]
	var surnames = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller"]
	
	var first_name = ""
	if gender == "Male":
		first_name = male_names[randi() % male_names.size()]
	else:
		first_name = female_names[randi() % female_names.size()]
	
	var surname = surnames[randi() % surnames.size()]
	
	return first_name + " " + surname

func update_needs(amount):
	# Natural decreases in energy and increases in hunger over time
	energy = max(energy - amount, 0)
	hunger = min(hunger + amount, 100)
	
	# Update happiness based on needs
	var avg_needs = (energy + (100 - hunger)) / 2
	happiness = lerp(float(happiness), avg_needs, 0.01)

func set_state(new_state):
	if new_state != current_state:
		previous_state = current_state
		current_state = new_state
		emit_signal("state_changed", previous_state, current_state)
		
		# Debug log state change
		print("Villager " + villager_name + " changed state from " + 
			state_to_string(previous_state) + " to " + state_to_string(current_state))

func update_state_from_time():
	# Get time from village
	var village = get_parent()
	if not village or not "time_of_day" in village:
		return
		
	var time_of_day = village.time_of_day
	
	# State changes based on time
	if time_of_day >= wake_time and time_of_day < work_start_time:
		# Morning routine
		if current_state == State.SLEEPING:
			set_state(State.IDLE)
			# Move to workplace when waking up
			if workplace:
				move_to(workplace.position)
				set_state(State.WALKING)
	
	elif time_of_day >= work_start_time and time_of_day < work_end_time:
		# Work time
		if current_state != State.WORKING and current_state != State.WALKING:
			if workplace:
				move_to(workplace.position)
				set_state(State.WALKING)
				
		# Check if arrived at workplace
		if current_state == State.WALKING and reached_destination and is_at_workplace():
			set_state(State.WORKING)
	
	elif time_of_day >= work_end_time and time_of_day < sleep_time:
		# Evening routine
		if current_state == State.WORKING:
			set_state(State.IDLE)
			
			# Head home after work
			if home:
				move_to(home.position)
				set_state(State.WALKING)
				
		# Check if arrived at home
		if current_state == State.WALKING and reached_destination and is_at_home():
			set_state(State.IDLE)
			
			# Eat if hungry
			if hunger > 50:
				set_state(State.EATING)
	
	elif time_of_day >= sleep_time or time_of_day < wake_time:
		# Night time - sleep
		if current_state != State.SLEEPING and is_at_home():
			set_state(State.SLEEPING)
		elif current_state != State.SLEEPING and current_state != State.WALKING:
			# Go home to sleep
			if home:
				move_to(home.position)
				set_state(State.WALKING)

func move_to(target_position):
	# Request a path from navigation
	request_path(position, target_position)

func request_path(start_pos, end_pos):
	# No matter what happens, we'll try to move the character
	path = [end_pos]  # Direct path to destination
	path_index = 0
	reached_destination = false
	current_destination = end_pos
	set_state(State.WALKING)
	
	# Now try to get a proper path if navigation exists
	var nav_map = get_world_2d().navigation_map
	var nav_path = NavigationServer2D.map_get_path(nav_map, start_pos, end_pos, true)
	
	if nav_path.size() > 0:
		# We got a proper path, use it
		path = nav_path
		print("Villager " + villager_name + " found a path with " + str(path.size()) + " points")
	else:
		# No path found, use direct path but print warning
		print("INFO: Using direct path for " + villager_name)

func get_scene_navigation():
	# Find navigation in the scene
	var village = get_parent()
	if village and village.has_node("NavigationRegion2D"):
		return village.get_node("NavigationRegion2D")
	return null

func move_along_path(delta):
	if path.size() == 0 or path_index >= path.size():
		# We've reached the end of the path or have no path
		reached_destination = true
		path = []
		path_index = 0
		velocity = Vector2.ZERO
		emit_signal("destination_reached")  # Updated signal name
		return

	# Get the next point in the path
	var target = path[path_index]

	# Calculate direction and distance to the target
	var direction = (target - position).normalized()
	var distance = position.distance_to(target)

	# Set velocity based on direction and speed
	velocity = direction * speed

	# Check if close enough to the target to move to next point
	if distance < 10: # Slightly larger threshold to prevent getting stuck
		path_index += 1
		
		# If we reached the last point, signal completion
		if path_index >= path.size():
			reached_destination = true
			path = []
			velocity = Vector2.ZERO
			emit_signal("destination_reached")
			return
		
		# Get next target
		if path_index < path.size():
			target = path[path_index]
	
	# Move character
	position += velocity * delta  # Direct position update
	
	# Visual feedback 
	if direction.x > 0:
		# Facing right
		if $Sprite2D:
			$Sprite2D.flip_h = false
	elif direction.x < 0:
		# Facing left
		if $Sprite2D:
			$Sprite2D.flip_h = true

func wander():
	# Pick a random point nearby
	var wander_distance = 200
	var random_offset = Vector2(
		randf_range(-wander_distance, wander_distance),
		randf_range(-wander_distance, wander_distance)
	)
	
	var target_pos = position + random_offset
	
	# Ensure we stay within village bounds
	var village = get_parent()
	if village and "village_width" in village and "village_height" in village:
		target_pos.x = clamp(target_pos.x, 0, village.village_width)
		target_pos.y = clamp(target_pos.y, 0, village.village_height)
	
	# Move there
	move_to(target_pos)

func is_at_home():
	if home:
		return position.distance_to(home.position) < 50
	return false

func is_at_workplace():
	if workplace:
		return position.distance_to(workplace.position) < 50
	return false

func on_click():
	# Handle being clicked on in the UI
	print("Villager " + villager_name + " clicked!")
	
	# Show UI for this villager if available
	var ui = get_parent().get_node_or_null("UI")
	if ui and ui.has_method("show_villager_info"):
		ui.show_villager_info(self)

func get_state_string():
	return state_to_string(current_state)

func state_to_string(state_enum):
	match state_enum:
		State.IDLE: return "Idle"
		State.WALKING: return "Walking"
		State.WORKING: return "Working"
		State.SHOPPING: return "Shopping"
		State.SLEEPING: return "Sleeping"
		State.EATING: return "Eating"
		_: return "Unknown"

func add_to_inventory(item):
	inventory.append(item)

func get_rect():
	var texture_size = Vector2(32, 32)
	if $Sprite2D and $Sprite2D.texture:
		texture_size = $Sprite2D.texture.get_size() * $Sprite2D.scale
	
	return Rect2(position - texture_size/2, texture_size)

func get_data():
	return {
		"id": name,
		"name": villager_name,
		"age": age,
		"gender": gender,
		"health": health,
		"energy": energy,
		"hunger": hunger,
		"happiness": happiness,
		"state": get_state_string(),
		"home": home.name if home else "None",
		"workplace": workplace.name if workplace else "None",
		"position": {"x": position.x, "y": position.y},
		"inventory": inventory,
		"money": money
	}
