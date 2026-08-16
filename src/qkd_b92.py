import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt

def run_b92_simulation(num_bits=1000, eve_present=False):
    """
    Simulates the B92 Quantum Key Distribution protocol.
    Alice sends |0> for bit 0, and |+> for bit 1.
    Bob measures randomly in standard (Z) or Hadamard (X) basis.
    """
    # Alice generates random bits
    alice_bits = np.random.randint(2, size=num_bits)
    
    # Bob generates random measurement bases (0 for Z, 1 for X)
    bob_bases = np.random.randint(2, size=num_bits)
    
    eve_bases = []
    if eve_present:
        eve_bases = np.random.randint(2, size=num_bits)

    simulator = AerSimulator()
    
    bob_results = []
    
    for i in range(num_bits):
        qc = QuantumCircuit(1, 1)
        
        # ALICE PREPARATION
        if alice_bits[i] == 0:
            pass # State |0>
        else:
            qc.h(0) # State |+>
            
        # EVE INTERCEPTION (Intercept-Resend)
        if eve_present:
            if eve_bases[i] == 0:
                qc.measure(0, 0) # Measure in Z basis
            else:
                qc.h(0)
                qc.measure(0, 0)
                qc.h(0) # Re-encode into X basis before sending to Bob
                
            # We need to simulate mid-circuit measurement for Eve or just break it into 2 circuits.
            # Qiskit Aer supports mid-circuit measurements. 
            
        # BOB MEASUREMENT
        if bob_bases[i] == 0:
            # Measure in Z basis (to detect |+>)
            qc.measure(0, 0)
        else:
            # Measure in X basis (to detect |0>)
            qc.h(0)
            qc.measure(0, 0)
            
        # Execute the circuit for 1 shot
        compiled_circuit = transpile(qc, simulator)
        result = simulator.run(compiled_circuit, shots=1).result()
        counts = result.get_counts()
        
        # Extract the single bit result ('0' or '1')
        measured_bit = int(list(counts.keys())[0])
        bob_results.append(measured_bit)

    # B92 Sifting Phase
    # Bob only gets a conclusive result if he measures '1'. 
    # If Bob measures '1' in Z basis, Alice must have sent |+> (bit 1).
    # If Bob measures '1' in X basis, Alice must have sent |0> (bit 0).
    
    sifted_key_alice = []
    sifted_key_bob = []
    
    for i in range(num_bits):
        # In B92, a measurement of '1' means Bob guessed the WRONG basis 
        # relative to what Alice sent, which paradoxically gives him certainty!
        if bob_results[i] == 1:
            if bob_bases[i] == 0: 
                # Bob measured 1 in Z basis. He knows Alice sent |+> (bit 1).
                sifted_key_bob.append(1)
                sifted_key_alice.append(alice_bits[i])
            else:
                # Bob measured 1 in X basis. He knows Alice sent |0> (bit 0).
                sifted_key_bob.append(0)
                sifted_key_alice.append(alice_bits[i])
                
    # Calculate Quantum Bit Error Rate (QBER)
    errors = sum(1 for a, b in zip(sifted_key_alice, sifted_key_bob) if a != b)
    sifted_length = len(sifted_key_alice)
    
    qber = (errors / sifted_length) * 100 if sifted_length > 0 else 0
    
    return sifted_length, qber

if __name__ == "__main__":
    print("[*] Running B92 Protocol WITHOUT Eavesdropper...")
    length_clean, qber_clean = run_b92_simulation(num_bits=5000, eve_present=False)
    print(f"    Sifted Key Length: {length_clean}")
    print(f"    QBER: {qber_clean:.2f}%\n")
    
    print("[*] Running B92 Protocol WITH Intercept-Resend Eavesdropper (Eve)...")
    length_eve, qber_eve = run_b92_simulation(num_bits=5000, eve_present=True)
    print(f"    Sifted Key Length: {length_eve}")
    print(f"    QBER: {qber_eve:.2f}%")
    
    if qber_eve > 25.0:
        print("\n[!] HIGH QBER DETECTED! Eavesdropper presence confirmed. Aborting key exchange.")
