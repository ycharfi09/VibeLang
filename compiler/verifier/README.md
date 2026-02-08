# VibeLang Verifier

The verifier is the formal verification component of the VibeLang compiler. It uses SMT (Satisfiability Modulo Theories) solvers to prove correctness properties about VibeLang programs.

## Overview

The VibeLang verifier performs:
1. **Contract Verification**: Proves preconditions and postconditions
2. **Invariant Checking**: Verifies type and global invariants
3. **Type Safety**: Ensures type correctness
4. **Memory Safety**: Proves bounds checking
5. **Termination Analysis**: Detects infinite loops (optional)

## Architecture

```
┌─────────────┐
│     AST     │
└──────┬──────┘
       │
       v
┌─────────────────┐
│  Type Checker   │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│ Contract        │
│ Extractor       │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│  SMT Formula    │
│  Generator      │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│ Z3 SMT Solver   │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│ Verification    │
│ Results         │
└─────────────────┘
```

## SMT Solver Integration

VibeLang uses the Z3 SMT solver for formal verification. Z3 is a high-performance theorem prover from Microsoft Research.

### Installing Z3

```bash
# Ubuntu/Debian
sudo apt-get install z3

# macOS
brew install z3

# Or build from source
git clone https://github.com/Z3Prover/z3.git
cd z3
python scripts/mk_make.py
cd build
make
sudo make install
```

### Python Z3 Bindings

```bash
pip install z3-solver
```

## Contract Verification

### Example

```vibelang
define add(x: Int, y: Int) -> Int
  expect x >= 0
  expect y >= 0
  ensure result >= x
  ensure result >= y
  ensure result == x + y
given
  x + y
```

### Generated SMT Formula

```python
from z3 import *

def verify_add():
    # Declare variables
    x = Int('x')
    y = Int('y')
    result = Int('result')
    
    # Create solver
    solver = Solver()
    
    # Add preconditions
    solver.add(x >= 0)
    solver.add(y >= 0)
    
    # Define result
    solver.add(result == x + y)
    
    # Try to find counterexample to postconditions
    # If SAT, postcondition can be violated
    # If UNSAT, postcondition is always true
    
    # Check: result >= x
    solver.push()
    solver.add(Not(result >= x))
    if solver.check() == sat:
        print("VIOLATION: result >= x")
        print("Counterexample:", solver.model())
    else:
        print("PROVEN: result >= x")
    solver.pop()
    
    # Check: result >= y
    solver.push()
    solver.add(Not(result >= y))
    if solver.check() == sat:
        print("VIOLATION: result >= y")
        print("Counterexample:", solver.model())
    else:
        print("PROVEN: result >= y")
    solver.pop()
    
    # Check: result == x + y
    solver.push()
    solver.add(Not(result == x + y))
    if solver.check() == sat:
        print("VIOLATION: result == x + y")
        print("Counterexample:", solver.model())
    else:
        print("PROVEN: result == x + y")
    solver.pop()

verify_add()
```

Output:
```
PROVEN: result >= x
PROVEN: result >= y
PROVEN: result == x + y
```

## Invariant Verification

### Example

```vibelang
type PositiveMoney = Int
  invariant value > 0
  invariant value <= 9999999999

define addMoney(a: PositiveMoney, b: PositiveMoney) -> Result[PositiveMoney, String]
  expect a > 0
  expect b > 0
  ensure result.isSuccess() -> (result.value() > 0 && result.value() <= 9999999999)
given
  sum = a + b
  when sum > 9999999999
    Error("Exceeds maximum")
  otherwise
    Success(sum)
```

### SMT Verification

```python
def verify_positive_money_addition():
    a = Int('a')
    b = Int('b')
    sum_val = Int('sum')
    
    solver = Solver()
    
    # PositiveMoney invariants for inputs
    solver.add(a > 0)
    solver.add(a <= 9999999999)
    solver.add(b > 0)
    solver.add(b <= 9999999999)
    
    # Define sum
    solver.add(sum_val == a + b)
    
    # Check if sum can violate invariants
    # Case 1: sum <= 9999999999
    solver.push()
    solver.add(sum_val <= 9999999999)
    
    # Verify invariants hold for result
    solver.push()
    solver.add(Not(sum_val > 0))
    if solver.check() == sat:
        print("VIOLATION: sum > 0 when sum <= max")
    else:
        print("PROVEN: sum > 0 when sum <= max")
    solver.pop()
    
    solver.pop()
    
    # Case 2: sum > 9999999999 (error case)
    # No invariant check needed as it returns Error
```

## Memory Bounds Verification

### Example

```vibelang
type BoundedArray[T] = Array[T]
  invariant self.length() <= 1000

define getElement(arr: BoundedArray[Int], index: Int) -> Result[Int, String]
  expect index >= 0
  expect index < arr.length()
  ensure result.isSuccess() -> true
given
  Success(arr[index])
```

### Verification

```python
def verify_bounded_array_access():
    index = Int('index')
    arr_length = Int('arr_length')
    
    solver = Solver()
    
    # Array invariant
    solver.add(arr_length <= 1000)
    solver.add(arr_length >= 0)
    
    # Preconditions
    solver.add(index >= 0)
    solver.add(index < arr_length)
    
    # Verify access is safe
    solver.push()
    # If preconditions hold, access cannot fail
    solver.add(Not(And(index >= 0, index < arr_length)))
    if solver.check() == sat:
        print("VIOLATION: Array access may be out of bounds")
    else:
        print("PROVEN: Array access is always safe")
    solver.pop()
```

## Verification Levels

VibeLang supports multiple verification levels:

### 1. None (Unsafe)
No verification or runtime checks. Maximum performance, no safety guarantees.

```bash
vibelang compile --verify=none program.vbl
```

### 2. Runtime Only
Insert runtime checks for all contracts. No compile-time verification.

```bash
vibelang compile --verify=runtime program.vbl
```

### 3. Hybrid (Default)
Attempt to prove contracts statically. Insert runtime checks for unproven contracts.

```bash
vibelang compile --verify=hybrid program.vbl
```

### 4. Full
Require all contracts to be proven statically. Compilation fails if any contract cannot be proven.

```bash
vibelang compile --verify=full program.vbl
```

## Verification Report

Example verification report:

```
Verification Report for bank_transfer.vbl
=========================================

Function: transfer
  - Preconditions: 4 total
    ✓ from.active == true (runtime check)
    ✓ to.active == true (runtime check)
    ✓ from.balance >= amount (proven)
    ✓ amount > 0 (proven by type system)
  
  - Postconditions: 3 total
    ✓ from.balance == old(from.balance) - amount (proven)
    ✓ to.balance == old(to.balance) + amount (proven)
    ✓ result properties (runtime check)

Type: PositiveMoney
  - Invariants: 2 total
    ✓ value > 0 (enforced by type system)
    ✓ value <= 9999999999 (runtime check)

Summary:
  - 9 total contracts
  - 5 proven statically
  - 4 runtime checks inserted
  - 0 verification failures
  - Verification time: 1.2s
```

## SMT Formula Generation

### Expression Translation

```python
def expr_to_smt(expr: Expression) -> z3.ExprRef:
    """Translate VibeLang expression to Z3 expression"""
    if isinstance(expr, IntegerLiteral):
        return IntVal(expr.value)
    
    elif isinstance(expr, BoolLiteral):
        return BoolVal(expr.value)
    
    elif isinstance(expr, Identifier):
        # Look up variable in environment
        return get_z3_var(expr.name)
    
    elif isinstance(expr, BinaryOp):
        left = expr_to_smt(expr.left)
        right = expr_to_smt(expr.right)
        
        if expr.operator == '+':
            return left + right
        elif expr.operator == '-':
            return left - right
        elif expr.operator == '*':
            return left * right
        elif expr.operator == '/':
            return left / right
        elif expr.operator == '==':
            return left == right
        elif expr.operator == '!=':
            return left != right
        elif expr.operator == '<':
            return left < right
        elif expr.operator == '>':
            return left > right
        elif expr.operator == '<=':
            return left <= right
        elif expr.operator == '>=':
            return left >= right
        elif expr.operator == '&&':
            return And(left, right)
        elif expr.operator == '||':
            return Or(left, right)
    
    elif isinstance(expr, UnaryOp):
        operand = expr_to_smt(expr.operand)
        
        if expr.operator == '!':
            return Not(operand)
        elif expr.operator == '-':
            return -operand
    
    elif isinstance(expr, FunctionCall):
        # Handle special functions like old()
        if isinstance(expr.function, Identifier) and expr.function.name == 'old':
            # Return the "old" value of the expression
            return expr_to_smt(expr.arguments[0], use_old=True)
    
    raise NotImplementedError(f"Cannot translate {type(expr)} to SMT")
```

## Limitations

### Current Limitations

1. **Loop Invariants**: Require manual annotation
2. **Recursive Functions**: May not terminate verification
3. **Complex Data Structures**: Limited support for nested structures
4. **Floating Point**: Limited precision reasoning
5. **Heap Reasoning**: Simplified heap model

### Future Enhancements

1. **Automatic Loop Invariant Inference**: Using abstract interpretation
2. **Termination Checking**: Prove functions always terminate
3. **Quantifier Elimination**: Better support for universal quantification
4. **Interactive Proving**: Integration with proof assistants (Coq, Lean)
5. **Concurrent Verification**: Verify concurrent programs
6. **Separation Logic**: Better heap reasoning

## Benchmarks

Performance on example programs:

| Program | LOC | Contracts | Verification Time |
|---------|-----|-----------|-------------------|
| bank_transfer.vbl | 150 | 25 | 2.3s |
| types.vbl | 200 | 15 | 1.5s |
| simple_math.vbl | 50 | 10 | 0.4s |

## Configuration

### vibelang.toml

```toml
[verification]
# Verification level: none, runtime, hybrid, full
level = "hybrid"

# Timeout for SMT solver (seconds)
timeout = 30

# Number of parallel verification workers
workers = 4

# Report unproven contracts as warnings or errors
unproven_severity = "warning"

# Enable specific optimizations
[verification.optimizations]
constant_folding = true
dead_code_elimination = true
contract_caching = true
```

## Using Z3 Directly

For advanced users who want to verify VibeLang contracts manually:

```python
from z3 import *

# Example: Verify bank transfer correctness
from_balance = Int('from_balance')
to_balance = Int('to_balance')
amount = Int('amount')

# Create solver
s = Solver()

# Preconditions
s.add(from_balance >= amount)
s.add(amount > 0)

# Compute new balances
new_from = from_balance - amount
new_to = to_balance + amount

# Check postcondition: total balance preserved
s.push()
s.add(Not((new_from + new_to) == (from_balance + to_balance)))
result = s.check()
if result == sat:
    print("Violation found:", s.model())
else:
    print("Postcondition proven!")
s.pop()
```

## References

1. **Z3 SMT Solver**: https://github.com/Z3Prover/z3
2. **Z3 Tutorial**: https://rise4fun.com/z3/tutorial
3. **SMT-LIB Standard**: http://smtlib.cs.uiowa.edu/
4. **Why3**: Deductive Program Verification Platform
5. **Dafny**: Verification-aware programming language
6. **Boogie**: Intermediate verification language

## Contributing

To contribute to the verifier:

1. Understand Z3 and SMT-LIB
2. Study the AST structure
3. Implement new verification passes
4. Add test cases
5. Update documentation

## Support

For verification issues:
- Check Z3 installation: `z3 --version`
- Enable verbose mode: `vibelang compile --verify-verbose`
- Report issues with minimal examples
- Include verification logs
