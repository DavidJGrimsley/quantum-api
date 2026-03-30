from quantum_api_sdk import QuantumApiClient


def main() -> None:
    client = QuantumApiClient(base_url="http://127.0.0.1:8000/v1", api_key="dev-local-key")
    try:
        print(client.health())
        print(client.run_gate("bit_flip"))
        print(client.transform_text("memory and quantum signal"))
    finally:
        client.close()


if __name__ == "__main__":
    main()
