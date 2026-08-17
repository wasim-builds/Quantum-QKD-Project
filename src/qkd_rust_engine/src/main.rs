use rand::Rng;
use rayon::prelude::*;
use std::time::Instant;

fn simulate_b92(num_bits: usize, eve_present: bool, noise_prob: f64) -> (usize, f64) {
    let results: Vec<(Option<usize>, Option<usize>)> = (0..num_bits)
        .into_par_iter()
        .map(|_| {
            let mut rng = rand::thread_rng();
            let alice_bit: usize = rng.gen_range(0..2);
            let mut c0 = if alice_bit == 0 { 1.0 } else { std::f64::consts::FRAC_1_SQRT_2 };
            let mut c1 = if alice_bit == 0 { 0.0 } else { std::f64::consts::FRAC_1_SQRT_2 };

            // Eve intercept-resend
            if eve_present {
                let eve_basis: usize = rng.gen_range(0..2);
                if eve_basis == 0 { // Z basis
                    let p0 = c0 * c0;
                    if rng.gen_range(0.0..1.0) < p0 { c0 = 1.0; c1 = 0.0; } 
                    else { c0 = 0.0; c1 = 1.0; }
                } else { // X basis
                    let h_c0 = (c0 + c1) * std::f64::consts::FRAC_1_SQRT_2;
                    let _h_c1 = (c0 - c1) * std::f64::consts::FRAC_1_SQRT_2;
                    let p0 = h_c0 * h_c0;
                    let measured = if rng.gen_range(0.0..1.0) < p0 { 0 } else { 1 };
                    c0 = if measured == 0 { std::f64::consts::FRAC_1_SQRT_2 } else { std::f64::consts::FRAC_1_SQRT_2 };
                    c1 = if measured == 0 { std::f64::consts::FRAC_1_SQRT_2 } else { -std::f64::consts::FRAC_1_SQRT_2 };
                }
            }

            // Simple depolarizing noise
            if noise_prob > 0.0 && rng.gen_range(0.0..1.0) < noise_prob {
                // Completely mix state
                let state: usize = rng.gen_range(0..4); // |0>, |1>, |+>, |->
                match state {
                    0 => { c0 = 1.0; c1 = 0.0; },
                    1 => { c0 = 0.0; c1 = 1.0; },
                    2 => { c0 = std::f64::consts::FRAC_1_SQRT_2; c1 = std::f64::consts::FRAC_1_SQRT_2; },
                    _ => { c0 = std::f64::consts::FRAC_1_SQRT_2; c1 = -std::f64::consts::FRAC_1_SQRT_2; },
                }
            }

            // Bob measurement
            let bob_basis: usize = rng.gen_range(0..2);
            let bob_measured_1 = if bob_basis == 0 { // Z basis
                let p1 = c1 * c1;
                rng.gen_range(0.0..1.0) < p1
            } else { // X basis
                let h_c1 = (c0 - c1) * std::f64::consts::FRAC_1_SQRT_2;
                let p1 = h_c1 * h_c1;
                rng.gen_range(0.0..1.0) < p1
            };

            if bob_measured_1 {
                let sifted_bob = if bob_basis == 0 { 1 } else { 0 };
                (Some(alice_bit), Some(sifted_bob))
            } else {
                (None, None)
            }
        })
        .collect();

    let mut sifted_len = 0;
    let mut errors = 0;
    for (a, b) in results {
        if let (Some(alice), Some(bob)) = (a, b) {
            sifted_len += 1;
            if alice != bob {
                errors += 1;
            }
        }
    }
    
    let qber = if sifted_len > 0 { (errors as f64 / sifted_len as f64) * 100.0 } else { 0.0 };
    (sifted_len, qber)
}

fn main() {
    let n_qubits = 10_000_000;
    println!("[*] Rust B92 Quantum Simulator Engine");
    println!("    Simulating {} qubits using Rayon parallelism...", n_qubits);

    let start = Instant::now();
    let (sifted_clean, qber_clean) = simulate_b92(n_qubits, false, 0.0);
    println!("[+] Clean Channel: Sifted Key = {}, QBER = {:.2}% (Expected ~0.0%)", sifted_clean, qber_clean);

    let (sifted_eve, qber_eve) = simulate_b92(n_qubits, true, 0.0);
    println!("[+] Eve Intercept: Sifted Key = {}, QBER = {:.2}% (Expected ~33.3%)", sifted_eve, qber_eve);

    println!("[*] Simulation completed in {:.2?}", start.elapsed());
}
