using System.Threading.Tasks;
using QuantumApi.Unity;
using UnityEngine;

namespace QuantumApi.Unity.Samples
{
    public sealed class QuantumApiExample : MonoBehaviour
    {
        [SerializeField]
        private string baseUrl = "https://example.com/public-facing/api/quantum";

        [SerializeField]
        private bool backendProxyMode = true;

        [SerializeField]
        private string apiKey = "";

        private QuantumApiClient _client;

        private void Awake()
        {
            _client = new QuantumApiClient(new QuantumApiClientOptions
            {
                BaseUrl = baseUrl,
                BackendProxyMode = backendProxyMode,
                ApiKey = apiKey,
                TimeoutSeconds = 15,
            });
        }

        private void Start()
        {
            StartCoroutine(_client.HealthCoroutine(
                health => Debug.Log($"Quantum API ready: {health.status} ({health.runtime_mode})"),
                error => Debug.LogWarning($"Health check failed: {error.Message}")));

            _ = RunTextTransformExampleAsync();
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
