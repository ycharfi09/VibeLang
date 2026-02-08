# VibeLang Lexer Implementation

Implementation status: 📋 Planned

## Roadmap

- [ ] Token definitions
- [ ] Lexer state machine
- [ ] Indentation handling (2-space requirement)
- [ ] Comment parsing
- [ ] String literal parsing with escape sequences
- [ ] Numeric literal parsing
- [ ] Operator tokenization
- [ ] Error reporting with line/column info
- [ ] Unit tests

## Implementation Notes

The lexer will be implemented in Python initially, following the design outlined in the README.md.

Key features:
- Enforces 2-space indentation (no tabs)
- Generates INDENT/DEDENT tokens for significant whitespace
- Handles single-line (#) and multi-line (##...##) comments
- Tracks line and column numbers for error reporting
