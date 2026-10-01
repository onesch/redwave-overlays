import { TelemetryApi } from './telemetryApi.js';
import { TelemetryRenderer } from './telemetryRenderer.js';
import { TelemetryUpdater } from './telemetryUpdater.js';

const api = new TelemetryApi();
const renderer = new TelemetryRenderer(document, window);
const updater = new TelemetryUpdater(api, renderer);

updater.start();
