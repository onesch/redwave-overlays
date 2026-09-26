import { RadarApi } from './radarApi.js';
import { RadarRenderer } from './radarRenderer.js';
import { RadarUpdater } from './radarUpdater.js';

const api = new RadarApi();
const renderer = new RadarRenderer(document);
const updater = new RadarUpdater(api, renderer);

updater.start();
