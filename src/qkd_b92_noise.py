"""
qkd_b92_noise.py - B92 Noise Sensitivity Analysis
===================================================
Sweeps depolarizing + phase-damping noise probability across
lambda in [0.0, 0.25] with 6 equally spaced steps (matching paper Table IV).
N = 500 bits per noise level (matching paper claims).
Random seed fixed at 42 for full reproducibility.

Outputs:
    data/qber_noise_plot.eps / .png
    Prints a table of (lambda, clean_QBER, eve_QBER, gap)
"""

import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, phase_damping_error

# ---- Reproducibility ----
SEED = 42
np.random.seed(SEED)

# ---- Simulation Parameters (must match paper Table IV) ----
N_BITS    = 500
N_LEVELS  = 6
NOISE_MIN = 0.00
NOISE_MAX = 0.25


def simulate_b92_batch(num_bits: int, noise_prob: float, eve_present: bool) -> tuple[int, float]:
    """
    Batch B92 simulation with depolarizing + phase-damping noise.
    Returns: (sifted_key_length, QBER_percentage)
    """
    alice_bits = np.random.randint(2, size=num_bits)
    bob_bases  = np.random.randint(2, size=num_bits)
    eve_bases  = np.random.randint(2, size=num_bits) if eve_present else None

    circuits = []
    for i in range(num_bits):
        qc = QuantumCircuit(1, 1)

        # Alice Preparation
        if alice_bits[i] == 1:
            qc.h(0)

        # Eve Interception
        if eve_present:
            qc.barrier()
            if eve_bases[i] == 1:
                qc.h(0)
            qc.measure(0, 0)
            if eve_bases[i] == 1:
                qc.h(0)

        qc.barrier()

        # Bob Measurement
        if bob_bases[i] == 1:
            qc.h(0)
        qc.measure(0, 0)
        circuits.append(qc)

    # Build Noise Model
    noise_model = NoiseModel()
    if noise_prob > 0:
        error_depol = depolarizing_error(noise_prob, 1)
        error_phase = phase_damping_error(noise_prob, 1)
        # Depolarizing on all single-qubit gates (except measure/reset)
        noise_model.add_all_qubit_quantum_error(error_depol, ['id', 'u1', 'u2', 'u3', 'x', 'z'])
        # Phase damping specifically on H gates (diagonal basis rotations)
        noise_model.add_all_qubit_quantum_error(error_phase, ['h'])

    simulator = AerSimulator(noise_model=noise_model, seed_simulator=SEED)
    compiled   = transpile(circuits, simulator, seed_transpiler=SEED)
    result     = simulator.run(compiled, shots=1).result()

    # B92 Sifting
    sifted_alice = []
    sifted_bob   = []

    for i in range(num_bits):
        counts   = result.get_counts(i)
        measured = list(counts.keys())[0]
        if measured == '1':
            if bob_bases[i] == 0:
                sifted_bob.append(1)
                sifted_alice.append(alice_bits[i])
            else:
                sifted_bob.append(0)
                sifted_alice.append(alice_bits[i])

    errors        = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
    sifted_length = len(sifted_alice)
    qber          = (errors / sifted_length) * 100 if sifted_length > 0 else 0.0

    return sifted_length, qber


if __name__ == "__main__":
    noise_levels = np.linspace(NOISE_MIN, NOISE_MAX, N_LEVELS)
    qber_clean   = []
    qber_eve     = []

    print(f"[*] B92 Noise Simulation (N={N_BITS} bits/level, {N_LEVELS} levels, seed={SEED})")
    print(f"    Noise range: [{NOISE_MIN}, {NOISE_MAX}]")
    print("=" * 70)
    print(f"  {'lambda':>8}  {'Clean QBER':>12}  {'Eve QBER':>12}  {'Gap':>10}")
    print("  " + "-" * 56)

    for p in noise_levels:
        _, q_c = simulate_b92_batch(num_bits=N_BITS, noise_prob=p, eve_present=False)
        _, q_e = simulate_b92_batch(num_bits=N_BITS, noise_prob=p, eve_present=True)
        qber_clean.append(q_c)
        qber_eve.append(q_e)
        print(f"  {p:>8.2f}  {q_c:>11.2f}%  {q_e:>11.2f}%  {q_e - q_c:>9.2f}%")

    print("=" * 70)

    # --- Plot ---
    plt.figure(figsize=(10, 6))
    plt.plot(noise_levels, qber_clean, marker='o', label='No Eavesdropper (Clean Channel)', color='steelblue')
    plt.plot(noise_levels, qber_eve,   marker='s', color='crimson', label='Intercept-Resend Eavesdropper')
    plt.axhline(y=33.33, color='darkorange', linestyle='--', label='Theoretical Eve QBER Floor (33.3%)')
    plt.axhline(y=25.0,  color='black',      linestyle=':',  label='Abort Threshold (25%)')
    plt.fill_between(noise_levels, 25.0, 100, color='red', alpha=0.05)

    plt.title('B92 QKD: QBER vs. Channel Noise (N=500 bits, seed=42)', fontsize=14)
    plt.xlabel('Depolarizing / Phase-Damping Error Probability ($\\lambda$)', fontsize=12)
    plt.ylabel('Quantum Bit Error Rate (QBER %)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.ylim(0, 60)
    plt.tight_layout()
    plt.savefig('data/qber_noise_plot.eps', format='eps')
    plt.savefig('data/qber_noise_plot.png', format='png', dpi=150)
    print("\n[+] Saved QBER plot to data/qber_noise_plot.eps / .png")
