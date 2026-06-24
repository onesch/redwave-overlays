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
        self, my_dist: float, dist: float, est_lap_time: float
    ) -> dict[str, float | None] | None:
        """
        Calculate the lap and time gap between the player and another car.
        """
        if not isinstance(dist, (int, float)) or dist < 0:
            return None

        gap_pct = (dist - my_dist) % 1.0
        gap_sec = gap_pct * est_lap_time if est_lap_time else None
        return {"gap_pct": gap_pct, "gap_sec": gap_sec}

    def _collect_candidates(
        self, player_idx: int, ctx: LeaderboardContext
    ) -> tuple[list[dict], list[dict]]:
        """Collect all potential neighboring cars around the player."""
        my_dist: float = ctx.lap_dist_pct[player_idx]
        my_est_lap_time: float = (
            ctx.drivers[player_idx]
            .get("CarClassEstLapTime")
        )

        ahead, behind = [], []

        for idx, dist in enumerate(ctx.lap_dist_pct):
            if idx == player_idx:
                continue
            if idx >= len(ctx.drivers):
                continue
            car_data = self.builder.build(idx, ctx)
            if not car_data:
                continue

            gap = self._calc_gap(my_dist, dist, my_est_lap_time)
            if not gap:
                continue

            lap_diff = ctx.laps_started[idx] - ctx.laps_started[player_idx]

            if lap_diff > 0:
                car_data["lap_status"] = "ahead_lap"
            elif lap_diff < 0:
                car_data["lap_status"] = "behind_lap"
            else:
                car_data["lap_status"] = None

            if 0 < gap["gap_pct"] <= 0.5:
                ahead.append({"car": car_data, **gap})
            elif gap["gap_pct"] > 0.5:
                behind.append(
                    {
                        "car": car_data,
                        "gap_pct": gap["gap_pct"] - 1.0,
                        "gap_sec": (gap["gap_pct"] - 1.0) * my_est_lap_time,
                    }
                )

        return ahead, behind

    @staticmethod
    def _sort_candidates(
        ahead: list[dict], behind: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        """Sort neighboring cars in-place by their distance to the player."""
        ahead.sort(key=lambda x: x["gap_pct"])
        behind.sort(key=lambda x: x["gap_pct"], reverse=True)
        return ahead, behind

    @staticmethod
    def _format_neighbors(
        ahead: list[dict], behind: list[dict], limit=3
    ) -> dict[str, list[dict]]:
        """
        Format neighboring car data for external use.

        Limits the number of cars returned and normalizes gap values,
        returning a structure ready for API or UI consumption.
        """

        def fmt(c):
            return {
                **c["car"],
                "gap_pct": round(abs(c["gap_pct"]), 3),
                "gap_sec": (
                    round(abs(c["gap_sec"]), 2) if c["gap_sec"] else None
                ),
            }

        return {
            "ahead": [fmt(c) for c in ahead[:limit]],
            "behind": [fmt(c) for c in behind[:limit]],
        }
