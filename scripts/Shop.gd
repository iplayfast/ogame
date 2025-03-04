# Shop.gd - Extends Building with shop functionality
extends "res://scripts/Building.gd"

# Shop properties
var shop_type = "General Store"
var shop_level = 1  # 1-3 scale for shop upgrades
var max_occupants = 3
var max_customers = 5
var current_customers = []

# Shop owner
var shop_owner = null  # Reference to villager who owns this shop (renamed from 'owner')
var employees = []

# Business variables
var income = 0.0
var daily_income = 0.0
var expenses = 5.0  # Base daily expenses
var shop_hours = {"open": 8, "close": 18}  # 8 AM to 6 PM

# Inventory
var inventory = []
var max_inventory = 20
var prices = {}
var restocking = false

# Shop types and their default inventories
var shop_types = {
	"Bakery": ["Bread", "Cake", "Pastry", "Pie", "Cookies"],
	"Blacksmith": ["Sword", "Shield", "Hammer", "Nails", "Horseshoe"],
	"General Store": ["Rope", "Lamp", "Cloth", "Tools", "Food"],
	"Tavern": ["Ale", "Wine", "Stew", "Roast", "Cheese"],
	"Apothecary": ["Herbs", "Potions", "Bandages", "Remedies", "Tonics"]
}

func _ready():
	super._ready()
	building_type = "Shop"
	
	# Randomly select shop type
	var types = shop_types.keys()
	shop_type = types[randi() % types.size()]
	
	# Set building name based on shop type
	building_name = shop_type
	
	# Generate inventory based on shop type
	generate_inventory()
	
	# Add a light that dims at night
	var light = PointLight2D.new()
	light.texture = load("res://assets/sprites/light.png")
	light.energy = 0.8
	light.enabled = false
	light.name = "ShopLight"
	add_child(light)
	
	# Add shop sign (visual indicator)
	var sign = Sprite2D.new()
	if ResourceLoader.exists("res://assets/sprites/shop_sign.png"):
		sign.texture = load("res://assets/sprites/shop_sign.png")
		sign.position = Vector2(0, -40)  # Position above the shop
		sign.name = "ShopSign"
		add_child(sign)

func _process(delta):
	# Update open/closed status based on time
	update_open_status()
	
	# Process customers
	if is_open():
		# Chance to generate income from customers
		process_customers(delta)
		
		# Check if we need to restock
		if inventory.size() < max_inventory / 2 and !restocking:
			start_restocking()
	
	# Process restocking
	if restocking:
		process_restocking(delta)

func update_open_status():
	# Get the time from village
	var time_of_day = 12.0  # Default to noon
	var parent = get_parent().get_node('UI')
	if parent and "time_of_day" in parent:
		time_of_day = parent.time_of_day
	
	# Check if shop is open
	var open = time_of_day >= shop_hours.open and time_of_day < shop_hours.close
	
	# Update light based on open status
	if has_node("ShopLight"):
		$ShopLight.enabled = open or (time_of_day >= 18.0 or time_of_day < 6.0)
	
	# Update sign visibility based on open status
	if has_node("ShopSign"):
		$ShopSign.modulate = Color(1.0, 1.0, 0.2) if open else Color(0.5, 0.5, 0.5)

func is_open():
	# Get the time from village
	var time_of_day = 12.0  # Default to noon
	var parent = get_parent()
	if parent and "time_of_day" in parent:
		time_of_day = parent.time_of_day
	
	# Check if shop is open based on time
	return time_of_day >= shop_hours.open and time_of_day < shop_hours.close

func generate_inventory():
	# Clear existing inventory
	inventory.clear()
	prices.clear()
	
	# Get items for this shop type
	var shop_items = []
	if shop_type in shop_types:
		shop_items = shop_types[shop_type]
	
	# Generate a random number of items
	var num_items = randi() % 10 + 5  # 5-15 items
	
	for i in range(num_items):
		# Select a random item from the shop's possible inventory
		var item = shop_items[randi() % shop_items.size()]
		
		# Add to inventory
		inventory.append(item)
		
		# Set a random price (1-10 gold)
		prices[item] = randi() % 10 + 1
	
	# Ensure we don't have exact duplicates (though similar items are fine)
	inventory = Array(inventory)  # Convert back to array to remove duplicates

func add_customer(villager):
	if current_customers.size() < max_customers and !current_customers.has(villager):
		current_customers.append(villager)
		return true
	return false

func remove_customer(villager):
	if current_customers.has(villager):
		current_customers.erase(villager)
		return true
	return false

func process_customers(delta):
	# Process income from existing customers
	for customer in current_customers:
		# Each customer has a small chance to generate income each frame
		if randf() < 0.01 * delta:
			var purchase_amount = randi() % 5 + 1  # 1-5 gold
			income += purchase_amount
			daily_income += purchase_amount
			
			# Remove an item from inventory if available
			if inventory.size() > 0:
				var item_index = randi() % inventory.size()
				var item = inventory[item_index]
				inventory.remove_at(item_index)
				
				# Notify customer of purchase if they have a method for it
				if customer.has_method("add_to_inventory"):
					customer.add_to_inventory(item)

func start_restocking():
	restocking = true
	# Set a timer for restocking completion
	if has_node("RestockTimer"):
		$RestockTimer.start(10.0)  # Restocking takes 10 seconds

func process_restocking(delta):
	# Check if restocking is complete
	if has_node("RestockTimer") and $RestockTimer.is_stopped():
		# Restock complete!
		restocking = false
		generate_inventory()

func upgrade():
	if shop_level < 3:
		shop_level += 1
		max_inventory += 10
		max_customers += 2
		
		# Update appearance
		match shop_level:
			2:
				modulate = Color(1.1, 1.1, 1.0)  # Slightly brighter
			3:
				modulate = Color(1.2, 1.2, 1.0)  # Even brighter
				
				# Add particle effect for high-level shop
				var particles = CPUParticles2D.new()
				particles.amount = 10
				particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
				particles.emission_rect_extents = Vector2(20, 5)
				particles.gravity = Vector2(0, -10)
				particles.color = Color(1.0, 0.8, 0.0, 0.5)
				particles.position = Vector2(0, -20)
				add_child(particles)
		
		return true
	
	return false

func add_employee(villager):
	if !employees.has(villager):
		employees.append(villager)
		# Increase shop productivity with more employees
		max_customers += 1
		return true
	return false

func remove_employee(villager):
	if employees.has(villager):
		employees.erase(villager)
		# Decrease shop productivity with fewer employees
		max_customers = max(3, max_customers - 1)
		return true
	return false

func calculate_daily_profit():
	var profit = daily_income - expenses
	
	# Reset daily income for next day
	daily_income = 0
	
	# Adjust expenses based on shop level and employee count
	expenses = 5.0 + (shop_level - 1) * 2 + employees.size() * 3
	
	return profit

func get_inventory():
	return inventory

func get_data():
	var data = super.get_data()
	
	# Add shop-specific data
	data["shop_type"] = shop_type
	data["shop_level"] = shop_level
	data["is_open"] = is_open()
	data["inventory"] = inventory
	
	# Add price data
	var price_data = {}
	for item in prices:
		price_data[item] = prices[item]
	data["prices"] = price_data
	
	# Add business data
	data["daily_income"] = daily_income
	data["expenses"] = expenses
	
	# Add customer data
	var customer_names = []
	for customer in current_customers:
		customer_names.append(customer.villager_name)
	data["customers"] = customer_names
	
	# Add employee data
	var employee_names = []
	for employee in employees:
		employee_names.append(employee.villager_name)
	data["employees"] = employee_names
	
	return data

func on_click():
	# Show shop info in UI
	super.on_click()  # Call parent method
	
	# Perform any shop-specific click actions here
	if has_node("ShopLight"):
		# Toggle lights when clicked (for testing)
		$ShopLight.enabled = !$ShopLight.enabled

# Make sure we have the appropriate timer for restocking
func _enter_tree():
	if !has_node("RestockTimer"):
		var timer = Timer.new()
		timer.name = "RestockTimer"
		timer.one_shot = true
		add_child(timer)
