"""
perplexity_rcg.py

Generate random quantum circuits and inject controllable bugs using Qiskit.

Requirements:
    pip install qiskit
"""

import math
import random
from typing import List, Optional, Dict, Any, Tuple

from qiskit import QuantumCircuit  # type: ignore


# -----------------------------
# Random circuit configuration
# -----------------------------


DEFAULT_SINGLE_QUBIT_GATES = ["h", "x", "y", "z", "s", "t", "rx", "ry", "rz"]
DEFAULT_TWO_QUBIT_GATES = ["cx", "cz"]


class RandomCircuitGenerator:
    """
    Simple random quantum circuit generator.

    Generates circuits by stacking 'depth' layers of random 1- or 2-qubit gates.
    """

    def __init__(
        self,
        num_qubits: int,
        depth: int,
        single_qubit_gates: Optional[List[str]] = None,
        two_qubit_gates: Optional[List[str]] = None,
        seed: Optional[int] = None,
    ):
        if num_qubits < 1:
            raise ValueError("num_qubits must be >= 1")
        if depth < 1:
            raise ValueError("depth must be >= 1")

        self.num_qubits = num_qubits
        self.depth = depth
        self.single_qubit_gates = single_qubit_gates or DEFAULT_SINGLE_QUBIT_GATES
        self.two_qubit_gates = two_qubit_gates or DEFAULT_TWO_QUBIT_GATES
        self.rng = random.Random(seed)

    def _random_angle(self) -> float:
        # Uniform angle in [0, 2π)
        return self.rng.random() * 2.0 * math.pi

    def _apply_single_qubit_gate(self, qc: QuantumCircuit, gate: str, qubit: int):
        if gate == "h":
            qc.h(qubit)
        elif gate == "x":
            qc.x(qubit)
        elif gate == "y":
            qc.y(qubit)
        elif gate == "z":
            qc.z(qubit)
        elif gate == "s":
            qc.s(qubit)
        elif gate == "t":
            qc.t(qubit)
        elif gate == "rx":
            qc.rx(self._random_angle(), qubit)
        elif gate == "ry":
            qc.ry(self._random_angle(), qubit)
        elif gate == "rz":
            qc.rz(self._random_angle(), qubit)
        else:
            raise ValueError(f"Unknown single-qubit gate: {gate}")

    def _apply_two_qubit_gate(self, qc: QuantumCircuit, gate: str, q0: int, q1: int):
        if gate == "cx":
            qc.cx(q0, q1)
        elif gate == "cz":
            qc.cz(q0, q1)
        else:
            raise ValueError(f"Unknown two-qubit gate: {gate}")

    def generate(self) -> QuantumCircuit:
        """
        Generate a random circuit.

        Strategy:
        - For each depth layer, choose a random mix of 1- and 2-qubit gates.
        - Do not allow overlapping multi-qubit gates in a single layer.
        """
        qc = QuantumCircuit(self.num_qubits)

        for _ in range(self.depth):
            free_qubits = list(range(self.num_qubits))
            self.rng.shuffle(free_qubits)

            i = 0
            while i < len(free_qubits):
                # Decide randomly: 2-qubit gate (if possible) or 1-qubit gate.
                use_two_qubit = (
                    len(free_qubits) - i >= 2 and self.rng.random() < 0.5
                )

                if use_two_qubit and self.two_qubit_gates:
                    gate = self.rng.choice(self.two_qubit_gates)
                    q0 = free_qubits[i]
                    q1 = free_qubits[i + 1]
                    self._apply_two_qubit_gate(qc, gate, q0, q1)
                    i += 2
                else:
                    gate = self.rng.choice(self.single_qubit_gates)
                    q = free_qubits[i]
                    self._apply_single_qubit_gate(qc, gate, q)
                    i += 1

        return qc


# -----------------------------
# Bug injection
# -----------------------------


class BugInjector:
    """
    Injects different types of bugs into a QuantumCircuit.

    Supported bug types:
        - 'gate_replacement'
        - 'angle_perturbation'
        - 'gate_deletion'
        - 'gate_insertion'
        - 'swap_control_target'
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    # ---- Public API ----

    def inject_bugs(
        self,
        circuit: QuantumCircuit,
        bug_types: Optional[List[str]] = None,
        num_bugs: int = 1,
    ) -> Tuple[QuantumCircuit, List[Dict[str, Any]]]:
        """
        Return a new circuit with `num_bugs` randomly injected bugs.

        Parameters:
            circuit: original circuit
            bug_types: subset of supported bug strings; if None, use all
            num_bugs: how many bug operations to attempt

        Returns:
            (buggy_circuit, bug_log)
        """
        supported = [
            "gate_replacement",
            "angle_perturbation",
            "gate_deletion",
            "gate_insertion",
            "swap_control_target",
        ]
        if bug_types is None:
            bug_types = supported
        for bt in bug_types:
            if bt not in supported:
                raise ValueError(f"Unsupported bug type: {bt}")

        # Work on a shallow copy of circuit.data (list of instructions).
        new_circ = circuit.copy()
        bug_log: List[Dict[str, Any]] = []

        for _ in range(num_bugs):
            if not new_circ.data and "gate_insertion" not in bug_types:
                break  # nothing to mutate

            bug_choice = self.rng.choice(bug_types)
            if bug_choice == "gate_replacement":
                log_entry = self._bug_gate_replacement(new_circ)
            elif bug_choice == "angle_perturbation":
                log_entry = self._bug_angle_perturbation(new_circ)
            elif bug_choice == "gate_deletion":
                log_entry = self._bug_gate_deletion(new_circ)
            elif bug_choice == "gate_insertion":
                log_entry = self._bug_gate_insertion(new_circ)
            elif bug_choice == "swap_control_target":
                log_entry = self._bug_swap_control_target(new_circ)
            else:
                log_entry = None

            if log_entry is not None:
                bug_log.append(log_entry)

        return new_circ, bug_log

    # ---- Individual bug implementations ----

    def _choose_instruction_index(self, circuit: QuantumCircuit) -> Optional[int]:
        if not circuit.data:
            return None
        return self.rng.randrange(len(circuit.data))

    def _bug_gate_replacement(self, circuit: QuantumCircuit) -> Optional[Dict[str, Any]]:
        idx = self._choose_instruction_index(circuit)
        if idx is None:
            return None

        instr, qargs, cargs = circuit.data[idx]
        old_name = instr.name

        # Simple replacement: flip between 'h' and 'x', or between 'cx' and 'cz'.
        if old_name == "h":
            new_name = "x"
            circuit.h(qargs[0])  # placeholder to get an Instruction object
            new_instr = circuit.data[-1][0]
            circuit.data.pop()  # remove placeholder
        elif old_name == "x":
            new_name = "h"
            circuit.h(qargs[0])
            new_instr = circuit.data[-1][0]
            circuit.data.pop()
        elif old_name == "cx":
            new_name = "cz"
            circuit.cz(qargs[0], qargs[1])
            new_instr = circuit.data[-1][0]
            circuit.data.pop()
        elif old_name == "cz":
            new_name = "cx"
            circuit.cx(qargs[0], qargs[1])
            new_instr = circuit.data[-1][0]
            circuit.data.pop()
        else:
            # If not a recognized gate, do nothing.
            return None

        circuit.data[idx] = (new_instr, qargs, cargs)

        return {
            "type": "gate_replacement",
            "index": idx,
            "old_name": old_name,
            "new_name": new_name,
        }

    def _bug_angle_perturbation(
        self, circuit: QuantumCircuit
    ) -> Optional[Dict[str, Any]]:
        # Find a parameterized rotation gate, if any.
        rot_indices = [
            i
            for i, (instr, _, _) in enumerate(circuit.data)
            if instr.name in {"rx", "ry", "rz"}
        ]
        if not rot_indices:
            return None

        idx = self.rng.choice(rot_indices)
        instr, qargs, cargs = circuit.data[idx]

        # Assume the first parameter is the rotation angle.
        old_params = list(instr.params)
        if not old_params:
            return None

        old_angle = float(old_params[0])
        delta = self.rng.uniform(-0.5, 0.5)  # perturb up to ±0.5 radians
        new_angle = old_angle + delta

        new_params = [new_angle] + old_params[1:]
        new_instr = instr.copy()
        new_instr.params = new_params
        circuit.data[idx] = (new_instr, qargs, cargs)

        return {
            "type": "angle_perturbation",
            "index": idx,
            "old_angle": old_angle,
            "new_angle": new_angle,
            "delta": delta,
        }

    def _bug_gate_deletion(
        self, circuit: QuantumCircuit
    ) -> Optional[Dict[str, Any]]:
        idx = self._choose_instruction_index(circuit)
        if idx is None:
            return None

        instr, qargs, cargs = circuit.data[idx]
        circuit.data.pop(idx)

        return {
            "type": "gate_deletion",
            "index": idx,
            "deleted_name": instr.name,
            "deleted_qubits": [q.index for q in qargs],
        }

    def _bug_gate_insertion(
        self, circuit: QuantumCircuit
    ) -> Optional[Dict[str, Any]]:
        num_qubits = circuit.num_qubits
        if num_qubits == 0:
            return None

        # Choose random position to insert.
        idx = self.rng.randrange(len(circuit.data) + 1)

        # Randomly decide single or two qubit insert.
        use_two_qubit = num_qubits >= 2 and self.rng.random() < 0.5
        if use_two_qubit:
            q0, q1 = self.rng.sample(range(num_qubits), 2)
            # Insert a CX as the buggy gate.
            circuit.cx(q0, q1)
            new_instr, qargs, cargs = circuit.data[-1]
            circuit.data.pop()  # remove from end

            circuit.data.insert(idx, (new_instr, qargs, cargs))
            return {
                "type": "gate_insertion",
                "index": idx,
                "name": "cx",
                "qubits": [q0, q1],
            }
        else:
            q = self.rng.randrange(num_qubits)
            circuit.h(q)
            new_instr, qargs, cargs = circuit.data[-1]
            circuit.data.pop()

            circuit.data.insert(idx, (new_instr, qargs, cargs))
            return {
                "type": "gate_insertion",
                "index": idx,
                "name": "h",
                "qubits": [q],
            }

    def _bug_swap_control_target(
        self, circuit: QuantumCircuit
    ) -> Optional[Dict[str, Any]]:
        # Find controlled gates that have exactly two qubits (e.g. cx, cz).
        ctrl_indices = [
            i
            for i, (instr, qargs, _cargs) in enumerate(circuit.data)
            if instr.name in {"cx", "cz"} and len(qargs) == 2
        ]
        if not ctrl_indices:
            return None

        idx = self.rng.choice(ctrl_indices)
        instr, qargs, cargs = circuit.data[idx]
        old_qubits = [q.index for q in qargs]

        # Swap the order of the qubits in the qargs tuple.
        new_qargs = (qargs[1], qargs[0])
        circuit.data[idx] = (instr, new_qargs, cargs)

        return {
            "type": "swap_control_target",
            "index": idx,
            "name": instr.name,
            "old_qubits": old_qubits,
            "new_qubits": [q.index for q in new_qargs],
        }


# -----------------------------
# Example usage
# -----------------------------


def demo():
    print("=== Random circuit generator + bug injector demo ===")
    gen = RandomCircuitGenerator(num_qubits=4, depth=5, seed=42)
    qc = gen.generate()

    print("\nOriginal circuit:")
    print(qc.draw())

    injector = BugInjector(seed=1234)
    buggy_qc, bug_log = injector.inject_bugs(
        qc,
        bug_types=[
            "gate_replacement",
            "angle_perturbation",
            "gate_deletion",
            "gate_insertion",
            "swap_control_target",
        ],
        num_bugs=3,
    )

    print("\nBuggy circuit:")
    print(buggy_qc.draw())

    print("\nBug log:")
    for i, entry in enumerate(bug_log):
        print(f"Bug #{i+1}: {entry}")


if __name__ == "__main__":
    demo()