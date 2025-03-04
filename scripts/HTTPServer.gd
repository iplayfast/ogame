# HTTPServer.gd - Custom REST API server implementation
extends Node

var server = TCPServer.new()
var port = 8080
var connections = []

# Use a preload for HTTPResponse with a class_name
const HTTPResponse = preload("res://scripts/HTTPResponse.gd")

signal request_received(request, response)

func _ready():
	set_process(true)

func start():
	var err = server.listen(port)
	if err != OK:
		print("Error starting server: ", err)
		return false
	
	print("REST API server started on port ", port)
	return true

func stop():
	server.stop()
	for connection in connections:
		connection.disconnect_from_host()
	connections.clear()

func _process(_delta):
	if server.is_connection_available():
		var connection = server.take_connection()
		connections.append(connection)
	
	for i in range(connections.size() - 1, -1, -1):
		var connection = connections[i]
		if !connection.is_connected_to_host():
			connections.remove_at(i)
			continue
		
		if connection.get_available_bytes() > 0:
			handle_connection(connection)
			connections.remove_at(i)

func handle_connection(connection):
	var request_data = connection.get_string(connection.get_available_bytes())
	var request = parse_request(request_data)
	var response = HTTPResponse.new(connection)
	
	emit_signal("request_received", request, response)

func parse_request(request_data):
	var lines = request_data.split("\r\n")
	var request = {"headers": {}, "body": ""}
	
	if lines.size() > 0:
		var first_line = lines[0].split(" ")
		if first_line.size() >= 3:
			request["method"] = first_line[0]
			request["url"] = first_line[1]
			request["version"] = first_line[2]
	
	var reading_headers = true
	for i in range(1, lines.size()):
		var line = lines[i]
		
		if reading_headers:
			if line.empty():
				reading_headers = false
				continue
			
			var header_parts = line.split(": ", true, 1)
			if header_parts.size() == 2:
				request["headers"][header_parts[0]] = header_parts[1]
		else:
			request["body"] += line + "\r\n"
	
	return request
