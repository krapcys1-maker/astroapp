from __future__ import annotations

SIGNS = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)


def normalize_angle(value: float) -> float:
    normalized = value % 360.0
    if normalized < 0:
        normalized += 360.0
    return normalized


def shortest_angular_distance(first: float, second: float) -> float:
    difference = abs(normalize_angle(first) - normalize_angle(second))
    return min(difference, 360.0 - difference)


def signed_angular_difference(first: float, second: float) -> float:
    difference = (normalize_angle(first) - normalize_angle(second) + 180.0) % 360.0 - 180.0
    return difference


def is_angle_between(target: float, start: float, end: float) -> bool:
    normalized_target = normalize_angle(target)
    normalized_start = normalize_angle(start)
    normalized_end = normalize_angle(end)
    if normalized_start <= normalized_end:
        return normalized_start <= normalized_target < normalized_end
    return normalized_target >= normalized_start or normalized_target < normalized_end


def zodiac_sign(longitude: float) -> str:
    normalized = normalize_angle(longitude)
    return SIGNS[int(normalized // 30)]


def degree_in_sign(longitude: float) -> float:
    return normalize_angle(longitude) % 30.0
