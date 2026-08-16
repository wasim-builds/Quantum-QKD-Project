import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

def binary_entropy(p):
    """Calculate the binary entropy function H(p)."""
    if p <= 0 or p >= 1:
        return 0
    return -p * np.log2(p) - (1 - p) * np.log2(1 - p)

def calculate_skr(qber, f_ec=1.2):
    """
    Calculate the Secret Key Rate (SKR) per sifted bit.
    SKR = 1 - f_ec * H(QBER) - H(QBER)
    Where f_ec is the error correction inefficiency (Cascade is typically ~1.2)
    and the second H(QBER) is the privacy amplification term (Eve's info).
    For B92, Eve's info leaks faster, but we'll use standard bounds.
    """
    if qber >= 0.25:  # Absolute theoretical limit for QKD (BB84 is 11%, B92 is strict)
        return 0.0
    
    # Information leaked to Eve during Error Correction (Cascade)
    leakage_ec = f_ec * binary_entropy(qber)
    
    # Information intrinsically held by Eve (Privacy Amplification bound)
    leakage_eve = binary_entropy(qber)
    
    skr = 1.0 - leakage_ec - leakage_eve
    return max(0.0, skr)

if __name__ == "__main__":
    noise_levels = np.linspace(0, 0.20, 50)
    
    # Calculate QBER based on noise. 
    # Depolarizing noise p results in QBER approx p/2.
    qbers = noise_levels / 2.0 
    
    skr_ideal = [calculate_skr(q, f_ec=1.0) for q in qbers]
    skr_cascade = [calculate_skr(q, f_ec=1.2) for q in qbers]
    
    plt.figure(figsize=(10, 6))
    plt.plot(noise_levels * 100, skr_ideal, label='Ideal Error Correction (Shannon Limit)', linestyle='--', color='blue')
    plt.plot(noise_levels * 100, skr_cascade, label='Cascade Protocol (f_ec = 1.2)', color='green', linewidth=2)
    
    # Fill area where SKR drops to zero
    plt.fill_between(noise_levels * 100, 0, skr_cascade, color='green', alpha=0.1)
    plt.axvline(x=22.0, color='red', linestyle=':', label='Theoretical SKR Cutoff')
    
    plt.title('B92 Secret Key Rate (SKR) vs. Depolarizing Noise', fontsize=14)
    plt.xlabel('Depolarizing Error Probability (%)', fontsize=12)
    plt.ylabel('Secret Key Rate (Bits / Sifted Qubit)', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig('data/skr_post_processing.eps', format='eps')
    plt.savefig('data/skr_post_processing.png', format='png')
    print("[+] Saved SKR plot to data/skr_post_processing.png")
