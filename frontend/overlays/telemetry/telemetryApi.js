export class TelemetryApi {
    constructor(
        endpoint = '/api/telemetry',
        fetchImpl = globalThis.fetch.bind(globalThis),
    ) {
        this.endpoint = endpoint;
        this.fetchImpl = fetchImpl;
    }

    async getTelemetry() {
        const response = await this.fetchImpl(this.endpoint);
        if (!response.ok) {
            throw new Error(`Failed to fetch telemetry: ${response.status}`);
        }
        return response.json();
    }
}
