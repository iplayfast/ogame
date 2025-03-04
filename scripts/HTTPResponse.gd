# HTTPResponse.gd - Helper class for HTTP responses
extends RefCounted

var connection
var status_code = 200
var headers = {
	"Content-Type": "application/json",
	"Access-Control-Allow-Origin": "*"
}

func _init(conn):
	connection = conn

func send_text(text, content_type = "text/plain"):
	headers["Content-Type"] = content_type
	var header = "HTTP/1.1 %d OK\r\n" % status_code
	
	for key in headers:
		header += "%s: %s\r\n" % [key, headers[key]]
	
	header += "Content-Length: %d\r\n\r\n" % text.length()
	connection.put_data((header + text).to_utf8())

func send_json(data):
	var json_text = JSON.stringify(data)
	send_text(json_text, "application/json")
