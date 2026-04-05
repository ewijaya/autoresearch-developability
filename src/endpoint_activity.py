"""Activity endpoint: antimicrobial MIC from DBAASP.

For the candidate pool (DBAASP peptides), activity is ground truth —
directly from the database. This module provides normalization and
the scoring interface.

Convention: higher activity score = better (more potent).
Since lower MIC = more potent, we use -log10(MIC) as the score.
"""

import numpy as np


def mic_to_activity_score(mic_values: list, unit: str = "uM") -> list:
    """Convert MIC values to activity scores.

    Args:
        mic_values: list of MIC concentrations (float).
        unit: concentration unit from DBAASP (typically "uM" or "ug/mL").

    Returns:
        list of activity scores (higher = more potent).
    """
    scores = []
    for mic in mic_values:
        if mic is None or mic <= 0:
            scores.append(0.0)  # missing or invalid → neutral score
        else:
            # -log10(MIC): lower MIC → higher score
            scores.append(-np.log10(mic))
    return scores


def normalize_activity(scores: list) -> list:
    """Min-max normalize activity scores to [0, 1]."""
    arr = np.array(scores, dtype=float)
    smin, smax = arr.min(), arr.max()
    if smax - smin < 1e-10:
        return [0.5] * len(scores)
    return ((arr - smin) / (smax - smin)).tolist()
