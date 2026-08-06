"""
chm.signals
===========
Physiological feature extraction.

Design note -- avoiding circularity
-----------------------------------
A model that estimates the latent load x_t and its drivers (S, T, U) from the
*same* signal is not falsifiable: any apparent coupling could be an artefact of
shared measurement noise.  We therefore assign the load coordinate and the
drivers to DISJOINT SENSORS, and repeat the analysis under a second, equally
disjoint assignment.

    configuration B (PRIMARY)
        x   electrodermal load        z(tonic EDA / SCL)        [EDA]
        S   cardiac arousal drive     z(HR)                     [BVP]
        U   cardiac unpredictability  AR(1) residual variance   [BVP-derived HR]
        T   activity-regime change    per-window motion change  [accelerometer]

    configuration C (ROBUSTNESS)
        x   peripheral vasomotor load z(skin temperature)       [TEMP]
        S   sensory-arousal drive     SCR event rate            [EDA phasic]
        U   contextual uncertainty    AR(1) residual variance   [EDA tonic]
        T   activity-regime change                              [accelerometer]

    configuration A (NEGATIVE CONTROL)
        x   cardiac autonomic load    z(HR) - z(RMSSD)          [BVP / PPG]
        ... drivers as in configuration C

Why the cardiac index is a negative control rather than a candidate
------------------------------------------------------------------
The latent coordinate of a slow relaxation process must itself be slow.
Measured on WESAD at a 30 s window, tonic EDA has a lag-1 autocorrelation of
0.985, whereas z(HR) - z(RMSSD) has 0.19: RMSSD estimated from ~10-30 beats is
dominated by beat-detection error, so configuration A is very nearly white
noise and carries no recoverable drift.  We keep it and report it, because a
method that claimed to find bistability there would be finding it in anything.
It is the cheapest available check that the pipeline can return a null.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import signal as sps
from scipy.ndimage import median_filter

__all__ = [
    "bandpass",
    "zscore",
    "tonic_phasic",
    "scr_rate",
    "hr_from_bvp",
    "rmssd",
    "ar1_residual_variance",
    "activity_index",
    "windowise",
    "build_frame",
]

_EPS = 1e-12


# --------------------------------------------------------------------------- #
# primitives
# --------------------------------------------------------------------------- #
def bandpass(x, fs, lo, hi, order=3):
    ny = fs / 2.0
    lo_n, hi_n = max(lo / ny, 1e-6), min(hi / ny, 0.99)
    if hi_n <= lo_n:
        return np.asarray(x, float)
    sos = sps.butter(order, [lo_n, hi_n], btype="band", output="sos")
    return sps.sosfiltfilt(sos, np.asarray(x, float))


def zscore(x):
    """Robust z-score (median / IQR); physiological signals are heavy-tailed."""
    x = np.asarray(x, float)
    med = np.nanmedian(x)
    iqr = np.nanpercentile(x, 75) - np.nanpercentile(x, 25)
    return (x - med) / (iqr / 1.349 + _EPS)


def tonic_phasic(eda, fs, tonic_win_s=60.0):
    """
    Split EDA into slow tonic (SCL) and fast phasic (SCR) components.

    Median filtering rather than a low-pass filter, because SCRs are asymmetric
    spikes and a linear filter leaks them into the tonic estimate.
    """
    eda = np.asarray(eda, float)
    k = max(int(tonic_win_s * fs) | 1, 3)
    tonic = median_filter(eda, size=k, mode="nearest")
    return tonic, eda - tonic


def scr_rate(phasic, fs, window_s, amp_thresh=0.01):
    """Skin-conductance-response events per minute, per non-overlapping window."""
    phasic = np.asarray(phasic, float)
    w = max(int(window_s * fs), 1)
    n = len(phasic) // w
    out = np.zeros(n)
    thr = max(amp_thresh, 0.05 * np.nanstd(phasic))
    for i in range(n):
        seg = phasic[i * w : (i + 1) * w]
        pk, _ = sps.find_peaks(seg, height=thr, distance=max(int(1.0 * fs), 1))
        out[i] = len(pk) * 60.0 / window_s
    return out


def hr_from_bvp(bvp, fs, window_s):
    """
    Heart rate (bpm) and RMSSD (ms) per window, from raw PPG/BVP.

    Peaks are detected on the 0.7-3.5 Hz band (42-210 bpm).  Windows whose
    detected beat count is physiologically implausible return NaN and are
    interpolated by the caller.
    """
    bvp = np.asarray(bvp, float)
    filt = bandpass(bvp, fs, 0.7, 3.5)
    w = max(int(window_s * fs), 1)
    n = len(filt) // w
    hr = np.full(n, np.nan)
    rr = np.full(n, np.nan)

    for i in range(n):
        seg = filt[i * w : (i + 1) * w]
        if np.std(seg) < _EPS:
            continue
        pk, _ = sps.find_peaks(seg, distance=max(int(0.33 * fs), 1),
                               height=0.2 * np.std(seg))
        if len(pk) < 3:
            continue
        ibi = np.diff(pk) / fs * 1000.0                     # ms
        ibi = ibi[(ibi > 300) & (ibi < 1600)]               # 37-200 bpm
        if len(ibi) < 2:
            continue
        hr[i] = 60000.0 / np.mean(ibi)
        rr[i] = np.sqrt(np.mean(np.diff(ibi) ** 2))
    return hr, rr


def rmssd(ibi_ms):
    ibi_ms = np.asarray(ibi_ms, float)
    return float(np.sqrt(np.mean(np.diff(ibi_ms) ** 2))) if len(ibi_ms) > 1 else np.nan


def ar1_residual_variance(y, window):
    """
    Rolling one-step-ahead prediction error of an AR(1) fit -- our operational
    definition of contextual uncertainty U_t: how unpredictable the immediate
    environment is, independent of how intense it is.
    """
    y = np.asarray(y, float)
    out = np.full(y.shape, np.nan)
    for i in range(window, len(y)):
        seg = y[i - window : i]
        if np.std(seg) < 1e-9:
            out[i] = 0.0
            continue
        phi = np.corrcoef(seg[:-1], seg[1:])[0, 1]
        phi = 0.0 if not np.isfinite(phi) else float(np.clip(phi, -0.99, 0.99))
        out[i] = np.var(seg[1:] - phi * seg[:-1])
    if np.isnan(out[:window]).all() and np.isfinite(out[window:]).any():
        out[:window] = np.nanmedian(out[window:])
    return out


def activity_index(acc, fs, window_s):
    """
    Per-window motion intensity from tri-axial accelerometry, and the magnitude
    of change between consecutive windows (our task/behaviour switch cost T_t).
    """
    acc = np.asarray(acc, float)
    mag = np.linalg.norm(acc, axis=1) if acc.ndim == 2 else np.abs(acc)
    w = max(int(window_s * fs), 1)
    n = len(mag) // w
    act = np.array([np.std(mag[i * w : (i + 1) * w]) for i in range(n)])
    switch = np.abs(np.diff(act, prepend=act[0] if n else 0.0))
    return act, switch


# --------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------- #
def windowise(labels, fs_label, window_s, n_windows):
    """Majority experimental label per analysis window (used for validation only)."""
    labels = np.asarray(labels).ravel()
    w = max(int(window_s * fs_label), 1)
    out = np.full(n_windows, -1, dtype=int)
    for i in range(n_windows):
        seg = labels[i * w : (i + 1) * w]
        if seg.size:
            vals, cnt = np.unique(seg, return_counts=True)
            out[i] = int(vals[np.argmax(cnt)])
    return out


def _fill(a):
    s = pd.Series(np.asarray(a, float))
    return s.interpolate(limit_direction="both").fillna(0.0).to_numpy()


def build_frame(hr, rr, scr, tonic_win, act_switch, window_s,
                config="B", unc_window=20, temp_win=None):
    """
    Assemble the modelling frame (x, S, T, U) under the chosen sensor
    assignment.  All series are per-window and equal length.
    """
    n = min(len(hr), len(rr), len(scr), len(tonic_win), len(act_switch))
    if temp_win is not None:
        n = min(n, len(temp_win))
    hr, rr = _fill(hr[:n]), _fill(rr[:n])
    scr, ton, sw = _fill(scr[:n]), _fill(tonic_win[:n]), _fill(act_switch[:n])
    tmp = _fill(temp_win[:n]) if temp_win is not None else None

    if config == "B":                                # PRIMARY
        x = zscore(ton)                              # electrodermal load
        S = zscore(hr)                               # cardiac drive
        U = zscore(ar1_residual_variance(zscore(hr), unc_window))
        T = zscore(sw)                               # accelerometer
    elif config == "C":                              # ROBUSTNESS
        if tmp is None:
            raise ValueError("config C requires skin temperature")
        x = zscore(tmp)                              # peripheral vasomotor load
        S = zscore(scr)                              # EDA phasic
        U = zscore(ar1_residual_variance(zscore(ton), unc_window))
        T = zscore(sw)
    elif config == "A":                              # NEGATIVE CONTROL
        x = zscore(hr) - zscore(rr)                  # cardiac; noise-dominated
        S = zscore(scr)
        U = zscore(ar1_residual_variance(zscore(ton), unc_window))
        T = zscore(sw)
    else:
        raise ValueError("config must be 'A', 'B' or 'C'")

    # bound the latent coordinate to the cusp's natural scale; the cubic term
    # otherwise dominates on outliers and destabilises the optimiser
    x = np.clip(x, -4.0, 4.0)
    return pd.DataFrame({"x": x, "S": np.clip(S, -4, 4), "T": np.clip(T, -4, 4),
                         "U": np.clip(U, -4, 4)})
