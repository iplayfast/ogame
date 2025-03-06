extends Node2D

func _ready():
	print("Generating placeholder sprites...")
	
	# Create the basic sprites with solid colors
	create_simple_sprite("res://assets/sprites/house.png", Color(0.7, 0.4, 0.3))
	create_simple_sprite("res://assets/sprites/house_small.png", Color(0.65, 0.4, 0.3))
	create_simple_sprite("res://assets/sprites/house_medium.png", Color(0.7, 0.45, 0.3))
	create_simple_sprite("res://assets/sprites/house_large.png", Color(0.75, 0.5, 0.3))
	create_simple_sprite("res://assets/sprites/house_farm.png", Color(0.7, 0.5, 0.25))
	create_simple_sprite("res://assets/sprites/shop.png", Color(0.3, 0.5, 0.7))
	create_simple_sprite("res://assets/sprites/villager.png", Color(0.9, 0.7, 0.5))
	create_simple_sprite("res://assets/sprites/light.png", Color(1.0, 1.0, 0.8, 0.7), Vector2(128, 128))
	
	# Create terrain tileset image
	create_terrain_sprite()
	
	print("Sprite generation complete!")
	get_tree().quit()

func create_simple_sprite(path, color, size = Vector2(64, 64)):
	var img = Image.create(int(size.x), int(size.y), false, Image.FORMAT_RGBA8)
	img.fill(color)
	
	# Save the image
	var err = img.save_png(path)
	if err == OK:
		print("Created sprite: " + path)
	else:
		print("Failed to create sprite: " + path + ", error: " + str(err))

func create_terrain_sprite():
	var img = Image.create(128, 128, false, Image.FORMAT_RGBA8)
	
	# Fill the 4 quadrants with different colors
	# Top-left: grass
	for x in range(64):
		for y in range(64):
			img.set_pixel(x, y, Color(0.2, 0.7, 0.2))
			
	# Top-right: water
	for x in range(64, 128):
		for y in range(64):
			img.set_pixel(x, y, Color(0.2, 0.4, 0.8))
			
	# Bottom-left: path
	for x in range(64):
		for y in range(64, 128):
			img.set_pixel(x, y, Color(0.6, 0.5, 0.3))
			
	# Bottom-right: stone
	for x in range(64, 128):
		for y in range(64, 128):
			img.set_pixel(x, y, Color(0.5, 0.5, 0.5))
	
	# Save the image
	var err = img.save_png("res://assets/sprites/terrain.png")
	if err == OK:
		print("Created terrain tileset sprite")
	else:
		print("Failed to create terrain sprite, error: " + str(err))
