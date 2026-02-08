# VibeLang Standard Library

The VibeLang standard library provides core types, functions, and utilities for VibeLang programs.

## Core Types

### Result Type

The `Result[T, E]` type represents either a successful value or an error.

```vibelang
type Result[T, E] =
  | Success(T)
  | Error(E)
```

**Methods:**

```vibelang
define isSuccess[T, E](result: Result[T, E]) -> Bool
given
  given result
    Success(_) -> true
    Error(_) -> false

define isError[T, E](result: Result[T, E]) -> Bool
given
  given result
    Success(_) -> false
    Error(_) -> true

define unwrap[T, E](result: Result[T, E]) -> T
  expect result.isSuccess()
given
  given result
    Success(value) -> value
    Error(_) -> panic("Called unwrap on Error")

define unwrapOr[T, E](result: Result[T, E], default: T) -> T
given
  given result
    Success(value) -> value
    Error(_) -> default

define map[T, E, U](result: Result[T, E], f: (T) -> U) -> Result[U, E]
given
  given result
    Success(value) -> Success(f(value))
    Error(err) -> Error(err)

define flatMap[T, E, U](result: Result[T, E], f: (T) -> Result[U, E]) -> Result[U, E]
given
  given result
    Success(value) -> f(value)
    Error(err) -> Error(err)
```

### Option Type

The `Option[T]` type represents an optional value.

```vibelang
type Option[T] =
  | Some(T)
  | None

define isSome[T](option: Option[T]) -> Bool
given
  given option
    Some(_) -> true
    None -> false

define isNone[T](option: Option[T]) -> Bool
given
  given option
    Some(_) -> false
    None -> true

define unwrap[T](option: Option[T]) -> T
  expect option.isSome()
given
  given option
    Some(value) -> value
    None -> panic("Called unwrap on None")

define unwrapOr[T](option: Option[T], default: T) -> T
given
  given option
    Some(value) -> value
    None -> default

define map[T, U](option: Option[T], f: (T) -> U) -> Option[U]
given
  given option
    Some(value) -> Some(f(value))
    None -> None

define flatMap[T, U](option: Option[T], f: (T) -> Option[U]) -> Option[U]
given
  given option
    Some(value) -> f(value)
    None -> None
```

## Collections

### Array

```vibelang
define length[T](arr: Array[T]) -> Int
  ensure result >= 0
given
  # Built-in implementation

define get[T](arr: Array[T], index: Int) -> Result[T, String]
  expect index >= 0
  expect index < arr.length()
given
  when index >= 0 && index < arr.length()
    Success(arr[index])
  otherwise
    Error("Index out of bounds")

define map[T, U](arr: Array[T], f: (T) -> U) -> Array[U]
  ensure result.length() == arr.length()
given
  # Built-in implementation

define filter[T](arr: Array[T], predicate: (T) -> Bool) -> Array[T]
  ensure result.length() <= arr.length()
given
  # Built-in implementation

define reduce[T, U](arr: Array[T], initial: U, f: (U, T) -> U) -> U
given
  # Built-in implementation

define find[T](arr: Array[T], predicate: (T) -> Bool) -> Option[T]
given
  # Built-in implementation

define contains[T](arr: Array[T], element: T) -> Bool
given
  # Built-in implementation

define append[T](arr: Array[T], element: T) -> Array[T]
  ensure result.length() == arr.length() + 1
given
  # Built-in implementation

define slice[T](arr: Array[T], start: Int, end: Int) -> Array[T]
  expect start >= 0
  expect end <= arr.length()
  expect start <= end
  ensure result.length() == end - start
given
  # Built-in implementation
```

## String Operations

```vibelang
define length(s: String) -> Int
  ensure result >= 0
given
  # Built-in implementation

define isEmpty(s: String) -> Bool
given
  s.length() == 0

define concat(s1: String, s2: String) -> String
  ensure result.length() == s1.length() + s2.length()
given
  s1 + s2

define substring(s: String, start: Int, end: Int) -> Result[String, String]
  expect start >= 0
  expect end <= s.length()
  expect start <= end
given
  when start >= 0 && end <= s.length() && start <= end
    Success(# Built-in substring)
  otherwise
    Error("Invalid substring range")

define contains(s: String, substring: String) -> Bool
given
  # Built-in implementation

define startsWith(s: String, prefix: String) -> Bool
given
  # Built-in implementation

define endsWith(s: String, suffix: String) -> Bool
given
  # Built-in implementation

define split(s: String, delimiter: String) -> Array[String]
given
  # Built-in implementation

define trim(s: String) -> String
given
  # Built-in implementation

define toUpperCase(s: String) -> String
  ensure result.length() == s.length()
given
  # Built-in implementation

define toLowerCase(s: String) -> String
  ensure result.length() == s.length()
given
  # Built-in implementation
```

## Numeric Operations

```vibelang
define abs(x: Int) -> Int
  ensure result >= 0
  ensure result == x || result == -x
given
  when x >= 0
    x
  otherwise
    -x

define min(a: Int, b: Int) -> Int
  ensure result <= a
  ensure result <= b
  ensure result == a || result == b
given
  when a <= b
    a
  otherwise
    b

define max(a: Int, b: Int) -> Int
  ensure result >= a
  ensure result >= b
  ensure result == a || result == b
given
  when a >= b
    a
  otherwise
    b

define clamp(value: Int, minVal: Int, maxVal: Int) -> Int
  expect minVal <= maxVal
  ensure result >= minVal
  ensure result <= maxVal
given
  when value < minVal
    minVal
  otherwise when value > maxVal
    maxVal
  otherwise
    value

define sqrt(x: Float) -> Result[Float, String]
  expect x >= 0.0
given
  when x >= 0.0
    Success(# Built-in sqrt)
  otherwise
    Error("Cannot take square root of negative number")

define pow(base: Float, exponent: Float) -> Float
given
  # Built-in implementation
```

## Comparison

```vibelang
type Ordering =
  | Less
  | Equal
  | Greater

define compare(a: Int, b: Int) -> Ordering
given
  when a < b
    Less
  otherwise when a > b
    Greater
  otherwise
    Equal
```

## I/O Operations

```vibelang
type IOError =
  | FileNotFound
  | PermissionDenied
  | AlreadyExists
  | Other(String)

define print(message: String) -> Unit
given
  # Built-in implementation

define println(message: String) -> Unit
given
  print(message + "\n")

define readFile(path: String) -> Result[String, IOError]
given
  # Built-in implementation

define writeFile(path: String, content: String) -> Result[Unit, IOError]
given
  # Built-in implementation

define fileExists(path: String) -> Bool
given
  # Built-in implementation
```

## Utility Functions

```vibelang
define panic(message: String) -> Unit
given
  # Built-in panic - terminates program

define assert(condition: Bool, message: String) -> Unit
given
  when !condition
    panic(message)
  otherwise
    Unit

define identity[T](x: T) -> T
given
  x

define const[T, U](x: T, y: U) -> T
given
  x

define compose[A, B, C](f: (B) -> C, g: (A) -> B) -> (A) -> C
given
  (x: A) -> f(g(x))
```

## Type Conversions

```vibelang
define toString(x: Int) -> String
given
  # Built-in implementation

define toInt(s: String) -> Result[Int, String]
given
  # Built-in parsing

define toFloat(s: String) -> Result[Float, String]
given
  # Built-in parsing

define intToFloat(x: Int) -> Float
given
  # Built-in conversion
```

## Time and Randomness

```vibelang
define currentTimestamp() -> Int
  ensure result > 0
given
  # Built-in system time (Unix timestamp)

define randomInt(min: Int, max: Int) -> Int
  expect min <= max
  ensure result >= min
  ensure result <= max
given
  # Built-in random number generator

define randomUUID() -> String
  ensure result.length() == 36
given
  # Built-in UUID generation
```

## Usage Example

```vibelang
import stdlib

define example() -> Result[Unit, String]
given
  # Use Result type
  given divide(10, 2)
    Success(result) ->
      println("Result: " + result.toString())
      Success(Unit)
    Error(msg) ->
      Error(msg)

define processArray(numbers: Array[Int]) -> Int
given
  # Use array operations
  positives = numbers.filter(x -> x > 0)
  sum = positives.reduce(0, (acc, x) -> acc + x)
  sum
```

## Module Organization

```
stdlib/
  ├── core.vbl          # Core types (Result, Option)
  ├── collections.vbl   # Array, List, Set, Map
  ├── string.vbl        # String operations
  ├── math.vbl          # Numeric operations
  ├── io.vbl            # I/O operations
  ├── time.vbl          # Time and date utilities
  └── random.vbl        # Random number generation
```

## Compilation

The standard library is automatically linked with every VibeLang program:

```bash
vibelang compile program.vbl
# stdlib is automatically included
```

To disable automatic stdlib inclusion:

```bash
vibelang compile --no-stdlib program.vbl
```

## Future Additions

Planned standard library additions:

- **Async/Await**: Asynchronous programming primitives
- **Regular Expressions**: Pattern matching for strings
- **JSON**: Parsing and serialization
- **HTTP**: HTTP client and server
- **Testing**: Unit testing framework
- **Benchmarking**: Performance testing utilities
- **Logging**: Structured logging
- **Cryptography**: Hashing and encryption
- **Compression**: Data compression utilities
