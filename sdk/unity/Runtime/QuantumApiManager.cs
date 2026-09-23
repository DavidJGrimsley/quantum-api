using UnityEngine;

namespace QuantumApi.Unity
{
    /// <summary>One shared Quantum API client for a Unity game.</summary>
    [DisallowMultipleComponent]
    public sealed class QuantumApiManager : MonoBehaviour
    {
        [Header("Quantum API")]
        [SerializeField] private bool backendProxyMode;
        [SerializeField] private string apiKey = "";
        [SerializeField, Min(1)] private int timeoutSeconds = 20;

        public static QuantumApiManager Instance { get; private set; }
        public QuantumApiClient Client { get; private set; }
        public bool BackendProxyMode => backendProxyMode;
        public bool IsConfigured => backendProxyMode || !string.IsNullOrWhiteSpace(apiKey);

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetInstance()
        {
            Instance = null;
        }

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }

            Instance = this;
            DontDestroyOnLoad(gameObject);
            Client = new QuantumApiClient(new QuantumApiClientOptions
            {
                BackendProxyMode = backendProxyMode,
                ApiKey = backendProxyMode ? "" : (apiKey ?? "").Trim(),
                TimeoutSeconds = timeoutSeconds > 0 ? timeoutSeconds : 20,
            });
        }

        private void Start()
        {
            CheckHealth();
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
        }

        [ContextMenu("Check Health")]
        public void CheckHealth()
        {
            if (!ReadyForRequest())
            {
                return;
            }

            StartCoroutine(Client.HealthCoroutine(
                response => Debug.Log($"Quantum API health: {response.status} ({response.runtime_mode})", this),
                error => Debug.LogWarning($"Quantum API health check failed: {error.Message}", this)));
        }

        [ContextMenu("Request Random (0-1)")]
        public void RequestRandom()
        {
            if (!ReadyForRequest())
            {
                return;
            }

            if (!IsConfigured)
            {
                Debug.LogWarning("Quantum API key is empty. Set API Key on QuantumApiManager in the Inspector.", this);
                return;
            }

            StartCoroutine(Client.RandomIntCoroutine(
                0,
                1,
                response => Debug.Log($"Quantum API random: {response.value} (source: {response.source})", this),
                error => Debug.LogWarning($"Quantum API random request failed: {error.Message}", this)));
        }

        private bool ReadyForRequest()
        {
            if (Application.isPlaying && Instance == this && Client != null)
            {
                return true;
            }

            Debug.LogWarning("Enter Play Mode to use QuantumApiManager requests.", this);
            return false;
        }
    }
}
