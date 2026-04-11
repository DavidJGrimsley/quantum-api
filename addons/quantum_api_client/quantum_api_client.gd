class_name QuantumApiClient
extends Node

const DEFAULT_BASE_URL := "https://davidjgrimsley.com/public-facing/api/quantum-gateway/v1"
const DIRECT_API_KEY := ""
const PUBLISHABLE_GATEWAY_CLIENT_KEY := ""
const DEFAULT_IBM_PROFILE := ""
const SETTINGS_BASE_URL := "quantum_api/base_url"
const SETTINGS_BACKEND_PROXY_MODE := "quantum_api/backend_proxy_mode"
const SETTINGS_DIRECT_API_KEY := "quantum_api/direct_api_key"
const SETTINGS_PUBLISHABLE_GATEWAY_CLIENT_KEY := "quantum_api/publishable_gateway_client_key"
const SETTINGS_DEFAULT_IBM_PROFILE := "quantum_api/default_ibm_profile"
const DEFAULT_BACKEND_PROXY_MODE := false
const RUNTIME_TOKEN_REFRESH_BUFFER_SECONDS := 15.0

var base_url: String = DEFAULT_BASE_URL
var api_key: String = DIRECT_API_KEY
var publishable_gateway_client_key: String = PUBLISHABLE_GATEWAY_CLIENT_KEY
var default_ibm_profile: String = DEFAULT_IBM_PROFILE
var backend_proxy_mode: bool = DEFAULT_BACKEND_PROXY_MODE
var runtime_token: String = ""
var runtime_token_expires_at_unix: float = 0.0
var runtime_project_id: String = ""

func _init(
	custom_base_url: String = DEFAULT_BASE_URL,
	custom_api_key: String = DIRECT_API_KEY,
	use_backend_proxy: bool = DEFAULT_BACKEND_PROXY_MODE,
	custom_default_ibm_profile: String = DEFAULT_IBM_PROFILE,
	custom_publishable_gateway_client_key: String = PUBLISHABLE_GATEWAY_CLIENT_KEY,
) -> void:
	base_url = _normalize_base_url(custom_base_url)
	api_key = custom_api_key.strip_edges()
	default_ibm_profile = custom_default_ibm_profile.strip_edges()
	backend_proxy_mode = use_backend_proxy
	publishable_gateway_client_key = custom_publishable_gateway_client_key.strip_edges()

func set_base_url(url: String) -> void:
	base_url = _normalize_base_url(url)
	clear_runtime_token()

func set_api_key(key: String) -> void:
	api_key = key.strip_edges()
	if !api_key.is_empty():
		clear_runtime_token()

func set_publishable_gateway_client_key(key: String) -> void:
	publishable_gateway_client_key = key.strip_edges()
	clear_runtime_token()

func set_default_ibm_profile(profile_name: String) -> void:
	default_ibm_profile = profile_name.strip_edges()

func set_backend_proxy_mode(enabled: bool) -> void:
	backend_proxy_mode = enabled
	if backend_proxy_mode:
		clear_runtime_token()

func clear_runtime_token() -> void:
	runtime_token = ""
	runtime_token_expires_at_unix = 0.0
	runtime_project_id = ""

func apply_project_settings() -> void:
	var configured_base_url := str(ProjectSettings.get_setting(SETTINGS_BASE_URL, DEFAULT_BASE_URL)).strip_edges()
	if configured_base_url.is_empty():
		configured_base_url = DEFAULT_BASE_URL

	set_base_url(configured_base_url)
	set_backend_proxy_mode(
		_variant_to_bool(
			ProjectSettings.get_setting(SETTINGS_BACKEND_PROXY_MODE, DEFAULT_BACKEND_PROXY_MODE),
			DEFAULT_BACKEND_PROXY_MODE
		)
	)
	set_api_key(str(ProjectSettings.get_setting(SETTINGS_DIRECT_API_KEY, DIRECT_API_KEY)).strip_edges())
	set_publishable_gateway_client_key(
		str(
			ProjectSettings.get_setting(
				SETTINGS_PUBLISHABLE_GATEWAY_CLIENT_KEY,
				PUBLISHABLE_GATEWAY_CLIENT_KEY
			)
		).strip_edges()
	)
	set_default_ibm_profile(str(ProjectSettings.get_setting(SETTINGS_DEFAULT_IBM_PROFILE, DEFAULT_IBM_PROFILE)).strip_edges())

func get_default_base_url() -> String:
	return DEFAULT_BASE_URL

func get_config_snapshot() -> Dictionary:
	return {
		"base_url": base_url,
		"backend_proxy_mode": backend_proxy_mode,
		"api_key_present": !api_key.is_empty(),
		"publishable_gateway_client_key_present": !publishable_gateway_client_key.is_empty(),
		"default_ibm_profile": default_ibm_profile,
		"runtime_token_present": !runtime_token.is_empty(),
		"runtime_project_id": runtime_project_id,
	}

func health_check(callback: Callable) -> void:
	_request_json("/health", HTTPClient.METHOD_GET, null, callback, false)

func mint_runtime_token(callback: Callable, client_session_id: String = "") -> void:
	_ensure_runtime_token(callback, true, client_session_id)

func transform_text(text: String, callback: Callable, fallback_text: String = "") -> void:
	var wrapped_callback := func(success: bool, payload: Dictionary) -> void:
		if success:
			callback.call(true, payload)
			return

		var fallback_payload: Dictionary = payload.duplicate(true)
		fallback_payload["original"] = text
		fallback_payload["transformed"] = fallback_text if !fallback_text.is_empty() else text
		if !fallback_payload.has("message"):
			fallback_payload["message"] = "Text transform failed"
		if !fallback_payload.has("status_code"):
			fallback_payload["status_code"] = 0
		callback.call(false, fallback_payload)

	_request_json(
		"/text/transform",
		HTTPClient.METHOD_POST,
		{"text": text},
		wrapped_callback,
		true,
	)

func run_gate(gate_type: String, callback: Callable, rotation_angle_rad: Variant = null) -> void:
	var payload: Dictionary = {
		"gate_type": gate_type,
	}
	if rotation_angle_rad != null:
		payload["rotation_angle_rad"] = rotation_angle_rad

	_request_json("/gates/run", HTTPClient.METHOD_POST, payload, callback, true)

func list_backends(
	callback: Callable,
	provider: String = "",
	simulator_only: bool = false,
	min_qubits: int = 1,
	ibm_profile: String = "",
) -> void:
	var normalized_provider := provider.strip_edges().to_lower()
	var resolved_profile := ibm_profile.strip_edges()
	if resolved_profile.is_empty() and normalized_provider == "ibm":
		resolved_profile = _resolve_optional_ibm_profile()

	var query: Dictionary = {
		"simulator_only": simulator_only,
		"min_qubits": min_qubits if min_qubits >= 1 else 1,
	}
	if !normalized_provider.is_empty():
		query["provider"] = normalized_provider
	if !resolved_profile.is_empty():
		query["ibm_profile"] = resolved_profile

	_request_json("/list_backends", HTTPClient.METHOD_GET, null, callback, true, query)

func transpile(payload: Dictionary, callback: Callable, ibm_profile: String = "") -> void:
	var request_payload: Dictionary = payload.duplicate(true)
	_apply_optional_ibm_profile(request_payload, ibm_profile)
	_request_json("/transpile", HTTPClient.METHOD_POST, request_payload, callback, true)

func submit_circuit_job(payload: Dictionary, callback: Callable, ibm_profile: String = "") -> void:
	var request_payload: Dictionary = payload.duplicate(true)
	_apply_optional_ibm_profile(request_payload, ibm_profile, true)
	_request_json("/jobs/circuits", HTTPClient.METHOD_POST, request_payload, callback, true)

func get_circuit_job(job_id: String, callback: Callable) -> void:
	var normalized_job_id := job_id.strip_edges()
	if normalized_job_id.is_empty():
		callback.call(false, {
			"error": "invalid_job_id",
			"message": "Job id is required.",
			"status_code": 400,
		})
		return

	_request_json("/jobs/" + normalized_job_id.uri_encode(), HTTPClient.METHOD_GET, null, callback, true)

func get_circuit_job_result(job_id: String, callback: Callable) -> void:
	var normalized_job_id := job_id.strip_edges()
	if normalized_job_id.is_empty():
		callback.call(false, {
			"error": "invalid_job_id",
			"message": "Job id is required.",
			"status_code": 400,
		})
		return

	_request_json("/jobs/" + normalized_job_id.uri_encode() + "/result", HTTPClient.METHOD_GET, null, callback, true)

func _request_json(
	endpoint_path: String,
	method: int,
	payload: Variant,
	callback: Callable,
	requires_api_key: bool,
	query_params: Variant = null,
) -> void:
	var resolved_base_url := _resolve_runtime_base_url(requires_api_key)
	var request_url: String = _build_request_url(endpoint_path, query_params, resolved_base_url)
	var method_name: String = _http_method_to_string(method)
	var body_string := ""
	if payload != null:
		body_string = JSON.stringify(payload)

	if requires_api_key and !backend_proxy_mode and api_key.is_empty() and publishable_gateway_client_key.is_empty():
		callback.call(
			false,
			_local_error_payload(
				"missing_runtime_auth",
				"Set quantum_api/publishable_gateway_client_key for Gateway runtime mode, or set quantum_api/direct_api_key for direct Quantum API mode.",
				request_url,
				endpoint_path,
				method_name,
				requires_api_key
			)
		)
		return

	if requires_api_key and !backend_proxy_mode and api_key.is_empty() and !publishable_gateway_client_key.is_empty():
		_ensure_runtime_token(
			func(success: bool, runtime_payload: Dictionary) -> void:
				if !success:
					callback.call(false, runtime_payload)
					return

				_dispatch_request(
					request_url,
					_build_headers(requires_api_key, payload != null),
					method,
					body_string,
					callback,
					endpoint_path,
					method_name,
					requires_api_key
				)
			)
		return

	_dispatch_request(
		request_url,
		_build_headers(requires_api_key, payload != null),
		method,
		body_string,
		callback,
		endpoint_path,
		method_name,
		requires_api_key
	)

func _dispatch_request(
	request_url: String,
	headers: PackedStringArray,
	method: int,
	body_string: String,
	callback: Callable,
	endpoint_path: String,
	method_name: String,
	requires_api_key: bool,
	cache_runtime_token_on_success: bool = false,
) -> void:
	var http_request := HTTPRequest.new()
	add_child(http_request)

	http_request.request_completed.connect(
		func(result: int, response_code: int, response_headers: PackedStringArray, body: PackedByteArray) -> void:
			var parsed := _parse_response(
				result,
				response_code,
				response_headers,
				body,
				request_url,
				endpoint_path,
				method_name,
				requires_api_key
			)
			http_request.queue_free()

			if parsed["success"] and cache_runtime_token_on_success:
				var parsed_payload := parsed["payload"]
				if parsed_payload is Dictionary and _cache_runtime_token_from_payload(parsed_payload):
					callback.call(true, parsed_payload)
					return

				callback.call(
					false,
					_local_error_payload(
						"invalid_runtime_token_payload",
						"Gateway runtime token response was missing required fields.",
						request_url,
						endpoint_path,
						method_name,
						requires_api_key
					)
				)
				return

			callback.call(parsed["success"], parsed["payload"])
	)

	var error := http_request.request(request_url, headers, method, body_string)
	if error != OK:
		http_request.queue_free()
		callback.call(
			false,
			_local_error_payload(
				"request_start_failed",
				"Failed to start HTTP request: " + error_string(error),
				request_url,
				endpoint_path,
				method_name,
				requires_api_key,
				error
			)
		)

func _build_headers(requires_api_key: bool, include_json_content_type: bool) -> PackedStringArray:
	var headers: PackedStringArray = []
	if include_json_content_type:
		headers.append("Content-Type: application/json")
	if requires_api_key and !backend_proxy_mode and !api_key.is_empty():
		headers.append("X-API-Key: " + api_key)
	elif requires_api_key and !backend_proxy_mode and !runtime_token.is_empty():
		headers.append("Authorization: Bearer " + runtime_token)
		if !runtime_project_id.is_empty():
			headers.append("X-Project-Id: " + runtime_project_id)
	return headers

func _parse_response(
	result: int,
	response_code: int,
	headers: PackedStringArray,
	body: PackedByteArray,
	request_url: String,
	endpoint_path: String,
	method_name: String,
	requires_api_key: bool,
) -> Dictionary:
	var response_text := body.get_string_from_utf8()
	var payload: Dictionary = {}
	var request_id := _extract_response_header(headers, "x-request-id")

	if !response_text.is_empty():
		var json := JSON.new()
		if json.parse(response_text) == OK and json.data is Dictionary:
			payload = json.data

	if result != HTTPRequest.RESULT_SUCCESS:
		if payload.is_empty():
			payload = {
				"error": "transport_error",
				"message": "HTTP transport failed: " + _http_request_result_to_message(result),
			}
		elif !payload.has("message"):
			payload["message"] = "HTTP transport failed: " + _http_request_result_to_message(result)

		_attach_diagnostics(
			payload,
			result,
			response_code,
			request_url,
			endpoint_path,
			method_name,
			requires_api_key,
			response_text,
			request_id
		)
		return {"success": false, "payload": payload}

	if response_code >= 200 and response_code < 300:
		return {"success": true, "payload": payload}

	if payload.is_empty():
		var default_message := response_text if !response_text.is_empty() else "Quantum API request failed"
		if response_code == 401 and requires_api_key:
			default_message = "Unauthorized (401). Configure a publishable Gateway client key, a direct Quantum API key, or your own backend proxy mode."

		payload = {
			"error": "http_error",
			"message": default_message,
		}
	elif !payload.has("message"):
		payload["message"] = response_text if !response_text.is_empty() else "Quantum API request failed"

	if response_code == 401:
		payload["error"] = "unauthorized"
		if requires_api_key:
			if !api_key.is_empty():
				payload["auth_hint"] = "Set [quantum_api] direct_api_key and ensure the endpoint accepts direct Quantum API key mode."
			elif !publishable_gateway_client_key.is_empty():
				payload["auth_hint"] = "Set [quantum_api] publishable_gateway_client_key and make sure the Gateway project is active."
			else:
				payload["auth_hint"] = "Configure a publishable Gateway client key, a direct Quantum API key, or your own backend proxy mode."

	_attach_diagnostics(
		payload,
		result,
		response_code,
		request_url,
		endpoint_path,
		method_name,
		requires_api_key,
		response_text,
		request_id
	)
	return {"success": false, "payload": payload}

func _attach_diagnostics(
	payload: Dictionary,
	result: int,
	response_code: int,
	request_url: String,
	endpoint_path: String,
	method_name: String,
	requires_api_key: bool,
	response_text: String,
	request_id: String,
) -> void:
	payload["result"] = result
	payload["result_text"] = _http_request_result_to_message(result)
	payload["status_code"] = response_code
	payload["request_url"] = request_url
	payload["endpoint_path"] = endpoint_path
	payload["method"] = method_name
	payload["backend_proxy_mode"] = backend_proxy_mode
	payload["api_key_present"] = !api_key.is_empty()
	payload["publishable_gateway_client_key_present"] = !publishable_gateway_client_key.is_empty()
	payload["default_ibm_profile_present"] = !default_ibm_profile.is_empty()
	payload["requires_api_key"] = requires_api_key
	payload["runtime_token_present"] = !runtime_token.is_empty()
	payload["runtime_project_id"] = runtime_project_id
	if !request_id.is_empty() and !payload.has("request_id"):
		payload["request_id"] = request_id
	if !response_text.is_empty():
		payload["response_text"] = response_text.substr(0, min(response_text.length(), 512))

func _extract_response_header(headers: PackedStringArray, name: String) -> String:
	var expected := name.to_lower()
	for raw_header in headers:
		var separator := raw_header.find(":")
		if separator == -1:
			continue
		var header_name := raw_header.substr(0, separator).strip_edges().to_lower()
		if header_name == expected:
			return raw_header.substr(separator + 1).strip_edges()
	return ""

func _local_error_payload(
	error_code: String,
	message: String,
	request_url: String,
	endpoint_path: String,
	method_name: String,
	requires_api_key: bool,
	result: int = 0,
) -> Dictionary:
	var payload := {
		"error": error_code,
		"message": message,
		"status_code": 0,
		"request_url": request_url,
		"endpoint_path": endpoint_path,
		"method": method_name,
		"backend_proxy_mode": backend_proxy_mode,
		"api_key_present": !api_key.is_empty(),
		"publishable_gateway_client_key_present": !publishable_gateway_client_key.is_empty(),
		"default_ibm_profile_present": !default_ibm_profile.is_empty(),
		"requires_api_key": requires_api_key,
		"runtime_token_present": !runtime_token.is_empty(),
		"runtime_project_id": runtime_project_id,
		"result": result,
	}
	if result != 0:
		payload["result_text"] = error_string(result)
	return payload

func _build_request_url(endpoint_path: String, query_params: Variant = null, custom_base_url: String = "") -> String:
	var resolved_base_url := custom_base_url if !custom_base_url.is_empty() else base_url
	var request_url := resolved_base_url + endpoint_path
	if query_params == null:
		return request_url
	if !(query_params is Dictionary):
		return request_url

	var params: Dictionary = query_params
	if params.is_empty():
		return request_url

	var query_pairs: Array[String] = []
	for key in params.keys():
		var value: Variant = params[key]
		if value == null:
			continue
		query_pairs.append(str(key).uri_encode() + "=" + _query_value_to_string(value).uri_encode())

	if query_pairs.is_empty():
		return request_url
	return request_url + "?" + "&".join(query_pairs)

func _query_value_to_string(value: Variant) -> String:
	if value is bool:
		return "true" if value else "false"
	return str(value)

func _apply_optional_ibm_profile(
	payload: Dictionary,
	ibm_profile: String = "",
	assume_ibm_provider_if_missing: bool = false,
) -> void:
	var resolved_override := ibm_profile.strip_edges()
	if !resolved_override.is_empty():
		payload["ibm_profile"] = resolved_override
		return

	var existing_profile := str(payload.get("ibm_profile", "")).strip_edges()
	if !existing_profile.is_empty():
		return

	var provider := str(payload.get("provider", "")).strip_edges().to_lower()
	var backend_name := str(payload.get("backend_name", "")).strip_edges().to_lower()
	var provider_is_ibm := provider == "ibm" or (
		provider.is_empty() and (assume_ibm_provider_if_missing or backend_name.begins_with("ibm"))
	)

	if provider_is_ibm:
		var fallback_profile := _resolve_optional_ibm_profile()
		if !fallback_profile.is_empty():
			payload["ibm_profile"] = fallback_profile

func _resolve_optional_ibm_profile(override_profile: String = "") -> String:
	var explicit_profile := override_profile.strip_edges()
	if !explicit_profile.is_empty():
		return explicit_profile
	return default_ibm_profile.strip_edges()

func _ensure_runtime_token(
	callback: Callable,
	force_refresh: bool = false,
	client_session_id: String = "",
) -> void:
	var endpoint_path := "/runtime-sessions"
	var request_url := _build_request_url(endpoint_path)
	var method_name := "POST"

	if backend_proxy_mode:
		callback.call(
			false,
			_local_error_payload(
				"backend_proxy_mode_enabled",
				"Runtime tokens are not used when backend_proxy_mode=true.",
				request_url,
				endpoint_path,
				method_name,
				false
			)
		)
		return

	if !api_key.is_empty() and publishable_gateway_client_key.is_empty():
		callback.call(
			false,
			_local_error_payload(
				"direct_mode_enabled",
				"Direct Quantum API key mode does not mint Gateway runtime tokens.",
				request_url,
				endpoint_path,
				method_name,
				false
			)
		)
		return

	if publishable_gateway_client_key.is_empty():
		callback.call(
			false,
			_local_error_payload(
				"missing_publishable_gateway_client_key",
				"Set quantum_api/publishable_gateway_client_key to mint Gateway runtime tokens.",
				request_url,
				endpoint_path,
				method_name,
				false
			)
		)
		return

	if !force_refresh and _runtime_token_is_valid():
		callback.call(
			true,
			{
				"token": runtime_token,
				"project_id": runtime_project_id,
				"expires_at_unix": runtime_token_expires_at_unix,
			}
		)
		return

	var headers: PackedStringArray = []
	headers.append("X-Gateway-Publishable-Key: " + publishable_gateway_client_key)
	var body_string := ""
	var normalized_client_session_id := client_session_id.strip_edges()
	if !normalized_client_session_id.is_empty():
		headers.append("Content-Type: application/json")
		body_string = JSON.stringify({"client_session_id": normalized_client_session_id})
	if !runtime_project_id.is_empty():
		headers.append("X-Project-Id: " + runtime_project_id)

	_dispatch_request(
		request_url,
		headers,
		HTTPClient.METHOD_POST,
		body_string,
		callback,
		endpoint_path,
		method_name,
		false,
		true
	)

func _runtime_token_is_valid() -> bool:
	if runtime_token.is_empty():
		return false
	if runtime_token_expires_at_unix <= 0.0:
		return false
	return runtime_token_expires_at_unix > (_current_unix_time() + RUNTIME_TOKEN_REFRESH_BUFFER_SECONDS)

func _cache_runtime_token_from_payload(payload: Dictionary) -> bool:
	var token := str(payload.get("token", "")).strip_edges()
	if token.is_empty():
		return false

	runtime_token = token
	runtime_project_id = str(payload.get("project_id", "")).strip_edges()
	runtime_token_expires_at_unix = _parse_datetime_to_unix(
		str(payload.get("expires_at", "")).strip_edges()
	)
	if runtime_token_expires_at_unix <= 0.0:
		runtime_token_expires_at_unix = _current_unix_time() + 300.0
	return true

func _parse_datetime_to_unix(value: String) -> float:
	var normalized := value.strip_edges()
	if normalized.is_empty():
		return 0.0
	return float(Time.get_unix_time_from_datetime_string(normalized))

func _current_unix_time() -> float:
	return float(Time.get_unix_time_from_system())

func _resolve_runtime_base_url(requires_api_key: bool) -> String:
	if !requires_api_key or backend_proxy_mode or api_key.is_empty():
		return base_url
	if base_url.find("/public-facing/api/quantum-gateway") != -1:
		return base_url.replace("/public-facing/api/quantum-gateway", "/public-facing/api/quantum")
	return base_url

func _normalize_base_url(url: String) -> String:
	var normalized := url.strip_edges().trim_suffix("/")
	if normalized.is_empty():
		return DEFAULT_BASE_URL
	if normalized.ends_with("/v1"):
		return normalized
	return normalized + "/v1"

func _variant_to_bool(value: Variant, fallback: bool) -> bool:
	if value is bool:
		return value
	if value is int:
		return value != 0
	if value is String:
		var normalized: String = str(value).strip_edges().to_lower()
		if normalized == "1" or normalized == "true" or normalized == "yes" or normalized == "on":
			return true
		if normalized == "0" or normalized == "false" or normalized == "no" or normalized == "off":
			return false
	return fallback

func _http_method_to_string(method: int) -> String:
	match method:
		HTTPClient.METHOD_GET:
			return "GET"
		HTTPClient.METHOD_POST:
			return "POST"
		HTTPClient.METHOD_PUT:
			return "PUT"
		HTTPClient.METHOD_DELETE:
			return "DELETE"
		HTTPClient.METHOD_PATCH:
			return "PATCH"
		_:
			return "METHOD_" + str(method)

func _http_request_result_to_message(result: int) -> String:
	match result:
		HTTPRequest.RESULT_SUCCESS:
			return "SUCCESS"
		HTTPRequest.RESULT_CHUNKED_BODY_SIZE_MISMATCH:
			return "CHUNKED_BODY_SIZE_MISMATCH"
		HTTPRequest.RESULT_CANT_CONNECT:
			return "CANT_CONNECT"
		HTTPRequest.RESULT_CANT_RESOLVE:
			return "CANT_RESOLVE"
		HTTPRequest.RESULT_CONNECTION_ERROR:
			return "CONNECTION_ERROR"
		HTTPRequest.RESULT_TLS_HANDSHAKE_ERROR:
			return "TLS_HANDSHAKE_ERROR"
		HTTPRequest.RESULT_NO_RESPONSE:
			return "NO_RESPONSE"
		HTTPRequest.RESULT_BODY_SIZE_LIMIT_EXCEEDED:
			return "BODY_SIZE_LIMIT_EXCEEDED"
		HTTPRequest.RESULT_BODY_DECOMPRESS_FAILED:
			return "BODY_DECOMPRESS_FAILED"
		HTTPRequest.RESULT_REQUEST_FAILED:
			return "REQUEST_FAILED"
		HTTPRequest.RESULT_DOWNLOAD_FILE_CANT_OPEN:
			return "DOWNLOAD_FILE_CANT_OPEN"
		HTTPRequest.RESULT_DOWNLOAD_FILE_WRITE_ERROR:
			return "DOWNLOAD_FILE_WRITE_ERROR"
		HTTPRequest.RESULT_REDIRECT_LIMIT_REACHED:
			return "REDIRECT_LIMIT_REACHED"
		HTTPRequest.RESULT_TIMEOUT:
			return "TIMEOUT"
		_:
			return "RESULT_" + str(result)
