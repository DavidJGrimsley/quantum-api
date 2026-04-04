from quantum_api_sdk import QuantumApiClient, QuantumApiError


def main() -> None:
    with QuantumApiClient(
        base_url="http://127.0.0.1:8000",
        api_key="dev-local-key",
    ) as client:
        try:
            print(client.health())
            print(client.run_gate({"gate_type": "bit_flip"}))
            print(client.transform_text({"text": "memory and quantum signal"}))
        except QuantumApiError as exc:
            print(exc.status_code, exc.code, exc.request_id, exc.details)


if __name__ == "__main__":
    main()
