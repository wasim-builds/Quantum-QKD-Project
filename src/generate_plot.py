import matplotlib.pyplot as plt
import numpy as np

engines = ['Qiskit AerSimulator\n(Python, sequential batch)', 'Bespoke Rust Engine\n(qkd_rust_engine, Rayon)']
qubits = [10_000, 10_000_000]
time_ms = [30000, 335.65] # 30s vs 335.65ms

# Let's plot execution time vs number of qubits on a log-log scale, or just a bar chart
fig, ax1 = plt.subplots(figsize=(8, 6))

x = np.arange(len(engines))
width = 0.35

color1 = 'tab:blue'
ax1.set_xlabel('Simulation Engine')
ax1.set_ylabel('Execution Time (ms)', color=color1)
bars1 = ax1.bar(x - width/2, time_ms, width, color=color1, label='Execution Time (ms)')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_yscale('log')

ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('Simulated Qubits', color=color2)
bars2 = ax2.bar(x + width/2, qubits, width, color=color2, label='Simulated Qubits')
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_yscale('log')

ax1.set_xticks(x)
ax1.set_xticklabels(engines)

# Add text labels on bars
for bar in bars1:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, yval, f'{yval:,.0f} ms' if yval > 1000 else f'{yval:,.2f} ms', va='bottom', ha='center', color=color1)

for bar in bars2:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, yval, f'{yval:,}', va='bottom', ha='center', color=color2)

plt.title('B92 QKD Simulation Performance: Qiskit vs Rust Engine')
fig.tight_layout()

plt.savefig('/run/media/wasim/2ADE-F06D/research/Quantum-QKD-Project/data/rust_benchmark_results.png', dpi=300)
print("Saved to data/rust_benchmark_results.png")
