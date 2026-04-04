class_name QuantumApiClient
extends Node

const DEFAULT_BASE_URL := "https://davidjgrimsley.com/public-facing/api/quantum/v1"
const DIRECT_API_KEY := ""

var base_url: String = DEFAULT_BASE_URL
var api_key: String = DIRECT_API_KEY
var backend_proxy_mode: bool = DIRECT_API_KEY.is_empty()

func _init(custom_base_url: String = DEFAULT_BASE_URL, custom_api_key: String = DIRECT_API_KEY, use_backend_proxy: bool = DIRECT_API_KEY.is_empty()) -> void:
	base_url = _normalize_base_url(custom_base_url)
	api_key = custom_api_key.strip_edges()
	backend_proxy_mode = use_backend_proxy

func set_base_url(url: String) -> void:
	base_url = _normalize_base_url(url)

func set_api_key(key: String) -> void:
	api_key = key.strip_edges()

func set_backend_proxy_mode(enabled: bool) -> void:
	backend_proxy_mode = enabled

func health_check(callback: Callable) -> void:
	_request_json("/health", HTTPClient.METHOD_GET, null, callback, false)

func transform_text(text: String, callback: Callable, fallback_text: String = "") -> void:
	_request_json(
		"/text/transform",
		HTTPClient.METHOD_POST,
		{"text": text},
		func(success: bool, payload: Dictionary) -> void:
			if success:
				callback.call(true, payload)
				return
			var fallback := {
				"original": text,
				"transformed": fallback_text if !fallback_text.is_empty() else text,
				"message": payload.get("message", "Text transform failed"),
				"status_code": payload.get("status_code", 0),
			}
			callback.call(false, fallback)
		,
		true,
	)

func run_gate(gate_type: String, callback: Callable, rotation_angle_rad: Variant = null) -> void:
	var payload: Dictionary = {
		"gate_type": gate_type,
	}
	if rotation_angle_rad != null:
		payload["rotation_angle_rad"] = rotation_angle_rad

	_request_json("/gates/run", HTTPClient.METHOD_POST, payload, callback, true)

func _request_json(
	endpoint_path: String,
	method: int,
	payload: Variant,
	callback: Callable,
	requires_api_key: bool,
) -> void:
	if requires_api_key and !backend_proxy_mode and api_key.is_empty():
		callback.call(
			false,
			{
				"error": "missing_api_key",
				"message": "Direct API-key mode is enabled, but no Quantum API key is configured.",
				"status_code": 0,
			},
		)
		return

	var http_request := HTTPRequest.new()
	add_child(http_request)

	http_request.request_completed.connect(
		func(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
			var parsed := _parse_response(result, response_code, body)
			http_request.queue_free()
			callback.call(parsed["success"], parsed["payload"])
	)

	var body_string := ""
	var headers := _build_headers(requires_api_key, payload != null)
	if payload != null:
		body_string = JSON.stringify(payload)

	var error := http_request.request(base_url + endpoint_path, headers, method, body_string)
	if error != OK:
		http_request.queue_free()
		callback.call(
			false,
			{
				"error": "request_failed",
				"message": "Failed to start HTTP request",
				"status_code": error,
			},
		)

func _build_headers(requires_api_key: bool, include_json_content_type: bool) -> PackedStringArray:
	var headers: PackedStringArray = []
	if include_json_content_type:
		headers.append("Content-Type: application/json")
	if requires_api_key and !backend_proxy_mode and !api_key.is_empty():
		headers.append("X-API-Key: " + api_key)
	return headers

func _parse_response(result: int, response_code: int, body: PackedByteArray) -> Dictionary:
	var response_text := body.get_string_from_utf8()
	var payload: Dictionary = {}

	if !response_text.is_empty():
		var json := JSON.new()
		if json.parse(response_text) == OK and json.data is Dictionary:
			payload = json.data

	if response_code >= 200 and response_code < 300:
		return {"success": true, "payload": payload}

	if payload.is_empty():
		payload = {
			"error": "http_error",
			"message": response_text if !response_text.is_empty() else "Quantum API request failed",
		}

	payload["result"] = result
	payload["status_code"] = response_code
	return {"success": false, "payload": payload}

func _normalize_base_url(url: String) -> String:
	var normalized := url.strip_edges().trim_suffix("/")
	if normalized.ends_with("/v1"):
		return normalized
	return normalized + "/v1"
