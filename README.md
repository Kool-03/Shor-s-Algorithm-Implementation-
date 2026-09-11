# Dynamic n-bit Shor's Algorithm Implementation

**Author:** Mohamed Khalaf  
**Course:** EC580  
**Instructor:** Professor Muharrem  

## Project Overview
This repository contains a scalable Python implementation of Shor's Algorithm using IBM's Qiskit framework. Unlike standard educational scripts that hardcode quantum gates specifically for N = 15, this implementation dynamically allocates physical memory footprints and algorithmically generates custom unitary permutation matrices on the fly.

## Key Engineering Features
* **Dynamic Resource Allocation:** Calculates target workspace sizing using logarithmic scaling and automatically configures control lines for full phase precision.
* **Universal Unitary Generation:** Mathematically constructs explicit permutation matrices for modular multiplication and converts them directly into custom quantum gates.
* **Automated Circuit Compilation:** Programmatically maps and cascades controlled-unitary gates across registers without manual circuit rewiring.
* **Hybrid Post-Processing:** Interfaces quantum simulation measurements with classical Continued Fractions and GCD routines to extract true period loops and factor the target integer.
* **Phase Alignment Visualization:** Generates a polar unit-circle plot showing vector alignments directly derived from Quantum Phase Estimation.

## Setup & Execution
Install the required dependencies:
```bash
pip install numpy qiskit qiskit-aer matplotlib

Run the script:

python "shor_algorithm_Latest version .py"
