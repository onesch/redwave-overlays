export class TrackMapApi {
    constructor(
        endpoint = '/api/track-map',
        fetchImpl = globalThis.fetch.bind(globalThis),
    ) {
        this.endpoint = endpoint;
        this.fetchImpl = fetchImpl;
    }

    async getTrackMap() {
        const response = await this.fetchImpl(this.endpoint);
        if (!response.ok) {
            throw new Error(`Failed to fetch track map: ${response.status}`);
        }
        return response.json();
    }
}
