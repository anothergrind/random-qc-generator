"""
claude_rcg.py

Random Quantum Circuit Generator using Cirq
Features:
- Multiple circuit generation strategies
- Circuit validation and analysis
- Export to multiple formats
- Parameterized circuit generation
- Circuit optimization hints
"""

import cirq
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
from dataclasses import dataclass
from enum import Enum


class GateStrategy(Enum):
    """Strategy for selecting gates during circuit generation"""
    RANDOM = "random"
    WEIGHTED = "weighted"  # More common gates appear more often
    LAYERED = "layered"    # Organize by gate types
    ENTANGLING = "entangling"  # Focus on creating entanglement


@dataclass
class CircuitConfig:
    """Configuration for circuit generation"""
    num_qubits: int
    depth: int
    strategy: GateStrategy = GateStrategy.RANDOM
    single_qubit_gates: List[str] = None
    two_qubit_gates: List[str] = None
    seed: Optional[int] = None
    allow_measurements: bool = True
    connectivity: Optional[List[Tuple[int, int]]] = None  # Custom qubit connectivity


class ClaudeCircuitGenerator:
    """
    Random quantum circuit generator with multiple strategies and features.
    Uses Cirq framework for broader ecosystem compatibility.
    """
    
    # Available gate sets
    SINGLE_QUBIT_GATES = {
        'H': cirq.H,      # Hadamard
        'X': cirq.X,      # Pauli-X (NOT)
        'Y': cirq.Y,      # Pauli-Y
        'Z': cirq.Z,      # Pauli-Z
        'S': cirq.S,      # Phase gate
        'T': cirq.T,      # π/8 gate
        'RX': lambda angle: cirq.rx(angle),  # Rotation around X
        'RY': lambda angle: cirq.ry(angle),  # Rotation around Y
        'RZ': lambda angle: cirq.rz(angle),  # Rotation around Z
    }
    
    TWO_QUBIT_GATES = {
        'CNOT': cirq.CNOT,     # Controlled-NOT
        'CZ': cirq.CZ,         # Controlled-Z
        'SWAP': cirq.SWAP,     # Swap gate
        'ISWAP': cirq.ISWAP,   # iSwap gate
    }
    
    # Default weights for weighted strategy
    DEFAULT_WEIGHTS = {
        'H': 0.3, 'X': 0.2, 'Y': 0.1, 'Z': 0.1,
        'S': 0.1, 'T': 0.1, 'RX': 0.05, 'RY': 0.03, 'RZ': 0.02,
        'CNOT': 0.4, 'CZ': 0.3, 'SWAP': 0.2, 'ISWAP': 0.1
    }
    
    def __init__(self, config: CircuitConfig):
        self.config = config
        self.rng = np.random.RandomState(config.seed)
        
        # Set default gate sets if not specified
        if config.single_qubit_gates is None:
            self.single_gates = ['H', 'X', 'Y', 'Z']
        else:
            self.single_gates = config.single_qubit_gates
            
        if config.two_qubit_gates is None:
            self.two_gates = ['CNOT', 'CZ']
        else:
            self.two_gates = config.two_qubit_gates
        
        # Initialize qubits
        self.qubits = cirq.LineQubit.range(config.num_qubits)
        
        # Build connectivity graph
        self._build_connectivity()
    
    def _build_connectivity(self):
        """Build qubit connectivity graph"""
        if self.config.connectivity is not None:
            self.connectivity = self.config.connectivity
        else:
            # Default: nearest-neighbor connectivity
            self.connectivity = [
                (i, i+1) for i in range(self.config.num_qubits - 1)
            ]
    
    def generate(self) -> cirq.Circuit:
        """Generate circuit based on strategy"""
        strategy_map = {
            GateStrategy.RANDOM: self._generate_random,
            GateStrategy.WEIGHTED: self._generate_weighted,
            GateStrategy.LAYERED: self._generate_layered,
            GateStrategy.ENTANGLING: self._generate_entangling,
        }
        
        circuit = strategy_map[self.config.strategy]()
        
        if self.config.allow_measurements:
            circuit.append(cirq.measure(*self.qubits, key='result'))
        
        return circuit
    
    def _generate_random(self) -> cirq.Circuit:
        """Pure random gate selection"""
        circuit = cirq.Circuit()
        
        for _ in range(self.config.depth):
            for qubit_idx in range(self.config.num_qubits):
                # Decide: single or two-qubit gate
                if self.rng.random() < 0.7:  # 70% single-qubit
                    gate_name = self.rng.choice(self.single_gates)
                    gate = self._get_gate(gate_name, single_qubit=True)
                    circuit.append(gate(self.qubits[qubit_idx]))
                else:  # 30% two-qubit
                    if len(self.connectivity) > 0:
                        control, target = self.rng.choice(self.connectivity)
                        gate_name = self.rng.choice(self.two_gates)
                        gate = self._get_gate(gate_name, single_qubit=False)
                        circuit.append(gate(self.qubits[control], self.qubits[target]))
        
        return circuit
    
    def _generate_weighted(self) -> cirq.Circuit:
        """Weighted random selection (common gates appear more)"""
        circuit = cirq.Circuit()
        
        # Build weighted gate list
        all_gates = self.single_gates + self.two_gates
        weights = [self.DEFAULT_WEIGHTS.get(g, 0.1) for g in all_gates]
        weights = np.array(weights) / np.sum(weights)  # Normalize
        
        for _ in range(self.config.depth):
            gate_name = self.rng.choice(all_gates, p=weights)
            
            if gate_name in self.single_gates:
                qubit_idx = self.rng.randint(0, self.config.num_qubits)
                gate = self._get_gate(gate_name, single_qubit=True)
                circuit.append(gate(self.qubits[qubit_idx]))
            else:
                if len(self.connectivity) > 0:
                    control, target = self.rng.choice(self.connectivity)
                    gate = self._get_gate(gate_name, single_qubit=False)
                    circuit.append(gate(self.qubits[control], self.qubits[target]))
        
        return circuit
    
    def _generate_layered(self) -> cirq.Circuit:
        """Layer-by-layer generation (all single-qubit, then entangling)"""
        circuit = cirq.Circuit()
        
        layers_per_depth = 2  # Single-qubit layer + entangling layer
        
        for _ in range(self.config.depth // layers_per_depth):
            # Single-qubit layer
            for qubit in self.qubits:
                gate_name = self.rng.choice(self.single_gates)
                gate = self._get_gate(gate_name, single_qubit=True)
                circuit.append(gate(qubit))
            
            # Entangling layer
            for control, target in self.connectivity:
                gate_name = self.rng.choice(self.two_gates)
                gate = self._get_gate(gate_name, single_qubit=False)
                circuit.append(gate(self.qubits[control], self.qubits[target]))
        
        return circuit
    
    def _generate_entangling(self) -> cirq.Circuit:
        """Focus on creating maximum entanglement"""
        circuit = cirq.Circuit()
        
        for _ in range(self.config.depth):
            # Always do entangling operations
            for control, target in self.connectivity:
                # Add single-qubit gates before entangling
                h_or_not = self.rng.choice([cirq.H, cirq.I])
                circuit.append(h_or_not(self.qubits[control]))
                
                gate_name = self.rng.choice(self.two_gates)
                gate = self._get_gate(gate_name, single_qubit=False)
                circuit.append(gate(self.qubits[control], self.qubits[target]))
        
        return circuit
    
    def _get_gate(self, gate_name: str, single_qubit: bool):
        """Get gate operation from name"""
        if single_qubit:
            gate_class = self.SINGLE_QUBIT_GATES[gate_name]
        else:
            gate_class = self.TWO_QUBIT_GATES[gate_name]
        
        # Handle parameterized gates
        if gate_name in ['RX', 'RY', 'RZ']:
            angle = self.rng.uniform(0, 2 * np.pi)
            return gate_class(angle)
        
        return gate_class
    
    def analyze_circuit(self, circuit: cirq.Circuit) -> Dict:
        """Analyze generated circuit properties"""
        gate_counts = {}
        total_gates = 0
        
        for moment in circuit:
            for op in moment:
                gate_name = str(op.gate)
                gate_counts[gate_name] = gate_counts.get(gate_name, 0) + 1
                total_gates += 1
        
        return {
            'total_gates': total_gates,
            'actual_depth': len(circuit),
            'gate_distribution': gate_counts,
            'num_qubits': len(self.qubits),
        }
    
    def export_qasm(self, circuit: cirq.Circuit, filename: str):
        """Export circuit to QASM format"""
        qasm_str = cirq.qasm(circuit)
        with open(filename, 'w') as f:
            f.write(qasm_str)
        print(f"Exported to {filename}")
    
    def export_json(self, circuit: cirq.Circuit, filename: str):
        """Export circuit analysis to JSON"""
        analysis = self.analyze_circuit(circuit)
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"Analysis exported to {filename}")


def main():
    """Interactive CLI for circuit generation"""
    print("=" * 50)
    print("Claude's Random Quantum Circuit Generator (Cirq)")
    print("=" * 50)
    
    # Get user input
    num_qubits = int(input("\nNumber of qubits: "))
    depth = int(input("Circuit depth: "))
    
    print("\nAvailable strategies:")
    for i, strategy in enumerate(GateStrategy, 1):
        print(f"{i}. {strategy.value}")
    
    strategy_choice = int(input("\nChoose strategy (1-4): ")) - 1
    strategy = list(GateStrategy)[strategy_choice]
    
    seed = input("\nRandom seed (press Enter for random): ")
    seed = int(seed) if seed else None
    
    # Create configuration
    config = CircuitConfig(
        num_qubits=num_qubits,
        depth=depth,
        strategy=strategy,
        seed=seed
    )
    
    # Generate circuit
    generator = ClaudeCircuitGenerator(config)
    circuit = generator.generate()
    
    # Display results
    print("\n" + "=" * 50)
    print("Generated Circuit:")
    print("=" * 50)
    print(circuit)
    
    # Analysis
    print("\n" + "=" * 50)
    print("Circuit Analysis:")
    print("=" * 50)
    analysis = generator.analyze_circuit(circuit)
    for key, value in analysis.items():
        print(f"{key}: {value}")
    
    # Export options
    export = input("\nExport circuit? (qasm/json/no): ").lower()
    if export == 'qasm':
        filename = input("Filename (without extension): ")
        generator.export_qasm(circuit, f"{filename}.qasm")
    elif export == 'json':
        filename = input("Filename (without extension): ")
        generator.export_json(circuit, f"{filename}.json")
    
    print("\nDone!")


if __name__ == "__main__":
    main()