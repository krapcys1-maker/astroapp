from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.engine.natal.aspect_calculator import MAJOR_ASPECTS
from app.utils.angle_utils import (
    normalize_angle,
    shortest_angular_distance,
    signed_angular_difference,
)


def aspect_deviation(transit_longitude: float, natal_longitude: float, aspect_type: str) -> float:
    target_angle = MAJOR_ASPECTS[aspect_type]
    separation = shortest_angular_distance(transit_longitude, natal_longitude)
    return abs(separation - target_angle)


def in_orb(
    transit_longitude: float,
    natal_longitude: float,
    aspect_type: str,
    orb: float,
) -> bool:
    return aspect_deviation(transit_longitude, natal_longitude, aspect_type) <= orb


def _candidate_targets(natal_longitude: float, aspect_type: str) -> tuple[float, ...]:
    exact_angle = MAJOR_ASPECTS[aspect_type]
    if exact_angle in {0.0, 180.0}:
        return (normalize_angle(natal_longitude + exact_angle),)
    return (
        normalize_angle(natal_longitude + exact_angle),
        normalize_angle(natal_longitude - exact_angle),
    )


@dataclass(slots=True, frozen=True)
class RefinedExact:
    exact_dt: datetime | None
    exact_orb: float | None
    phase: str


class EventRefiner:
    def __init__(self, resolution: timedelta = timedelta(minutes=1)) -> None:
        self._resolution = resolution

    def refine_boundary(
        self,
        start_dt: datetime,
        end_dt: datetime,
        evaluator,
        expected_state_at_end: bool,
    ) -> datetime:
        left = start_dt
        right = end_dt
        while right - left > self._resolution:
            midpoint = left + (right - left) / 2
            state = evaluator(midpoint)
            if state == expected_state_at_end:
                right = midpoint
            else:
                left = midpoint
        return right if expected_state_at_end else left

    def refine_exact(
        self,
        start_dt: datetime,
        end_dt: datetime,
        longitude_at,
        natal_longitude: float,
        aspect_type: str,
    ) -> RefinedExact:
        exact_dt = self._find_exact_crossing(
            start_dt,
            end_dt,
            longitude_at,
            natal_longitude,
            aspect_type,
        )
        if exact_dt is not None:
            return RefinedExact(exact_dt=exact_dt, exact_orb=0.0, phase="applying-separating")

        start_orb = aspect_deviation(longitude_at(start_dt), natal_longitude, aspect_type)
        end_orb = aspect_deviation(longitude_at(end_dt), natal_longitude, aspect_type)
        phase = "applying" if end_orb < start_orb else "separating"
        return RefinedExact(exact_dt=None, exact_orb=None, phase=phase)

    def _find_exact_crossing(
        self,
        start_dt: datetime,
        end_dt: datetime,
        longitude_at,
        natal_longitude: float,
        aspect_type: str,
    ) -> datetime | None:
        sample_step = min(timedelta(hours=1), max(self._resolution * 10, timedelta(minutes=30)))
        timestamps = [start_dt]
        cursor = start_dt
        while cursor < end_dt:
            cursor = min(cursor + sample_step, end_dt)
            timestamps.append(cursor)

        for target in _candidate_targets(natal_longitude, aspect_type):
            previous_time = timestamps[0]
            previous_value = signed_angular_difference(longitude_at(previous_time), target)
            if abs(previous_value) < 1e-6:
                return previous_time
            for current_time in timestamps[1:]:
                current_value = signed_angular_difference(longitude_at(current_time), target)
                if abs(current_value) < 1e-6:
                    return current_time
                if previous_value == 0:
                    return previous_time
                if current_value == 0 or previous_value * current_value < 0:
                    return self._refine_target_crossing(
                        previous_time,
                        current_time,
                        longitude_at,
                        target,
                    )
                previous_time = current_time
                previous_value = current_value
        return None

    def _refine_target_crossing(
        self,
        start_dt: datetime,
        end_dt: datetime,
        longitude_at,
        target: float,
    ) -> datetime:
        left = start_dt
        right = end_dt
        left_value = signed_angular_difference(longitude_at(left), target)
        while right - left > self._resolution:
            midpoint = left + (right - left) / 2
            midpoint_value = signed_angular_difference(longitude_at(midpoint), target)
            if midpoint_value == 0:
                return midpoint
            if left_value == 0 or left_value * midpoint_value <= 0:
                right = midpoint
            else:
                left = midpoint
                left_value = midpoint_value
        return right
