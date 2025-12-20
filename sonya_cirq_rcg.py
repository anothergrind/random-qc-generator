"""
Random circuit generators (Cirq)
There are simple random circuit generators that build circuits by sampling gates and qubits at random (with some bias toward 1-qubit vs 2-qubit gates). 
They are basic, task-agnostic generators and sit at the very bottom of the ecosystem: they do not use any specification (truth table, unitary, task objective), 
only random choices. They are useful for benchmarks, noise studies, and ML datasets, but they do not leverage any of the structured methods discussed in the 
automated synthesis literature.
"""

import cirq
import random
def random_cirq_circuit(n_qubits, depth):
    qubits = cirq.LineQubit.range(n_qubits)
    circuit = cirq.Circuit()
    one_qubit_gates = [cirq.X, cirq.Y, cirq.Z, cirq.H]
    two_qubit_gates = [cirq.CNOT]
    for _ in range(depth):
        if random.random() < 0.7:
            gate = random.choice(one_qubit_gates)
            q = random.choice(qubits)
            circuit.append(gate(q))
        else:
            gate = random.choice(two_qubit_gates)
            q1, q2 = random.sample(qubits, 2)
            circuit.append(gate(q1, q2))
    return circuit
c = random_cirq_circuit(n_qubits=5, depth=20)
print(c)