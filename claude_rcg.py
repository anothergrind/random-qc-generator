import random
from typing import List, Tuple, Dict
import json

class QuantumCircuit:
    """Represents a quantum circuit with gates and qubits."""
    
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.gates = []
        
    def add_gate(self, gate_type: str, qubits: List[int], params: Dict = None):
        """Add a gate to the circuit."""
        self.gates.append({
            'type': gate_type,
            'qubits': qubits,
            'params': params or {}
        })
    
    def __str__(self):
        result = f"Quantum Circuit ({self.num_qubits} qubits)\n"
        result += "=" * 50 + "\n"
        for i, gate in enumerate(self.gates):
            qubits_str = ", ".join(f"q{q}" for q in gate['qubits'])
            params_str = ""
            if gate['params']:
                params_str = f" {gate['params']}"
            result += f"{i+1}. {gate['type']}({qubits_str}){params_str}\n"
        return result
    
    def to_qasm(self) -> str:
        """Export circuit to OpenQASM format."""
        qasm = f"OPENQASM 2.0;\ninclude \"qelib1.inc\";\n"
        qasm += f"qreg q[{self.num_qubits}];\n"
        qasm += f"creg c[{self.num_qubits}];\n\n"
        
        for gate in self.gates:
            gate_type = gate['type'].lower()
            qubits = gate['qubits']
            
            if gate_type in ['h', 'x', 'y', 'z', 's', 't']:
                qasm += f"{gate_type} q[{qubits[0]}];\n"
            elif gate_type == 'cx' or gate_type == 'cnot':
                qasm += f"cx q[{qubits[0]}],q[{qubits[1]}];\n"
            elif gate_type == 'cz':
                qasm += f"cz q[{qubits[0]}],q[{qubits[1]}];\n"
            elif gate_type == 'rx':
                angle = gate['params'].get('theta', 0)
                qasm += f"rx({angle}) q[{qubits[0]}];\n"
            elif gate_type == 'ry':
                angle = gate['params'].get('theta', 0)
                qasm += f"ry({angle}) q[{qubits[0]}];\n"
            elif gate_type == 'rz':
                angle = gate['params'].get('theta', 0)
                qasm += f"rz({angle}) q[{qubits[0]}];\n"
        
        return qasm

class QuantumCircuitGenerator:
    """Generates random quantum circuits."""
    
    SINGLE_QUBIT_GATES = ['H', 'X', 'Y', 'Z', 'S', 'T', 'RX', 'RY', 'RZ']
    TWO_QUBIT_GATES = ['CNOT', 'CZ']
    
    @staticmethod
    def generate(num_qubits: int, num_gates: int, 
                 use_parametric: bool = True) -> QuantumCircuit:
        """
        Generate a random quantum circuit.
        
        Args:
            num_qubits: Number of qubits in the circuit
            num_gates: Number of gates to add
            use_parametric: Whether to use parametric gates (RX, RY, RZ)
        """
        circuit = QuantumCircuit(num_qubits)
        
        available_gates = QuantumCircuitGenerator.SINGLE_QUBIT_GATES.copy()
        if num_qubits > 1:
            available_gates.extend(QuantumCircuitGenerator.TWO_QUBIT_GATES)
        
        if not use_parametric:
            available_gates = [g for g in available_gates 
                             if g not in ['RX', 'RY', 'RZ']]
        
        for _ in range(num_gates):
            gate_type = random.choice(available_gates)
            
            if gate_type in QuantumCircuitGenerator.SINGLE_QUBIT_GATES:
                qubit = random.randint(0, num_qubits - 1)
                params = {}
                
                if gate_type in ['RX', 'RY', 'RZ']:
                    params['theta'] = random.uniform(0, 2 * 3.14159)
                
                circuit.add_gate(gate_type, [qubit], params)
            
            elif gate_type in QuantumCircuitGenerator.TWO_QUBIT_GATES:
                control = random.randint(0, num_qubits - 1)
                target = random.randint(0, num_qubits - 1)
                while target == control:
                    target = random.randint(0, num_qubits - 1)
                circuit.add_gate(gate_type, [control, target])
        
        return circuit

class BugInjector:
    """Injects various types of bugs into quantum circuits."""
    
    @staticmethod
    def inject_invalid_qubit(circuit: QuantumCircuit) -> Tuple[QuantumCircuit, str]:
        """Add a gate that references a non-existent qubit."""
        if not circuit.gates:
            return circuit, "No gates to modify"
        
        gate_idx = random.randint(0, len(circuit.gates) - 1)
        gate = circuit.gates[gate_idx]
        
        # Change one qubit to an invalid index
        invalid_qubit = circuit.num_qubits + random.randint(0, 5)
        gate['qubits'][0] = invalid_qubit
        
        return circuit, f"Bug: Gate {gate_idx+1} references invalid qubit {invalid_qubit}"
    
    @staticmethod
    def inject_duplicate_control_target(circuit: QuantumCircuit) -> Tuple[QuantumCircuit, str]:
        """Make a two-qubit gate's control and target the same."""
        two_qubit_gates = [i for i, g in enumerate(circuit.gates) 
                          if len(g['qubits']) == 2]
        
        if not two_qubit_gates:
            return circuit, "No two-qubit gates to modify"
        
        gate_idx = random.choice(two_qubit_gates)
        gate = circuit.gates[gate_idx]
        gate['qubits'][1] = gate['qubits'][0]
        
        return circuit, f"Bug: Gate {gate_idx+1} has same control and target qubit"
    
    @staticmethod
    def inject_missing_parameter(circuit: QuantumCircuit) -> Tuple[QuantumCircuit, str]:
        """Remove required parameter from a parametric gate."""
        parametric_gates = [i for i, g in enumerate(circuit.gates) 
                          if g['type'] in ['RX', 'RY', 'RZ']]
        
        if not parametric_gates:
            return circuit, "No parametric gates to modify"
        
        gate_idx = random.choice(parametric_gates)
        gate = circuit.gates[gate_idx]
        gate['params'] = {}
        
        return circuit, f"Bug: Gate {gate_idx+1} missing required 'theta' parameter"
    
    @staticmethod
    def inject_wrong_gate_arity(circuit: QuantumCircuit) -> Tuple[QuantumCircuit, str]:
        """Give a gate the wrong number of qubits."""
        if not circuit.gates:
            return circuit, "No gates to modify"
        
        gate_idx = random.randint(0, len(circuit.gates) - 1)
        gate = circuit.gates[gate_idx]
        
        if len(gate['qubits']) == 1:
            # Add an extra qubit to single-qubit gate
            gate['qubits'].append(random.randint(0, circuit.num_qubits - 1))
            return circuit, f"Bug: Single-qubit gate {gate_idx+1} given 2 qubits"
        else:
            # Remove a qubit from two-qubit gate
            gate['qubits'] = [gate['qubits'][0]]
            return circuit, f"Bug: Two-qubit gate {gate_idx+1} given only 1 qubit"
    
    @staticmethod
    def inject_invalid_gate_name(circuit: QuantumCircuit) -> Tuple[QuantumCircuit, str]:
        """Change a gate name to something invalid."""
        if not circuit.gates:
            return circuit, "No gates to modify"
        
        gate_idx = random.randint(0, len(circuit.gates) - 1)
        gate = circuit.gates[gate_idx]
        old_name = gate['type']
        gate['type'] = 'INVALID_GATE_' + str(random.randint(1, 100))
        
        return circuit, f"Bug: Gate {gate_idx+1} changed from {old_name} to {gate['type']}"
    
    @staticmethod
    def inject_random_bug(circuit: QuantumCircuit) -> Tuple[QuantumCircuit, str]:
        """Inject a random bug type."""
        bug_types = [
            BugInjector.inject_invalid_qubit,
            BugInjector.inject_duplicate_control_target,
            BugInjector.inject_missing_parameter,
            BugInjector.inject_wrong_gate_arity,
            BugInjector.inject_invalid_gate_name
        ]
        
        bug_func = random.choice(bug_types)
        return bug_func(circuit)

# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("QUANTUM CIRCUIT GENERATOR WITH BUG INJECTION")
    print("=" * 60)
    
    # Generate a clean circuit
    print("\n1. CLEAN CIRCUIT")
    print("-" * 60)
    clean_circuit = QuantumCircuitGenerator.generate(
        num_qubits=4, 
        num_gates=8, 
        use_parametric=True
    )
    print(clean_circuit)
    
    # Generate a buggy circuit
    print("\n2. BUGGY CIRCUIT")
    print("-" * 60)
    buggy_circuit = QuantumCircuitGenerator.generate(
        num_qubits=4, 
        num_gates=8, 
        use_parametric=True
    )
    buggy_circuit, bug_description = BugInjector.inject_random_bug(buggy_circuit)
    print(f"Injected: {bug_description}\n")
    print(buggy_circuit)
    
    # Export to QASM
    print("\n3. QASM EXPORT (Clean Circuit)")
    print("-" * 60)
    print(clean_circuit.to_qasm())
    
    print("\n4. MULTIPLE BUG INJECTION")
    print("-" * 60)
    multi_bug_circuit = QuantumCircuitGenerator.generate(
        num_qubits=3, 
        num_gates=6, 
        use_parametric=True
    )
    bugs = []
    for i in range(3):
        multi_bug_circuit, bug_desc = BugInjector.inject_random_bug(multi_bug_circuit)
        bugs.append(bug_desc)
    
    print("Injected bugs:")
    for bug in bugs:
        print(f"  - {bug}")
    print("\n" + str(multi_bug_circuit))