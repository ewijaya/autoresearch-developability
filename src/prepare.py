"""Fixed evaluation harness: data preparation and pipeline orchestration.

THIS FILE IS FROZEN. Do not modify during the autoresearch loop.

Pipeline steps:
1. Download public datasets (DBAASP, ToxinPred3, HLP)
2. Filter and clean the DBAASP candidate pool
3. Train endpoint models (toxicity, stability) on their native datasets
4. Score all candidates on all four endpoints
5. Split into train/val/test with leakage control
6. Save processed DataFrames

Usage:
    python -m src.prepare [--skip-download]
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from src.endpoint_activity import mic_to_activity_score, normalize_activity
from src.endpoint_dev import score_batch as score_developability
from src.endpoint_stability import (
    normalize_stability,
    predict_stability,
    train_stability_model,
)
from src.endpoint_toxicity import predict_toxicity, train_toxicity_model
from src.features import is_valid_sequence

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
MANIFEST_DIR = Path("data/manifests")

# DBAASP API config
DBAASP_API = "https://dbaasp.org"
TARGET_SPECIES = "Escherichia coli ATCC 25922"
DBAASP_PAGE_SIZE = 100

# Peptide length filters
MIN_LENGTH = 5
MAX_LENGTH = 50

# Split ratios
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15


# --- Download functions ---


def download_dbaasp(output_dir: Path) -> Path:
    """Download DBAASP peptides with MIC against E. coli ATCC 25922.

    Two-phase download:
    1. List endpoint to get all peptide IDs (fast, paginated)
    2. Detail endpoint to get MIC values (slower, batched with concurrency)

    Uses the JSON REST API (no auth required).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    detail_file = output_dir / "dbaasp_ecoli_details.json"
    list_file = output_dir / "dbaasp_ecoli.json"

    if detail_file.exists():
        logger.info(f"DBAASP detail data already exists: {detail_file}")
        return detail_file

    # Phase 1: Get list of peptide IDs
    if list_file.exists():
        logger.info(f"DBAASP list data already exists, loading...")
        with open(list_file) as f:
            all_peptides = json.load(f)
    else:
        logger.info(f"Downloading DBAASP list for {TARGET_SPECIES}...")
        all_peptides = []
        offset = 0
        while True:
            url = (f"{DBAASP_API}/peptides"
                   f"?targetSpecies.value={TARGET_SPECIES.replace(' ', '+')}"
                   f"&offset={offset}&limit={DBAASP_PAGE_SIZE}")
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()
            except (requests.RequestException, json.JSONDecodeError) as e:
                logger.error(f"DBAASP API error at offset {offset}: {e}")
                if all_peptides:
                    logger.warning("Continuing with partial data")
                    break
                raise

            records = data.get("data", data) if isinstance(data, dict) else data
            if not records:
                break

            all_peptides.extend(records)
            total = data.get("totalCount", None) if isinstance(data, dict) else None
            if total and len(all_peptides) >= total:
                break
            offset += DBAASP_PAGE_SIZE
            time.sleep(0.3)

        with open(list_file, "w") as f:
            json.dump(all_peptides, f)
        logger.info(f"Saved {len(all_peptides)} DBAASP list entries")

    # Phase 2: Fetch details with MIC values
    # Filter to monomers with valid sequences first
    candidates = []
    for entry in all_peptides:
        pid = entry.get("id")
        seq = entry.get("sequence", "")
        if pid and seq and entry.get("complexity") == "monomer":
            candidates.append({"id": pid, "sequence": seq})

    logger.info(f"Fetching MIC details for {len(candidates)} monomer peptides...")
    details = _fetch_dbaasp_details(candidates)

    with open(detail_file, "w") as f:
        json.dump(details, f)
    logger.info(f"Saved {len(details)} DBAASP detail records to {detail_file}")

    return detail_file


def _fetch_dbaasp_details(candidates: list) -> list:
    """Fetch DBAASP detail records to extract MIC for E. coli ATCC 25922.

    Uses concurrent requests for reasonable speed.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    details = []
    errors = 0

    def fetch_one(entry):
        pid = entry["id"]
        try:
            resp = requests.get(f"{DBAASP_API}/peptides/{pid}", timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # Extract E. coli ATCC 25922 MIC
            for ta in data.get("targetActivities", []):
                species = ta.get("targetSpecies", {}).get("name", "")
                measure = ta.get("activityMeasureGroup", {}).get("name", "")
                if ("Escherichia coli" in species
                        and "ATCC 25922" in species
                        and measure == "MIC"):
                    conc_str = str(ta.get("concentration", "")).strip()
                    unit = ta.get("unit", {}).get("name", "")
                    try:
                        conc = float(conc_str)
                        return {
                            "id": pid,
                            "sequence": data.get("sequence", entry["sequence"]),
                            "name": data.get("name", ""),
                            "mic": conc,
                            "mic_unit": unit,
                            "activity_score": ta.get("activity"),
                            "medium": ta.get("medium", {}).get("name", ""),
                            "dbaaspId": data.get("dbaaspId", ""),
                        }
                    except (ValueError, TypeError):
                        continue
            return None  # No valid E. coli MIC found

        except Exception:
            return None

    # Use 10 concurrent workers (polite but faster than sequential)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_one, c): c for c in candidates}
        done = 0
        for future in as_completed(futures):
            done += 1
            result = future.result()
            if result:
                details.append(result)
            else:
                errors += 1
            if done % 500 == 0:
                logger.info(f"  Detail fetch progress: {done}/{len(candidates)}, "
                            f"found {len(details)} with MIC, {errors} errors")

    logger.info(f"Detail fetch complete: {len(details)} peptides with E. coli MIC "
                f"out of {len(candidates)} attempted ({errors} errors)")
    return details


def download_toxinpred(output_dir: Path) -> Path:
    """Download ToxinPred3 training data."""
    output_dir.mkdir(parents=True, exist_ok=True)
    base_url = "https://webs.iiitd.edu.in/raghava/toxinpred3/download"

    for fname in ["train_pos.csv", "train_neg.csv"]:
        out = output_dir / fname
        if out.exists():
            logger.info(f"ToxinPred3 {fname} already exists")
            continue
        url = f"{base_url}/{fname}"
        logger.info(f"Downloading {url}...")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        with open(out, "w") as f:
            f.write(resp.text)
        logger.info(f"  Saved {fname}: {len(resp.text.splitlines())} lines")

    return output_dir


def download_hlp(output_dir: Path) -> Path:
    """Download HLP half-life data."""
    output_dir.mkdir(parents=True, exist_ok=True)
    base_url = "https://webs.iiitd.edu.in/raghava/hlp"

    for fname in ["10mer-peptides.txt", "16mer-peptides.txt"]:
        out = output_dir / fname
        if out.exists():
            logger.info(f"HLP {fname} already exists")
            continue
        url = f"{base_url}/{fname}"
        logger.info(f"Downloading {url}...")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        with open(out, "w") as f:
            f.write(resp.text)
        logger.info(f"  Saved {fname}: {len(resp.text.splitlines())} lines")

    return output_dir


# --- Data processing ---


def parse_dbaasp(json_path: Path) -> pd.DataFrame:
    """Parse DBAASP detail JSON into a clean DataFrame.

    Expects the output of _fetch_dbaasp_details: a list of dicts
    with keys: id, sequence, name, mic, mic_unit, dbaaspId, etc.

    Filters to valid peptides with standard amino acids and proper length.
    """
    with open(json_path) as f:
        raw = json.load(f)

    records = []
    for entry in raw:
        seq = entry.get("sequence", "")
        if not seq:
            continue

        seq = seq.upper().strip().replace(" ", "").replace("-", "")

        mic = entry.get("mic")
        if mic is None:
            continue
        try:
            mic = float(mic)
        except (ValueError, TypeError):
            continue

        if mic <= 0:
            continue

        records.append({
            "sequence": seq,
            "mic": mic,
            "mic_unit": entry.get("mic_unit", "uM"),
            "dbaasp_id": str(entry.get("dbaaspId", entry.get("id", ""))),
            "name": entry.get("name", ""),
            "length": len(seq),
        })

    df = pd.DataFrame(records)
    if len(df) == 0:
        logger.error("No valid DBAASP records parsed!")
        return df

    logger.info(f"Parsed DBAASP: {len(df)} records with valid MIC")

    # Filter by length
    df = df[(df["length"] >= MIN_LENGTH) & (df["length"] <= MAX_LENGTH)]
    logger.info(f"After length filter ({MIN_LENGTH}-{MAX_LENGTH}): {len(df)}")

    # Filter to standard amino acids only
    df = df[df["sequence"].apply(is_valid_sequence)]
    logger.info(f"After standard AA filter: {len(df)}")

    # Deduplicate by exact sequence (keep lowest MIC = most potent)
    df = df.sort_values("mic").drop_duplicates(subset="sequence", keep="first")
    logger.info(f"After deduplication: {len(df)}")

    df = df.reset_index(drop=True)
    return df


def split_data(df: pd.DataFrame, seed: int = 42) -> tuple:
    """Split DataFrame into train/val/test.

    Uses cluster-aware splitting if mmseqs2 is available,
    otherwise falls back to random split with documentation.

    Returns:
        (train_df, val_df, test_df, split_method)
    """
    # Try mmseqs2 cluster-aware splitting
    split_method = _try_mmseqs_split(df, seed)
    if split_method is not None:
        return split_method

    # Fallback: random split (documented limitation)
    logger.warning("mmseqs2 not available. Using random split. "
                   "This is a known limitation — fix before paper submission.")
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(df))

    n_train = int(len(df) * TRAIN_RATIO)
    n_val = int(len(df) * VAL_RATIO)

    train_df = df.iloc[idx[:n_train]].reset_index(drop=True)
    val_df = df.iloc[idx[n_train:n_train + n_val]].reset_index(drop=True)
    test_df = df.iloc[idx[n_train + n_val:]].reset_index(drop=True)

    logger.info(f"Random split: train={len(train_df)}, val={len(val_df)}, "
                f"test={len(test_df)}")
    return train_df, val_df, test_df, "random"


def _try_mmseqs_split(df: pd.DataFrame, seed: int) -> tuple | None:
    """Attempt cluster-aware splitting using mmseqs2.

    Returns (train_df, val_df, test_df, 'mmseqs2') or None if unavailable.
    """
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("mmseqs"):
        logger.info("mmseqs2 not found in PATH")
        return None

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Write sequences as FASTA
            fasta_path = tmpdir / "seqs.fasta"
            with open(fasta_path, "w") as f:
                for i, row in df.iterrows():
                    f.write(f">{i}\n{row['sequence']}\n")

            # Create mmseqs2 database
            db_path = tmpdir / "seqdb"
            subprocess.run(
                ["mmseqs", "createdb", str(fasta_path), str(db_path)],
                capture_output=True, check=True, timeout=120,
            )

            # Cluster at 90% sequence identity
            clu_path = tmpdir / "clu"
            subprocess.run(
                ["mmseqs", "cluster", str(db_path), str(clu_path),
                 str(tmpdir / "tmp"),
                 "--min-seq-id", "0.9", "-c", "0.8", "--cov-mode", "1"],
                capture_output=True, check=True, timeout=300,
            )

            # Extract cluster assignments
            tsv_path = tmpdir / "clu.tsv"
            subprocess.run(
                ["mmseqs", "createtsv", str(db_path), str(db_path),
                 str(clu_path), str(tsv_path)],
                capture_output=True, check=True, timeout=120,
            )

            # Parse cluster assignments
            cluster_map = {}  # seq_idx -> cluster_rep_idx
            with open(tsv_path) as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) >= 2:
                        rep, member = int(parts[0]), int(parts[1])
                        cluster_map[member] = rep

            # Assign clusters to splits
            unique_clusters = list(set(cluster_map.values()))
            rng = np.random.RandomState(seed)
            rng.shuffle(unique_clusters)

            n_train = int(len(unique_clusters) * TRAIN_RATIO)
            n_val = int(len(unique_clusters) * VAL_RATIO)

            train_clusters = set(unique_clusters[:n_train])
            val_clusters = set(unique_clusters[n_train:n_train + n_val])
            test_clusters = set(unique_clusters[n_train + n_val:])

            train_idx = [i for i, c in cluster_map.items() if c in train_clusters]
            val_idx = [i for i, c in cluster_map.items() if c in val_clusters]
            test_idx = [i for i, c in cluster_map.items() if c in test_clusters]

            train_df = df.iloc[train_idx].reset_index(drop=True)
            val_df = df.iloc[val_idx].reset_index(drop=True)
            test_df = df.iloc[test_idx].reset_index(drop=True)

            logger.info(f"mmseqs2 cluster split: {len(unique_clusters)} clusters, "
                        f"train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
            return train_df, val_df, test_df, "mmseqs2"

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        logger.warning(f"mmseqs2 clustering failed: {e}")
        return None


def _load_toxinpred_sequences(data_dir: Path) -> set:
    """Load all ToxinPred3 training sequences as a set for overlap checking."""
    seqs = set()
    for fname in ["train_pos.csv", "train_neg.csv"]:
        fpath = data_dir / fname
        if not fpath.exists():
            continue
        with open(fpath) as f:
            for line in f:
                s = line.strip().upper()
                if s and all(c.isalpha() for c in s):
                    seqs.add(s)
    return seqs


def build_candidate_pool(
    dbaasp_df: pd.DataFrame,
    toxinpred_dir: Path,
    hlp_dir: Path,
) -> pd.DataFrame:
    """Build the unified candidate pool with all endpoint scores.

    Also flags candidates that overlap with ToxinPred3 training data
    (column: tox_train_overlap). These candidates have potentially
    optimistic toxicity predictions.

    Args:
        dbaasp_df: Parsed DBAASP DataFrame with sequence and MIC columns.
        toxinpred_dir: Directory containing ToxinPred3 training files.
        hlp_dir: Directory containing HLP data files.

    Returns:
        DataFrame with columns: sequence, activity, toxicity, stability,
        dev_penalty, tox_train_overlap, mic_raw, dbaasp_id
    """
    sequences = dbaasp_df["sequence"].tolist()
    n = len(sequences)
    logger.info(f"Building candidate pool for {n} peptides...")

    # 1. Activity (ground truth from DBAASP)
    activity_raw = mic_to_activity_score(dbaasp_df["mic"].tolist())
    activity = normalize_activity(activity_raw)
    logger.info(f"  Activity: scored {n} peptides")

    # 2. Toxicity (trained model)
    logger.info("  Training toxicity model...")
    tox_model = train_toxicity_model(toxinpred_dir)
    toxicity = predict_toxicity(sequences, model=tox_model)
    logger.info(f"  Toxicity: predicted {n} peptides, "
                f"mean={np.mean(toxicity):.3f}")

    # 3. Stability (trained model)
    logger.info("  Training stability model...")
    stab_model = train_stability_model(hlp_dir)
    stability_raw = predict_stability(sequences, model=stab_model)
    stability = normalize_stability(stability_raw)
    logger.info(f"  Stability: predicted {n} peptides, "
                f"mean={np.mean(stability):.3f}")

    # 4. Developability (rule-based)
    dev_penalty = score_developability(sequences)
    logger.info(f"  Developability: scored {n} peptides, "
                f"mean penalty={np.mean(dev_penalty):.3f}")

    # 5. Flag ToxinPred3 training overlap
    tox_train_seqs = _load_toxinpred_sequences(toxinpred_dir)
    overlap_flags = [seq in tox_train_seqs for seq in sequences]
    n_overlap = sum(overlap_flags)
    logger.info(f"  ToxinPred3 training overlap: {n_overlap}/{n} "
                f"({100*n_overlap/n:.1f}%) candidates flagged")

    pool = pd.DataFrame({
        "sequence": sequences,
        "activity": activity,
        "toxicity": toxicity,
        "stability": stability,
        "dev_penalty": dev_penalty,
        "tox_train_overlap": overlap_flags,
        "mic_raw": dbaasp_df["mic"].values,
        "dbaasp_id": dbaasp_df["dbaasp_id"].values,
    })
    return pool


def generate_esm_embeddings(sequences: list, output_path: Path,
                            model_name: str = "esm2_t6_8M_UR50D",
                            batch_size: int = 64) -> np.ndarray | None:
    """Generate ESM-2 per-sequence embeddings for all candidates.

    Uses the smallest ESM-2 model (8M params) by default — fast on CPU,
    very fast on GPU. Returns mean-pooled per-residue embeddings.

    Args:
        sequences: list of peptide sequences.
        output_path: path to save embeddings as .npy file.
        model_name: ESM-2 model name. Options:
            esm2_t6_8M_UR50D   (8M, 320-dim, fast)
            esm2_t12_35M_UR50D (35M, 480-dim, moderate)
            esm2_t30_150M_UR50D (150M, 640-dim, needs GPU)
        batch_size: sequences per batch.

    Returns:
        np.ndarray of shape (n_sequences, embed_dim) or None if unavailable.
    """
    if output_path.exists():
        logger.info(f"ESM embeddings already exist: {output_path}")
        return np.load(output_path)

    try:
        import torch
        import esm
    except ImportError:
        logger.warning("ESM-2 not available (requires torch + fair-esm). "
                       "Skipping embedding generation. "
                       "Install with: pip install torch fair-esm")
        return None

    logger.info(f"Loading ESM-2 model: {model_name}...")
    model, alphabet = esm.pretrained.load_model_and_alphabet(model_name)
    batch_converter = alphabet.get_batch_converter()
    model.eval()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    logger.info(f"ESM-2 running on {device}")

    all_embeddings = []
    n = len(sequences)

    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        batch_seqs = [(f"seq_{i}", seq) for i, seq in
                      enumerate(sequences[start:end])]

        _, _, batch_tokens = batch_converter(batch_seqs)
        batch_tokens = batch_tokens.to(device)

        with torch.no_grad():
            results = model(batch_tokens, repr_layers=[model.num_layers])

        # Mean-pool over residue positions (excluding BOS/EOS tokens)
        token_embeddings = results["representations"][model.num_layers]
        # tokens: [BOS, aa1, aa2, ..., EOS, PAD, PAD, ...]
        for i in range(len(batch_seqs)):
            seq_len = len(batch_seqs[i][1])
            # Positions 1..seq_len are the actual residues
            emb = token_embeddings[i, 1:seq_len + 1, :].mean(dim=0)
            all_embeddings.append(emb.cpu().numpy())

        if (start // batch_size) % 10 == 0:
            logger.info(f"  ESM embeddings: {end}/{n} sequences")

    embeddings = np.array(all_embeddings)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, embeddings)
    logger.info(f"Saved ESM embeddings: {embeddings.shape} to {output_path}")
    return embeddings


def save_manifest(pool: pd.DataFrame, split_method: str, output_dir: Path):
    """Save a manifest describing the processed dataset."""
    manifest = {
        "total_candidates": len(pool),
        "split_method": split_method,
        "activity_source": "DBAASP_v4_Ecoli_ATCC_25922",
        "toxicity_source": "ToxinPred3_RF",
        "stability_source": "HLP_RF",
        "developability_source": "rule_based",
        "sequence_representation": "AAindex_physicochemical",
        "min_length": MIN_LENGTH,
        "max_length": MAX_LENGTH,
        "splits": {
            "train_ratio": TRAIN_RATIO,
            "val_ratio": VAL_RATIO,
            "test_ratio": TEST_RATIO,
        },
        "endpoint_stats": {
            col: {
                "mean": float(pool[col].mean()),
                "std": float(pool[col].std()),
                "min": float(pool[col].min()),
                "max": float(pool[col].max()),
            }
            for col in ["activity", "toxicity", "stability", "dev_penalty"]
        },
        "data_hash": hashlib.md5(
            pool["sequence"].str.cat().encode()
        ).hexdigest(),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved manifest to {output_dir / 'manifest.json'}")


def main(skip_download: bool = False):
    """Run the full preparation pipeline."""
    logger.info("=" * 60)
    logger.info("autoresearch-developability: data preparation pipeline")
    logger.info("=" * 60)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Download datasets
    if not skip_download:
        dbaasp_json = download_dbaasp(RAW_DIR)
        download_toxinpred(RAW_DIR)
        download_hlp(RAW_DIR)
    else:
        # Prefer detail file, fall back to list file
        dbaasp_json = RAW_DIR / "dbaasp_ecoli_details.json"
        if not dbaasp_json.exists():
            dbaasp_json = RAW_DIR / "dbaasp_ecoli.json"
        if not dbaasp_json.exists():
            logger.error("Cannot skip download: DBAASP data not found")
            sys.exit(1)
        logger.info(f"Using existing DBAASP data: {dbaasp_json}")

    # Step 2: Parse DBAASP
    logger.info("-" * 40)
    logger.info("Parsing DBAASP candidate pool...")
    dbaasp_df = parse_dbaasp(dbaasp_json)

    if len(dbaasp_df) < 100:
        logger.error(f"Only {len(dbaasp_df)} usable peptides. "
                     "Check DBAASP data quality.")
        sys.exit(1)

    # Step 3: Build candidate pool with all endpoint scores
    logger.info("-" * 40)
    logger.info("Building candidate pool with endpoint scores...")
    pool = build_candidate_pool(dbaasp_df, RAW_DIR, RAW_DIR)

    # Step 3b: ESM-2 embeddings (optional, requires torch + fair-esm)
    logger.info("-" * 40)
    logger.info("Generating ESM-2 embeddings (optional)...")
    esm_path = PROCESSED_DIR / "esm_embeddings.npy"
    generate_esm_embeddings(pool["sequence"].tolist(), esm_path)

    # Step 4: Split
    logger.info("-" * 40)
    logger.info("Splitting data...")
    train_df, val_df, test_df, split_method = split_data(pool)

    # Step 5: Save
    logger.info("-" * 40)
    logger.info("Saving processed data...")
    train_df.to_csv(PROCESSED_DIR / "train.csv", index=False)
    val_df.to_csv(PROCESSED_DIR / "val.csv", index=False)
    test_df.to_csv(PROCESSED_DIR / "test.csv", index=False)
    pool.to_csv(PROCESSED_DIR / "full_pool.csv", index=False)

    save_manifest(pool, split_method, MANIFEST_DIR)

    logger.info("-" * 40)
    logger.info("DONE. Summary:")
    logger.info(f"  Total candidates: {len(pool)}")
    logger.info(f"  Train: {len(train_df)}")
    logger.info(f"  Val: {len(val_df)}")
    logger.info(f"  Test: {len(test_df)}")
    logger.info(f"  Split method: {split_method}")
    logger.info(f"  Output: {PROCESSED_DIR}")

    return pool, train_df, val_df, test_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare peptide benchmark data")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip dataset downloads (use existing files)")
    args = parser.parse_args()
    main(skip_download=args.skip_download)
