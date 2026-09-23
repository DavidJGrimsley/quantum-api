using System.Threading.Tasks;
using QuantumApi.Unity;
using UnityEngine;

namespace QuantumApi.Unity.Samples
{
    public sealed class QuantumApiExample : MonoBehaviour
    {
        private QuantumApiClient _client;

        private void Start()
        {
            _client = QuantumApiManager.Instance?.Client;
            if (_client == null)
            {
                Debug.LogError("Add QuantumApiManager to the scene before using QuantumApiExample.", this);
                return;
            }

            StartCoroutine(_client.HealthCoroutine(
                health => Debug.Log($"Quantum API ready: {health.status} ({health.runtime_mode})"),
                error => Debug.LogWarning($"Health check failed: {error.Message}")));

            StartCoroutine(_client.GetEchoTypesCoroutine(
                response => Debug.Log($"Echo types loaded: {response.echo_types.Length}"),
                error => Debug.LogWarning($"Echo types failed: {error.Message}")));

            StartCoroutine(_client.RunGateCoroutine(
                new GateRunRequest { gate_type = "bit_flip" },
                response => Debug.Log($"Bit flip measurement: {response.measurement}"),
                error => Debug.LogWarning($"Bit flip failed: {error.Message}")));

            _ = RunAsyncExamples();
        }

        private async Task RunAsyncExamples()
        {
            await RunGateExamplesAsync();
            await RunRandomExamplesAsync();
            await RunReadableErrorExampleAsync();
            await RunTextTransformExampleAsync();
        }

        private async Task RunGateExamplesAsync()
        {
            try
            {
                var phaseFlip = await _client.RunGateAsync(new GateRunRequest
                {
                    gate_type = "phase_flip",
                });
                Debug.Log($"Phase flip measurement: {phaseFlip.measurement}");

                var rotation = await _client.RunGateAsync(new GateRunRequest
                {
                    gate_type = "rotation",
                    sendRotationAngle = true,
                    rotation_angle_rad = Mathf.PI / 2f,
                });
                Debug.Log($"Rotation measurement: {rotation.measurement}");
            }
            catch (QuantumApiError error)
            {
                Debug.LogWarning($"Gate example failed: {error.Message}");
            }
        }

        private async Task RunRandomExamplesAsync()
        {
            try
            {
                for (var index = 0; index < 5; index += 1)
                {
                    var response = await _client.RandomIntAsync(0, 1);
                    Debug.Log($"QRNG coin flip {index + 1}: {response.value} ({response.source})");
                }
            }
            catch (QuantumApiError error)
            {
                Debug.LogWarning($"QRNG example failed: {error.Message}");
            }
        }

        private async Task RunReadableErrorExampleAsync()
        {
            try
            {
                await _client.RandomIntAsync(1, 0);
            }
            catch (QuantumApiError error)
            {
                Debug.LogWarning($"Expected validation error: {error.ErrorCode} {error.Message}");
            }
        }

        private async Task RunTextTransformExampleAsync()
        {
            var request = new TextTransformRequest
            {
                text = "memory signal and quantum circuit",
            };

            try
            {
                var response = await _client.TransformTextAsync(request);
                Debug.Log($"Transformed text: {response.transformed}");
            }
            catch (QuantumApiError error)
            {
                var fallback = QuantumApiClient.CreateTextTransformFallback(request.text, request.text);
                Debug.LogWarning($"Transform failed, using fallback text: {error.Message}");
                Debug.Log($"Fallback text: {fallback.transformed}");
            }
        }
    }
}
