"""Offline GPS track contract. Distances exclude pauses / discontinuities."""
import copy
import math
from pyproj import Geod
from .geometry import check_position


def validate_track(payload):
    value = copy.deepcopy(payload)
    if not isinstance(value.get('title'), str) or not value['title'].strip():
        raise ValueError('Track title required')
    points = value.get('positions')
    if not isinstance(points, list) or len(points) > 20000:
        raise ValueError('Invalid track points')
    previous = 0
    for point in points:
        if not isinstance(point, list) or len(point) != 4:
            raise ValueError('Expected lon/lat/accuracy/timestamp')
        check_position(point[0], point[1])
        if not isinstance(point[2], (int, float)) or not math.isfinite(point[2]) or point[2] < 0:
            raise ValueError('Invalid accuracy')
        if type(point[3]) is not int or point[3] < previous:
            raise ValueError('Invalid track timestamp')
        previous = point[3]
    starts = value.setdefault('segment_starts', [0] if points else [])
    if not isinstance(starts, list) or any(type(i) is not int or not 0 <= i < len(points) for i in starts):
        raise ValueError('Invalid track segments')
    if sorted(set(starts)) != starts or (points and (not starts or starts[0] != 0)):
        raise ValueError('Invalid segment order')
    if value.get('state') not in ('recording', 'paused', 'stopped'):
        raise ValueError('Invalid track state')
    for key in ('started_at', 'ended_at', 'duration_ms'):
        if type(value.get(key)) is not int or value[key] < 0:
            raise ValueError('Invalid track time')
    distance = value.get('distance_m')
    if not isinstance(distance, (int, float)) or not math.isfinite(distance) or distance < 0:
        raise ValueError('Invalid track distance')
    geod = Geod(ellps='WGS84'); breaks = set(starts)
    actual = sum(geod.inv(*points[i-1][:2], *points[i][:2])[2] for i in range(1,len(points)) if i not in breaks)
    if abs(actual-distance) > .01:
        raise ValueError('Track distance mismatch')
    return value
