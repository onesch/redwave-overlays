import { TrackMapApi } from './track-mapApi.js';
import { TrackMapRenderer } from './track-mapRenderer.js';
import { TrackMapUpdater } from './track-mapUpdater.js';

const api = new TrackMapApi();
const renderer = new TrackMapRenderer(document);
const updater = new TrackMapUpdater(api, renderer);

updater.start();
