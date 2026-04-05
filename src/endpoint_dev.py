"""Developability / manufacturability proxy scoring.

Rule-based composite penalty computed from sequence properties.
Higher penalty = worse developability. No ML model needed.

Rules are explicit, documented, and deterministic.
"""

from src.features import (
    HYDROPHOBICITY,
    HYDROPHOBIC_AA,
    CHARGE,
    STANDARD_AA,
    is_valid_sequence,
)


def score_developability(seq: str) -> float:
    """Compute developability penalty for a peptide sequence.

    Returns a non-negative float. 0 = no issues. Higher = worse.
    Each rule contributes 0 or 1 penalty point (some scaled).
    """
    seq = seq.upper().strip()
    if not is_valid_sequence(seq):
        return 10.0  # maximum penalty for invalid sequences

    penalties = []

    # 1. Length penalty: outside 8-40 residues
    n = len(seq)
    if n < 8:
        penalties.append(1.0)
    elif n > 40:
        penalties.append(1.0)

    # 2. Aggregation-prone motifs: 3+ consecutive hydrophobic residues
    max_hydro_run = 0
    run = 0
    for c in seq:
        if c in HYDROPHOBIC_AA:
            run += 1
            max_hydro_run = max(max_hydro_run, run)
        else:
            run = 0
    if max_hydro_run >= 3:
        penalties.append(min(max_hydro_run - 2, 3) * 0.5)  # 0.5 per extra

    # 3. Difficult synthesis motifs: consecutive prolines
    if "PP" in seq:
        penalties.append(0.5)
    if "PPP" in seq:
        penalties.append(0.5)  # additional

    # 4. Net charge extremes: |charge| > 5
    net_charge = sum(CHARGE.get(c, 0) for c in seq)
    if abs(net_charge) > 5:
        penalties.append(1.0)

    # 5. Hydrophobicity extremes: mean > 2.0 (Kyte-Doolittle)
    valid = [c for c in seq if c in STANDARD_AA]
    if valid:
        mean_hydro = sum(HYDROPHOBICITY.get(c, 0) for c in valid) / len(valid)
        if mean_hydro > 2.0:
            penalties.append(1.0)

    # 6. Cysteine count: > 2 cysteines in peptides < 30 residues
    cys_count = seq.count("C")
    if cys_count > 2 and n < 30:
        penalties.append(1.0)

    # 7. Unusual residues (non-standard AA in original input)
    # Already handled by is_valid_sequence check above

    return sum(penalties)


def score_batch(sequences: list) -> list:
    """Score developability for a list of sequences."""
    return [score_developability(seq) for seq in sequences]
