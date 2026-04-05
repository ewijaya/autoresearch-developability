"""Physicochemical feature extraction from peptide sequences.

Uses a subset of AAindex-derived properties computed directly from
amino acid composition. No external database file needed — the property
tables are embedded as constants.

This module is shared by all endpoint models.
"""

import numpy as np

# Kyte-Doolittle hydrophobicity scale
HYDROPHOBICITY = {
    "A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5,
    "Q": -3.5, "E": -3.5, "G": -0.4, "H": -3.2, "I": 4.5,
    "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8, "P": -1.6,
    "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2,
}

# Amino acid molecular weights (Da)
MOLECULAR_WEIGHT = {
    "A": 89.1, "R": 174.2, "N": 132.1, "D": 133.1, "C": 121.2,
    "Q": 146.2, "E": 147.1, "G": 75.0, "H": 155.2, "I": 131.2,
    "L": 131.2, "K": 146.2, "M": 149.2, "F": 165.2, "P": 115.1,
    "S": 105.1, "T": 119.1, "W": 204.2, "Y": 181.2, "V": 117.2,
}

# Charge at pH 7 (simplified)
CHARGE = {
    "A": 0, "R": 1, "N": 0, "D": -1, "C": 0,
    "Q": 0, "E": -1, "G": 0, "H": 0.1, "I": 0,
    "L": 0, "K": 1, "M": 0, "F": 0, "P": 0,
    "S": 0, "T": 0, "W": 0, "Y": 0, "V": 0,
}

# Bulkiness (Zimmerman et al., 1968)
BULKINESS = {
    "A": 11.50, "R": 14.28, "N": 12.82, "D": 11.68, "C": 13.46,
    "Q": 14.45, "E": 13.57, "G": 3.40, "H": 13.69, "I": 21.40,
    "L": 21.40, "K": 15.71, "M": 16.25, "F": 19.80, "P": 17.43,
    "S": 9.47, "T": 15.77, "W": 21.67, "Y": 18.03, "V": 21.57,
}

# Flexibility (Bhaskaran & Ponnuswamy, 1988)
FLEXIBILITY = {
    "A": 0.357, "R": 0.529, "N": 0.463, "D": 0.511, "C": 0.346,
    "Q": 0.493, "E": 0.497, "G": 0.544, "H": 0.323, "I": 0.462,
    "L": 0.365, "K": 0.466, "M": 0.295, "F": 0.314, "P": 0.509,
    "S": 0.507, "T": 0.444, "W": 0.305, "Y": 0.420, "V": 0.386,
}

STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")

# Hydrophobic residues for motif detection
HYDROPHOBIC_AA = set("AILMFVW")


def is_valid_sequence(seq: str) -> bool:
    """Check if sequence contains only standard amino acids."""
    return len(seq) > 0 and all(c in STANDARD_AA for c in seq.upper())


def compute_features(seq: str) -> dict:
    """Compute physicochemical feature vector for a peptide sequence.

    Returns a dict of named features suitable for DataFrame construction.
    """
    seq = seq.upper().strip()
    n = len(seq)
    if n == 0:
        raise ValueError("Empty sequence")

    # Filter to valid residues for property computation
    valid = [c for c in seq if c in STANDARD_AA]
    nv = len(valid)
    if nv == 0:
        raise ValueError(f"No standard amino acids in: {seq}")

    # Composition features (fraction of each AA)
    aa_counts = {aa: 0 for aa in sorted(STANDARD_AA)}
    for c in valid:
        aa_counts[c] += 1
    composition = {f"frac_{aa}": aa_counts[aa] / nv for aa in sorted(STANDARD_AA)}

    # Global physicochemical features
    hydro_vals = [HYDROPHOBICITY.get(c, 0) for c in valid]
    charge_vals = [CHARGE.get(c, 0) for c in valid]
    bulk_vals = [BULKINESS.get(c, 0) for c in valid]
    flex_vals = [FLEXIBILITY.get(c, 0) for c in valid]
    mw_vals = [MOLECULAR_WEIGHT.get(c, 0) for c in valid]

    features = {
        "length": n,
        "mw": sum(mw_vals) - (nv - 1) * 18.02,  # subtract water loss
        "hydrophobicity_mean": np.mean(hydro_vals),
        "hydrophobicity_std": np.std(hydro_vals) if nv > 1 else 0,
        "charge_net": sum(charge_vals),
        "charge_pos": sum(1 for c in valid if CHARGE.get(c, 0) > 0),
        "charge_neg": sum(1 for c in valid if CHARGE.get(c, 0) < 0),
        "bulkiness_mean": np.mean(bulk_vals),
        "flexibility_mean": np.mean(flex_vals),
        "isoelectric_approx": sum(charge_vals),  # simplified
        "frac_hydrophobic": sum(1 for c in valid if c in HYDROPHOBIC_AA) / nv,
        "frac_charged": sum(1 for c in valid if abs(CHARGE.get(c, 0)) > 0.5) / nv,
        "frac_polar": sum(1 for c in valid if c in set("STNQCY")) / nv,
        "frac_aromatic": sum(1 for c in valid if c in set("FWY")) / nv,
        "cysteine_count": aa_counts.get("C", 0),
        "proline_count": aa_counts.get("P", 0),
        # Sequence pattern features
        "max_hydrophobic_run": _max_run(seq, HYDROPHOBIC_AA),
        "max_charge_run": _max_run(seq, set("RK")),
    }
    features.update(composition)
    return features


def _max_run(seq: str, target_set: set) -> int:
    """Longest consecutive run of residues from target_set."""
    max_run = 0
    current = 0
    for c in seq.upper():
        if c in target_set:
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    return max_run


def feature_names() -> list:
    """Return ordered list of feature names for consistent DataFrame columns."""
    # Build from a dummy sequence
    dummy = compute_features("ACDEFGHIKLMNPQRSTVWY")
    return sorted(dummy.keys())


def sequences_to_feature_matrix(sequences: list) -> tuple:
    """Convert list of sequences to feature matrix.

    Returns:
        (feature_matrix: np.ndarray, feature_names: list, valid_mask: list[bool])
    """
    feat_list = []
    valid_mask = []
    names = None

    for seq in sequences:
        try:
            feats = compute_features(seq)
            if names is None:
                names = sorted(feats.keys())
            feat_list.append([feats[k] for k in names])
            valid_mask.append(True)
        except (ValueError, KeyError):
            feat_list.append([0.0] * (len(names) if names else 1))
            valid_mask.append(False)

    return np.array(feat_list), names or [], valid_mask
