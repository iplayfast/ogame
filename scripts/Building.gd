# Building.gd - Base class for all buildings
extends StaticBody2D

@export var building_name = "Building"
@export var building_type = "Generic"
var occupants = []

func _ready():
	pass

func get_data():
	# Get list of current occupants
	var current_occupants = []
	for occupant in occupants:
		current_occupants.append(occupant.name)
	
	return {
		"id": name,
		"name": building_name,
		"type": building_type,
		"position": {"x": position.x, "y": position.y},
		"occupants": current_occupants
	}

func on_click():
	# Show building info
	get_parent().get_node('UI')

func get_rect():
	var size = $Sprite2D.texture.get_size() * $Sprite2D.scale
	return Rect2(position - size/2, size)
