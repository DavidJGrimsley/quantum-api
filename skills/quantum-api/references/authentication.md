# Runtime credentials

The public `GET /v1/health` endpoint needs no credentials. Other runtime
endpoints, including `GET /v1/echo-types`, use `X-API-Key`.

Ask the user for an existing key or for the URL of a backend proxy that adds
the key server-side. Do not place a key in source control, a browser bundle,
or a distributed game. The example key
`qapi_devlocal_0123456789abcdef0123456789abcdef` works only against a local
server configured with `APP_ENV=development`.

For IBM backend discovery, transpilation, and jobs, send an existing
`ibm_profile` name supplied by the user when needed. If omitted, the service
may use the owner's configured default. Do not collect or transmit an IBM
token in a runtime request.

Key lifecycle and IBM credential-profile administration are reserved for the
owner. Integration agents do not perform those operations. If the required
key or profile does not exist, ask the owner to arrange it.
