# VibeLang Code Generator

Translates the VibeLang AST into executable Python source code.

## Usage

```python
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.codegen import CodeGenerator

source = 'define add(x: Int, y: Int) -> Int\ngiven\n  x + y'
tokens = Lexer(source).tokenize()
program = Parser(tokens).parse()
code = CodeGenerator().generate(program)
print(code)
```

## Translation Rules

| VibeLang                         | Python                                      |
|----------------------------------|---------------------------------------------|
| `define f(x: Int) -> Int`        | `def f(x):`                                 |
| `expect expr`                    | `assert expr, "Precondition failed: ..."`   |
| `ensure expr`                    | `assert expr, "Postcondition failed: ..."`  |
| `type Name = Int invariant ...`  | class with `__init__` validation             |
| `type E = \| A \| B(T)`         | base class + variant subclasses              |
| `when cond ... otherwise ...`    | `if cond: ... else: ...`                    |
| `given expr ...`                 | chained `if/elif` conditions                 |
| `&&` / `\|\|` / `!`             | `and` / `or` / `not`                        |
| `IntegerLiteral`                 | Python `int`                                 |
| `BoolLiteral`                    | `True` / `False`                             |
| `ArrayLiteral`                   | Python `list`                                |
| `RecordLiteral`                  | Python `dict`                                |

A runtime header is prepended with `_VL_Success` and `_VL_Error` helper classes
for `Result` type support.
