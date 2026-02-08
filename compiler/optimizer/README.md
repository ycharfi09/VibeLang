# VibeLang Optimizer

The optimizer performs AST-to-AST transformations to simplify and improve VibeLang programs at compile time. It operates on a deep copy of the input AST, leaving the original untouched.

## Usage

```python
from compiler.optimizer import Optimizer
from compiler.lexer import Lexer
from compiler.parser import Parser

tokens = Lexer(source).tokenize()
program = Parser(tokens).parse()

optimizer = Optimizer()
optimized = optimizer.optimize(program)
print(f"Applied {optimizer.optimizations_applied} optimizations")
```

## Optimizations

### 1. Constant Folding

Evaluates constant expressions at compile time:

- **Arithmetic**: `3 + 4` → `7`, `2 * 3` → `6`, `10 / 2` → `5`
- **Logical**: `true && false` → `false`, `true || false` → `true`
- **Comparison**: `3 > 2` → `true`, `1 == 2` → `false`
- **Unary**: `!true` → `false`, `-5` → `-5` (literal)
- **String concatenation**: `"hello" + " world"` → `"hello world"`

### 2. Dead Code Elimination

Removes unreachable branches in conditional expressions:

- `when true { body } otherwise { dead }` → `body`
- `when false { dead } otherwise { body }` → `body`

### 3. Identity Simplification

Simplifies operations involving identity/absorbing elements:

- `x + 0` → `x`, `0 + x` → `x`
- `x * 1` → `x`, `1 * x` → `x`
- `x * 0` → `0`, `0 * x` → `0`
- `x - 0` → `x`
- `!!x` → `x` (double negation elimination)
