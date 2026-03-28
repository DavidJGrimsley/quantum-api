# Quantum API Python SDK (Scaffold)

Python HTTPX client scaffold for Quantum API `/v1`.

## Usage

```python
from quantum_api_sdk import QuantumApiClient

client = QuantumApiClient(base_url="http://127.0.0.1:8000/v1")

health = client.health()
print(health)

gate = client.run_gate("rotation", rotation_angle_rad=1.57079632679)
print(gate)

client.close()
```
