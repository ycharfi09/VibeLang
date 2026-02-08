# Contributing to VibeLang

Thank you for your interest in contributing to VibeLang! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/VibeLang.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Commit your changes: `git commit -m "Add feature X"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Open a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/ycharfi09/VibeLang.git
cd VibeLang

# Install dependencies (when available)
# pip install -r requirements.txt

# Run tests (when available)
# make test
```

## Areas to Contribute

### 1. Compiler Implementation
- Lexer development
- Parser development  
- Type checker
- Code generation

### 2. Verification System
- Z3 integration
- SMT formula generation
- Contract verification
- Invariant checking

### 3. Standard Library
- Core type implementations
- Collection types
- String operations
- I/O operations

### 4. Documentation
- Tutorial content
- API documentation
- Example programs
- Best practices guide

### 5. Tooling
- IDE integration (Language Server Protocol)
- Syntax highlighting
- Package manager
- Build system

### 6. Testing
- Unit tests
- Integration tests
- Property-based tests
- Benchmark tests

## Code Style

### VibeLang Code
- Use 2-space indentation (enforced by language)
- Follow naming conventions:
  - Types: PascalCase
  - Functions: camelCase
  - Constants: UPPER_SNAKE_CASE
- Write clear contracts for all functions
- Document complex algorithms

### Python Code (Compiler)
- Follow PEP 8 style guide
- Use type hints
- Write docstrings for all public functions
- Keep functions focused and small

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
Add lexer support for string literals

- Implement string tokenization
- Handle escape sequences
- Add tests for string parsing
```

Format:
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed description (if needed)

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New features include tests
- [ ] Documentation is updated
- [ ] Commit messages are clear

### PR Description

Include:
1. **What**: What does this PR do?
2. **Why**: Why is this change needed?
3. **How**: How does it work?
4. **Testing**: How was it tested?

Example:
```markdown
## What
Implements the lexer for VibeLang

## Why
The lexer is the first stage of the compiler pipeline

## How
- Uses Python to tokenize source code
- Handles indentation with INDENT/DEDENT tokens
- Tracks line/column for error reporting

## Testing
- Added unit tests for all token types
- Tested edge cases (nested indentation, comments)
- All tests passing
```

## Testing Guidelines

### Writing Tests

```python
def test_lexer_keywords():
    """Test that keywords are tokenized correctly"""
    lexer = Lexer("define type expect")
    tokens = lexer.tokenize()
    
    assert tokens[0].type == TokenType.DEFINE
    assert tokens[1].type == TokenType.TYPE
    assert tokens[2].type == TokenType.EXPECT
```

### Test Coverage

- Aim for >90% code coverage
- Test edge cases and error conditions
- Include property-based tests for complex logic

## Documentation Guidelines

### Code Comments

- Use comments to explain "why", not "what"
- Document complex algorithms
- Include examples for non-obvious usage

### README Files

- Keep README files up to date
- Include examples
- Document prerequisites and setup

### Language Documentation

- Update LANGUAGE_SPEC.md for language changes
- Add examples to illustrate new features
- Document breaking changes

## Issue Guidelines

### Reporting Bugs

Include:
1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: How to trigger the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, version, etc.
6. **Code Sample**: Minimal example demonstrating the bug

### Feature Requests

Include:
1. **Use Case**: Why is this feature needed?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other approaches considered
4. **Examples**: Example code showing the feature

## Code Review Process

1. **Automated Checks**: CI runs tests and linting
2. **Peer Review**: At least one approval required
3. **Maintainer Review**: Final review by maintainer
4. **Merge**: Once approved and checks pass

## Communication

- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions
- **Discussions**: Design discussions and Q&A

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open an issue with the "question" label
- Start a discussion in GitHub Discussions
- Check existing documentation

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project website (when available)

Thank you for contributing to VibeLang! 🚀
