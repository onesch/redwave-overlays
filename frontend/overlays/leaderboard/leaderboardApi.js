export class LeaderboardApi {
    constructor(
        endpoint = '/api/leaderboard',
        fetchImpl = globalThis.fetch.bind(globalThis),
    ) {
        this.endpoint = endpoint;
        this.fetchImpl = fetchImpl;
    }

    async getLeaderboard() {
        const response = await this.fetchImpl(this.endpoint);

        if (!response.ok) {
            throw new Error(
                `Failed to fetch leaderboard: ${response.status}`
            );
        }

        return response.json();
    }
}
