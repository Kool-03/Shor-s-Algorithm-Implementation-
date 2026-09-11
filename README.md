# Shor's Algorithm — Quantum Integer Factorization

> **Author:** Mohamed Khalaf  
> **Course:** EC580 — Computer Engineering Department  
> **Institution:** University of Tripoli, Faculty of Engineering

---

## Table of Contents

- [Overview](#overview)
- [Theoretical Background](#theoretical-background)
  - [The Factoring Problem](#the-factoring-problem)
  - [How Shor's Algorithm Works](#how-shors-algorithm-works)
- [Architecture & Design](#architecture--design)
  - [High-Level Pipeline](#high-level-pipeline)
  - [Register Sizing Strategy](#register-sizing-strategy)
- [Code Walkthrough](#code-walkthrough)
  - [`create_universal_mod_multiplier()`](#create_universal_mod_multipliera-power-n-n_target)
  - [`qft_inverse()`](#qft_inversen)
  - [`classical_gcd()`](#classical_gcda-b)
  - [`continued_fraction_convergents()`](#continued_fraction_convergentsphase-max_denominator)
  - [`plot_phase_circle()`](#plot_phase_circlecounts-t_control)
  - [`run_universal_shor()`](#run_universal_shorn-a)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [Visualizations](#visualizations)
- [Limitations & Notes](#limitations--notes)

---

## Overview

This project implements **Shor's Algorithm** using IBM's [Qiskit](https://qiskit.org/) framework. The implementation is **fully universal** — it dynamically sizes quantum registers, constructs modular exponentiation gates via explicit permutation matrices, and extracts prime factors through classical post-processing with continued fractions.

The default demo factors **N = 15** using base **a = 7**, producing the well-known factors **3 × 5**.

---

## Theoretical Background

### The Factoring Problem

Given a composite integer **N**, find two non-trivial factors **p** and **q** such that:

$$N = p \times q$$

Classical algorithms (e.g., trial division, general number field sieve) scale exponentially or sub-exponentially with the number of digits of **N**. Shor's Algorithm achieves this in **polynomial time** on a quantum computer, which has profound implications for RSA cryptography.

### How Shor's Algorithm Works

Shor's Algorithm reduces factoring to **order-finding** (period detection):

1. **Choose** a random base `a` such that `1 < a < N` and `gcd(a, N) = 1`.
2. **Find the order** `r` — the smallest positive integer such that `a^r ≡ 1 (mod N)`.
3. If `r` is even and `a^(r/2) ≢ −1 (mod N)`, then the factors are:
   - `gcd(a^(r/2) − 1, N)`
   - `gcd(a^(r/2) + 1, N)`

The quantum part (Quantum Phase Estimation) efficiently finds `r` by:

- Preparing a superposition over the **control register** via Hadamard gates.
- Applying **controlled modular exponentiation** `a^(2^k) mod N` to the **target register**.
- Applying the **Inverse Quantum Fourier Transform (IQFT)** to extract phase information.
- **Measuring** the control register to obtain a phase estimate `s/r`.

---

## Architecture & Design

### High-Level Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                    SHOR'S ALGORITHM PIPELINE                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Trivial Check ──► gcd(a, N) ≠ 1 ? → Return factor directly  │
│          │                                                       │
│          ▼                                                       │
│  2. Register Sizing                                              │
│     • Target qubits:  n = ⌈log₂(N)⌉                             │
│     • Control qubits: t = 2n                                     │
│          │                                                       │
│          ▼                                                       │
│  3. Quantum Circuit Construction                                 │
│     • Hadamard on all control qubits                             │
│     • X gate on first target qubit (initialize |1⟩)              │
│     • Controlled-U^(2^k) modular multiplication gates            │
│     • Inverse QFT on control register                            │
│     • Measurement                                                │
│          │                                                       │
│          ▼                                                       │
│  4. Simulation (AerSimulator, 1024 shots)                        │
│          │                                                       │
│          ▼                                                       │
│  5. Classical Post-Processing                                    │
│     • Continued fraction expansion of measured phases            │
│     • Period extraction with multiplier search                   │
│     • Factor computation via gcd                                 │
│          │                                                       │
│          ▼                                                       │
│  6. Visualizations                                               │
│     • Gate architecture bar chart                                │
│     • Circuit wire diagram                                       │
│     • Measurement histogram                                      │
│     • Phase estimation unit circle                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Register Sizing Strategy

| Register   | Size              | Purpose                                           |
|------------|-------------------|----------------------------------------------------|
| **Control** | `t = 2 × ⌈log₂(N)⌉` | Encodes the phase information for period finding  |
| **Target**  | `n = ⌈log₂(N)⌉`      | Stores the state `|a^x mod N⟩`                   |
| **Classical** | `t` bits           | Stores measurement outcomes from control register |

For the default case **N = 15**: `n = 4`, `t = 8`, giving a **12-qubit** circuit.

---

## Code Walkthrough

### `create_universal_mod_multiplier(a, power, N, n_target)`

Constructs a **controlled unitary gate** that performs modular multiplication by `a^(2^power) mod N`.

- Builds an explicit `2^n × 2^n` **permutation matrix** mapping each computational basis state `|x⟩` to `|x · a^(2^power) mod N⟩`.
- States `x ≥ N` are mapped to themselves (identity) to preserve unitarity.
- Wraps the matrix into a Qiskit `Operator`, converts to an instruction, and returns a **controlled** version.

### `qft_inverse(n)`

Implements the **Inverse Quantum Fourier Transform** on `n` qubits:

1. **Swap** qubits to reverse bit ordering.
2. For each qubit `j`, apply controlled phase rotations `CP(-π/2^(j-m))` from all preceding qubits `m`, followed by a **Hadamard** gate.

This converts phase-encoded quantum states back into computational basis states for measurement.

### `classical_gcd(a, b)`

Standard **Euclidean algorithm** for computing the greatest common divisor. Used both for the trivial factor check and for extracting factors from the period.

### `continued_fraction_convergents(phase, max_denominator)`

Performs a **continued fraction expansion** of a measured phase value to extract rational approximations `p/q` where `q ≤ max_denominator`.

- Iterates up to 20 partial quotients.
- Tracks convergents `(p, q)` using the standard recurrence relations.
- Returns all valid convergents — the denominators are candidate periods `r`.

### `plot_phase_circle(counts, t_control)`

Renders the top 6 measurement outcomes on a **polar (unit circle) plot**:

- Each measured binary string is converted to a phase `φ = C / 2^t`.
- A vector arrow is drawn from the origin to angle `2πφ` on the unit circle.
- Labels show the phase value and shot count.

This visualization reveals how Quantum Phase Estimation concentrates probability around specific angular positions corresponding to `s/r` fractions.

### `run_universal_shor(N, a)`

The **main orchestrator** that ties everything together:

1. **Trivial check** — if `gcd(a, N) ≠ 1`, outputs the factor immediately.
2. **Dynamic register sizing** — computes `n_target` and `t_control` from `N`.
3. **Circuit construction** — Hadamards, initialization, controlled modular exponentiation, IQFT, measurement.
4. **Metrics & visualization** — gate count bar chart, circuit diagram.
5. **Simulation** — runs on `AerSimulator` with 1024 shots, profiles execution time.
6. **Post-processing** — iterates over the top 5 measurement outcomes, applies continued fractions, searches for valid periods with multipliers 1–4, and computes factors via GCD.

---

## Usage

### Basic Execution

```python
# Factor N = 15 using base a = 7
python "Mohamed_Khalaf_Shor's_algorithm.py"
```

### Custom Inputs

Modify the entry point in the script:

```python
if __name__ == "__main__":
    run_universal_shor(N=15, a=7)   # Change N and a here
```

**Constraints:**
- `N` must be a composite (non-prime) integer.
- `a` must satisfy `1 < a < N` and `gcd(a, N) = 1`.
- Larger `N` values require significantly more qubits and simulation time.

### Example Output

```
======================================================================
UNIVERSAL SHOR ENGINE: Factoring N = 15 with Base a = 7
Dynamic Register Sizing: 8 Control Qubits | 4 Target Qubits
======================================================================
Building universal gate connections...

[METRICS] Total Circuit Logical Depth: <depth>
[METRICS] Simulation completed in X.XXXX seconds.

🎉 SUCCESS! Determined true period loop r = 4
👉 Prime Factors of 15 are: 3 and 5
```

---

## Dependencies

| Package       | Version | Purpose                                     |
|---------------|---------|----------------------------------------------|
| `numpy`       | ≥ 1.21  | Matrix construction and numerical operations |
| `qiskit`      | ≥ 1.0   | Quantum circuit construction and transpilation |
| `qiskit-aer`  | ≥ 0.13  | Quantum circuit simulation backend           |
| `matplotlib`  | ≥ 3.5   | Visualization (histograms, circuits, plots)  |

### Installation

```bash
pip install numpy qiskit qiskit-aer matplotlib
```

> **Note:** The script gracefully handles the absence of `qiskit-aer` by setting `AER_AVAILABLE = False` and printing an error message if simulation is attempted without it.

---

## Visualizations

The implementation produces **four** visual outputs during execution:

| # | Visualization | Description |
|---|---------------|-------------|
| 1 | **Gate Architecture Breakdown** | Bar chart showing the count of each gate type used in the circuit |
| 2 | **Circuit Wire Layout** | Full quantum circuit diagram showing all qubit wires and gate connections |
| 3 | **Measurement Histogram** | Distribution of measurement outcomes across 1024 shots |
| 4 | **Phase Estimation Unit Circle** | Polar plot mapping measured phases as vectors on the unit circle |

---

## Limitations & Notes

- **Simulation scale:** The permutation matrix approach constructs a `2^n × 2^n` dense matrix, which limits practical simulation to small `N` values (typically `N < 100` depending on available RAM).
- **Probabilistic nature:** Shor's Algorithm is probabilistic. The post-processing may not find factors on every run — re-running with a different base `a` or repeating the experiment often resolves this.
- **`display()` calls:** The script uses `display()` (lines 163, 179), which is a Jupyter/IPython function. When running from the command line, replace these with `plt.show()` or use `print()`.
- **Shot count:** The default 1024 shots provides a good balance of accuracy and speed. Increasing shots improves phase resolution for larger `N`.

---

## References

- Shor, P. W. (1994). *Algorithms for quantum computation: discrete logarithms and factoring*. Proceedings 35th Annual Symposium on Foundations of Computer Science, pp. 124–134.
- Nielsen, M. A. & Chuang, I. L. (2010). *Quantum Computation and Quantum Information*. Cambridge University Press.
- [Qiskit Documentation](https://docs.quantum.ibm.com/)
- [Qiskit Textbook — Shor's Algorithm](https://learn.qiskit.org/course/ch-algorithms/shors-algorithm)
