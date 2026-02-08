# VibeLang Language Specification

Version: 0.1.0  
Date: February 2026

## 1. Introduction

VibeLang is an AI-native programming language with built-in formal verification capabilities. It is designed to make software correctness guarantees accessible and enforceable through mandatory contracts, type guards, and global invariants.

## 2. Design Principles

- **Safety First**: No null values, mandatory error handling with Result types
- **Formal Verification**: Built-in contract checking and SMT solver integration
- **AI-Native**: Designed for LLM code generation and analysis
- **Explicit Over Implicit**: All contracts and invariants must be explicitly stated
- **Memory Safety**: Automatic bounds checking and memory management

## 3. Core Keywords

### 3.1 Type System
- `type`: Define new types
- `define`: Define functions and constants

### 3.2 Contracts
- `expect`: Preconditions that must be true before function execution
- `ensure`: Postconditions that must be true after function execution
- `invariant`: Global invariants that must always hold

### 3.3 Control Flow
- `given`: Pattern matching and type narrowing
- `when`: Conditional branching (replaces if)
- `otherwise`: Default case for when statements

## 4. Type System

### 4.1 Primitive Types
- `Int`: Arbitrary precision integers
- `Float`: Floating-point numbers
- `Bool`: Boolean values (true/false)
- `String`: UTF-8 strings
- `Byte`: Single byte values

### 4.2 Result Type
VibeLang uses `Result[T, E]` for error handling. There is no null.

```vibelang
type Result[T, E] =
  | Success(T)
  | Error(E)
```

### 4.3 Refined Types
Types can be refined with contracts:

```vibelang
type PositiveMoney = Int
  invariant value > 0
  invariant value <= 9999999999
```

## 5. Function Definitions

Functions are defined using the `define` keyword with mandatory contracts:

```vibelang
define transfer(from: Account, to: Account, amount: PositiveMoney) -> Result[Unit, TransferError]
  expect from.balance >= amount
  expect to.exists()
  ensure from.balance == old(from.balance) - amount
  ensure to.balance == old(to.balance) + amount
given
  # Implementation
```

## 6. Control Flow

### 6.1 When/Otherwise
VibeLang uses `when`/`otherwise` instead of if/else:

```vibelang
when condition
  # code when true
otherwise
  # code when false
```

### 6.2 Pattern Matching
The `given` keyword enables pattern matching:

```vibelang
given result
  Success(value) -> handleSuccess(value)
  Error(err) -> handleError(err)
```

## 7. Memory Safety

### 7.1 Bounds Checking
All array and collection accesses are bounds-checked:

```vibelang
define getElement(arr: Array[Int], index: Int) -> Result[Int, IndexError]
  expect index >= 0
  expect index < arr.length
given
  Success(arr[index])
```

### 7.2 Memory Limits
Types can specify memory bounds:

```vibelang
type BoundedString = String
  invariant self.bytes() <= 1024
```

## 8. Formal Verification

### 8.1 Contract Verification
All `expect` and `ensure` clauses are verified at compile time using SMT solvers when possible, and at runtime otherwise.

### 8.2 Invariant Checking
Global invariants are checked:
- At program startup
- After each public function call
- Before program termination

### 8.3 SMT Solver Integration
VibeLang integrates with Z3 SMT solver for:
- Proving contract satisfaction
- Finding counterexamples
- Verifying invariants
- Detecting unreachable code

## 9. Code Style

### 9.1 Indentation
VibeLang uses 2-space indentation (enforced by compiler):

```vibelang
define example() -> Unit
given
  when condition
    doSomething()
  otherwise
    doSomethingElse()
```

### 9.2 Naming Conventions
- Types: PascalCase
- Functions: camelCase
- Constants: UPPER_SNAKE_CASE
- Variables: camelCase

## 10. Error Handling

All errors must be explicitly handled using Result types:

```vibelang
type TransferError =
  | InsufficientFunds
  | AccountNotFound
  | InvalidAmount

define processTransfer(amount: PositiveMoney) -> Result[Receipt, TransferError]
  expect amount > 0
given
  given validateAmount(amount)
    Success(_) -> executeTransfer(amount)
    Error(err) -> Error(err)
```

## 11. Examples

See `/examples` directory for complete examples:
- `bank_transfer.vbl`: Banking operations with contracts
- `types.vbl`: Type system demonstrations

## 12. Future Features

- Dependent types
- Effect system
- Parallel execution primitives
- Proof obligations export
- Interactive theorem proving integration

## 13. References

- Z3 SMT Solver: https://github.com/Z3Prover/z3
- Design by Contract: Bertrand Meyer
- Formal Verification: See `/docs/spec.md`
