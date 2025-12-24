import numpy as np
import random
from typing import List, Dict, Tuple, Optional, Union
import itertools

class QuantumBugInjector:
    """Class to inject various types of bugs into quantum circuits"""
    
    BUG_TYPES = [
        'gate_error',           # Wrong gate applied
        'parameter_error',      # Wrong rotation parameter
        'qubit_error',          # Wrong target qubit
        'control_error',        # Wrong control qubit
        'missing_gate',         # Gate omitted
        'extra_gate',          # Extra gate added
        'measurement_error',    # Wrong measurement basis
        'timing_error',         # Wrong gate timing/ordering
        'decoherence_error',    # Simulated decoherence
        'crosstalk_error'       # Unintended qubit interaction
    ]
    
    def __init__(self, bug_probability: float = 0.1):
        self.bug_probability = bug_probability
        self.injected_bugs = []
    
    def inject_bug(self, circuit: Dict, bug_type: str = None) -> Dict:
        """Inject a specific type of bug into the circuit"""
        if bug_type is None:
            bug_type = random.choice(self.BUG_TYPES)
        
        circuit_copy = circuit.copy()
        circuit_copy['gates'] = circuit['gates'].copy()
        
        if not circuit_copy['gates']:
            return circuit_copy
        
        bug_info = {
            'type': bug_type,
            'location': None,
            'description': ''
        }
        
        if bug_type == 'gate_error':
            circuit_copy, bug_info = self._inject_gate_error(circuit_copy)
        elif bug_type == 'parameter_error':
            circuit_copy, bug_info = self._inject_parameter_error(circuit_copy)
        elif bug_type == 'qubit_error':
            circuit_copy, bug_info = self._inject_qubit_error(circuit_copy)
        elif bug_type == 'control_error':
            circuit_copy, bug_info = self._inject_control_error(circuit_copy)
        elif bug_type == 'missing_gate':
            circuit_copy, bug_info = self._inject_missing_gate(circuit_copy)
        elif bug_type == 'extra_gate':
            circuit_copy, bug_info = self._inject_extra_gate(circuit_copy)
        elif bug_type == 'measurement_error':
            circuit_copy, bug_info = self._inject_measurement_error(circuit_copy)
        elif bug_type == 'timing_error':
            circuit_copy, bug_info = self._inject_timing_error(circuit_copy)
        elif bug_type == 'decoherence_error':
            circuit_copy, bug_info = self._inject_decoherence_error(circuit_copy)
        elif bug_type == 'crosstalk_error':
            circuit_copy, bug_info = self._inject_crosstalk_error(circuit_copy)
        
        self.injected_bugs.append(bug_info)
        return circuit_copy
    
    def _inject_gate_error(self, circuit: Dict) -> Tuple[Dict, Dict]:
        """Replace a correct gate with a wrong one"""
        if not circuit['gates']:
            return circuit, {'type': 'gate_error', 'description': 'No gates to modify'}
        
        gate_idx = random.randrange(len(circuit['gates']))
        original_gate = circuit['gates'][gate_idx]
        
        # Available single-qubit gates
        single_qubit_gates = ['X', 'Y', 'Z', 'H', 'S', 'T', 'RX', 'RY', 'RZ']
        # Available two-qubit gates
        two_qubit_gates = ['CNOT', 'CZ', 'SWAP', 'CPHASE']
        
        # Choose wrong gate based on original gate type
        if len(original_gate['qubits']) == 1:
            wrong_gate = random.choice([g for g in single_qubit_gates if g != original_gate['type']])
        else:
            wrong_gate = random.choice([g for g in two_qubit_gates if g != original_gate['type']])
        
        circuit['gates'][gate_idx]['type'] = wrong_gate
        
        bug_info = {
            'type': 'gate_error',
            'location': gate_idx,
            'description': f"Gate {original_gate['type']} replaced with {wrong_gate}",
            'original_gate': original_gate['type'],
            'wrong_gate': wrong_gate
        }
        
        return circuit, bug_info
    
    def _inject_parameter_error(self, circuit: Dict) -> Tuple[Dict, Dict]:
        """Change rotation parameter of a gate"""
        rotation_gates = [i for i, g in enumerate(circuit['gates']) 
                         if g['type'] in ['RX', 'RY', 'RZ', 'CPHASE']]
        
        if not rotation_gates:
            return circuit, {'type': 'parameter_error', 'description': 'No rotation gates found'}
        
        gate_idx = random.choice(rotation_gates)
        original_gate = circuit['gates'][gate_idx]
        
        # Add error to parameter
        error = random.uniform(-np.pi/2, np.pi/2)
        original_param = original_gate.get('parameter', 0)
        wrong_param = original_param + error
        
        circuit['gates'][gate_idx]['parameter'] = wrong_param
        circuit['gates'][gate_idx]['parameter_error'] = error
        
        bug_info = {
            'type': 'parameter_error',
            'location': gate_idx,
            'description': f"Parameter error of {error:.3f} added to {original_gate['type']} gate",
            'original_parameter': original_param,
            'wrong_parameter': wrong_param,
            'error_magnitude': error
        }
        
        return circuit, bug_info
    
    def _inject_qubit_error(self, circuit: Dict) -> Tuple[Dict, Dict]:
        """Apply gate to wrong qubit"""
        if not circuit['gates']:
            return circuit, {'type': 'qubit_error', 'description': 'No gates to modify'}
        
        gate_idx = random.randrange(len(circuit['gates']))
        original_gate = circuit['gates'][gate_idx]
        
        # Choose a wrong qubit that exists in the circuit but different from original
        available_qubits = list(range(circuit['n_qubits']))
        
        if len(original_gate['qubits']) == 1:
            wrong_qubit = random.choice([q for q in available_qubits 
                                        if q != original_gate['qubits'][0]])
            circuit['gates'][gate_idx]['qubits'] = [wrong_qubit]
        else:
            # For two-qubit gates, choose wrong target or control
            if random.choice([True, False]):
                # Wrong target
                wrong_target = random.choice([q for q in available_qubits 
                                            if q not in original_gate['qubits']])
                circuit['gates'][gate_idx]['qubits'] = [original_gate['qubits'][0], wrong_target]
            else:
                # Wrong control
                wrong_control = random.choice([q for q in available_qubits 
                                             if q not in original_gate['qubits']])
                circuit['gates'][gate_idx]['qubits'] = [wrong_control, original_gate['qubits'][1]]
        
        bug_info = {
            'type': 'qubit_error',
            'location': gate_idx,
            'description': f"Gate applied to wrong qubit(s)",
            'original_qubits': original_gate['qubits'].copy(),
            'wrong_qubits': circuit['gates'][gate_idx]['qubits'].copy()
        }
        
        return circuit, bug_info
    
    def _inject_missing_gate(self, circuit: Dict) -> Tuple[Dict, Dict]:
        """Remove a gate from the circuit"""
        if not circuit['gates']:
            return circuit, {'type': 'missing_gate', 'description': 'No gates to remove'}
        
        gate_idx = random.randrange(len(circuit['gates']))
        removed_gate = circuit['gates'].pop(gate_idx)
        
        bug_info = {
            'type': 'missing_gate',
            'location': gate_idx,
            'description': f"Gate {removed_gate['type']} on qubits {removed_gate['qubits']} removed",
            'removed_gate': removed_gate
        }
        
        return circuit, bug_info
    
    def _inject_extra_gate(self, circuit: Dict) -> Tuple[Dict, Dict]:
        """Add an extra unnecessary gate"""
        single_qubit_gates = ['X', 'Y', 'Z', 'H', 'S', 'T']
        two_qubit_gates = ['CNOT', 'CZ']
        
        # Randomly decide gate type
        if random.random() < 0.7 or circuit['n_qubits'] < 2:
            gate_type = random.choice(single_qubit_gates)
            qubits = [random.randrange(circuit['n_qubits'])]
        else:
            gate_type = random.choice(two_qubit_gates)
            qubits = random.sample(range(circuit['n_qubits']), 2)
        
        extra_gate = {
            'type': gate_type,
            'qubits': qubits,
            'is_bug': True,
            'bug_type': 'extra_gate'
        }
        
        # Add random rotation parameter if needed
        if gate_type in ['RX', 'RY', 'RZ']:
            extra_gate['parameter'] = random.uniform(0, 2*np.pi)
        
        # Insert at random position
        insert_idx = random.randrange(len(circuit['gates']) + 1)
        circuit['gates'].insert(insert_idx, extra_gate)
        
        bug_info = {
            'type': 'extra_gate',
            'location': insert_idx,
            'description': f"Extra {gate_type} gate added on qubits {qubits}",
            'extra_gate': extra_gate
        }
        
        return circuit, bug_info
    
    def _inject_measurement_error(self, circuit: Dict) -> Tuple[Dict, Dict]:
        """Add measurement error by changing measurement basis"""
        if 'measurements' not in circuit:
            circuit['measurements'] = [{'qubit': q, 'basis': 'Z'} for q in range(circuit['n_qubits'])]
        
        measurement_idx = random.randrange(len(circuit['measurements']))
        original_measurement = circuit['measurements'][measurement_idx]
        
        # Choose wrong measurement basis
        bases = ['X', 'Y', 'Z']
        wrong_basis = random.choice([b for b in bases if b != original_measurement.get('basis', 'Z')])
        
        circuit['measurements'][measurement_idx]['basis'] = wrong_basis
        circuit['measurements'][measurement_idx]['is_bug'] = True
        
        bug_info = {
            'type': 'measurement_error',
            'location': measurement_idx,
            'description': f"Measurement basis changed from {original_measurement.get('basis', 'Z')} to {wrong_basis}",
            'original_basis': original_measurement.get('basis', 'Z'),
            'wrong_basis': wrong_basis
        }
        
        return circuit, bug_info
    
    def _inject_timing_error(self, circuit: Dict) -> Tuple[Dict, Dict]:
        """Swap order of two consecutive gates"""
        if len(circuit['gates']) < 2:
            return circuit, {'type': 'timing_error', 'description': 'Not enough gates for timing error'}
        
        idx = random.randrange(len(circuit['gates']) - 1)
        
        # Swap gates
        circuit['gates'][idx], circuit['gates'][idx + 1] = \
            circuit['gates'][idx + 1], circuit['gates'][idx]
        
        # Mark them as having timing issues
        circuit['gates'][idx]['timing_bug'] = True
        circuit['gates'][idx + 1]['timing_bug'] = True
        
        bug_info = {
            'type': 'timing_error',
            'location': (idx, idx + 1),
            'description': f"Gates at positions {idx} and {idx+1} swapped",
            'gate1': circuit['gates'][idx]['type'],
            'gate2': circuit['gates'][idx + 1]['type']
        }
        
        return circuit, bug_info
    
    def _inject_decoherence_error(self, circuit: Dict) -> Tuple[Dict, Dict]:
        """Add simulated decoherence by inserting identity gates with noise parameter"""
        # Add decoherence parameter to circuit
        circuit['decoherence'] = circuit.get('decoherence', {})
        circuit['decoherence']['T1'] = random.uniform(10, 100)  # Random T1 time
        circuit['decoherence']['T2'] = random.uniform(5, 50)    # Random T2 time
        
        # Mark random gates as affected by decoherence
        n_affected = max(1, len(circuit['gates']) // 4)
        affected_indices = random.sample(range(len(circuit['gates'])), 
                                        min(n_affected, len(circuit['gates'])))
        
        for idx in affected_indices:
            circuit['gates'][idx]['decoherence_affected'] = True
        
        bug_info = {
            'type': 'decoherence_error',
            'description': f"Added decoherence with T1={circuit['decoherence']['T1']:.1f}, T2={circuit['decoherence']['T2']:.1f}",
            'affected_gates': affected_indices,
            'T1': circuit['decoherence']['T1'],
            'T2': circuit['decoherence']['T2']
        }
        
        return circuit, bug_info
    
    def _inject_crosstalk_error(self, circuit: Dict) -> Tuple[Dict, Dict]:
        """Add unintended qubit interactions"""
        if circuit['n_qubits'] < 2:
            return circuit, {'type': 'crosstalk_error', 'description': 'Need at least 2 qubits for crosstalk'}
        
        # Add crosstalk matrix to circuit
        n = circuit['n_qubits']
        crosstalk_matrix = np.random.rand(n, n) * 0.1  # Small crosstalk coefficients
        
        # Make symmetric and zero diagonal
        crosstalk_matrix = (crosstalk_matrix + crosstalk_matrix.T) / 2
        np.fill_diagonal(crosstalk_matrix, 0)
        
        circuit['crosstalk'] = crosstalk_matrix.tolist()
        
        # Mark some gates as particularly affected
        two_qubit_gates = [i for i, g in enumerate(circuit['gates']) 
                          if len(g['qubits']) == 2]
        
        if two_qubit_gates:
            affected_idx = random.choice(two_qubit_gates)
            circuit['gates'][affected_idx]['crosstalk_affected'] = True
        
        bug_info = {
            'type': 'crosstalk_error',
            'description': f"Added crosstalk between qubits",
            'crosstalk_matrix': circuit['crosstalk'],
            'max_crosstalk': np.max(crosstalk_matrix)
        }
        
        return circuit, bug_info


class RandomQuantumCircuitGenerator:
    """Generate random quantum circuits"""
    
    def __init__(self, n_qubits: int = 3, depth: int = 10):
        self.n_qubits = n_qubits
        self.depth = depth
        self.bug_injector = QuantumBugInjector()
        
        # Define available gates
        self.single_qubit_gates = ['X', 'Y', 'Z', 'H', 'S', 'T', 'RX', 'RY', 'RZ']
        self.two_qubit_gates = ['CNOT', 'CZ', 'SWAP', 'CPHASE']
    
    def generate_circuit(self, add_bugs: bool = False, bug_types: List[str] = None) -> Dict:
        """Generate a random quantum circuit"""
        circuit = {
            'n_qubits': self.n_qubits,
            'depth': self.depth,
            'gates': [],
            'measurements': []
        }
        
        # Generate random gates
        for _ in range(self.depth):
            # Randomly choose gate type
            if random.random() < 0.3 and self.n_qubits >= 2:
                # Two-qubit gate
                gate_type = random.choice(self.two_qubit_gates)
                qubits = random.sample(range(self.n_qubits), 2)
                
                gate = {
                    'type': gate_type,
                    'qubits': qubits,
                    'layer': _
                }
                
                # Add parameter for parameterized gates
                if gate_type == 'CPHASE':
                    gate['parameter'] = random.uniform(0, 2*np.pi)
                    
            else:
                # Single-qubit gate
                gate_type = random.choice(self.single_qubit_gates)
                qubit = random.randrange(self.n_qubits)
                
                gate = {
                    'type': gate_type,
                    'qubits': [qubit],
                    'layer': _
                }
                
                # Add parameter for rotation gates
                if gate_type in ['RX', 'RY', 'RZ']:
                    gate['parameter'] = random.uniform(0, 2*np.pi)
            
            circuit['gates'].append(gate)
        
        # Add measurements
        measurement_bases = ['X', 'Y', 'Z']
        for q in range(self.n_qubits):
            circuit['measurements'].append({
                'qubit': q,
                'basis': random.choice(measurement_bases)
            })
        
        # Inject bugs if requested
        if add_bugs:
            if bug_types:
                for bug_type in bug_types:
                    circuit = self.bug_injector.inject_bug(circuit, bug_type)
            else:
                # Randomly inject some bugs
                n_bugs = random.randint(1, 3)
                for _ in range(n_bugs):
                    if random.random() < self.bug_injector.bug_probability:
                        circuit = self.bug_injector.inject_bug(circuit)
        
        return circuit
    
    def generate_multiple_circuits(self, n_circuits: int, bug_ratio: float = 0.5) -> List[Dict]:
        """Generate multiple circuits, some with bugs, some without"""
        circuits = []
        
        for i in range(n_circuits):
            add_bugs = random.random() < bug_ratio
            circuit = self.generate_circuit(add_bugs=add_bugs)
            circuit['id'] = f"circuit_{i:03d}"
            circuit['has_bugs'] = add_bugs
            if add_bugs:
                circuit['injected_bugs'] = self.bug_injector.injected_bugs.copy()
                self.bug_injector.injected_bugs.clear()
            
            circuits.append(circuit)
        
        return circuits


def print_circuit(circuit: Dict, show_details: bool = True):
    """Print circuit in a readable format"""
    print(f"\n{'='*60}")
    print(f"QUANTUM CIRCUIT (ID: {circuit.get('id', 'N/A')})")
    print(f"{'='*60}")
    print(f"Qubits: {circuit['n_qubits']}, Depth: {circuit['depth']}")
    
    if circuit.get('has_bugs', False):
        print("⚠️  CONTAINS BUGS ⚠️")
        if 'injected_bugs' in circuit and circuit['injected_bugs']:
            print(f"Injected bugs: {len(circuit['injected_bugs'])}")
            for i, bug in enumerate(circuit['injected_bugs']):
                print(f"  {i+1}. {bug['type']}: {bug['description']}")
    
    print("\nGate Sequence:")
    print("-" * 40)
    
    for i, gate in enumerate(circuit['gates']):
        gate_str = f"{i:3d}. {gate['type']:6s} on q{gate['qubits']}"
        
        if gate.get('parameter') is not None:
            gate_str += f" (θ={gate['parameter']:.3f})"
        
        # Mark bugs
        bug_marks = []
        if gate.get('is_bug'):
            bug_marks.append("EXTRA")
        if gate.get('timing_bug'):
            bug_marks.append("TIMING")
        if gate.get('decoherence_affected'):
            bug_marks.append("DECOH")
        if gate.get('crosstalk_affected'):
            bug_marks.append("XTALK")
        
        if bug_marks:
            gate_str += f"  ⚠️ [{', '.join(bug_marks)}]"
        
        print(gate_str)
    
    print("\nMeasurements:")
    print("-" * 40)
    for meas in circuit['measurements']:
        meas_str = f"q{meas['qubit']}: {meas['basis']}-basis"
        if meas.get('is_bug'):
            meas_str += "  ⚠️ [WRONG_BASIS]"
        print(meas_str)
    
    if 'decoherence' in circuit:
        print(f"\nDecoherence: T1={circuit['decoherence']['T1']:.1f}, T2={circuit['decoherence']['T2']:.1f}")
    
    if 'crosstalk' in circuit:
        print(f"\nCrosstalk Matrix (max: {np.max(circuit['crosstalk']):.4f})")
    
    print(f"{'='*60}")


# Example usage and demonstration
def main():
    print("Quantum Circuit Generator with Bug Injection")
    print("=" * 60)
    
    # Create generator
    generator = RandomQuantumCircuitGenerator(n_qubits=4, depth=8)
    
    # Generate a clean circuit
    print("\n1. Generating a clean circuit (no bugs):")
    clean_circuit = generator.generate_circuit(add_bugs=False)
    print_circuit(clean_circuit)
    
    # Generate a circuit with random bugs
    print("\n\n2. Generating a circuit with random bugs:")
    buggy_circuit = generator.generate_circuit(add_bugs=True)
    print_circuit(buggy_circuit)
    
    # Generate multiple circuits
    print("\n\n3. Generating multiple circuits with varying bugs:")
    circuits = generator.generate_multiple_circuits(n_circuits=3, bug_ratio=0.7)
    
    for i, circuit in enumerate(circuits):
        print_circuit(circuit)
    
    # Demonstrate specific bug injection
    print("\n\n4. Injecting specific bug types:")
    test_circuit = generator.generate_circuit(add_bugs=False)
    
    bug_injector = QuantumBugInjector()
    
    # Inject specific bugs
    specific_bugs = ['gate_error', 'parameter_error', 'qubit_error']
    for bug_type in specific_bugs:
        test_circuit = bug_injector.inject_bug(test_circuit, bug_type)
    
    test_circuit['id'] = 'specific_bugs'
    test_circuit['has_bugs'] = True
    test_circuit['injected_bugs'] = bug_injector.injected_bugs
    print_circuit(test_circuit)
    
    # Statistics
    print("\n\n5. Bug Type Statistics:")
    all_bugs = []
    for circuit in circuits + [buggy_circuit, test_circuit]:
        if 'injected_bugs' in circuit:
            all_bugs.extend([bug['type'] for bug in circuit['injected_bugs']])
    
    if all_bugs:
        from collections import Counter
        bug_counts = Counter(all_bugs)
        print("\nBug frequency:")
        for bug_type, count in bug_counts.most_common():
            print(f"  {bug_type}: {count} times")


if __name__ == "__main__":
    main()