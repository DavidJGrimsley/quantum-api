extends Node

const FIXTURE_BASE_URL := "http://127.0.0.1:18101/v1"
const UNREACHABLE_BASE_URL := "http://127.0.0.1:9/v1"
const ClientScript = preload("res://addons/quantum_api_client/quantum_api_client.gd")
const ProjectSettingsScript = preload("res://addons/quantum_api_client/project_settings.gd")

var failures: Array[String] = []
var case_index := 0
var cases: Array[Callable] = []

func _ready() -> void:
	set_process(true)
	print("Godot package harness starting")
	cases = [
		Callable(self, "_test_project_settings_registration"),
		Callable(self, "_test_url_normalization_and_snapshot"),
		Callable(self, "_test_proxy_auth"),
		Callable(self, "_test_direct_auth"),
		Callable(self, "_test_missing_key"),
		Callable(self, "_test_request_start_failure"),
		Callable(self, "_test_health"),
		Callable(self, "_test_bit_flip"),
		Callable(self, "_test_phase_flip"),
		Callable(self, "_test_rotation"),
		Callable(self, "_test_rotation_without_angle"),
		Callable(self, "_test_braid_defaults"),
		Callable(self, "_test_braid_explicit_request"),
		Callable(self, "_test_concurrent_requests"),
		Callable(self, "_test_text_success"),
		Callable(self, "_test_unauthorized_fallback"),
		Callable(self, "_test_rate_limit_fallback"),
		Callable(self, "_test_server_error_fallback"),
		Callable(self, "_test_empty_json_fallback"),
		Callable(self, "_test_malformed_json_fallback"),
		Callable(self, "_test_timeout_fallback"),
		Callable(self, "_test_unreachable_server"),
		Callable(self, "_test_list_backends"),
		Callable(self, "_test_transpile"),
		Callable(self, "_test_submit"),
		Callable(self, "_test_job_status"),
		Callable(self, "_test_job_result"),
	]
	_next_case()

func _test_project_settings_registration() -> void:
	ProjectSettings.set_setting("quantum_api/default_ibm_profile", "existing-profile")
	ProjectSettingsScript.register()
	_expect(ProjectSettings.has_setting("quantum_api/default_ibm_profile"), "IBM profile setting should be registered")
	_expect(
		str(ProjectSettings.get_setting("quantum_api/default_ibm_profile")) == "existing-profile",
		"settings helper must not overwrite an existing IBM profile",
	)
	_expect(ProjectSettings.has_setting("quantum_api/request_timeout_seconds"), "timeout setting should be registered")
	var profile_setting_is_basic := false
	for property_info in ProjectSettings.get_property_list():
		if str(property_info.get("name", "")) == "quantum_api/default_ibm_profile":
			profile_setting_is_basic = (
				int(property_info.get("usage", 0)) & PROPERTY_USAGE_EDITOR_BASIC_SETTING
			) != 0
			break
	_expect(profile_setting_is_basic, "IBM profile setting should be visible in Basic Project Settings")
	var client: Variant = ClientScript.new()
	client.set_default_ibm_profile("__quantum_api_use_account_default__")
	_expect(
		str(client.get_config_snapshot().get("default_ibm_profile", "missing")).is_empty(),
		"editor account-default marker must not be sent as an IBM profile name",
	)
	_next_case()

func _process(_delta: float) -> void:
	# The harness progresses from HTTP callbacks; keeping the node processing
	# prevents headless Godot from ending the scene between asynchronous cases.
	pass

func _next_case() -> void:
	print("Godot package harness case " + str(case_index + 1))
	if case_index >= cases.size():
		if failures.is_empty():
			print("Godot package harness passed")
			get_tree().quit(0)
			return
		for failure in failures:
			push_error(failure)
		get_tree().quit(1)
		return
	var next := cases[case_index]
	case_index += 1
	next.call()

func _new_client(base_url: String = FIXTURE_BASE_URL, proxy_mode: bool = true, key: String = ""):
	var client: Variant = ClientScript.new()
	client.set_base_url(base_url)
	client.set_backend_proxy_mode(proxy_mode)
	client.set_api_key(key)
	add_child(client)
	return client

func _release(client) -> void:
	if is_instance_valid(client):
		client.queue_free()

func _expect(condition: bool, message: String) -> void:
	if !condition:
		failures.append(message)

func _start_request(
	client,
	start_request: Callable,
	verifier: Callable,
	label: String,
	settle_seconds: float = 0.05,
) -> void:
	var state: Dictionary = {
		"callback_count": 0,
		"client": client,
		"label": label,
		"settle_seconds": settle_seconds,
		"verifier": verifier,
	}
	start_request.call(Callable(self, "_handle_request_case").bind(state))

func _handle_request_case(success: bool, payload: Dictionary, state: Dictionary) -> void:
	state["callback_count"] = int(state["callback_count"]) + 1
	if int(state["callback_count"]) > 1:
		_expect(false, str(state["label"]) + " callback ran more than once.")
		return

	var verifier: Callable = state["verifier"]
	verifier.call(success, payload)
	get_tree().create_timer(float(state["settle_seconds"])).timeout.connect(
		Callable(self, "_finish_request_case").bind(state), CONNECT_ONE_SHOT
	)

func _finish_request_case(state: Dictionary) -> void:
	_expect(int(state["callback_count"]) == 1, str(state["label"]) + " callback should run exactly once.")
	_release(state["client"])
	call_deferred("_next_case")

func _test_url_normalization_and_snapshot() -> void:
	var client = _new_client("  http://127.0.0.1:18101////  ")
	_expect(client.base_url == FIXTURE_BASE_URL, "URL normalization should add exactly one /v1.")
	client.set_base_url("  http://127.0.0.1:18101/v1////  ")
	_expect(client.base_url == FIXTURE_BASE_URL, "URL normalization should remove repeated trailing slashes.")
	client.set_request_timeout_seconds(0.0)
	_expect(client.request_timeout_seconds == 0.1, "Timeout setter should apply its positive safety floor.")
	client.set_request_timeout_seconds(0.2)
	_expect(client.get_config_snapshot().get("request_timeout_seconds") == 0.2, "Config snapshot should expose request timeout.")
	_release(client)
	_next_case()

func _test_proxy_auth() -> void:
	var client = _new_client(FIXTURE_BASE_URL, true, "dummy-key")
	_start_request(client, func(callback: Callable): client.run_gate("bit_flip", callback), func(success: bool, payload: Dictionary):
		_expect(success, "Proxy-mode gate request should succeed.")
		_expect(!bool(payload.get("saw_api_key", true)), "Proxy mode must omit X-API-Key.")
	, "proxy auth")

func _test_direct_auth() -> void:
	var client = _new_client(FIXTURE_BASE_URL, false, "dummy-key")
	_start_request(client, func(callback: Callable): client.run_gate("bit_flip", callback), func(success: bool, payload: Dictionary):
		_expect(success, "Direct-mode gate request should succeed.")
		_expect(bool(payload.get("saw_api_key", false)), "Direct mode must send X-API-Key.")
	, "direct auth")

func _test_missing_key() -> void:
	var client = _new_client(FIXTURE_BASE_URL, false)
	_start_request(client, func(callback: Callable): client.run_gate("phase_flip", callback), func(success: bool, payload: Dictionary):
		_expect(!success and payload.get("error") == "missing_api_key", "Direct mode without a key must fail locally.")
	, "missing key")

func _test_request_start_failure() -> void:
	var client = _new_client("not a valid URL", true)
	_start_request(client, func(callback: Callable): client.health_check(callback), func(success: bool, payload: Dictionary):
		_expect(!success and payload.get("error") == "request_start_failed", "Invalid request URL should report request-start failure.")
	, "request start failure")

func _test_health() -> void:
	var client = _new_client()
	_start_request(client, func(callback: Callable): client.health_check(callback), func(success: bool, payload: Dictionary):
		_expect(success and payload.get("status") == "ok", "Health check should parse a JSON response.")
	, "health")

func _test_bit_flip() -> void:
	var client = _new_client()
	_start_request(client, func(callback: Callable): client.run_gate("bit_flip", callback), func(success: bool, _payload: Dictionary):
		_expect(success, "bit_flip should succeed.")
	, "bit flip")

func _test_phase_flip() -> void:
	var client = _new_client()
	_start_request(client, func(callback: Callable): client.run_gate("phase_flip", callback), func(success: bool, _payload: Dictionary):
		_expect(success, "phase_flip should succeed.")
	, "phase flip")

func _test_rotation() -> void:
	var client = _new_client()
	_start_request(client, func(callback: Callable): client.run_gate("rotation", callback, 0.5), func(success: bool, _payload: Dictionary):
		_expect(success, "Rotation with an angle should succeed.")
	, "rotation")

func _test_rotation_without_angle() -> void:
	var client = _new_client()
	_start_request(client, func(callback: Callable): client.run_gate("rotation", callback), func(success: bool, payload: Dictionary):
		_expect(!success and payload.get("status_code") == 422, "Rotation without an angle should preserve validation failure.")
	, "missing rotation angle")

func _test_braid_defaults() -> void:
	var client = _new_client()
	var request := {"braid_word": [{"generator": 2, "power": 1}]}
	_start_request(client, func(callback: Callable): client.evaluate_braid(request, callback), func(success: bool, response: Dictionary):
		var body: Dictionary = response.get("body", {})
		var braid_word: Array = body.get("braid_word", [])
		var state: Array = response.get("logical_state", [])
		var probabilities: Dictionary = response.get("fusion_probabilities", {})
		_expect(success and response.get("path") == "/v1/topological/braid", "Braid should reach the protected endpoint.")
		_expect(!bool(response.get("saw_api_key", true)), "Proxy-mode braid must omit X-API-Key.")
		_expect(body.get("model") == "fibonacci" and body.get("anyon_count") == 3, "Braid defaults should select the supported model.")
		_expect(body.get("total_charge") == "tau" and body.get("initial_state") == "0", "Braid defaults should select the standard initial state.")
		_expect(braid_word.size() == 1, "Braid word should contain the requested operation.")
		if braid_word.size() == 1:
			var operation: Dictionary = braid_word[0]
			_expect(int(operation.get("generator", 0)) == 2 and int(operation.get("power", 0)) == 1, "Braid word should preserve the generator and power.")
		_expect(body.get("measure") == false and body.get("shots") == 0, "Braid should not sample unless requested.")
		_expect(!request.has("model"), "Braid defaults must not mutate the caller's dictionary.")
		_expect(state.size() == 2, "Braid response should include both complex amplitudes.")
		if state.size() == 2:
			_expect(absf(float(state[0].get("real", 0.0)) + 0.5) < 1e-9 and absf(float(state[0].get("imag", 0.0)) - 0.3632712640026805) < 1e-9, "Braid response should preserve the sigma_2 vacuum amplitude.")
			_expect(absf(float(state[1].get("real", 0.0)) + 0.24293413587832285) < 1e-9 and absf(float(state[1].get("imag", 0.0)) + 0.7476743906106105) < 1e-9, "Braid response should preserve the sigma_2 tau amplitude.")
		_expect(absf(float(probabilities.get("vacuum", 0.0)) - 0.3819660112501051) < 1e-9 and absf(float(probabilities.get("tau", 0.0)) - 0.6180339887498949) < 1e-9, "Braid response should preserve the sigma_2 reference probabilities.")
		_expect(response.get("measurement") == null and response.get("counts") == null, "Unsampled braid should not report a collapse.")
	, "braid defaults")

func _test_braid_explicit_request() -> void:
	var client = _new_client(FIXTURE_BASE_URL, false, "dummy-key")
	var request := {
		"model": "fibonacci",
		"anyon_count": 3,
		"total_charge": "tau",
		"initial_state": "1",
		"braid_word": [],
		"measure": true,
		"shots": 5,
		"seed": 42,
	}
	_start_request(client, func(callback: Callable): client.evaluate_braid(request, callback), func(success: bool, response: Dictionary):
		var body: Dictionary = response.get("body", {})
		var braid_word: Array = body.get("braid_word", [])
		var counts: Dictionary = response.get("counts", {})
		_expect(success and bool(response.get("saw_api_key", false)), "Direct-mode braid should use the configured API key.")
		_expect(body.get("model") == "fibonacci" and int(body.get("anyon_count", 0)) == 3 and body.get("total_charge") == "tau", "Explicit braid model fields should pass through unchanged.")
		_expect(body.get("initial_state") == "1" and body.get("measure") == true and int(body.get("shots", 0)) == 5 and int(body.get("seed", 0)) == 42, "Explicit braid state, sampling, and seed should pass through unchanged.")
		_expect(braid_word.is_empty(), "Explicit empty braid word should remain empty.")
		_expect(response.get("measurement") == "tau", "Measured braid should preserve the collapse label.")
		_expect(counts.get("tau") == 5, "Measured braid should preserve shot counts.")
	, "braid explicit request")

func _test_concurrent_requests() -> void:
	var client = _new_client()
	var state: Dictionary = {"callback_count": 0, "first_success": false, "second_success": false, "done": false}
	var finish := func() -> void:
		if bool(state["done"]) or int(state["callback_count"]) != 2:
			return
		state["done"] = true
		get_tree().create_timer(0.05).timeout.connect(func() -> void:
			_expect(bool(state["first_success"]) and bool(state["second_success"]), "Concurrent requests should complete independently.")
			_expect(int(state["callback_count"]) == 2, "Concurrent callbacks should each run exactly once.")
			_release(client)
			call_deferred("_next_case")
		)
	client.run_gate("bit_flip", func(success: bool, _payload: Dictionary) -> void:
		state["callback_count"] = int(state["callback_count"]) + 1
		state["first_success"] = success
		finish.call()
	)
	client.run_gate("phase_flip", func(success: bool, _payload: Dictionary) -> void:
		state["callback_count"] = int(state["callback_count"]) + 1
		state["second_success"] = success
		finish.call()
	)
	get_tree().create_timer(3.0).timeout.connect(func() -> void:
		if bool(state["done"]):
			return
		state["done"] = true
		_expect(false, "Concurrent requests did not both complete within the fixture deadline.")
		_release(client)
		call_deferred("_next_case")
	)

func _test_text_success() -> void:
	var client = _new_client()
	_start_request(client, func(callback: Callable): client.transform_text("hello", callback, "fallback"), func(success: bool, payload: Dictionary):
		_expect(success and payload.get("transformed") == "fixture:hello", "Text transform should parse its response.")
	, "text success")

func _text_failure_case(text: String, expected_error: String, expected_status: int, label: String) -> void:
	var client = _new_client()
	_start_request(client, func(callback: Callable): client.transform_text(text, callback, "fallback"), func(success: bool, payload: Dictionary):
		_expect(!success, label + " should fail.")
		_expect(payload.get("error") == expected_error, label + " should retain a structured error.")
		_expect(payload.get("status_code") == expected_status, label + " should retain HTTP status.")
		_expect(payload.get("transformed") == "fallback", label + " should preserve text fallback.")
	, label)

func _test_unauthorized_fallback() -> void:
	_text_failure_case("fixture-unauthorized", "unauthorized", 401, "unauthorized")

func _test_rate_limit_fallback() -> void:
	_text_failure_case("fixture-rate-limit", "rate_limited", 429, "rate limit")

func _test_server_error_fallback() -> void:
	_text_failure_case("fixture-server-error", "upstream_error", 500, "server error")

func _test_empty_json_fallback() -> void:
	_text_failure_case("fixture-empty", "empty_response", 200, "empty JSON")

func _test_malformed_json_fallback() -> void:
	_text_failure_case("fixture-malformed", "malformed_json", 200, "malformed JSON")

func _test_timeout_fallback() -> void:
	var client = _new_client()
	client.set_request_timeout_seconds(0.1)
	_start_request(client, func(callback: Callable): client.transform_text("fixture-timeout", callback, "fallback"), func(success: bool, payload: Dictionary):
		_expect(!success and payload.get("error") == "timeout", "Timeout should report a structured failure.")
		_expect(payload.get("transformed") == "fallback", "Timeout should preserve text fallback.")
	, "timeout", 1.1)

func _test_unreachable_server() -> void:
	var client = _new_client(UNREACHABLE_BASE_URL)
	_start_request(client, func(callback: Callable): client.health_check(callback), func(success: bool, payload: Dictionary):
		_expect(!success and ["transport_error", "request_start_failed", "timeout"].has(payload.get("error")), "Unreachable server should report a structured connection failure.")
		_expect(payload.get("status_code") == 0, "Unreachable-server diagnostics should have no HTTP status.")
	, "unreachable server")

func _test_list_backends() -> void:
	var client = _new_client(FIXTURE_BASE_URL, false, "dummy-key")
	client.set_default_ibm_profile("fixture-profile")
	_start_request(client, func(callback: Callable): client.list_backends(callback, "ibm", true, 0), func(success: bool, payload: Dictionary):
		var query: Dictionary = payload.get("query", {})
		_expect(success, "Backend discovery should succeed.")
		_expect(query.get("ibm_profile", [""])[0] == "fixture-profile", "IBM profile should be sent in backend query.")
		_expect(query.get("min_qubits", [""])[0] == "1", "Minimum qubits should be normalized.")
	, "list backends")

func _ibm_circuit_payload() -> Dictionary:
	return {"provider": "ibm", "backend_name": "ibm_fixture", "circuit": {"qubits": 1}}

func _test_transpile() -> void:
	var client = _new_client(FIXTURE_BASE_URL, false, "dummy-key")
	client.set_default_ibm_profile("fixture-profile")
	_start_request(client, func(callback: Callable): client.transpile(_ibm_circuit_payload(), callback), func(success: bool, payload: Dictionary):
		var body: Dictionary = payload.get("body", {})
		_expect(success and body.get("ibm_profile") == "fixture-profile", "Transpile should apply IBM profile.")
	, "transpile")

func _test_submit() -> void:
	var client = _new_client(FIXTURE_BASE_URL, false, "dummy-key")
	client.set_default_ibm_profile("fixture-profile")
	_start_request(client, func(callback: Callable): client.submit_circuit_job(_ibm_circuit_payload(), callback), func(success: bool, payload: Dictionary):
		var body: Dictionary = payload.get("body", {})
		_expect(success and body.get("ibm_profile") == "fixture-profile", "Submit should apply IBM profile.")
	, "submit")

func _test_job_status() -> void:
	var client = _new_client(FIXTURE_BASE_URL, false, "dummy-key")
	_start_request(client, func(callback: Callable): client.get_circuit_job("fixture-job", callback), func(success: bool, _payload: Dictionary):
		_expect(success, "Job status route should succeed.")
	, "job status")

func _test_job_result() -> void:
	var client = _new_client(FIXTURE_BASE_URL, false, "dummy-key")
	_start_request(client, func(callback: Callable): client.get_circuit_job_result("fixture-job", callback), func(success: bool, _payload: Dictionary):
		_expect(success, "Job result route should succeed.")
	, "job result")
