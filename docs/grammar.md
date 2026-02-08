# VibeLang Grammar

This document defines the formal grammar of VibeLang using Extended Backus-Naur Form (EBNF).

## Lexical Structure

### Keywords
```
keyword ::= "define" | "type" | "expect" | "ensure" | "invariant" 
          | "given" | "when" | "otherwise" | "import" | "export"
          | "true" | "false" | "self" | "old"
```

### Identifiers
```
identifier ::= letter (letter | digit | "_")*
letter     ::= "a".."z" | "A".."Z"
digit      ::= "0".."9"
```

### Literals
```
integer_literal ::= digit+
float_literal   ::= digit+ "." digit+
string_literal  ::= '"' (character | escape_sequence)* '"'
escape_sequence ::= "\" ("n" | "t" | "r" | '"' | "\")
```

### Operators
```
operator ::= "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<" | ">" 
           | "<=" | ">=" | "&&" | "||" | "!" | "->" | "|" | "&"
```

### Symbols
```
symbol ::= "(" | ")" | "[" | "]" | "{" | "}" | "," | ":" | "." | "=" | "|"
```

## Syntax Structure

### Program
```
program ::= (import_statement)* (top_level_declaration)*

import_statement ::= "import" module_path

top_level_declaration ::= type_declaration
                        | function_declaration
                        | constant_declaration
```

### Type Declarations
```
type_declaration ::= "type" type_name type_parameters? "=" type_definition
                     (invariant_clause)*

type_name ::= identifier

type_parameters ::= "[" identifier ("," identifier)* "]"

type_definition ::= simple_type
                  | sum_type
                  | refined_type

simple_type ::= type_name (type_arguments)?

type_arguments ::= "[" type ("," type)* "]"

sum_type ::= "|" variant ("|" variant)*

variant ::= identifier ("(" type ("," type)* ")")?

refined_type ::= base_type "where" expression

invariant_clause ::= "invariant" expression
```

### Function Declarations
```
function_declaration ::= "define" function_name "(" parameters? ")" 
                        "->" return_type
                        (contract_clause)*
                        "given" block

function_name ::= identifier

parameters ::= parameter ("," parameter)*

parameter ::= identifier ":" type

return_type ::= type

contract_clause ::= expect_clause | ensure_clause

expect_clause ::= "expect" expression

ensure_clause ::= "ensure" expression
```

### Expressions
```
expression ::= literal
             | identifier
             | function_call
             | binary_expression
             | unary_expression
             | when_expression
             | given_expression
             | array_literal
             | member_access
             | "(" expression ")"

literal ::= integer_literal | float_literal | string_literal | bool_literal

bool_literal ::= "true" | "false"

function_call ::= identifier "(" arguments? ")"

arguments ::= expression ("," expression)*

binary_expression ::= expression operator expression

unary_expression ::= operator expression

member_access ::= expression "." identifier

array_literal ::= "[" (expression ("," expression)*)? "]"
```

### Control Flow
```
when_expression ::= "when" expression block ("otherwise" block)?

given_expression ::= "given" expression pattern_match+

pattern_match ::= pattern "->" expression

pattern ::= identifier "(" pattern ("," pattern)* ")"
          | identifier
          | literal
          | "_"
```

### Statements and Blocks
```
block ::= statement+

statement ::= expression
            | let_binding
            | assignment
            | return_statement

let_binding ::= identifier "=" expression

assignment ::= identifier "=" expression

return_statement ::= expression
```

### Types
```
type ::= primitive_type
       | type_name (type_arguments)?
       | function_type
       | array_type
       | result_type

primitive_type ::= "Int" | "Float" | "Bool" | "String" | "Byte" | "Unit"

function_type ::= "(" type ("," type)* ")" "->" type

array_type ::= "Array" "[" type "]"

result_type ::= "Result" "[" type "," type "]"
```

## Indentation Rules

VibeLang uses significant indentation with 2 spaces per level:

```
indentation ::= "  " (indentation)?
```

The parser enforces:
- Each nested block must be indented exactly 2 spaces more than its parent
- All statements at the same level must have the same indentation
- Mixing tabs and spaces is not allowed

## Comments

```
comment ::= "#" (any_character)* newline
          | "##" (any_character | newline)* "##"
```

Single-line comments start with `#` and extend to the end of the line.
Multi-line comments are enclosed in `##`.

## Example Grammar Usage

```vibelang
# Type declaration with invariant
type PositiveMoney = Int
  invariant value > 0

# Function with contracts
define transfer(amount: PositiveMoney) -> Result[Unit, Error]
  expect amount > 0
  ensure balance >= 0
given
  when amount <= balance
    Success(Unit)
  otherwise
    Error(InsufficientFunds)
```

## Operator Precedence

From highest to lowest:

1. Member access (`.`)
2. Function call, array indexing
3. Unary operators (`!`, `-`)
4. Multiplicative (`*`, `/`, `%`)
5. Additive (`+`, `-`)
6. Comparison (`<`, `>`, `<=`, `>=`)
7. Equality (`==`, `!=`)
8. Logical AND (`&&`)
9. Logical OR (`||`)
10. Arrow (`->`)

## Reserved Words

The following words are reserved and cannot be used as identifiers:

```
define, type, expect, ensure, invariant, given, when, otherwise,
import, export, true, false, self, old, Int, Float, Bool, String,
Byte, Unit, Array, Result, Success, Error
```

## Whitespace

- Spaces and tabs for indentation (2 spaces required)
- Newlines separate statements
- Blank lines are ignored
- Whitespace around operators is optional but recommended for readability
