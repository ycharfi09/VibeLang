# VibeLang Formatter

The formatter pretty-prints a VibeLang AST back to canonical source code with
consistent 2-space indentation.

## Usage

```python
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.formatter import Formatter

tokens = Lexer(source).tokenize()
program = Parser(tokens).parse()
formatted = Formatter().format(program)
```

## Formatting Rules

- 2-space indentation (configurable)
- Blank line between top-level declarations
- Contracts (`expect`/`ensure`) indented under function signature
- Invariants indented under type declaration
- Sum type variants each on their own line with `|` prefix
- Spaces around binary operators
