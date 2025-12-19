"""
quantum_circuit_generator.py

Generate random quantum circuits, inject simple artificial "bugs",
and compare ideal vs noisy simulation using Qiskit Aer.
"""

import sys
import random

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt

# Parameter input (CLI)
def get_user_input():
    """
    Get and validate user inputs for the quantum circuit parameters.
    """
    try:
        num_qubits = int(input("Enter the number of qubits: "))
        if num_qubits <= 0:
            raise ValueError("Number of qubits must be positive.")
    except ValueError as e:
        print(f"Invalid input for number of qubits: {e}")
        sys.exit(1)

    available_gates = ["h", "x", "y", "z", "cx", "ccx"]
    print(f"Available gates: {', '.join(available_gates)}")
    selected_gates = input(
        "Enter the gates to include (comma-separated): "
    ).split(",")

    selected_gates = [gate.strip() for gate in selected_gates]
    for gate in selected_gates:
        if gate not in available_gates:
            print(f"Invalid gate selected: {gate}")
            sys.exit(1)

    try:
        circuit_depth = int(
            input("Enter the circuit depth (number of layers): ")
        )
        if circuit_depth <= 0:
            raise ValueError("Circuit depth must be positive.")
    except ValueError as e:
        print(f"Invalid input for circuit depth: {e}")
        sys.exit(1)

    gate_application = (
        input("Gate application strategy (random/sequential): ")
        .strip()
        .lower()
    )
    if gate_application not in ["random", "sequential"]:
        print("Invalid strategy. Choose 'random' or 'sequential'.")
        sys.exit(1)

    # Bug flags
    bug_flip_gate_str = input(
        "Enable bug: flip some gates to X? (y/n): "
    ).strip().lower()
    bug_wrong_target_str = input(
        "Enable bug: use wrong target for CX/CCX? (y/n): "
    ).strip().lower()

    bug_flip_gate = bug_flip_gate_str == "y"
    bug_wrong_target = bug_wrong_target_str == "y"

    return (
        num_qubits,
        selected_gates,
        circuit_depth,
        gate_application,
        bug_flip_gate,
        bug_wrong_target,
    )

# Circuit construction
def build_quantum_circuit(
    num_qubits,
    selected_gates,
    circuit_depth,
    gate_application,
    bug_flip_gate=False,
    bug_wrong_target=False,
):
    """
    Build a random quantum circuit with optional injected 'bugs'.
    """
    qc = QuantumCircuit(num_qubits, num_qubits)

    for layer in range(circuit_depth):
        for qubit in range(num_qubits):
            # choose gate
            if gate_application == "random":
                gate = random.choice(selected_gates)
            else:
                gate = selected_gates[layer % len(selected_gates)]

            # Simple bug: occasionally flip gate to X
            if bug_flip_gate and random.random() < 0.1:
                gate = "x"

            # Apply the gate
            if gate == "h":
                qc.h(qubit)
            elif gate == "x":
                qc.x(qubit)
            elif gate == "y":
                qc.y(qubit)
            elif gate == "z":
                qc.z(qubit)
            elif gate == "cx":
                if num_qubits >= 2:
                    if bug_wrong_target:
                        target = (qubit + 2) % num_qubits
                    else:
                        target = (qubit + 1) % num_qubits
                    qc.cx(qubit, target)
            elif gate == "ccx":
                if num_qubits >= 3:
                    control1 = qubit
                    control2 = (qubit + 1) % num_qubits
                    target = (qubit + (3 if bug_wrong_target else 2)) % num_qubits
                    qc.ccx(control1, control2, target)
            else:
                print(f"Unsupported gate encountered: {gate}")
                sys.exit(1)

    qc.measure(range(num_qubits), range(num_qubits))
    return qc

# Simulation (ideal & noisy)
def simulate_circuit_ideal(qc, shots=1024):
    """
    Ideal (noise-free) simulation with AerSimulator.
    """
    backend = AerSimulator()
    qc_t = transpile(qc, backend)
    job = backend.run(qc_t, shots=shots)
    result = job.result()
    return result.get_counts()


def build_simple_noise_model(p_gate=0.01, p_readout=0.02):
    """
    Very simple depolarizing + readout noise model.
    """
    noise_model = NoiseModel()

    single_qubit_error = depolarizing_error(p_gate, 1)
    two_qubit_error = depolarizing_error(p_gate, 2)

    for g in ["x", "y", "z", "h"]:
        noise_model.add_all_qubit_quantum_error(single_qubit_error, g)
    for g in ["cx", "cz"]:
        noise_model.add_all_qubit_quantum_error(two_qubit_error, g)

    readout = ReadoutError(
        [[1 - p_readout, p_readout], [p_readout, 1 - p_readout]]
    )
    noise_model.add_all_qubit_readout_error(readout)

    return noise_model

def run_on_hardware(qc, backend_name="ibm_fez", shots=1024):
    """
    Run a measured circuit on an IBM Quantum backend using Qiskit Runtime Sampler.
    Assumes you already called QiskitRuntimeService() once.
    """
    service = QiskitRuntimeService()
    backend = service.backend(backend_name)
    qc_t = transpile(qc, backend=backend)

    sampler = Sampler(mode=backend, options={"default_shots": shots})
    job = sampler.run([qc_t])
    result = job.result()

    pub_result = result[0]
    data_bin = pub_result.data

    if hasattr(data_bin, "c"):
        # Convert BitArray measurements to counts
        bitarray = data_bin.c
        counts = {}
        for bitstr in bitarray:
            bit_str = bitstr.to01()  # Convert to binary string
            counts[bit_str] = counts.get(bit_str, 0) + 1
        return counts

    # Fallback if structure changes in the future
    return {}
    

def simulate_circuit_noisy(qc, noise_model, shots=1024):
    """
    Noisy simulation with a given NoiseModel.
    """
    backend = AerSimulator(noise_model=noise_model)
    qc_t = transpile(qc, backend)
    job = backend.run(qc_t, shots=shots)
    result = job.result()
    return result.get_counts()


# Main function
def main():
    # Get parameters (including bug flags) from user
    (
        num_qubits,
        selected_gates,
        circuit_depth,
        gate_application,
        bug_flip_gate,
        bug_wrong_target,
    ) = get_user_input()

    # Build clean and buggy circuits
    qc_clean = build_quantum_circuit(
        num_qubits,
        selected_gates,
        circuit_depth,
        gate_application,
        bug_flip_gate=False,
        bug_wrong_target=False,
    )

    qc_buggy = build_quantum_circuit(
        num_qubits,
        selected_gates,
        circuit_depth,
        gate_application,
        bug_flip_gate=bug_flip_gate,
        bug_wrong_target=bug_wrong_target,
    )

    print("\nClean circuit:")
    print(qc_clean.draw(output="text"))
    print("\nBuggy circuit:")
    print(qc_buggy.draw(output="text"))

    # Simulate
    noise_model = build_simple_noise_model()

    shots = 1024
    counts_clean_ideal = simulate_circuit_ideal(qc_clean, shots=shots)
    counts_clean_noisy = simulate_circuit_noisy(qc_clean, noise_model, shots=shots)
    counts_buggy_noisy = simulate_circuit_noisy(qc_buggy, noise_model, shots=shots)

    print("\nClean ideal counts:")
    print(counts_clean_ideal)
    print("\nClean noisy counts:")
    print(counts_clean_noisy)
    print("\nBuggy noisy counts:")
    print(counts_buggy_noisy)

    # Plot histograms
    try:
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        plot_histogram(counts_clean_ideal, ax=axes[0], title="Clean (ideal)")
        plot_histogram(counts_clean_noisy, ax=axes[1], title="Clean (noisy)")
        plot_histogram(counts_buggy_noisy, ax=axes[2], title="Buggy (noisy)")
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"An error occurred while plotting histograms: {e}")

    run_hw = input("Also run on IBM hardware? (y/n): ").strip().lower()
    if run_hw == "y":
        backend_name = input("Backend name (e.g. ibm_sherbrooke): ").strip()
        counts_hw = run_on_hardware(qc_clean, backend_name, shots=1024)
        print("\nHardware counts:")
        print(counts_hw)

        # quick visual compare: noisy sim vs hardware
        try:
            fig, axes = plt.subplots(1, 2, figsize=(10, 4))
            plot_histogram(counts_clean_noisy, ax=axes[0], title="Clean (noisy simulator)")
            plot_histogram(counts_hw, ax=axes[1], title=f"Hardware: {backend_name}")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print(f"Error plotting hardware results: {e}")


if __name__ == "__main__":
    main()