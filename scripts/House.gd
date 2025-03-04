# House.gd - Extends Building
extends "res://scripts/Building.gd"

# House properties
var house_type = "Small Cottage"
var house_quality = 1  # 1-5 scale
var max_occupants = 2
var comfort_level = 3  # 1-10 scale
var repair_state = 5   # 1-5 scale (5 = perfect condition)

# Visuals
var house_types = {
	"Small Cottage": {"texture": "house_small.png", "quality": 1, "max_occupants": 2},
	"Family Home": {"texture": "house_medium.png", "quality": 2, "max_occupants": 4},
	"Large House": {"texture": "house_large.png", "quality": 3, "max_occupants": 6},
	"Farmhouse": {"texture": "house_farm.png", "quality": 2, "max_occupants": 4}
}

# Owner info
var house_owner = null  # Reference to the villager who owns this house (renamed from 'owner')
var rent = 10     # Daily rent cost if not owned

# Inventory/storage
var inventory = []
var max_inventory = 10

func _ready():
	super._ready()
	building_type = "House"
	
	# Randomly select a house type
	var types = house_types.keys()
	house_type = types[randi() % types.size()]
	
	# Set building name
	building_name = house_type
	
	# Set properties based on house type
	if house_type in house_types:
		var type_info = house_types[house_type]
		house_quality = type_info.quality
		max_occupants = type_info.max_occupants
		
		# Try to set the texture if it exists
		var texture_path = "res://assets/sprites/" + type_info.texture
		var texture = load(texture_path)
		if texture and $Sprite2D:
			$Sprite2D.texture = texture
	
	# Randomize initial repair state and comfort level
	repair_state = randi() % 3 + 3  # 3-5 (relatively good condition)
	comfort_level = house_quality * 2  # Base comfort on quality
	
	# Add a light that dims at night
	var light = PointLight2D.new()
	light.texture = load("res://assets/sprites/light.png")
	light.energy = 0.5
	light.enabled = false
	light.name = "HouseLight"
	add_child(light)

func _process(delta):
	# Check if lights should be on based on time of day
	update_lights()
	
	# Gradually decay repair state over time
	if randf() < 0.0001:  # Very small chance each frame
		repair_state = max(1, repair_state - 1)
		update_appearance()

func update_lights():
	if has_node("HouseLight"):
		var light = get_node("HouseLight")
		
		# Get time from village
		var time_of_day = 12.0  # Default to noon
		var parent = get_parent()
		if parent and "time_of_day" in parent:
			time_of_day = parent.time_of_day
		
		# Turn lights on at night or early morning
		var lights_on = time_of_day < 6.0 or time_of_day > 18.0
		
		# Also turn on when villagers are home
		if occupants.size() > 0:
			lights_on = lights_on or (time_of_day > 17.0)  # After work hours
		
		light.enabled = lights_on
		
		# Adjust brightness based on time
		if lights_on:
			# Brighter at night, dimmer at dawn/dusk
			if time_of_day < 5.0 or time_of_day > 20.0:
				light.energy = 1.0
			else:
				light.energy = 0.5
		
func update_appearance():
	# Update visuals based on repair state
	if repair_state <= 2:
		# House in disrepair
		modulate = Color(0.7, 0.7, 0.7)
	else:
		modulate = Color(1.0, 1.0, 1.0)
	
	# Could add other visual effects based on house properties

func add_occupant(villager):
	if occupants.size() < max_occupants:
		occupants.append(villager)
		return true
	return false

func remove_occupant(villager):
	if villager in occupants:
		occupants.erase(villager)
		return true
	return false

func repair():
	repair_state = 5  # Fully repaired
	update_appearance()

func upgrade():
	# Upgrade the house to a better type
	var current_index = house_types.keys().find(house_type)
	if current_index < house_types.keys().size() - 1:
		house_type = house_types.keys()[current_index + 1]
		var type_info = house_types[house_type]
		
		# Update properties
		house_quality = type_info.quality
		max_occupants = type_info.max_occupants
		comfort_level = house_quality * 2
		
		# Update visuals
		var texture_path = "res://assets/sprites/" + type_info.texture
		var texture = load(texture_path)
		if texture and $Sprite2D:
			$Sprite2D.texture = texture
		
		# Update name
		building_name = house_type
		
		return true
	
	return false

func add_to_inventory(item):
	if inventory.size() < max_inventory:
		inventory.append(item)
		return true
	return false

func remove_from_inventory(item):
	if item in inventory:
		inventory.erase(item)
		return true
	return false

func get_data():
	var data = super.get_data()  # Get base building data
	
	# Add house-specific data
	data["house_type"] = house_type
	data["quality"] = house_quality
	data["max_occupants"] = max_occupants
	data["comfort"] = comfort_level
	data["repair_state"] = repair_state
	
	if house_owner:
		data["owner"] = house_owner.villager_name
	else:
		data["owner"] = "None"
	
	data["rent"] = rent
	data["inventory"] = inventory
	
	return data

func on_click():
	# Show building info via UI
	super.on_click()  # Call parent method
	
	# Perform any house-specific click actions here
	if has_node("HouseLight"):
		# Toggle lights when clicked (for testing)
		$HouseLight.enabled = !$HouseLight.enabled
