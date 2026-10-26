import { LeaderboardApi } from './leaderboardApi.js';
import { LeaderboardRenderer } from './leaderboardRenderer.js';
import { LeaderboardUpdater } from './leaderboardUpdater.js';

const api = new LeaderboardApi();
const renderer = new LeaderboardRenderer(document);
const updater = new LeaderboardUpdater(api, renderer);

updater.start();
