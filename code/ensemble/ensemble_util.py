from __future__ import annotations
from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from pandas.api.types import is_integer_dtype
from typing import List, Dict
import numpy as np
import pandas as pd
from pathlib import Path
import re



def project_root() -> Path:
    """
    Returns the repository root by walking upwards until we find a marker file.
    """
    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        if (p / "environment_icail2026.yml").exists():  # choose a marker that is at repo root
            return p
    raise RuntimeError("Could not find project root (missing environment_icail2026.yml marker).")



EPS = 1e-6
LABELS = list(range(19))

def _assert_no_missing_and_integer(df: pd.DataFrame, cols: List[str]) -> None:
    missing_cols = [c for c in cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in df: {missing_cols}")

    for c in cols:
        if df[c].isna().any():
            raise ValueError(f"Column '{c}' contains missing values; aborting as requested.")
        # Accept either real integer dtype OR values that are integers (e.g., object with ints)
        if not is_integer_dtype(df[c]):
            # If dtype is float but all values are integer-like, allow (common after CSV read)
            vals = df[c].to_numpy()
            if not np.all(np.isfinite(vals)) or not np.all(np.equal(vals, np.floor(vals))):
                raise ValueError(f"Column '{c}' is not integer-valued; QWK expects ordinal integer categories.")

def _qwk(a: pd.Series, b: pd.Series) -> float:
    return float(cohen_kappa_score(a, b, labels=LABELS, weights="quadratic"))

def _pearson(a: pd.Series, b: pd.Series) -> float:
    r = float(pd.Series(a).corr(pd.Series(b), method="pearson"))
    if not np.isfinite(r):
        raise ValueError("Pearson correlation is undefined (likely constant input).")
    return r

def _spearman(a: pd.Series, b: pd.Series) -> float:
    r = float(pd.Series(a).corr(pd.Series(b), method="spearman"))
    if not np.isfinite(r):
        raise ValueError("Spearman correlation is undefined (likely constant input).")
    return r


def fisher_mean_and_sds(correlations: List[float], ddof: int = 1) -> Dict[str, float]:
    """
    Fisher-average a set of raw correlation values and report dispersion in raw correlation space.

    This function applies the Fisher z-transformation (arctanh) to each input
    correlation, computes the arithmetic mean in z-space, and back-transforms
    (tanh) to obtain a single Fisher-averaged correlation. It also returns the
    standard deviation of the raw correlation values (raw correlation space) to
    quantify variability across the aggregated correlations (e.g., across LLM runs
    or across raters).

    """

    if len(correlations) == 0:
        raise ValueError("No correlations to aggregate.")  # no values provided

    if len(correlations) == 1:
        r = float(correlations[0])  # single raw correlation
        # Compute z for completeness/consistency, even though it is not returned
        _ = float(np.arctanh(np.clip(r, -1 + EPS, 1 - EPS)))  # Fisher z of single correlation
        return {
            "mean_correlation_fisher": r,  # Fisher-mean equals the single correlation
            "sd_correlation_raw": 0.0,     # no dispersion with one value
        }

    correlations = np.asarray(correlations, dtype=float) # convert to NumPy array for vectorized operations. Space = correlation

    z = np.arctanh(np.clip(correlations, -1 + EPS, 1 - EPS))  # Fisher z-transform each correlation. Space = z

    mean_z = float(np.mean(z))                             # mean agreement in Fisher z-space. Space = z 
    mean_correlation_fisher = float(np.tanh(mean_z))       # back-transform to obtain final single Fisher-averaged correlation. Space = correlation

    sd_correlation_raw = float(np.std(correlations, ddof=ddof))  # SD in raw correlation space (variability across correlations). Space = correlation

    return {
        "mean_correlation_fisher": mean_correlation_fisher,  # Fisher-averaged correlation across inputs
        "sd_correlation_raw": sd_correlation_raw,        # SD of raw correlations across inputs.
    }



def raters_vs_reference(
    df: pd.DataFrame,
    rater_cols: List[str],
    reference_col: str,
    ddof: int = 1,
    verbose: bool = False,
) -> Dict[str, object]:
    """
    Compute agreement between multiple rater columns and a single reference column.

    For each rater column, this function computes three rater-vs-reference metrics:

    - Quadratic Weighted Kappa (QWK)
    - Pearson correlation
    - Spearman correlation
    """

    # Validate: required columns exist, contain no NaNs, and are integer-valued (ordinal)
    _assert_no_missing_and_integer(df, rater_cols + [reference_col])


    per_rater_qwk: Dict[str, float] = {} # raw QWK per rater vs reference
    per_rater_pearson: Dict[str, float] = {} # Pearson correlation per rater vs reference
    per_rater_spearman: Dict[str, float] = {} # Spearman correlation per rater vs reference

    qwks: List[float] = [] # raw QWKs to be Fisher-averaged across raters
    pears: List[float] = [] # raw Pearson correlations to be Fisher-averaged across raters
    spears: List[float] = [] # raw Spearman correlations to be Fisher-averaged across raters

    ref = df[reference_col]

    # Compute raw QWK, Pearson, and Spearman correlations between each rater column and the reference column
    for c in rater_cols:
        a = df[c]

        # raw QWK, Pearson, and Spearman correlations between rater and reference
        k = _qwk(a, ref)
        pr = _pearson(a, ref)
        sr = _spearman(a, ref)

        # store per-rater result
        per_rater_qwk[c] = k
        per_rater_pearson[c] = pr
        per_rater_spearman[c] = sr

        # collect for aggregation
        qwks.append(k)
        pears.append(pr)
        spears.append(sr)

    # Fisher-average QWKs, Pearson, and Spearman correlations across raters; SD is computed in raw space
    agg_qwk = fisher_mean_and_sds(qwks, ddof=ddof)
    agg_pearson = fisher_mean_and_sds(pears, ddof=ddof)
    agg_spearman = fisher_mean_and_sds(spears, ddof=ddof)

    result: Dict[str, object] = {
        "mean_qwk_fisher_across_raters": agg_qwk["mean_correlation_fisher"], # Fisher-averaged QWK across raters
        "sd_qwk_across_raters_kappa_space": agg_qwk["sd_correlation_raw"], # SD across raters in raw QWK space

        "mean_pearson_fisher_across_raters": agg_pearson["mean_correlation_fisher"],
        "sd_pearson_across_raters_raw_space": agg_pearson["sd_correlation_raw"],

        "mean_spearman_fisher_across_raters": agg_spearman["mean_correlation_fisher"],
        "sd_spearman_across_raters_raw_space": agg_spearman["sd_correlation_raw"],
    }

    if verbose:
        result["per_rater_raw_qwk"] = per_rater_qwk # raw QWK per rater vs reference
        result["per_rater_pearson"] = per_rater_pearson # Pearson correlation per rater vs reference
        result["per_rater_spearman"] = per_rater_spearman # Spearman correlation per rater vs reference

    return result



def fisher_metrics_with_optional_bootstrap(
    df: pd.DataFrame,
    rater_cols: List[str],
    reference_col: str,
    do_bootstrap: bool = False,   # default: NO bootstrap
    B: int = 10_000,
    alpha: float = 0.05,
    seed: int = 42,
    ddof: int = 1,
    verbose: bool = False,
    ci_metrics: List[str] = None, # which Fisher-means to bootstrap CIs for
) -> Dict[str, object]:
    
    """
    Computes your reported Fisher-aggregated metrics across raters (runs) vs a reference:
      - QWK (quadratic weighted kappa)
      - Pearson correlation
      - Spearman correlation
    """
    if ci_metrics is None:
        ci_metrics = [
            "mean_qwk_fisher_across_raters",
            "mean_pearson_fisher_across_raters",
            "mean_spearman_fisher_across_raters",
        ]

    # Point estimates (your existing pipeline)
    point = raters_vs_reference(
        df,
        rater_cols=rater_cols,
        reference_col=reference_col,
        ddof=ddof,
        verbose=verbose,
    )

    out: Dict[str, object] = {
        # QWK
        "point_mean_qwk_fisher": point["mean_qwk_fisher_across_raters"],
        "point_sd_qwk_across_runs_kappa_space": point["sd_qwk_across_raters_kappa_space"],
        # Pearson
        "point_mean_pearson_fisher": point["mean_pearson_fisher_across_raters"],
        "point_sd_pearson_across_runs_raw_space": point["sd_pearson_across_raters_raw_space"],
        # Spearman
        "point_mean_spearman_fisher": point["mean_spearman_fisher_across_raters"],
        "point_sd_spearman_across_runs_raw_space": point["sd_spearman_across_raters_raw_space"],
    }

    if verbose:
        out["per_run_qwk"] = point.get("per_rater_raw_qwk", None)
        out["per_run_pearson"] = point.get("per_rater_pearson", None)
        out["per_run_spearman"] = point.get("per_rater_spearman", None)

    # If bootstrap is disabled, return point estimates only
    if not do_bootstrap:
        return out

    # Bootstrap CIs over scripts (rows) for requested Fisher-mean metrics
    rng = np.random.default_rng(seed)
    n = len(df)

    samples_by_metric = {m: [] for m in ci_metrics}
    skipped = 0

    for _ in range(B):
        idx = rng.integers(0, n, size=n)
        df_b = df.iloc[idx].reset_index(drop=True)

        try:
            res_b = raters_vs_reference(
                df_b,
                rater_cols=rater_cols,
                reference_col=reference_col,
                ddof=ddof,
                verbose=False,
            )

            # Collect requested metrics
            any_added = False
            for m in ci_metrics:
                val = res_b.get(m, np.nan)
                if np.isnan(val):
                    continue
                samples_by_metric[m].append(float(val))
                any_added = True

            if not any_added:
                skipped += 1

        except Exception:
            skipped += 1

    # Convert to arrays and compute percentile CIs
    cis = {}
    samples_np = {}
    for m, vals in samples_by_metric.items():
        arr = np.asarray(vals, dtype=float)
        samples_np[m] = arr
        if len(arr) == 0:
            cis[m] = (np.nan, np.nan)
        else:
            lo = float(np.quantile(arr, alpha / 2))
            hi = float(np.quantile(arr, 1 - alpha / 2))
            cis[m] = (lo, hi)

    out.update({
        "bootstrap_cis": cis,
        "bootstrap_samples": samples_np,
        "bootstraps_used": int(min(len(v) for v in samples_np.values()) if len(samples_np) else 0),
        "bootstraps_skipped": int(skipped),
        "bootstrap_params": {
            "B": int(B),
            "alpha": float(alpha),
            "seed": int(seed),
            "ci_metrics": list(ci_metrics),
        },
    })
    return out




def verify_columns(df, models, prefix, suffix):
    """
    Verify that columns exist for all models with the given prefix and suffix.
    
    Parameters
    ----------
    df : pd.DataFrame
        The dataframe to search
    models : List[str]
        List of model names
    prefix : str
        Column name prefix to search for
    suffix : str
        Column name suffix to search for
    
    Returns
    -------
    dict
        Dictionary with model names as keys and column lists as values
    """
    results = {}
    all_found = True
    
    for m in models:
        cols = df.filter(regex=rf"{prefix}.*{re.escape(m)}.*{suffix}$").columns.tolist()
        results[m] = cols
        
        if len(cols) == 0:
            print(f"✗ {m}: 0 columns found")
            all_found = False
        elif len(cols) == 3:
            print(f"✓ {m}: {len(cols)} columns found")
            print(f"  Iterations: {[c.split('__i')[1].split('__')[0] for c in cols]}")
        else:
            print(f"⚠ {m}: {len(cols)} columns found (expected 3)")
            print(f"  Columns: {cols}")
    
    if all_found:
        print("\n✓ All models found!")
    else:
        print("\n✗ Some models missing. Check prefix/suffix or model names.")
    
    return results


def build_iter_cols(df, models, prefix, suffix, iters=(1, 2, 3)):
    iter_cols = {i: [] for i in iters}
    for m in models:
        cols = df.filter(regex=rf"{prefix}.*{re.escape(m)}.*{suffix}$").columns
        for i in iters:
            c = [c for c in cols if f"__i{i}__" in c]
            if len(c) != 1:
                raise ValueError(f"Expected exactly 1 column for model={m}, i{i}; found {len(c)}")
            iter_cols[i].append(c[0])
    return iter_cols


def ensemble_raters(
    df,
    iter_cols,
    models,
    agg="median",
    iters=(1, 2, 3),
    round_result=None,  # None => auto based on agg and #models
):
    agg = agg.lower()
    name_map = {"median": "median", "min": "min"}
    if agg not in name_map:
        raise ValueError(f"agg must be one of {list(name_map)}")

    # default rounding behavior:
    # - median: round only if even number of raters (median can be .5)
    # - min: no rounding by default (already one of the raters)
    if round_result is None:
        n_raters = len(models)
        round_result = (agg == "median" and n_raters % 2 == 0)

    models_tag = "_".join(models)
    rater_df = pd.DataFrame(index=df.index)

    for i in iters:
        vals = df[iter_cols[i]].apply(pd.to_numeric, errors="coerce")

        if agg == "median":
            s = vals.median(axis=1)
        else:  # agg == "min"
            s = vals.min(axis=1)

        if round_result:
            s = s.round()

        rater_df[f"ensembled_{name_map[agg]}_i{i}_{models_tag}"] = s.astype("Int64")

    return rater_df


def run_combo(df, models, prefix, *, suffix, iters, aggs, gold_col):
    iter_cols = build_iter_cols(df, models, prefix, suffix, iters=iters)

    out = []
    for agg in aggs:
        rater_df = ensemble_raters(df, iter_cols, models, agg=agg, iters=iters)
        tmp = pd.concat([rater_df, df[[gold_col]]], axis=1)

        metrics = fisher_metrics_with_optional_bootstrap(
            tmp,
            rater_cols=list(rater_df.columns),
            reference_col=gold_col,
        )

        for metric_name, metric_value in metrics.items():
            if "qwk" not in metric_name.lower():
                continue
            out.append({"agg": agg, "metric": metric_name, "value": float(metric_value)})

    return out
