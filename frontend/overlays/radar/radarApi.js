export class RadarApi {
    constructor(
        endpoint = '/api/radar',
        fetchImpl = globalThis.fetch.bind(globalThis),
    ) {
        this.endpoint = endpoint;
        this.fetchImpl = fetchImpl;
    }

    async getRadar() {
        const response = await this.fetchImpl(this.endpoint);

        if (!response.ok) {
            throw new Error(`Failed to fetch radar: ${response.status}`);
        }

        return response.json();
    }
}
