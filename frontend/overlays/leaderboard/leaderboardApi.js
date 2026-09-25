export class LeaderboardApi {
    constructor(
        endpoint = '/api/leaderboard',
        fetchImpl = globalThis.fetch.bind(globalThis),
    ) {
        this.endpoint = endpoint;
        this.fetchImpl = fetchImpl;
    }

    // Fetch the latest leaderboard DTO from the backend API.
    async getLeaderboard() {
        const response = await this.fetchImpl(this.endpoint);

        // Treat non-success HTTP responses as API errors.
        if (!response.ok) {
            throw new Error(
                `Failed to fetch leaderboard: ${response.status}`
            );
        }

        // Parse and return the backend DTO as-is.
        return response.json();
    }
}
