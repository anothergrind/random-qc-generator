# Key Features That Make This Unique

## Multiple Generation Strategies

- Random (like your existing ones)
- Weighted (realistic gate distributions)
- Layered (organized structure)
- Entangling (maximum entanglement)

### Cirq Framework (not Qiskit)

- Different gate syntax
- Different qubit model
- Interoperable with Google's ecosystem

### Configurable Connectivity

Can specify custom qubit connections
Useful for real hardware topology

### Circuit Analysis

Gate counting
Depth verification
Distribution statistics

### Export Formats

QASM (universal quantum format)
JSON (for data analysis)

### Parameterized Gates

Rotation gates with random angles
More realistic circuit generation

## Usage Examples

### Example 1: Simple random circuit

config = CircuitConfig(num_qubits=3, depth=5)
gen = ClaudeCircuitGenerator(config)
circuit = gen.generate()
print(circuit)

### Example 2: Entangling strategy

config = CircuitConfig(
    num_qubits=4,
    depth=10,
    strategy=GateStrategy.ENTANGLING
)
gen = ClaudeCircuitGenerator(config)
circuit = gen.generate()

### Example 3: Custom gates and connectivity

config = CircuitConfig(
    num_qubits=5,
    depth=8,
    single_qubit_gates=['H', 'RX', 'RY'],
    two_qubit_gates=['CNOT'],
    connectivity=[(0,1), (1,2), (2,3), (3,4)],  # Linear chain
    seed=42
)
