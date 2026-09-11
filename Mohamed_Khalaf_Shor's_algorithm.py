#Shor's Algorithm implementation mede by Mohamed Khalaf, as a course project EC580 in Computer Engineering Department (University Of Tripoli Faculty of Engineering).
import numpy as np
import time
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt

try:
    from qiskit_aer import AerSimulator
    AER_AVAILABLE = True
except ImportError:
    AER_AVAILABLE = False


def create_universal_mod_multiplier(a, power, N, n_target):
    """
    Dynamically generates a universal quantum gate for: a^(2^power) mod N.
    It builds the explicit permutation matrix and wraps it into a Unitary Operator.
    """
    actual_multiplier = pow(int(a), int(2**power), int(N))
    matrix_size = 2**n_target
    permutation_matrix = np.zeros((matrix_size, matrix_size))
    
    for x in range(matrix_size):
        if x < N:
            new_x = (x * actual_multiplier) % N
            permutation_matrix[new_x, x] = 1.0
        else:
            permutation_matrix[x, x] = 1.0
            
    unitary_operator = Operator(permutation_matrix)
    custom_gate = unitary_operator.to_instruction()
    custom_gate.name = f"{a}^{2**power} mod {N}"
    return custom_gate.control()


def qft_inverse(n):
    """Generates a universal Inverse Quantum Fourier Transform (IQFT) block."""
    qc = QuantumCircuit(n)
    for qubit in range(n // 2):
        qc.swap(qubit, n - qubit - 1)
    for j in range(n):
        for m in range(j):
            qc.cp(-np.pi / float(2**(j - m)), m, j)
        qc.h(j)
    qc.name = "IQFT"
    return qc


def classical_gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def continued_fraction_convergents(phase, max_denominator):
    convergents = []
    remain = phase
    a_coeffs = []
    for _ in range(20):
        floor_val = int(remain)
        a_coeffs.append(floor_val)
        diff = remain - floor_val
        if diff < 1e-10: break
        remain = 1.0 / diff
    p_prev2, p_prev1 = 0, 1
    q_prev2, q_prev1 = 1, 0
    for coeff in a_coeffs:
        p = coeff * p_prev1 + p_prev2
        q = coeff * q_prev1 + q_prev2
        if q > max_denominator: break
        convergents.append((p, q))
        p_prev2, p_prev1 = p_prev1, p
        q_prev2, q_prev1 = q_prev1, q
    return convergents


def plot_phase_circle(counts, t_control):
    """
    Plots the top measurement phase frequencies on a Unit Circle 
    to visualize how Phase Estimation isolates the periods.
    """
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_peaks = sorted_counts[:6]  # Isolate up to the top 6 peaks
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'projection': 'polar'})
    
    # Draw a clean baseline unit circle outline
    r_circle = np.ones(100)
    theta_circle = np.linspace(0, 2*np.pi, 100)
    ax.plot(theta_circle, r_circle, color='gray', linestyle='dashed', alpha=0.5)
    
    # Process and map each binary string outcome onto the circle
    for binary_str, count in top_peaks:
        decimal_val = int(binary_str, 2)
        phase = decimal_val / (2**t_control)
        angle_rad = phase * 2 * np.pi  # Convert phase fractional spacing to radians
        
        # Plot vector arrow pointing to the phase angle
        ax.annotate('', xy=(angle_rad, 1.0), xytext=(0, 0),
                    arrowprops=dict(facecolor='crimson', edgecolor='crimson', 
                                    arrowstyle="->", lw=2.5))
        # Fixed escape warning here by prepending the string with a raw string 'r' modifier
        ax.text(angle_rad, 1.15, rf"$\phi$={phase:.3f}\n({count} shots)", 
                horizontalalignment='center', fontsize=9, fontweight='bold')
                
    ax.set_yticklabels([])  # Strip radial indicators
    ax.set_rmax(1.3)
    plt.title("Quantum Phase Estimation Vector Alignment", va='bottom', fontweight='bold')
    plt.show()


def run_universal_shor(N, a):
    """
    Completely automated Shor's Algorithm.
    Dynamically sizes registers, maps universal connections, and extracts factors.
    Includes hardware metrics and Phase Circle visualization support.
    """
    if classical_gcd(a, N) != 1:
        trivial_factor = classical_gcd(a, N)
        print(f"[EASY OUT] {a} and {N} share a common factor already! Factor is: {trivial_factor}")
        return

    n_target = int(np.ceil(np.log2(N)))   
    t_control = 2 * n_target               
    
    print("=" * 70)
    print(f"UNIVERSAL SHOR ENGINE: Factoring N = {N} with Base a = {a}")
    print(f"Dynamic Register Sizing: {t_control} Control Qubits | {n_target} Target Qubits")
    print("=" * 70)
    
    qc = QuantumCircuit(t_control + n_target, t_control)
    
    for q in range(t_control):
        qc.h(q)
        
    qc.x(t_control)
    
    print("Building universal gate connections...")
    for q in range(t_control):
        controlled_mod_gate = create_universal_mod_multiplier(a, q, N, n_target)
        target_wires = [i + t_control for i in range(n_target)]
        qc.append(controlled_mod_gate, [q] + target_wires)
        
    qc.append(qft_inverse(t_control), range(t_control))
    qc.measure(range(t_control), range(t_control))
    
    # --- COMPLEXITY BREAKDOWN MAP ---
    gate_counts = qc.count_ops()
    circuit_depth = qc.depth()
    print(f"\n[METRICS] Total Circuit Logical Depth: {circuit_depth}")
    
    plt.figure(figsize=(6, 3))
    # Fixed the color typo below: changed 'darkslatealphablue' to 'darkslateblue'
    plt.bar(gate_counts.keys(), gate_counts.values(), color='darkslateblue', edgecolor='black')
    plt.title("Quantum Gate Architecture Component Breakdown")
    plt.ylabel("Operation Counts")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()
    
    print("\nDisplaying System Wire Layout:")
    display(qc.draw(output='mpl'))
    
    if not AER_AVAILABLE:
        print("\n[ERROR] execution context 'qiskit-aer' missing.")
        return
        
    # Execution on Simulator Backend with Profiling
    print("\nRunning simulator environment shots...")
    start_time = time.time()
    simulator = AerSimulator()
    compiled_circuit = transpile(qc, simulator)
    job = simulator.run(compiled_circuit, shots=1024)
    counts = job.result().get_counts()
    end_time = time.time()
    print(f"[METRICS] Simulation completed in {end_time - start_time:.4f} seconds.")
    
    display(plot_histogram(counts))
    
    # --- PHASE ESTIMATION VECTOR CIRCLE ---
    print("\nAnalyzing angular phase alignment on unit circle...")
    plot_phase_circle(counts, t_control)
    
    # Classical Post-Processing Loop
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    success = False
    
    for binary_str, count in sorted_counts[:5]:
        C = int(binary_str, 2)
        phase = C / (2**t_control)
        
        if phase == 0: continue
            
        convergents = continued_fraction_convergents(phase, N)
        for p, q in convergents:
            if q == 0: continue
            for multiplier in range(1, 5):
                r = q * multiplier
                if r >= N: continue
                if pow(a, r, N) == 1:
                    if r % 2 == 0:
                        half_power = pow(a, r // 2, N)
                        if half_power != N - 1:
                            factor1 = classical_gcd(half_power - 1, N)
                            factor2 = classical_gcd(half_power + 1, N)
                            if 1 < factor1 < N:
                                print(f"\n🎉 SUCCESS! Determined true period loop r = {r}")
                                print(f"👉 Prime Factors of {N} are: {factor1} and {factor2}")
                                success = True
                                break
            if success: break
        if success: break
            
    if not success:
        print(f"\n[INFO] Post-processing bypass: No non-trivial factors extracted for this particular setup.")


if __name__ == "__main__":
    # Running the 12-qubit system setup with valid color mappings
    run_universal_shor(N=15, a=7)
