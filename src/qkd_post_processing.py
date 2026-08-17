"""
qkd_post_processing.py - B92 Secret Key Rate Analysis
======================================================
Computes and plots the Secret Key Rate (SKR) for B92 under realistic
Cascade error correction (f_ec = 1.2) and Privacy Amplification.

SKR formula:
    SKR = 1 - f_ec * H(e) - H(e)
         = 1 - (1 + f_ec) * H(e)

For B92 the secure QBER threshold is derived from setting SKR = 0:
    1 - (1 + f_ec) * H(e) = 0
    H(e) = 1 / (1 + f_ec) = 1 / 2.2 ≈ 0.4545
    => e_threshold ≈ 0.0953  (9.53%) for f_ec = 1.2

NOTE: The earlier paper text claimed QBER < 25% based on the BB84/
      abort threshold. The 25% is the protocol-level abort threshold
      (eavesdropper detection). The actual KEY-RATE threshold (where
      SKR drops to 0 for Cascade) is ~9.53%. Both are reported here.

Also prints the correct Privacy Amplification compression table.

Random seed fixed at 42.
"""

import numpy as np
import matplotlib.pyplot as plt

# ---- Reproducibility ----
SEED = 42
np.random.seed(SEED)


def binary_entropy(p: float) -> float:
    """Binary entropy H(p) = -p*log2(p) - (1-p)*log2(1-p). Returns 0 at boundaries."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * np.log2(p) - (1 - p) * np.log2(1 - p)


def calculate_skr(qber: float, f_ec: float = 1.2) -> float:
    """
    Secret Key Rate (SKR) per sifted bit for B92 with Cascade + Privacy Amplification.

    SKR = 1 - (1 + f_ec) * H(QBER)

    - The first H(QBER) term is Eve's intrinsic quantum side-information.
    - The f_ec * H(QBER) term is the information leaked during error correction.
    - Returns 0.0 if SKR <= 0 (protocol cannot generate a secure key).
    """
    skr = 1.0 - (1.0 + f_ec) * binary_entropy(qber)
    return max(0.0, skr)


def skr_threshold(f_ec: float = 1.2) -> float:
    """
    Compute the QBER threshold where SKR -> 0.
    Solve: (1 + f_ec) * H(e) = 1  =>  H(e) = 1/(1+f_ec)
    Approximate numerically by scanning.
    """
    target_h = 1.0 / (1.0 + f_ec)
    # Binary search on e in (0, 0.5)
    lo, hi = 1e-9, 0.4999
    for _ in range(200):
        mid = (lo + hi) / 2
        if binary_entropy(mid) < target_h:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def compression_ratio(qber: float, f_ec: float = 1.2) -> float:
    """
    Fraction of the reconciled key that REMAINS after Privacy Amplification.
    compression = SKR = 1 - (1 + f_ec) * H(e)
    A value of 0.923 means 92.3% of the key is retained (7.7% discarded).
    Returns 0.0 if no secure key can be generated.
    """
    return calculate_skr(qber, f_ec)


if __name__ == "__main__":
    f_ec   = 1.2
    thresh = skr_threshold(f_ec)

    print(f"[*] B92 Secret Key Rate Analysis (seed={SEED})")
    print(f"    Error correction inefficiency f_ec = {f_ec}")
    print(f"    SKR = 1 - (1 + {f_ec}) * H(QBER)  =  1 - {1+f_ec:.1f} * H(QBER)")
    print(f"    Key-rate QBER threshold: {thresh*100:.2f}%  (SKR = 0 above this)")
    print(f"    Protocol abort threshold (eavesdropper detection): 25.0%")
    print()

    # ---- Privacy Amplification Table ----
    # These are the mathematically correct compression ratios
    qber_levels = [0.01, 0.05, 0.10, thresh]
    print(f"  {'QBER':>8}  {'H(e)':>8}  {'Info Leaked':>12}  {'SKR (Compression)':>20}")
    print("  " + "-" * 58)
    for e in qber_levels:
        h   = binary_entropy(e)
        skr = calculate_skr(e, f_ec)
        lk  = (1 + f_ec) * h
        label = f"{e*100:.1f}%"
        if abs(e - thresh) < 0.0001:
            label = f"{thresh*100:.2f}% (threshold)"
        print(f"  {label:>8}  {h:>8.4f}  {lk:>11.4f}x  {skr*100:>18.1f}%")
    print()

    # ---- Plot SKR vs noise ----
    noise_levels = np.linspace(0, 0.20, 500)
    # For clean channel: QBER ≈ lambda/2 for depolarizing noise
    qbers_from_noise = noise_levels / 2.0

    skr_ideal   = [calculate_skr(q, f_ec=1.0) for q in qbers_from_noise]
    skr_cascade = [calculate_skr(q, f_ec=f_ec)  for q in qbers_from_noise]

    thresh_ideal   = skr_threshold(1.0)
    thresh_cascade = thresh

    plt.figure(figsize=(10, 6))
    plt.plot(noise_levels * 100, skr_ideal,
             label=f'Ideal Error Correction (Shannon Limit, $f_{{EC}}=1.0$)',
             linestyle='--', color='steelblue')
    plt.plot(noise_levels * 100, skr_cascade,
             label=f'Cascade Protocol ($f_{{EC}}=1.2$)',
             color='seagreen', linewidth=2)

    plt.fill_between(noise_levels * 100, 0, skr_cascade, color='seagreen', alpha=0.1)

    plt.axvline(x=thresh_cascade * 200,
                color='crimson', linestyle=':',
                label=f'Cascade SKR Cutoff: QBER = {thresh_cascade*100:.2f}% (noise ≈ {thresh_cascade*200:.1f}%)')
    plt.axvline(x=thresh_ideal * 200,
                color='steelblue', linestyle=':',
                label=f'Ideal SKR Cutoff: QBER = {thresh_ideal*100:.2f}% (noise ≈ {thresh_ideal*200:.1f}%)')

    plt.title('B92 Secret Key Rate (SKR) vs. Depolarizing Noise (seed=42)', fontsize=14)
    plt.xlabel('Depolarizing Error Probability (%)', fontsize=12)
    plt.ylabel('Secret Key Rate (Bits / Sifted Qubit)', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(fontsize=9)
    plt.ylim(0, 1.05)
    plt.tight_layout()

    plt.savefig('data/skr_post_processing.eps', format='eps')
    plt.savefig('data/skr_post_processing.png', format='png', dpi=150)
    print("[+] Saved SKR plot to data/skr_post_processing.eps / .png")
