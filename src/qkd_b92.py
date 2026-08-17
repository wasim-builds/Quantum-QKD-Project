"""
qkd_b92.py - B92 QKD Protocol Baseline Simulation
===================================================
Simulates the B92 Quantum Key Distribution protocol using Qiskit AerSimulator.
Uses BATCH execution (no sequential circuit-per-qubit loop) for speed.
Random seed is fixed for full reproducibility.

Alice: |0> for bit 0, |+> for bit 1
Bob  : measures in Z-basis (b=0) or X-basis (b=1) randomly
Sifting: Bob keeps only conclusive results (measured '1').
"""

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt

# ---- Reproducibility ----
SEED = 42
np.random.seed(SEED)


def run_b92_batch(num_bits: int = 500, eve_present: bool = False) -> tuple[int, float]:
    """
    Simulates the B92 protocol using batched 1-qubit circuits.
    Returns: (sifted_key_length, QBER_percentage)
    """
    alice_bits = np.random.randint(2, size=num_bits)
    bob_bases  = np.random.randint(2, size=num_bits)
    eve_bases  = np.random.randint(2, size=num_bits) if eve_present else None

    circuits = []
    for i in range(num_bits):
        qc = QuantumCircuit(1, 1)

        # --- Alice Preparation ---
        if alice_bits[i] == 1:
            qc.h(0)  # |+> state

        # --- Eve's Intercept-Resend ---
        if eve_present:
            qc.barrier()
            if eve_bases[i] == 1:          # Eve measures in X basis
                qc.h(0)
            qc.measure(0, 0)               # Eve's mid-circuit measurement
            # Eve re-prepares the collapsed state and sends to Bob
            # Qiskit Aer handles state collapse correctly with mid-circuit measurement
            if eve_bases[i] == 1:
                qc.h(0)                    # Re-encode back to X basis for Bob

        qc.barrier()

        # --- Bob's Measurement ---
        if bob_bases[i] == 1:              # Bob measures in X basis
            qc.h(0)
        qc.measure(0, 0)
        circuits.append(qc)

    # --- Batch Execution ---
    simulator = AerSimulator(seed_simulator=SEED)
    compiled   = transpile(circuits, simulator, seed_transpiler=SEED)
    result     = simulator.run(compiled, shots=1).result()

    # --- B92 Sifting Phase ---
    # A conclusive measurement occurs ONLY when Bob measures '1'.
    # - Bob measures '1' in Z-basis (b=0)  => Alice sent |+> (bit 1)
    # - Bob measures '1' in X-basis (b=1)  => Alice sent |0>  (bit 0)
    sifted_alice = []
    sifted_bob   = []

    for i in range(num_bits):
        counts      = result.get_counts(i)
        measured    = list(counts.keys())[0]
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
    N = 500

    print(f"[*] B92 Protocol Simulation (N={N} bits, seed={SEED})")
    print("=" * 55)

    print(f"\n[*] Running WITHOUT Eavesdropper...")
    length_clean, qber_clean = run_b92_batch(num_bits=N, eve_present=False)
    print(f"    Sifted Key Length : {length_clean}")
    print(f"    QBER              : {qber_clean:.2f}%")

    print(f"\n[*] Running WITH Intercept-Resend Eavesdropper (Eve)...")
    length_eve, qber_eve = run_b92_batch(num_bits=N, eve_present=True)
    print(f"    Sifted Key Length : {length_eve}")
    print(f"    QBER              : {qber_eve:.2f}%")

    print(f"\n[*] Theoretical Prediction: QBER_Eve ~ 33.33%")

    if qber_eve > 25.0:
        print("\n[!] HIGH QBER DETECTED! Eavesdropper presence confirmed. Aborting key exchange.")
    else:
        print("\n[+] QBER within acceptable limits. Channel appears clean.")
