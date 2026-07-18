from backend.services.leaderboard.context import LeaderboardContext


class NeighborsService:
    """
    Service responsible for detecting cars around the player
    and preparing neighbor data for Leaderboard presentation.
    """

    PHYSICAL_TRAFFIC_LIMIT = 3  # display three nearby cars of a different class ahead and behind.

    def __init__(self, builder):
        self.builder = builder

    def get_neighbors(self, player_idx, ctx) -> dict:
        """
        Calculate and return cars surrounding the player.
        
        1. Collect all possible candidates around the player.
        2. Split candidates into:
        - cars ahead;
        - cars behind;
        - physical traffic ahead;
        - physical traffic behind.
        3. Sort cars by their physical distance from the player.
        4. Format data into a structure ready for API/UI.

        Returns:
            {
                "ahead": [...],
                "behind": [...],
                "physical_ahead": [...],
                "physical_behind": [...]
            }
        """
        ahead, behind, physical_ahead, physical_behind = self._collect_candidates(
            player_idx, ctx
        )
        ahead, behind = self._sort_candidates(ahead, behind)
        physical_ahead, physical_behind = self._sort_candidates(
            physical_ahead, physical_behind
        )
        result = self._format_neighbors(ahead, behind)
        result["physical_ahead"] = self._format_candidate_list(
            physical_ahead, self.PHYSICAL_TRAFFIC_LIMIT
        )
        result["physical_behind"] = self._format_candidate_list(
            physical_behind, self.PHYSICAL_TRAFFIC_LIMIT
        )
        return result

    def _calc_gap(
        self,
        my_dist: float,
        my_laps: int,
        my_est_time: float,
        my_est_lap_time: float,
        dist: float,
        other_laps: int,
        other_est_time: float,
    ) -> dict[str, float | None] | None:
        """
        Calculate physical and time distance between two cars.

        - gap_pct:
            Physical distance difference on the track.
        - gap_sec:
            Time difference between two cars based on CarIdxEstTime.
            """
        if not isinstance(dist, (int, float)) or dist < 0:
            return None

        if not isinstance(my_dist, (int, float)) or my_dist < 0:
            return None

        raw = (other_laps + dist) - (my_laps + my_dist)

        # Shortest signed positional distance on a circular track. Use this for
        # physical ahead/behind decisions, including S/F-line wrap-around.
        gap_pct = raw - round(raw)

        gap_sec = None
        if other_est_time > 0 and my_est_time > 0:
            gap_sec = other_est_time - my_est_time

            if my_est_lap_time:
                half_lap = my_est_lap_time / 2
                if gap_sec > half_lap:
                    gap_sec -= my_est_lap_time
                elif gap_sec < -half_lap:
                    gap_sec += my_est_lap_time

        return {
            "gap_pct": gap_pct,
            "gap_sec": gap_sec,
        }

    def _collect_candidates(
        self,
        player_idx: int,
        ctx: LeaderboardContext,
    ) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
        """
        Collect all cars that can be displayed around the player.

        1. Get player's current state
        2. Iterate through every driver in the session.
        3. Skip drivers that are the player or have incomplete telemetry.
        4. Calculate gap between player and candidate car.
        5. Add metadata:
            - lap_diff: Shows whether another car is on another lap.
            - same_class: Indicates if car belongs to the same racing class.
            - racing_relevance: direct racing competitor = class; another class, physical traffic only = traffic.
        6. Add candidate into:
            - ahead / behind: All physically nearby cars.
            - physical_ahead / physical_behind: Only multiclass traffic cars.
        """
        my_dist = ctx.lap_dist_pct[player_idx]
        my_laps = ctx.laps_started[player_idx]
        my_driver = ctx.drivers[player_idx]
        my_class_id = my_driver.get("CarClassID")
        my_est_lap_time = my_driver.get("CarClassEstLapTime") or 0.0

        my_est_time = (
            ctx.est_times[player_idx]
            if player_idx < len(ctx.est_times)
            else 0.0
        )

        ahead = []
        behind = []
        physical_ahead = []
        physical_behind = []

        for idx in range(len(ctx.drivers)):
            if idx == player_idx:
                continue

            if not self._has_required_arrays(idx, ctx):
                continue

            car_data = self.builder.build(idx, ctx)
            if not car_data:
                continue

            other_driver = ctx.drivers[idx]
            same_class = other_driver.get("CarClassID") == my_class_id
            other_laps = ctx.laps_started[idx]

            gap = self._calc_gap(
                my_dist=my_dist,
                my_laps=my_laps,
                my_est_time=my_est_time,
                my_est_lap_time=my_est_lap_time,
                dist=ctx.lap_dist_pct[idx],
                other_laps=other_laps,
                other_est_time=ctx.est_times[idx],
            )

            if not gap or gap["gap_pct"] == 0:
                continue

            car_data["lap_diff"] = self._get_lap_diff(my_laps, other_laps)
            car_data["same_class"] = same_class
            car_data["racing_relevance"] = "class" if same_class else "traffic"

            candidate = {"car": car_data, **gap}
            target = ahead if gap["gap_pct"] > 0 else behind
            target.append(candidate)

            if same_class:
                continue

            # Keep other-class cars available as a separate traffic layer,
            # but do not remove them from the main lap-distance neighbors.
            traffic_target = physical_ahead if gap["gap_pct"] > 0 else physical_behind
            traffic_target.append(candidate)

        return ahead, behind, physical_ahead, physical_behind

    @staticmethod
    def _has_required_arrays(idx: int, ctx: LeaderboardContext) -> bool:
        """
        Validate that driver has all required telemetry arrays.

        A driver can exist in the session data but have incomplete telemetry.

        Required data:
            - lap distance;
            - lap count;
            - estimated time.

        Returns:
            True if driver data is complete enough for calculations.
        """
        return (
            idx < len(ctx.lap_dist_pct)
            and idx < len(ctx.laps_started)
            and idx < len(ctx.est_times)
        )

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
        Sort neighboring cars by physical relative position.
        """
        ahead.sort(key=lambda x: x["gap_pct"])
        behind.sort(key=lambda x: x["gap_pct"], reverse=True)

        return ahead, behind

    @classmethod
    def _format_candidate_list(cls, cars: list[dict], limit: int) -> list[dict]:
        """
        Convert internal candidate objects into API/UI format.
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

        return [fmt(car) for car in cars[:limit]]

    @classmethod
    def _format_neighbors(
        cls,
        ahead: list[dict],
        behind: list[dict],
        limit: int = 3,
    ) -> dict[str, list[dict]]:
        """
        Format racing neighbors for API/UI.
        """
        return {
            "ahead": cls._format_candidate_list(ahead, limit),
            "behind": cls._format_candidate_list(behind, limit),
        }
