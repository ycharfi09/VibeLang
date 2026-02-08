# VibeLang Type Checker

The type checker validates VibeLang programs for type correctness after parsing.

## Usage

```python
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.typechecker import TypeChecker, TypeCheckError

tokens = Lexer(source).tokenize()
program = Parser(tokens).parse()
errors = TypeChecker().check(program)
for err in errors:
    print(f"{err.line}:{err.column}: {err.message}")
```

## Features

- **Literal type inference**: `IntegerLiteral` → `Int`, `FloatLiteral` → `Float`, etc.
- **Binary operator checking**: arithmetic on `Int`/`Float`, comparisons return `Bool`, logical ops require `Bool` operands.
- **Unary operator checking**: `!` requires `Bool`, `-` requires numeric.
- **Function declarations**: validates parameter types, return type vs. body type, and argument counts/types at call sites.
- **Type declarations**: registers type aliases, sum types, and refined types.
- **Contract validation**: preconditions (`expect`) and postconditions (`ensure`) must be `Bool`.
- **Invariant validation**: type invariants must be `Bool`.
- **Let bindings**: checks value type against annotation when present.
- **When expressions**: condition must be `Bool`, branches must agree.
- **Type aliases**: resolved through the type environment.

## Supported Primitive Types

`Int`, `Float`, `Bool`, `String`, `Byte`, `Unit`

## Composite Types

- `Array[T]` — homogeneous arrays
- `Result[T, E]` — success/error result type
- Named/user-defined types via `type` declarations

## Error Reporting

Errors are collected as `TypeCheckError` instances with `message`, `line`, and `column` attributes. The checker continues past errors to report as many issues as possible in a single pass.
