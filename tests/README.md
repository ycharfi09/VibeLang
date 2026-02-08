# VibeLang Tests

This directory contains the test suite for VibeLang.

## Test Structure

```
tests/
  ├── lexer/           # Lexer tests
  ├── parser/          # Parser tests
  ├── typechecker/     # Type checker tests
  ├── verifier/        # Verification tests
  ├── examples/        # End-to-end example tests
  └── stdlib/          # Standard library tests
```

## Running Tests

```bash
# Run all tests
vibelang test

# Run specific test suite
vibelang test tests/lexer/

# Run single test file
vibelang test tests/lexer/test_tokens.vbl

# Run with verbose output
vibelang test --verbose

# Run with coverage
vibelang test --coverage
```

## Writing Tests

### Basic Test Structure

```vibelang
import test

define testAddition() -> TestResult
given
  result = add(2, 3)
  assert(result == 5, "2 + 3 should equal 5")
  TestPass

define testSubtraction() -> TestResult
given
  result = subtract(5, 3)
  assert(result == 2, "5 - 3 should equal 2")
  TestPass

define testDivisionByZero() -> TestResult
given
  given divide(10, 0)
    Success(_) ->
      TestFail("Expected error for division by zero")
    Error(_) ->
      TestPass
```

## Example Test Cases

### 1. Lexer Tests

Test tokenization of VibeLang source code.

```vibelang
define testKeywordTokenization() -> TestResult
given
  source = "define type expect ensure invariant"
  tokens = tokenize(source)
  
  assert(tokens.length() == 6, "Should have 6 tokens")
  assert(tokens[0].type == DEFINE, "First token should be DEFINE")
  assert(tokens[1].type == TYPE, "Second token should be TYPE")
  
  TestPass

define testIndentation() -> TestResult
given
  source = "define example()
  when condition
    doSomething()"
  
  tokens = tokenize(source)
  
  # Verify INDENT and DEDENT tokens are generated correctly
  TestPass
```

### 2. Parser Tests

Test parsing of VibeLang syntax.

```vibelang
define testFunctionDeclaration() -> TestResult
given
  source = "define add(x: Int, y: Int) -> Int
  expect x >= 0
  expect y >= 0
  ensure result >= 0
given
  x + y"
  
  ast = parse(source)
  
  # Verify AST structure
  assert(ast.declarations.length() == 1, "Should have one declaration")
  
  func = ast.declarations[0]
  assert(func.name == "add", "Function name should be 'add'")
  assert(func.parameters.length() == 2, "Should have 2 parameters")
  assert(func.preconditions.length() == 2, "Should have 2 preconditions")
  assert(func.postconditions.length() == 1, "Should have 1 postcondition")
  
  TestPass

define testTypeDeclaration() -> TestResult
given
  source = "type PositiveMoney = Int
  invariant value > 0"
  
  ast = parse(source)
  
  # Verify AST structure
  typeDecl = ast.declarations[0]
  assert(typeDecl.name == "PositiveMoney", "Type name should be 'PositiveMoney'")
  assert(typeDecl.invariants.length() == 1, "Should have 1 invariant")
  
  TestPass
```

### 3. Type Checker Tests

Test type inference and checking.

```vibelang
define testBasicTypeInference() -> TestResult
given
  source = "define id(x: Int) -> Int
given
  x"
  
  ast = parse(source)
  typecheck(ast)  # Should not throw error
  
  TestPass

define testTypeError() -> TestResult
given
  source = "define bad(x: Int) -> String
given
  x"  # Type error: returns Int, expected String
  
  ast = parse(source)
  
  given typecheck(ast)
    Success(_) ->
      TestFail("Should have type error")
    Error(_) ->
      TestPass
```

### 4. Verification Tests

Test formal verification of contracts.

```vibelang
define testContractVerification() -> TestResult
given
  source = "define add(x: Int, y: Int) -> Int
  expect x >= 0
  expect y >= 0
  ensure result >= x
  ensure result >= y
given
  x + y"
  
  ast = parse(source)
  result = verify(ast)
  
  assert(result.allProven(), "All contracts should be proven")
  
  TestPass

define testInvariantChecking() -> TestResult
given
  source = "type Positive = Int
  invariant value > 0

define makePositive(x: Int) -> Result[Positive, String]
given
  when x > 0
    Success(x)
  otherwise
    Error('Not positive')"
  
  ast = parse(source)
  result = verify(ast)
  
  # Verification should succeed
  TestPass
```

### 5. End-to-End Tests

Test complete programs.

```vibelang
define testBankTransfer() -> TestResult
given
  account1 = { id: "A1", balance: 1000, owner: "Alice", active: true }
  account2 = { id: "A2", balance: 500, owner: "Bob", active: true }
  
  given transfer(account1, account2, 200)
    Success(receipt) ->
      assert(receipt.amount == 200, "Transfer amount should be 200")
      assert(receipt.fromAccount == "A1", "From account should be A1")
      assert(receipt.toAccount == "A2", "To account should be A2")
      TestPass
    Error(err) ->
      TestFail("Transfer should succeed")

define testPositiveMoney() -> TestResult
given
  given createPositiveMoney(100)
    Success(amount) ->
      assert(amount > 0, "Amount should be positive")
      assert(amount <= 9999999999, "Amount should be within bounds")
      TestPass
    Error(_) ->
      TestFail("Should create valid PositiveMoney")

define testPositiveMoneyInvalid() -> TestResult
given
  given createPositiveMoney(-50)
    Success(_) ->
      TestFail("Should reject negative amount")
    Error(_) ->
      TestPass
```

## Test Framework API

### Assertions

```vibelang
define assert(condition: Bool, message: String) -> Unit
given
  when !condition
    panic(message)
  otherwise
    Unit

define assertEquals[T](actual: T, expected: T, message: String) -> Unit
given
  when actual != expected
    panic(message + ": expected " + expected.toString() + ", got " + actual.toString())
  otherwise
    Unit

define assertNotEquals[T](actual: T, unexpected: T, message: String) -> Unit
given
  when actual == unexpected
    panic(message)
  otherwise
    Unit

define assertTrue(condition: Bool, message: String) -> Unit
given
  assert(condition, message)

define assertFalse(condition: Bool, message: String) -> Unit
given
  assert(!condition, message)
```

### Test Results

```vibelang
type TestResult =
  | TestPass
  | TestFail(String)
  | TestSkip(String)

type TestSuite = {
  name: String,
  tests: Array[(String, () -> TestResult)]
}
```

## Coverage Report

Example coverage report:

```
Coverage Report
===============

File: bank_transfer.vbl
  Lines: 150
  Covered: 142
  Coverage: 94.7%

File: types.vbl
  Lines: 200
  Covered: 195
  Coverage: 97.5%

Total Coverage: 96.1%

Uncovered Lines:
  bank_transfer.vbl:45 - Error case not tested
  types.vbl:123 - Edge case not reached
```

## Continuous Integration

Example CI configuration (`.github/workflows/test.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Install VibeLang
      run: |
        # Install VibeLang compiler
        
    - name: Run tests
      run: vibelang test --coverage
    
    - name: Upload coverage
      run: vibelang coverage upload
```

## Property-Based Testing

VibeLang supports property-based testing:

```vibelang
import test.property

define testAdditionCommutative() -> TestResult
given
  forAll((a: Int, b: Int) ->
    add(a, b) == add(b, a)
  )

define testAdditionAssociative() -> TestResult
given
  forAll((a: Int, b: Int, c: Int) ->
    add(add(a, b), c) == add(a, add(b, c))
  )
```

## Benchmark Tests

```vibelang
import test.bench

define benchmarkAddition() -> BenchResult
given
  benchmark("addition", () ->
    add(1000000, 2000000)
  )

define benchmarkTransfer() -> BenchResult
given
  account1 = createAccount(...)
  account2 = createAccount(...)
  
  benchmark("transfer", () ->
    transfer(account1, account2, 100)
  )
```

## Test Fixtures

```vibelang
define setupTestAccounts() -> (Account, Account)
given
  account1 = { id: "T1", balance: 1000, owner: "Test1", active: true }
  account2 = { id: "T2", balance: 500, owner: "Test2", active: true }
  (account1, account2)

define testWithFixture() -> TestResult
given
  (account1, account2) = setupTestAccounts()
  
  # Use accounts in test
  TestPass
```

## Best Practices

1. **Test Naming**: Use descriptive names starting with `test`
2. **One Assertion Per Test**: Keep tests focused
3. **Test Edge Cases**: Include boundary conditions
4. **Test Error Cases**: Verify error handling
5. **Use Fixtures**: Reuse common test setup
6. **Property Testing**: Use for complex invariants
7. **Coverage Goals**: Aim for >90% coverage
8. **Fast Tests**: Keep unit tests under 100ms

## Future Test Features

- Mutation testing
- Fuzzing integration
- Snapshot testing
- Visual regression testing
- Performance regression detection
