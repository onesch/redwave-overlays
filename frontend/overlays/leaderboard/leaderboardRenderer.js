import { BaseRenderer } from '../shared/baseRenderer.js';
import {
    DEFAULT_FORMAT,
    columnWidths,
    format,
    headerLabel,
    normalizeFormat,
    placeholder,
} from './lastLapTime.js';

export class LeaderboardRenderer extends BaseRenderer {
    constructor(document) {
        super(document);

        this.lastLapFormat = DEFAULT_FORMAT;
        this.data = null;
    }

    render(data) {
        this.data = data;
        if (!data.player || !data.neighbors) {
            return;
        }

        // Hide all neighbor rows first
        for (let i = 1; i <= 3; i++) {
            this.document.getElementById(`ahead-row-${i}`).style.display = 'none';
            this.document.getElementById(`behind-row-${i}`).style.display = 'none';
        }

        // Render the player
        this.renderPlayer(data.player);

        const aheadCars = data.neighbors.ahead || [];
        const behindCars = data.neighbors.behind || [];

        // Render ahead cars
        for (let i = 0; i < 3; i++) {
            const rowId = `ahead-row-${i + 1}`;
            if (i < aheadCars.length) {
                this.renderCar(rowId, aheadCars[i]);
            }
        }

        // Render behind cars
        for (let i = 0; i < 3; i++) {
            const rowId = `behind-row-${i + 1}`;
            if (i < behindCars.length) {
                this.renderCar(rowId, behindCars[i]);
            }
        }

        // Update session lap time
        this.updateSessionLapTime(
            data.leaderboard_data.session_laps,
            data.leaderboard_data.session_time,
            data.leaderboard_data.player_lap_time,
            data.player.laps_started
        );
        // Update Strength of Field
        this.updateStrengthOfField(data.leaderboard_data.sof);
        // Update session time
        this.updateSessionTime(
            data.leaderboard_data.session_time_current,
            data.leaderboard_data.session_time_formatted,
        );
    }

    setLastLapFormat(value) {
        this.lastLapFormat = normalizeFormat(value);
        this.updateColumnWidths();
        this.updateLastLapHeader();
        this.updateEmptyTimePlaceholders();

        if (this.data) this.render(this.data);
    }

    setBackgroundOpacity(value) {
        const card = this.document.querySelector('.overlay-bg-opacity-target');
        if (card) card.style.setProperty('--overlay-bg-opacity', value);
    }

    updateColumnWidths() {
        const card = this.document.querySelector('.card');
        if (!card) return;

        const widths = columnWidths(this.lastLapFormat);
        card.style.setProperty('--driver-column-width', widths.driver);
        card.style.setProperty('--time-column-width', widths.time);
    }

    updateLastLapHeader() {
        const header = this.document.getElementById('last-lap-header');
        if (header) header.textContent = headerLabel(this.lastLapFormat);
    }

    updateEmptyTimePlaceholders() {
        const emptyTime = placeholder(this.lastLapFormat);
        this.document.querySelectorAll('.time').forEach((element) => {
            if (element.classList.contains('empty') || element.textContent.startsWith('--')) {
                element.textContent = emptyTime;
            }
        });
    }

    renderPlayer(player) {
        const row = this.document.getElementById('player-row');
        this.renderRow(row, player);

        const posElement = row.querySelector('.pos');
        if (posElement && !posElement.classList.contains('me')) {
            posElement.classList.add('me');
        }

        const gapElement = row.querySelector('.gap');
        if (gapElement) {
            gapElement.textContent = '0.0';
        }
    }

    renderCar(rowId, car) {
        const row = this.document.getElementById(rowId);
        row.style.display = 'grid';
        this.renderRow(row, car);
    }

    intToRgb(num) {
        const r = (num >> 16) & 255;
        const g = (num >> 8) & 255;
        const b = num & 255;
        return [r, g, b];
    }

    applyGradient(numElement, rgbInt) {
        const [r, g, b] = this.intToRgb(rgbInt);
        numElement.style.backgroundImage = `
            linear-gradient(to right,
                rgba(${r},${g},${b},1),
                rgba(${r},${g},${b},0.2),
                rgba(${r},${g},${b},0)
            )
        `;
    }

    renderRow(rowElement, car) {
        this.renderPositionAndCar(rowElement, car);
        this.renderDriver(rowElement, car);
        this.renderLicenseAndIrating(rowElement, car);
        this.renderGapAndLap(rowElement, car);
    }

    renderPositionAndCar(rowElement, car) {
        if (!car) return;
        const posElement = rowElement.querySelector('.pos');
        posElement.textContent = car.pos || '--';
        const numElement = rowElement.querySelector('.num');
        numElement.textContent = car.car_number ? `#${car.car_number}` : '--';

        if (car.car_class_color) {
            if (car.car_class_color === 0xFFFFFF) {
                numElement.style.backgroundImage = 'none';
            } else {
                this.applyGradient(numElement, car.car_class_color);
            }
        } else {
            numElement.style.backgroundImage = '';
            numElement.style.color = '';
        }
    }

    renderDriver(rowElement, car) {
        if (!car) return;
        this.renderDriverName(rowElement, car);
        this.renderStatusIndicators(rowElement, car);
    }

    renderStatusIndicators(rowElement, car) {
        this.renderPitFlag(rowElement, car);
        this.renderRadioFlag(rowElement, car);
    }

    renderRadioFlag(rowElement, car) {
        const nameElement = rowElement.querySelector('.driver .name');
        const radioFlag = rowElement.querySelector('.driver .radio-flag');

        if (car.is_radio_transmitting) {
            radioFlag.style.display = 'inline-flex';
            nameElement.classList.add('with-flag', 'gradient');
            return;
        }

        radioFlag.style.display = 'none';
    }

    renderPitFlag(rowElement, car) {
        const nameElement = rowElement.querySelector('.driver .name');
        const pitFlag = rowElement.querySelector('.driver .pit-flag');

        let pitLapText = this.formatPitLap(car.last_pit_lap);

        if (car.is_in_pitroad) {
            nameElement.classList.add(
                'with-flag',
                'in-pit',
                'gradient'
            );

            this.showPitFlag(pitFlag, pitLapText);
            return;
        }

        if (pitLapText) {
            nameElement.classList.add(
                'with-flag',
                'gradient'
            );

            this.showPitFlag(pitFlag, pitLapText);
            return;
        }

        pitFlag.style.display = 'none';
    }

    formatPitLap(pitLapText) {
        switch (pitLapText) {
            case "IN L0":
                return "IN PIT";

            case "L0":
                return "";

            case "OUT L0":
                return "OUT PIT";

            default:
                return pitLapText;
        }
    }

    showPitFlag(element, text) {
        if (!text) {
            element.style.display = 'none';
            return;
        }

        element.textContent = text;
        element.style.display = 'inline-flex';
    }

    renderDriverName(rowElement, car) {
        const nameElement = rowElement.querySelector('.driver .name');
        nameElement.textContent = car.name || 'Unknown';

        nameElement.classList.remove(
            'with-flag',
            'in-pit',
            'gradient'
        );
    }

    renderLicenseAndIrating(rowElement, car) {
        if (!car) return;
        const licElement = rowElement.querySelector('.lic');
        if (car.license) {
            let licenseText = car.license;
            if (licenseText.length > 5) {
                licenseText = licenseText.slice(0, 5) + licenseText.slice(6);
            }
            licElement.textContent = licenseText;
            licElement.className = 'lic';
            licElement.classList.add(licenseText.charAt(0).toLowerCase());
        } else {
            licElement.textContent = '--';
            licElement.className = 'lic';
        }

        const irElement = rowElement.querySelector('.ir');
        irElement.textContent = car.irating
            ? (Math.floor(car.irating / 100) / 10).toFixed(1) + 'k'
            : '--';

        this.renderIratingDelta(rowElement, car);
    }

    renderIratingDelta(rowElement, car) {
        const deltaElement = rowElement.querySelector('.ir-delta');
        if (!deltaElement) return;

        const delta = this.data?.irating_deltas?.[car.driver_id];
        deltaElement.className = 'ir-delta';

        if (delta === undefined || delta === null) {
            deltaElement.textContent = '--';
            return;
        }

        deltaElement.textContent = `${delta > 0 ? '+' : ''}${delta}`;

        if (delta > 0) {
            deltaElement.classList.add('positive');
        } else if (delta < 0) {
            deltaElement.classList.add('negative');
        }
    }

    renderGapAndLap(rowElement, car) {
        if (!car) return;

        const gapElement = rowElement.querySelector('.gap');
        gapElement.className = 'gap';

        switch (car.lap_diff) {
            case "ahead_lap":
                gapElement.classList.add('ahead_lap');
                break;

            case "behind_lap":
                gapElement.classList.add('behind_lap');
                break;
        }

        if (car.is_in_pitroad) {
            gapElement.classList.add('in-pit');
        }

        this.updateLapTime(rowElement, car);
        this.updateGap(rowElement, car.gap_sec);
    }

    updateLapTime(row, car) {
        const lapElement = row.querySelector('.time');
        if (!lapElement) return;

        lapElement.textContent = format(car.last_lap_seconds, this.lastLapFormat);
        lapElement.className = 'time';

        // Increase spacing only when there is no valid lap time
        const isEmptyTime = car.last_lap_seconds === -1.0;
        lapElement.classList.toggle('empty', isEmptyTime);

        const color = this._resolveLapColor(car);
        if (color) {
            lapElement.classList.add(color);
        }
    }

    _resolveLapColor(car) {
        if (car.last_lap_seconds === -1.0 || car.best_lap_seconds === -1.0) return null;

        if (car.last_lap_seconds === car.session_fastest_lap_seconds ||
            car.last_lap_seconds === car.class_fastest_lap_seconds) {
            return 'session-best';
        }

        if (car.last_lap_seconds === car.best_lap_seconds) {
            return 'personal-best';
        }

        return null;
    }

    updateGap(row, gapSec) {
        const gapElement = row.querySelector('.gap');
        if (!gapElement) return;
        if (gapSec === undefined || gapSec === null) {
            gapElement.textContent = '--';
        } else {
            gapElement.textContent = `${gapSec.toFixed(1)}`;
        }
    }

    updateSessionLapTime(sessionLaps, sessionTime, playerLapTime, lapsStarted) {
        const currentElement = this.document.getElementById('laps-current');
        const totalElement = this.document.getElementById('laps-total');

        currentElement.textContent = lapsStarted;
        if (sessionLaps !== "unlimited") {
            totalElement.textContent = sessionLaps;
        } else {
            totalElement.textContent = `~${(sessionTime / playerLapTime).toFixed(1)}`;
        }
    }

    updateStrengthOfField(sof) {
        const sofElement = this.document.getElementById('sof');
        sofElement.textContent = sof || '--';
    }

    updateSessionTime(current_time, total_time) {
        const currentElement = this.document.getElementById('time-current');
        const totalElement = this.document.getElementById('time-total');
        currentElement.textContent = current_time;
        totalElement.textContent = total_time;
    }
}
