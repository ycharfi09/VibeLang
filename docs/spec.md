# VibeLang Technical Specification

Version: 0.1.0  
Status: Draft

## 1. Overview

VibeLang is a statically-typed, AI-native programming language with built-in formal verification. This specification describes the language's semantics, type system, verification framework, and implementation requirements.

## 2. Type System

### 2.1 Type Categories

#### 2.1.1 Primitive Types
- `Int`: Arbitrary precision integer (up to memory limits)
- `Float`: IEEE 754 double-precision floating-point
- `Bool`: Boolean type with values `true` and `false`
- `String`: Immutable UTF-8 encoded string
- `Byte`: 8-bit unsigned integer (0-255)
- `Unit`: Type with single value, represents void

#### 2.1.2 Composite Types
- **Array[T]**: Fixed-size homogeneous collection
- **Tuple[T1, T2, ...]**: Heterogeneous fixed-size collection
- **Record**: Named field collection (structural typing)

#### 2.1.3 Algebraic Data Types
- **Sum Types**: Tagged unions with pattern matching
- **Product Types**: Structures with named fields

#### 2.1.4 Result Type
```vibelang
type Result[T, E] =
  | Success(T)
  | Error(E)
```

All operations that can fail must return a Result type. The absence of null eliminates entire classes of errors.

### 2.2 Type Refinement

Types can be refined with invariants:

```vibelang
type PositiveMoney = Int
  invariant value > 0
  invariant value <= 9999999999

type NonEmptyString = String
  invariant self.length() > 0

type BoundedArray[T] = Array[T]
  invariant self.length() <= 1000
```

Refined types are verified at:
- Construction time
- After mutations
- At function boundaries

### 2.3 Type Guards

Type guards narrow types based on runtime checks:

```vibelang
define process(value: Int) -> String
given
  when value > 0
    # Here value has type PositiveInt (implicit refinement)
    "positive"
  otherwise
    "non-positive"
```

### 2.4 Subtyping Rules

- Refined types are subtypes of their base types
- Result[T, E] is covariant in T and contravariant in E
- Functions are contravariant in parameters, covariant in return type

## 3. Contract System

### 3.1 Preconditions (expect)

Preconditions specify requirements that must hold when a function is called:

```vibelang
define withdraw(account: Account, amount: PositiveMoney) -> Result[Unit, Error]
  expect amount > 0
  expect amount <= account.balance
  expect account.isActive()
given
  # Implementation
```

Preconditions are:
- Verified statically when possible
- Checked at runtime otherwise
- The caller's responsibility to satisfy

### 3.2 Postconditions (ensure)

Postconditions specify guarantees the function provides:

```vibelang
define deposit(account: Account, amount: PositiveMoney) -> Result[Unit, Error]
  ensure account.balance == old(account.balance) + amount
  ensure account.transactionCount == old(account.transactionCount) + 1
given
  # Implementation
```

The `old()` function captures the value of an expression at function entry.

### 3.3 Invariants

Global invariants must always hold:

```vibelang
type BankAccount = {
  balance: Int,
  owner: String
}
  invariant balance >= 0
  invariant owner.length() > 0
```

Invariants are checked:
- After construction
- After any method that modifies the type
- At program boundaries (entry/exit)

### 3.4 Contract Verification Strategy

1. **Static Analysis**: Use SMT solver to prove contracts when possible
2. **Runtime Checks**: Insert runtime checks for unproven contracts
3. **Test Generation**: Generate test cases for edge cases
4. **Counterexample Finding**: Identify contract violations

## 4. Memory Management

### 4.1 Ownership and Borrowing

VibeLang uses reference counting with cycle detection:

```vibelang
define transfer(from: Account, to: Account) -> Unit
  # from and to are borrowed (immutable references)
given
  # Implementation
```

### 4.2 Memory Bounds

All allocations have bounds:

```vibelang
type BoundedBuffer = Array[Byte]
  invariant self.length() <= 4096
  invariant self.capacity() <= 8192
```

### 4.3 Stack vs Heap

- Primitive types and small structs: Stack-allocated
- Large collections and recursive types: Heap-allocated
- Compiler determines allocation strategy

## 5. Control Flow

### 5.1 When/Otherwise

Replaces traditional if/else with mandatory otherwise clause for non-unit expressions:

```vibelang
result = when condition
  calculation1()
otherwise
  calculation2()
```

### 5.2 Pattern Matching (given)

Exhaustive pattern matching on sum types:

```vibelang
given result
  Success(value) -> processValue(value)
  Error(InsufficientFunds) -> handleInsufficientFunds()
  Error(AccountNotFound) -> handleAccountNotFound()
  Error(_) -> handleOtherError()
```

The compiler ensures:
- All cases are covered
- No unreachable cases
- Type narrowing in each branch

### 5.3 Loops

```vibelang
# For-each loop
for item in collection
  process(item)

# While loop with invariant
while condition
  invariant someProperty
given
  # body
```

## 6. Formal Verification

### 6.1 SMT Solver Integration

VibeLang uses Z3 SMT solver for:

#### 6.1.1 Contract Verification
```vibelang
define add(x: Int, y: Int) -> Int
  expect x >= 0
  expect y >= 0
  ensure result >= x
  ensure result >= y
given
  x + y
```

The compiler generates SMT formulas:
```smt2
(declare-const x Int)
(declare-const y Int)
(assert (>= x 0))
(assert (>= y 0))
(assert (not (>= (+ x y) x)))
(check-sat)
```

#### 6.1.2 Invariant Preservation
Verify that operations maintain type invariants.

#### 6.1.3 Reachability Analysis
Detect unreachable code and impossible conditions.

### 6.2 Verification Levels

1. **None**: No verification (unsafe mode)
2. **Runtime**: Only runtime checks
3. **Hybrid**: Static when possible, runtime fallback (default)
4. **Full**: Require all contracts proven statically

## 7. Error Handling

### 7.1 No Null Values

VibeLang has no null. Optional values use Result or Option:

```vibelang
type Option[T] =
  | Some(T)
  | None
```

### 7.2 Error Propagation

The `?` operator propagates errors:

```vibelang
define complexOperation() -> Result[Value, Error]
given
  value1 = operation1()?
  value2 = operation2(value1)?
  Success(combine(value1, value2))
```

### 7.3 Error Types

Errors are values and must be handled:

```vibelang
type TransferError =
  | InsufficientFunds
  | AccountNotFound
  | InvalidAmount
  | NetworkError(String)
```

## 8. Standard Library

### 8.1 Core Types
- Collections: Array, List, Set, Map
- Result and Option types
- Basic arithmetic and comparison operations

### 8.2 I/O Operations
All I/O returns Result types:

```vibelang
define readFile(path: String) -> Result[String, IOError]
define writeFile(path: String, content: String) -> Result[Unit, IOError]
```

### 8.3 Concurrency
Async operations with formal guarantees:

```vibelang
define fetchData() -> Async[Result[Data, Error]]
  expect validConnection()
given
  # Implementation
```

## 9. Compiler Architecture

### 9.1 Pipeline

1. **Lexer**: Tokenization
2. **Parser**: AST generation
3. **Type Checker**: Type inference and checking
4. **Contract Checker**: Verify contracts
5. **Optimizer**: Code optimization
6. **Code Generator**: Target code generation

### 9.2 Verification Pass

Between type checking and code generation:
1. Extract contracts and invariants
2. Generate SMT formulas
3. Query Z3 solver
4. Insert runtime checks for unproven contracts
5. Report verification results

### 9.3 Code Generation Targets

- **Native**: LLVM IR for native compilation
- **JavaScript**: For web platforms
- **Bytecode**: For VM execution

## 10. Interoperability

### 10.1 Foreign Function Interface (FFI)

```vibelang
import foreign "c" as C

define callNative() -> Result[Unit, Error]
  expect # Safety conditions
given
  C.nativeFunction()
```

FFI calls are unsafe by default and require explicit contracts.

### 10.2 Language Bindings

VibeLang can generate bindings for:
- C/C++
- Python
- JavaScript/TypeScript
- Rust

## 11. Tooling

### 11.1 Compiler
- `vibelang compile`: Compile source files
- `vibelang check`: Type check without compilation
- `vibelang verify`: Run formal verification

### 11.2 Package Manager
- `vibelang init`: Initialize new project
- `vibelang add`: Add dependency
- `vibelang build`: Build project

### 11.3 Testing
- `vibelang test`: Run test suite
- `vibelang coverage`: Generate coverage report

### 11.4 Formatting
- `vibelang fmt`: Format source code (2-space indent)

## 12. Performance Characteristics

### 12.1 Compile-Time
- Contract verification adds overhead
- Can be parallelized
- Incremental compilation supported

### 12.2 Runtime
- Runtime checks have small overhead (typically <5%)
- Can be disabled in production with verification level None
- Zero-cost abstractions for type-safe code

## 13. Security Considerations

### 13.1 Memory Safety
- No buffer overflows (bounds checking)
- No use-after-free (ownership system)
- No null pointer dereferences (no null)

### 13.2 Type Safety
- No type confusion
- No uninitialized memory
- No unsafe casts without contracts

### 13.3 Contract Safety
- Preconditions prevent invalid states
- Postconditions guarantee correctness
- Invariants maintain consistency

## 14. Future Directions

- Dependent types
- Effect system for side effects
- Refinement type inference
- Interactive proof assistant integration
- Distributed systems primitives
- Real-time guarantees

## 15. References

1. Design by Contract - Bertrand Meyer
2. Refinement Types - Freeman & Pfenning
3. Z3 SMT Solver Documentation
4. Programming with Contracts - Mitchell Wand
5. Formal Verification Techniques - Various authors
