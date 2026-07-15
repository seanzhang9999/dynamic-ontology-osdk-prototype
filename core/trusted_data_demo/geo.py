from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple


Point = Tuple[float, float]


def polygon_bbox(geojson: dict) -> Tuple[float, float, float, float]:
    coordinates = geojson["coordinates"][0]
    xs = [point[0] for point in coordinates]
    ys = [point[1] for point in coordinates]
    return min(xs), min(ys), max(xs), max(ys)


def line_bbox(line: Sequence[Sequence[float]]) -> Tuple[float, float, float, float]:
    xs = [point[0] for point in line]
    ys = [point[1] for point in line]
    return min(xs), min(ys), max(xs), max(ys)


def expand_bbox(
    bbox: Tuple[float, float, float, float], buffer_degrees: float
) -> Tuple[float, float, float, float]:
    min_x, min_y, max_x, max_y = bbox
    return (
        min_x - buffer_degrees,
        min_y - buffer_degrees,
        max_x + buffer_degrees,
        max_y + buffer_degrees,
    )


def bbox_intersects(
    left: Tuple[float, float, float, float], right: Tuple[float, float, float, float]
) -> bool:
    return not (
        left[2] < right[0]
        or left[0] > right[2]
        or left[3] < right[1]
        or left[1] > right[3]
    )

