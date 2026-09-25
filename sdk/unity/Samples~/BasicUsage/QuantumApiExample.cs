// Copyright (c) 2026 David J. Grimsley. All rights reserved.
using System;
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
            await RunBraidExampleAsync();
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

        private async Task RunBraidExampleAsync()
        {
            try
            {
                var braid = await _client.EvaluateBraidAsync(new TopologicalBraidRequest
                {
                    braid_word = new[]
                    {
                        new BraidOperation { generator = 2, power = 1 },
                    },
                });
                if (braid.logical_state == null || braid.logical_state.Length != 2 || braid.fusion_probabilities == null)
                {
                    Debug.LogWarning("Braid response is missing its logical state or probabilities.");
                    return;
                }

                var tauAmplitude = braid.logical_state[1];
                Debug.Log($"Braid tau probability: {braid.fusion_probabilities.tau:P1}; "
                    + $"tau amplitude: {tauAmplitude.real} + {tauAmplitude.imag}i");
                // TQSim's fixed-total-tau sigma_2 |0> reference, also used by the Godot package harness.
                if (Math.Abs(braid.logical_state[0].real + 0.5) > 1e-9
                    || Math.Abs(braid.logical_state[0].imag - 0.3632712640026805) > 1e-9
                    || Math.Abs(tauAmplitude.real + 0.24293413587832285) > 1e-9
                    || Math.Abs(tauAmplitude.imag + 0.7476743906106105) > 1e-9
                    || Math.Abs(braid.fusion_probabilities.tau - 0.6180339887498949) > 1e-9)
                {
                    Debug.LogWarning("Braid sigma_2 reference did not match the API result.");
                }
            }
            catch (QuantumApiError error)
            {
                Debug.LogWarning($"Braid example failed: {error.Message}");
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
