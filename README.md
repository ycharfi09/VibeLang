# VibeLang

**An AI-native programming language with built-in formal verification**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

VibeLang is a modern, statically-typed programming language designed from the ground up for:
- **Formal Verification**: Prove correctness with contracts and SMT solvers
- **AI-Native Design**: Optimized for LLM code generation and analysis
- **Memory Safety**: No null values, automatic bounds checking
- **Explicit Contracts**: Mandatory preconditions and postconditions

## Quick Start

```vibelang
type PositiveMoney = Int
  invariant value > 0
  invariant value <= 9999999999

define transfer(from: Account, to: Account, amount: PositiveMoney) -> Result[Unit, Error]
  expect from.balance >= amount
  expect to.active == true
  ensure from.balance == old(from.balance) - amount
  ensure to.balance == old(to.balance) + amount
given
  # Implementation with verified correctness
  Success(Unit)
```

## Features

### 🔒 Strong Type System
- No null values - use `Result[T, E]` and `Option[T]` instead
- Refined types with invariants
- Algebraic data types (sum and product types)
- Type guards and automatic narrowing

### ✅ Formal Verification
- Design-by-contract with `expect` and `ensure`
- Global invariants for types
- SMT solver integration (Z3)
- Compile-time proof when possible, runtime checks otherwise

### 🎯 AI-Native
- Clear, explicit syntax optimized for LLM understanding
- Mandatory contracts make intent explicit
- Predictable error handling patterns
- Comprehensive documentation

### 🚫 No Null, No Exceptions
- All errors handled explicitly with `Result` types
- Pattern matching with exhaustiveness checking
- `when`/`otherwise` control flow (no if/else)
- `given` for pattern matching

### 📏 Memory Safety
- Automatic bounds checking
- Memory-bounded types
- Safe array access
- No buffer overflows

## Installation

```bash
# Clone the repository
git clone https://github.com/ycharfi09/VibeLang.git
cd VibeLang

# Install in development mode
pip install -e .

# Use the CLI
vibelang lex program.vbl        # Show tokens
vibelang parse program.vbl      # Show AST summary
vibelang check program.vbl      # Type-check
vibelang compile program.vbl    # Compile to Python
vibelang verify program.vbl     # Verify contracts
vibelang optimize program.vbl   # Optimize and print
vibelang fmt program.vbl        # Format source code
```

## Documentation

- **[Language Specification](LANGUAGE_SPEC.md)** - Complete language reference
- **[Grammar](docs/grammar.md)** - Formal grammar definition
- **[Technical Spec](docs/spec.md)** - Implementation details
- **[Examples](examples/)** - Sample programs
  - [bank_transfer.vbl](examples/bank_transfer.vbl) - Banking with contracts
  - [types.vbl](examples/types.vbl) - Type system examples
- **[Standard Library](stdlib/)** - Core types and functions
- **[Tests](tests/)** - Test suite

## Language Overview

### Keywords

- **Type System**: `define`, `type`
- **Contracts**: `expect`, `ensure`, `invariant`
- **Control Flow**: `given`, `when`, `otherwise`

### Core Principles

1. **Contracts are Mandatory**: Functions must specify preconditions and postconditions
2. **No Implicit Behavior**: All operations are explicit
3. **Type Safety**: Strong static typing with inference
4. **Memory Safety**: Automatic bounds checking and safe memory management
5. **Formal Verification**: Prove correctness at compile time

### Example Programs

**Type Definition with Invariants:**

```vibelang
type EmailAddress = String
  invariant self.contains("@")
  invariant self.length() >= 3
  invariant self.length() <= 320
```

**Function with Contracts:**

```vibelang
define withdraw(account: Account, amount: PositiveMoney) -> Result[Account, Error]
  expect account.active == true
  expect account.balance >= amount
  ensure result.isSuccess() -> result.value().balance == old(account.balance) - amount
given
  when account.balance < amount
    Error(InsufficientFunds)
  otherwise
    Success({ ...account, balance: account.balance - amount })
```

**Pattern Matching:**

```vibelang
given parseInput(userInput)
  Success(value) ->
    processValue(value)
  Error(ParseError(msg)) ->
    handleParseError(msg)
  Error(_) ->
    handleGenericError()
```

## Compiler Architecture

```
Source Code (.vbl)
    ↓
┌─────────┐
│  Lexer  │  → Tokens
└────┬────┘
     ↓
┌─────────┐
│ Parser  │  → Abstract Syntax Tree (AST)
└────┬────┘
     ↓
┌──────────────┐
│ Type Checker │  → Typed AST
└──────┬───────┘
       ↓
┌──────────────┐
│  Verifier    │  → Verification Results
│  (Z3 SMT)    │     (Proven / Runtime Checks)
└──────┬───────┘
       ↓
┌──────────────┐
│   Optimizer  │  → Optimized AST
└──────┬───────┘
       ↓
┌──────────────┐
│   Code Gen   │  → Native Code / JS / Bytecode
└──────────────┘
```

## Development Status

Current status:
- ✅ Language specification complete
- ✅ Grammar definition complete
- ✅ Example programs written
- ✅ Compiler implementation complete
- 🚧 Standard library (in progress)
- ✅ Tooling (formatter, optimizer, verifier)

## Roadmap

### Phase 1: Core Language ✅
- [x] Lexer implementation
- [x] Parser implementation
- [x] Type checker
- [x] Basic code generation (Python target)

### Phase 2: Verification ✅
- [x] Contract verification (lightweight symbolic verifier)
- [x] Invariant checking
- [x] Runtime check insertion

### Phase 3: Optimization ✅
- [x] Dead code elimination
- [x] Constant folding
- [x] Identity simplification

### Phase 4: Tooling ✅
- [x] Formatter (`vibelang fmt`)
- [x] CLI toolchain (`vibelang lex|parse|check|compile|verify|optimize|fmt`)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas we need help:
- Compiler implementation
- Standard library development
- Documentation improvements
- Example programs
- Test suite expansion
- IDE integration

## Community

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Design discussions and Q&A
- **Discord**: Coming soon

## Resources

### Learning
- [Language Specification](LANGUAGE_SPEC.md)
- [Example Programs](examples/)
- [Standard Library Documentation](stdlib/)

### Research Papers
- Design by Contract - Bertrand Meyer
- Refinement Types - Freeman & Pfenning
- Why3: Deductive Program Verification
- Dafny: Verification-Aware Programming

### Tools
- [Z3 SMT Solver](https://github.com/Z3Prover/z3)
- [SMT-LIB Standard](http://smtlib.cs.uiowa.edu/)

## License

VibeLang is licensed under the [MIT License](LICENSE).

## Acknowledgments

- Inspired by Dafny, F*, and Idris
- Built with Z3 SMT solver
- Designed for the AI era

---

**Note**: VibeLang is an experimental language under active development. The specification and implementation may change as the project evolves.
