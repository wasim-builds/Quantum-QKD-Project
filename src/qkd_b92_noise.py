import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, phase_damping_error

def simulate_b92_batch(num_bits=1000, noise_prob=0.0, eve_present=False):
    """
    Simulates B92 efficiently using a batch of 1-qubit quantum circuits.
    """
    alice_bits = np.random.randint(2, size=num_bits)
    bob_bases = np.random.randint(2, size=num_bits)
    eve_bases = np.random.randint(2, size=num_bits) if eve_present else []

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
        noise_model.add_all_qubit_quantum_error(error_depol, ['id', 'u1', 'u2', 'u3', 'x', 'z'])
        noise_model.add_all_qubit_quantum_error(error_phase, ['h'])
        
    simulator = AerSimulator(noise_model=noise_model)
    compiled_circuits = transpile(circuits, simulator)
    
    # Run simulation (batch execution of 1-qubit circuits is fast)
    result = simulator.run(compiled_circuits, shots=1).result()
    
    # Sifting Phase
    sifted_alice = []
    sifted_bob = []
    
    for i in range(num_bits):
        counts = result.get_counts(i)
        measured_bit = list(counts.keys())[0]
        
        if measured_bit == '1':
            if bob_bases[i] == 0:
                sifted_bob.append(1)
                sifted_alice.append(alice_bits[i])
            else:
                sifted_bob.append(0)
                sifted_alice.append(alice_bits[i])
                
    errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
    sifted_length = len(sifted_alice)
    qber = (errors / sifted_length) * 100 if sifted_length > 0 else 0
    
    return sifted_length, qber

if __name__ == "__main__":
    noise_levels = np.linspace(0, 0.5, 10)
    qber_clean = []
    qber_eve = []
    
    print("[*] Running Batch Noise Simulations...")
    for p in noise_levels:
        _, q_c = simulate_b92_batch(num_bits=2000, noise_prob=p, eve_present=False)
        _, q_e = simulate_b92_batch(num_bits=2000, noise_prob=p, eve_present=True)
        qber_clean.append(q_c)
        qber_eve.append(q_e)
        print(f"    Noise {p:.2f} -> Clean QBER: {q_c:.2f}%, Eve QBER: {q_e:.2f}%")
        
    plt.figure(figsize=(10, 6))
    plt.plot(noise_levels, qber_clean, marker='o', label='No Eavesdropper (Clean Channel)')
    plt.plot(noise_levels, qber_eve, marker='s', color='red', label='Intercept-Resend Eavesdropper')
    plt.axhline(y=25.0, color='k', linestyle='--', label='Theoretical Abort Threshold (25%)')
    plt.fill_between(noise_levels, 25.0, 100, color='red', alpha=0.1)
    
    plt.title('B92 Quantum Key Distribution: QBER vs. Channel Noise', fontsize=14)
    plt.xlabel('Depolarizing/Phase Error Probability', fontsize=12)
    plt.ylabel('Quantum Bit Error Rate (QBER) %', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig('data/qber_noise_plot.eps', format='eps')
    plt.savefig('data/qber_noise_plot.png', format='png')
    print("[+] Saved QBER plot to data/qber_noise_plot.eps")
