"""
Random circuit generators (Qiskit)
There are simple random circuit generators that build circuits by sampling gates and qubits at random (with some bias toward 1-qubit vs 2-qubit gates). 
They are basic, task-agnostic generators and sit at the very bottom of the ecosystem: they do not use any specification (truth table, unitary, task objective), 
only random choices. They are useful for benchmarks, noise studies, and ML datasets, but they do not leverage any of the structured methods discussed in the 
automated synthesis literature.
"""

from qiskit import QuantumCircuit
import random
def random_circuit(n_qubits, depth, gate_set=("h", "x", "y", "z", "cx")):
    qc = QuantumCircuit(n_qubits)
    for _ in range(depth):
        gate = random.choice(gate_set)
        if gate in ("h", "x", "y", "z"):
            q = random.randrange(n_qubits)
            getattr(qc, gate)(q)
        elif gate == "cx":
            q1, q2 = random.sample(range(n_qubits), 2)
            qc.cx(q1, q2)
    return qc
def generate_dataset(num_circuits, n_qubits, depth):
    return [random_circuit(n_qubits, depth) for _ in range(num_circuits)]
dataset = generate_dataset(1000, 5, 20)