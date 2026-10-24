"""Bounded output grids and finite-state checks for offline fixture integration."""
from __future__ import annotations

import math

from .artifacts import InputError


def output_times(duration, step):
    """Include the actual terminal time, with a shortened last interval if needed."""
    count = math.floor(duration / step)
    times = [index * step for index in range(count + 1)]
    if count and math.isclose(times[-1], duration, rel_tol=1e-12, abs_tol=0.0):
        times[-1] = duration
    else:
        times.append(duration)
    return times


def require_finite(state):
    if not all(math.isfinite(value) for value in state):
        raise InputError("Integration produced a nonfinite state")
