"""
chatgpt_rcg.py

Generate random quantum circuits and optionally inject bugs.
"""

import argparse
import random

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit import transpile

SINGLE_QUBIT_GATES = ("h", "x", "y", "z")
TWO_QUBIT_GATES = ("cx", "cz")
THREE_QUBIT_GATES = ("ccx",)
VALID_GATES = set(SINGLE_QUBIT_GATES + TWO_QUBIT_GATES + THREE_QUBIT_GATES)

BUG_TYPES = (
    "flip_to_x",
    "wrong_target",
    "swap_controls",
    "drop_gate",
    "insert_random_gate",
)


def parse_gate_list(gates_str):
    if not gates_str:
        return ["h", "x", "y", "z", "cx", "ccx"]
    gates = [g.strip().lower() for g in gates_str.split(",") if g.strip()]
    unknown = [g for g in gates if g not in VALID_GATES]
    if unknown:
        raise ValueError(f"Unsupported gates: {', '.join(unknown)}")
    return gates


def parse_bug_types(bug_types_str):
    if not bug_types_str:
        return list(BUG_TYPES)
    bug_types = [b.strip().lower() for b in bug_types_str.split(",") if b.strip()]
    unknown = [b for b in bug_types if b not in BUG_TYPES]
    if unknown:
        raise ValueError(f"Unsupported bug types: {', '.join(unknown)}")
    return bug_types


def pick_gate(selected_gates, strategy, layer_idx, rng):
    if strategy == "sequential":
        return selected_gates[layer_idx % len(selected_gates)]
    return rng.choice(selected_gates)


def apply_gate(qc, gate, qubit, num_qubits, bug_action, rng):
    applied_bug = None

    if gate in SINGLE_QUBIT_GATES:
        if bug_action == "drop_gate":
            return "drop_gate"
        if bug_action == "flip_to_x":
            gate = "x"
            applied_bug = "flip_to_x"
        getattr(qc, gate)(qubit)
        if bug_action == "insert_random_gate":
            extra = rng.choice(SINGLE_QUBIT_GATES)
            getattr(qc, extra)(qubit)
            applied_bug = "insert_random_gate"
        return applied_bug

    if gate in TWO_QUBIT_GATES:
        if num_qubits < 2:
            return None
        if bug_action == "drop_gate":
            return "drop_gate"
        control = qubit
        target = (qubit + 1) % num_qubits
        if bug_action == "wrong_target":
            target = (qubit + 2) % num_qubits
            applied_bug = "wrong_target"
        if bug_action == "swap_controls":
            control, target = target, control
            applied_bug = "swap_controls"
        getattr(qc, gate)(control, target)
        if bug_action == "insert_random_gate":
            extra = rng.choice(SINGLE_QUBIT_GATES)
            getattr(qc, extra)(target)
            applied_bug = "insert_random_gate"
        return applied_bug

    if gate in THREE_QUBIT_GATES:
        if num_qubits < 3:
            return None
        if bug_action == "drop_gate":
            return "drop_gate"
        control1 = qubit
        control2 = (qubit + 1) % num_qubits
        target = (qubit + 2) % num_qubits
        if bug_action == "wrong_target":
            target = (qubit + 3) % num_qubits
            applied_bug = "wrong_target"
        if bug_action == "swap_controls":
            control1, target = target, control1
            applied_bug = "swap_controls"
        qc.ccx(control1, control2, target)
        if bug_action == "insert_random_gate":
            extra = rng.choice(SINGLE_QUBIT_GATES)
            getattr(qc, extra)(target)
            applied_bug = "insert_random_gate"
        return applied_bug

    raise ValueError(f"Unsupported gate: {gate}")


def build_quantum_circuit(
    num_qubits,
    selected_gates,
    circuit_depth,
    gate_application,
    bug_rate,
    bug_types,
    seed,
    measure,
):
    rng = random.Random(seed)
    qc = QuantumCircuit(num_qubits, num_qubits if measure else 0)
    bug_counts = {b: 0 for b in BUG_TYPES}
    total_gates = 0

    for layer in range(circuit_depth):
        for qubit in range(num_qubits):
            gate = pick_gate(selected_gates, gate_application, layer, rng)
            total_gates += 1
            bug_action = None
            if bug_rate > 0 and rng.random() < bug_rate:
                bug_action = rng.choice(bug_types)
            applied_bug = apply_gate(qc, gate, qubit, num_qubits, bug_action, rng)
            if applied_bug:
                bug_counts[applied_bug] += 1

    if measure:
        qc.measure(range(num_qubits), range(num_qubits))

    return qc, total_gates, bug_counts


def simulate_circuit(qc, shots):
    backend = AerSimulator()
    qc_transpiled = transpile(qc, backend)
    job = backend.run(qc_transpiled, shots=shots)
    result = job.result()
    return result.get_counts()


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Generate random quantum circuits with optional bug injection."
    )
    parser.add_argument("--num-qubits", type=int, required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--gates", type=str, default="")
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["random", "sequential"],
        default="random",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--bug-rate", type=float, default=0.0)
    parser.add_argument("--bug-types", type=str, default="")
    parser.add_argument("--no-measure", action="store_true")
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--shots", type=int, default=1024)
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.num_qubits <= 0:
        raise ValueError("--num-qubits must be positive")
    if args.depth <= 0:
        raise ValueError("--depth must be positive")
    if args.bug_rate < 0:
        raise ValueError("--bug-rate cannot be negative")

    selected_gates = parse_gate_list(args.gates)
    bug_types = parse_bug_types(args.bug_types)
    measure = not args.no_measure

    qc, total_gates, bug_counts = build_quantum_circuit(
        num_qubits=args.num_qubits,
        selected_gates=selected_gates,
        circuit_depth=args.depth,
        gate_application=args.strategy,
        bug_rate=args.bug_rate,
        bug_types=bug_types,
        seed=args.seed,
        measure=measure,
    )

    print("\nGenerated circuit:")
    print(qc.draw(output="text"))

    if args.bug_rate > 0:
        print("\nBug summary:")
        print(f"Total gates attempted: {total_gates}")
        for bug, count in bug_counts.items():
            print(f"  {bug}: {count}")

    if args.simulate:
        if not measure:
            raise ValueError("Simulation requires measurements. Remove --no-measure.")
        counts = simulate_circuit(qc, shots=args.shots)
        print("\nSimulation counts:")
        print(counts)


if __name__ == "__main__":
    main()
