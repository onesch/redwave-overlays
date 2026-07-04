from backend.services.leaderboard.context import LeaderboardContext


class NeighborsService:
    """
    Service responsible for finding and formatting neighboring cars
    (ahead and behind the player) based on lap distance.
    """

    def __init__(self, builder):
        self.builder = builder

    def get_neighbors(self, player_idx, ctx) -> dict:
        """
        Return neighboring cars ahead and behind the player.
        """
        ahead, behind = self._collect_candidates(player_idx, ctx)
        ahead, behind = self._sort_candidates(ahead, behind)
        return self._format_neighbors(ahead, behind)

    def _calc_gap(
        self,
        my_dist: float,
        my_laps: int,
        my_est_time: float,
        dist: float,
        other_laps: int,
        other_est_time: float,
        other_est_lap_time: float,
    ) -> dict[str, float | None] | None:
        """
        Calculate positional and time gap between the player
        and another car.
        """
        if not isinstance(dist, (int, float)) or dist < 0:
            return None

        raw = (other_laps + dist) - (my_laps + my_dist)

        # shortest positional distance on circular track
        gap_pct = raw - round(raw)

        gap_sec = None

        if other_est_time > 0 and my_est_time > 0:
            gap_sec = other_est_time - my_est_time

            if other_est_lap_time:
                half_lap = other_est_lap_time / 2

                if gap_sec > half_lap:
                    gap_sec -= other_est_lap_time
                elif gap_sec < -half_lap:
                    gap_sec += other_est_lap_time

        return {
            "gap_pct": gap_pct,
            "gap_sec": gap_sec,
        }

    def _collect_candidates(
        self,
        player_idx: int,
        ctx: LeaderboardContext,
    ) -> tuple[list[dict], list[dict]]:
        """
        Collect all potential neighboring cars around the player.
        """
        my_dist = ctx.lap_dist_pct[player_idx]
        my_laps = ctx.laps_started[player_idx]

        my_est_time = (
            ctx.est_times[player_idx]
            if player_idx < len(ctx.est_times)
            else 0.0
        )

        ahead = []
        behind = []

        for idx in range(len(ctx.drivers)):
            if idx == player_idx:
                continue

            if idx >= len(ctx.lap_dist_pct):
                continue

            if idx >= len(ctx.laps_started):
                continue

            if idx >= len(ctx.est_times):
                continue

            car_data = self.builder.build(idx, ctx)
            if not car_data:
                continue

            dist = ctx.lap_dist_pct[idx]
            other_laps = ctx.laps_started[idx]

            other_est_time = ctx.est_times[idx]

            other_est_lap_time = (
                ctx.drivers[idx].get("CarClassEstLapTime")
                or 0.0
            )

            gap = self._calc_gap(
                my_dist=my_dist,
                my_laps=my_laps,
                my_est_time=my_est_time,
                dist=dist,
                other_laps=other_laps,
                other_est_time=other_est_time,
                other_est_lap_time=other_est_lap_time,
            )

            if not gap:
                continue

            gap_sec = gap["gap_sec"]

            car_data["lap_diff"] = self._get_lap_diff(
                my_laps,
                other_laps,
            )

            if gap_sec is None:
                continue

            if gap_sec > 0:
                ahead.append(
                    {
                        "car": car_data,
                        **gap,
                    }
                )
            elif gap_sec < 0:
                behind.append(
                    {
                        "car": car_data,
                        **gap,
                    }
                )

        return ahead, behind

    @staticmethod
    def _get_lap_diff(
        player_laps: int,
        other_laps: int,
    ) -> str | None:
        """
        Determine lap relation between the player and another car.
        """
        lap_diff = other_laps - player_laps

        if lap_diff > 0:
            return "ahead_lap"

        if lap_diff < 0:
            return "behind_lap"

        return None

    @staticmethod
    def _sort_candidates(
        ahead: list[dict],
        behind: list[dict],
    ) -> tuple[list[dict], list[dict]]:
        """
        Sort neighboring cars by relative position.
        """
        ahead.sort(key=lambda x: x["gap_pct"])
        behind.sort(
            key=lambda x: x["gap_pct"],
            reverse=True,
        )

        return ahead, behind

    @staticmethod
    def _format_neighbors(
        ahead: list[dict],
        behind: list[dict],
        limit: int = 3,
    ) -> dict[str, list[dict]]:
        """
        Format neighboring cars for API/UI.
        """

        def fmt(car: dict) -> dict:
            return {
                **car["car"],
                "gap_pct": round(abs(car["gap_pct"]), 4),
                "gap_sec": (
                    round(abs(car["gap_sec"]), 2)
                    if car["gap_sec"] is not None
                    else None
                ),
            }

        return {
            "ahead": [fmt(car) for car in ahead[:limit]],
            "behind": [fmt(car) for car in behind[:limit]],
        }
