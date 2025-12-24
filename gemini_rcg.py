import random
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

class QuantumCircuitLab:
    def __init__(self, num_qubits):
        self.num_qubits = num_qubits
        self.simulator = AerSimulator()

    def generate_random_circuit(self, depth):
        """Generates a clean, random 'Golden' circuit."""
        qc = QuantumCircuit(self.num_qubits)
        gates = ['h', 'x', 'y', 'z', 's', 't']
        
        for _ in range(depth):
            # Add random single-qubit gates
            for q in range(self.num_qubits):
                gate = random.choice(gates)
                getattr(qc, gate)(q)
            
            # Add a random CNOT if we have enough qubits
            if self.num_qubits > 1:
                c, t = random.sample(range(self.num_qubits), 2)
                qc.cx(c, t)
        
        qc.measure_all()
        return qc

    def inject_bug(self, circuit, bug_type="swap"):
        """
        Creates a copy of the circuit and introduces a specific flaw.
        """
        buggy_qc = circuit.copy()
        # Remove the 'measure_all' instructions to edit the gates, 
        # then we will re-add them after the mutation.
        buggy_qc.remove_final_measurements()

        if bug_type == "swap":
            # BUG: Replace a random gate with a 'Z' gate (Phase flip)
            idx = random.randint(0, len(buggy_qc.data) - 1)
            print(f"[!] Bug Injected: Gate at index {idx} swapped for a Z-gate.")
            buggy_qc.data[idx] = buggy_qc.data[idx]._replace(operation=buggy_qc.data[idx].operation.to_mutable())
            # For simplicity in this demo, we just apply a Z to the first qubit of that instruction
            buggy_qc.z(0) 

        elif bug_type == "over_rotation":
            # BUG: Add a small unintended rotation (Calibration error)
            q = random.randint(0, self.num_qubits - 1)
            print(f"[!] Bug Injected: Unintended RZ rotation on Qubit {q}.")
            buggy_qc.rz(np.pi / 8, q)

        buggy_qc.measure_all()
        return buggy_qc

    def run_simulation(self, qc):
        """Runs the circuit and returns the counts."""
        compiled_circuit = transpile(qc, self.simulator)
        job = self.simulator.run(compiled_circuit, shots=1024)
        return job.result().get_counts()

# --- Main Execution ---
if __name__ == "__main__":
    lab = QuantumCircuitLab(num_qubits=3)

    # 1. Create the Golden Circuit
    print("Generating clean circuit...")
    golden_qc = lab.generate_random_circuit(depth=4)

    # 2. Create the Buggy Circuit
    print("Injecting bugs...")
    buggy_qc = lab.inject_bug(golden_qc, bug_type="over_rotation")

    # 3. Compare Results
    print("\nRunning simulations...")
    golden_results = lab.run_simulation(golden_qc)
    buggy_results = lab.run_simulation(buggy_qc)

    print("\n--- RESULTS COMPARISON ---")
    print(f"{'State':<10} | {'Golden':<10} | {'Buggy':<10}")
    print("-" * 35)
    
    # Get all unique states found in both results
    all_states = set(golden_results.keys()).union(set(buggy_results.keys()))
    for state in sorted(all_states):
        g_count = golden_results.get(state, 0)
        b_count = buggy_results.get(state, 0)
        print(f"{state:<10} | {g_count:<10} | {b_count:<10}")

    print("\nNote: Differences in counts indicate the impact of the injected bug.")