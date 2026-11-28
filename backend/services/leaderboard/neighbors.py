from backend.components.car_class import CarClassComponent
from backend.components.lap_relation import LapRelationComponent
from backend.components.time_gap import TimeGapComponent
from backend.components.track_position import TrackPositionComponent
from backend.services.leaderboard.context import LeaderboardContext


class NeighborsService:
    """
    Service responsible for detecting cars around the player
    and preparing neighbor data for Leaderboard presentation.
    """

    def __init__(self, builder):
        self.builder = builder
        self.time_gap = TimeGapComponent()

    def get_neighbors(self, player_idx, ctx) -> dict:
        """
        Calculate and return cars surrounding the player.
        
        1. Collect all cars on the track, of every class, and split them
           into cars ahead and cars behind the player.
        2. Sort cars by their physical distance from the player.
        3. Format data into a structure ready for API/UI.

        Returns:
            {
                "ahead": [...],
                "behind": [...]
            }
        """
        ahead, behind = self._collect_candidates(player_idx, ctx)
        ahead, behind = self._sort_candidates(ahead, behind)
        return self._format_neighbors(ahead, behind)

    def _collect_candidates(
        self,
        player_idx: int,
        ctx: LeaderboardContext,
    ) -> tuple[list[dict], list[dict]]:
        """
        Collect cars around the player and group them by relative
        track position.
        """
        # Validate the player's required telemetry arrays.
        if not self._has_required_arrays(player_idx, ctx):
            return [], []

        player = ctx.car_positions.get(player_idx)
        if player is None:
            return [], []

        ahead = []
        behind = []

        # Collect valid cars around the player.
        for idx in range(len(ctx.drivers)):
            if idx == player_idx:
                continue

            if not self._has_required_arrays(idx, ctx):
                continue

            car_data = self.builder.build(idx, ctx)
            if not car_data:
                continue

            car = ctx.car_positions.get(idx)
            if car is None:
                continue

            # Skip cars off the track or level with the player.
            gap_pct = TrackPositionComponent.distance_gap(
                player.lap_dist_pct,
                car.lap_dist_pct,
            )

            if gap_pct is None or gap_pct == 0:
                continue

            gap_sec = self.time_gap.time_gap(player, car, ctx.track_time_line)

            lap_delta = ctx.lap_deltas.get(idx)
            car_data["is_lap_ahead"] = LapRelationComponent.is_lap_ahead(lap_delta)
            car_data["is_lap_behind"] = LapRelationComponent.is_lap_behind(lap_delta)
            car_data["same_class"] = CarClassComponent.is_same_class(
                player.class_id,
                car.class_id,
            )

            candidate = {"car": car_data, "gap_pct": gap_pct, "gap_sec": gap_sec}
            target = ahead if gap_pct > 0 else behind
            target.append(candidate)

        return ahead, behind

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
    def _format_candidate_list(
        cls,
        cars: list[dict],
        limit: int = 3,
    ) -> list[dict]:
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
            0 <= idx < len(ctx.lap_dist_pct)
            and 0 <= idx < len(ctx.laps_started)
            and 0 <= idx < len(ctx.est_times)
        )
