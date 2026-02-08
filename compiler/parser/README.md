# VibeLang Parser

The parser is the second stage of the VibeLang compiler pipeline. It transforms a stream of tokens from the lexer into an Abstract Syntax Tree (AST).

## Overview

The parser uses recursive descent parsing to build an AST that represents the structure of VibeLang programs. It enforces:
- Syntax rules
- Proper nesting of constructs
- Type annotation requirements
- Contract placement rules

## AST Node Types

```python
from dataclasses import dataclass
from typing import List, Optional, Union
from enum import Enum

# Base AST Node
@dataclass
class ASTNode:
    line: int
    column: int

# Program
@dataclass
class Program(ASTNode):
    imports: List['ImportStatement']
    declarations: List[Union['TypeDeclaration', 'FunctionDeclaration']]

# Import Statement
@dataclass
class ImportStatement(ASTNode):
    module_path: str

# Type Declarations
@dataclass
class TypeDeclaration(ASTNode):
    name: str
    type_params: List[str]
    definition: 'TypeDefinition'
    invariants: List['Expression']

@dataclass
class SimpleType(ASTNode):
    name: str
    type_args: List['Type']

@dataclass
class SumType(ASTNode):
    variants: List['Variant']

@dataclass
class Variant(ASTNode):
    name: str
    parameters: List['Type']

@dataclass
class RefinedType(ASTNode):
    base_type: 'Type'
    condition: 'Expression'

# Function Declarations
@dataclass
class FunctionDeclaration(ASTNode):
    name: str
    parameters: List['Parameter']
    return_type: 'Type'
    preconditions: List['Expression']
    postconditions: List['Expression']
    body: 'Block'

@dataclass
class Parameter(ASTNode):
    name: str
    type_annotation: 'Type'

# Types
@dataclass
class Type(ASTNode):
    pass

@dataclass
class PrimitiveType(Type):
    name: str  # Int, Float, Bool, String, Byte, Unit

@dataclass
class ArrayType(Type):
    element_type: 'Type'

@dataclass
class ResultType(Type):
    success_type: 'Type'
    error_type: 'Type'

@dataclass
class FunctionType(Type):
    param_types: List['Type']
    return_type: 'Type'

@dataclass
class NamedType(Type):
    name: str
    type_args: List['Type']

# Expressions
@dataclass
class Expression(ASTNode):
    pass

@dataclass
class IntegerLiteral(Expression):
    value: int

@dataclass
class FloatLiteral(Expression):
    value: float

@dataclass
class StringLiteral(Expression):
    value: str

@dataclass
class BoolLiteral(Expression):
    value: bool

@dataclass
class Identifier(Expression):
    name: str

@dataclass
class BinaryOp(Expression):
    left: Expression
    operator: str
    right: Expression

@dataclass
class UnaryOp(Expression):
    operator: str
    operand: Expression

@dataclass
class FunctionCall(Expression):
    function: Expression
    arguments: List[Expression]

@dataclass
class MemberAccess(Expression):
    object: Expression
    member: str

@dataclass
class ArrayLiteral(Expression):
    elements: List[Expression]

@dataclass
class RecordLiteral(Expression):
    fields: List[tuple[str, Expression]]

@dataclass
class WhenExpression(Expression):
    condition: Expression
    then_block: 'Block'
    else_block: Optional['Block']

@dataclass
class GivenExpression(Expression):
    scrutinee: Expression
    cases: List['PatternCase']

@dataclass
class PatternCase(ASTNode):
    pattern: 'Pattern'
    expression: Expression

# Patterns
@dataclass
class Pattern(ASTNode):
    pass

@dataclass
class ConstructorPattern(Pattern):
    constructor: str
    parameters: List['Pattern']

@dataclass
class IdentifierPattern(Pattern):
    name: str

@dataclass
class LiteralPattern(Pattern):
    value: Union[int, float, str, bool]

@dataclass
class WildcardPattern(Pattern):
    pass

# Statements
@dataclass
class Statement(ASTNode):
    pass

@dataclass
class Block(Statement):
    statements: List[Statement]

@dataclass
class LetBinding(Statement):
    name: str
    type_annotation: Optional['Type']
    value: Expression

@dataclass
class Assignment(Statement):
    target: str
    value: Expression

@dataclass
class ExpressionStatement(Statement):
    expression: Expression
```

## Parser Implementation

```python
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
        
    def peek(self, offset: int = 0) -> Token:
        """Look ahead at token without consuming it"""
        pos = self.position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]  # Return EOF
    
    def advance(self) -> Token:
        """Consume and return current token"""
        token = self.peek()
        if token.type != TokenType.EOF:
            self.position += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        """Consume token of expected type or raise error"""
        token = self.peek()
        if token.type != token_type:
            raise ParseError(f"Expected {token_type}, got {token.type} at {token.line}:{token.column}")
        return self.advance()
    
    def skip_newlines(self):
        """Skip newline tokens"""
        while self.peek().type == TokenType.NEWLINE:
            self.advance()
    
    def parse(self) -> Program:
        """Parse entire program"""
        imports = []
        declarations = []
        
        self.skip_newlines()
        
        # Parse imports
        while self.peek().type == TokenType.IMPORT:
            imports.append(self.parse_import())
            self.skip_newlines()
        
        # Parse declarations
        while self.peek().type != TokenType.EOF:
            if self.peek().type == TokenType.TYPE:
                declarations.append(self.parse_type_declaration())
            elif self.peek().type == TokenType.DEFINE:
                declarations.append(self.parse_function_declaration())
            else:
                raise ParseError(f"Unexpected token {self.peek().type}")
            
            self.skip_newlines()
        
        return Program(imports=imports, declarations=declarations, line=1, column=1)
    
    def parse_import(self) -> ImportStatement:
        """Parse import statement"""
        import_token = self.expect(TokenType.IMPORT)
        
        # Parse module path (series of identifiers separated by dots)
        path_parts = []
        path_parts.append(self.expect(TokenType.IDENTIFIER).value)
        
        while self.peek().type == TokenType.DOT:
            self.advance()
            path_parts.append(self.expect(TokenType.IDENTIFIER).value)
        
        module_path = ".".join(path_parts)
        
        return ImportStatement(module_path=module_path, line=import_token.line, column=import_token.column)
    
    def parse_type_declaration(self) -> TypeDeclaration:
        """Parse type declaration"""
        type_token = self.expect(TokenType.TYPE)
        name = self.expect(TokenType.IDENTIFIER).value
        
        # Parse optional type parameters
        type_params = []
        if self.peek().type == TokenType.LBRACKET:
            self.advance()
            type_params.append(self.expect(TokenType.IDENTIFIER).value)
            
            while self.peek().type == TokenType.COMMA:
                self.advance()
                type_params.append(self.expect(TokenType.IDENTIFIER).value)
            
            self.expect(TokenType.RBRACKET)
        
        self.expect(TokenType.ASSIGN)
        
        # Parse type definition
        definition = self.parse_type_definition()
        
        # Parse invariants
        invariants = []
        while self.peek().type == TokenType.INVARIANT:
            self.advance()
            invariants.append(self.parse_expression())
            self.skip_newlines()
        
        return TypeDeclaration(
            name=name,
            type_params=type_params,
            definition=definition,
            invariants=invariants,
            line=type_token.line,
            column=type_token.column
        )
    
    def parse_function_declaration(self) -> FunctionDeclaration:
        """Parse function declaration"""
        define_token = self.expect(TokenType.DEFINE)
        name = self.expect(TokenType.IDENTIFIER).value
        
        # Parse parameters
        self.expect(TokenType.LPAREN)
        parameters = []
        
        if self.peek().type != TokenType.RPAREN:
            parameters.append(self.parse_parameter())
            
            while self.peek().type == TokenType.COMMA:
                self.advance()
                parameters.append(self.parse_parameter())
        
        self.expect(TokenType.RPAREN)
        
        # Parse return type
        self.expect(TokenType.ARROW)
        return_type = self.parse_type()
        
        self.skip_newlines()
        
        # Parse contracts (expect and ensure)
        preconditions = []
        postconditions = []
        
        while self.peek().type in [TokenType.EXPECT, TokenType.ENSURE]:
            if self.peek().type == TokenType.EXPECT:
                self.advance()
                preconditions.append(self.parse_expression())
            else:  # ENSURE
                self.advance()
                postconditions.append(self.parse_expression())
            
            self.skip_newlines()
        
        # Parse body
        self.expect(TokenType.GIVEN)
        self.skip_newlines()
        body = self.parse_block()
        
        return FunctionDeclaration(
            name=name,
            parameters=parameters,
            return_type=return_type,
            preconditions=preconditions,
            postconditions=postconditions,
            body=body,
            line=define_token.line,
            column=define_token.column
        )
    
    def parse_parameter(self) -> Parameter:
        """Parse function parameter"""
        name_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.COLON)
        type_annotation = self.parse_type()
        
        return Parameter(
            name=name_token.value,
            type_annotation=type_annotation,
            line=name_token.line,
            column=name_token.column
        )
    
    def parse_type(self) -> Type:
        """Parse type annotation"""
        token = self.peek()
        
        # Primitive types
        if token.type in [TokenType.INT, TokenType.FLOAT, TokenType.BOOL, 
                          TokenType.STRING, TokenType.BYTE, TokenType.UNIT]:
            self.advance()
            return PrimitiveType(name=token.value, line=token.line, column=token.column)
        
        # Array type
        if token.type == TokenType.ARRAY:
            self.advance()
            self.expect(TokenType.LBRACKET)
            element_type = self.parse_type()
            self.expect(TokenType.RBRACKET)
            return ArrayType(element_type=element_type, line=token.line, column=token.column)
        
        # Result type
        if token.type == TokenType.RESULT:
            self.advance()
            self.expect(TokenType.LBRACKET)
            success_type = self.parse_type()
            self.expect(TokenType.COMMA)
            error_type = self.parse_type()
            self.expect(TokenType.RBRACKET)
            return ResultType(
                success_type=success_type,
                error_type=error_type,
                line=token.line,
                column=token.column
            )
        
        # Named type
        if token.type == TokenType.IDENTIFIER:
            name = self.advance().value
            type_args = []
            
            if self.peek().type == TokenType.LBRACKET:
                self.advance()
                type_args.append(self.parse_type())
                
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    type_args.append(self.parse_type())
                
                self.expect(TokenType.RBRACKET)
            
            return NamedType(name=name, type_args=type_args, line=token.line, column=token.column)
        
        raise ParseError(f"Expected type, got {token.type}")
    
    def parse_expression(self) -> Expression:
        """Parse expression (with operator precedence)"""
        return self.parse_logical_or()
    
    def parse_logical_or(self) -> Expression:
        """Parse logical OR expression"""
        left = self.parse_logical_and()
        
        while self.peek().type == TokenType.OR:
            op_token = self.advance()
            right = self.parse_logical_and()
            left = BinaryOp(left=left, operator="||", right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_logical_and(self) -> Expression:
        """Parse logical AND expression"""
        left = self.parse_equality()
        
        while self.peek().type == TokenType.AND:
            op_token = self.advance()
            right = self.parse_equality()
            left = BinaryOp(left=left, operator="&&", right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_equality(self) -> Expression:
        """Parse equality expression"""
        left = self.parse_comparison()
        
        while self.peek().type in [TokenType.EQ, TokenType.NEQ]:
            op_token = self.advance()
            right = self.parse_comparison()
            left = BinaryOp(left=left, operator=op_token.value, right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_comparison(self) -> Expression:
        """Parse comparison expression"""
        left = self.parse_additive()
        
        while self.peek().type in [TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE]:
            op_token = self.advance()
            right = self.parse_additive()
            left = BinaryOp(left=left, operator=op_token.value, right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_additive(self) -> Expression:
        """Parse additive expression"""
        left = self.parse_multiplicative()
        
        while self.peek().type in [TokenType.PLUS, TokenType.MINUS]:
            op_token = self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(left=left, operator=op_token.value, right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_multiplicative(self) -> Expression:
        """Parse multiplicative expression"""
        left = self.parse_unary()
        
        while self.peek().type in [TokenType.STAR, TokenType.SLASH, TokenType.PERCENT]:
            op_token = self.advance()
            right = self.parse_unary()
            left = BinaryOp(left=left, operator=op_token.value, right=right, line=op_token.line, column=op_token.column)
        
        return left
    
    def parse_unary(self) -> Expression:
        """Parse unary expression"""
        if self.peek().type in [TokenType.NOT, TokenType.MINUS]:
            op_token = self.advance()
            operand = self.parse_unary()
            return UnaryOp(operator=op_token.value, operand=operand, line=op_token.line, column=op_token.column)
        
        return self.parse_postfix()
    
    def parse_postfix(self) -> Expression:
        """Parse postfix expression (function calls, member access, etc.)"""
        expr = self.parse_primary()
        
        while True:
            if self.peek().type == TokenType.LPAREN:
                # Function call
                self.advance()
                arguments = []
                
                if self.peek().type != TokenType.RPAREN:
                    arguments.append(self.parse_expression())
                    
                    while self.peek().type == TokenType.COMMA:
                        self.advance()
                        arguments.append(self.parse_expression())
                
                self.expect(TokenType.RPAREN)
                expr = FunctionCall(function=expr, arguments=arguments, line=expr.line, column=expr.column)
            
            elif self.peek().type == TokenType.DOT:
                # Member access
                self.advance()
                member_token = self.expect(TokenType.IDENTIFIER)
                expr = MemberAccess(object=expr, member=member_token.value, line=expr.line, column=expr.column)
            
            else:
                break
        
        return expr
    
    def parse_primary(self) -> Expression:
        """Parse primary expression"""
        token = self.peek()
        
        # Literals
        if token.type == TokenType.INTEGER_LITERAL:
            self.advance()
            return IntegerLiteral(value=int(token.value), line=token.line, column=token.column)
        
        if token.type == TokenType.FLOAT_LITERAL:
            self.advance()
            return FloatLiteral(value=float(token.value), line=token.line, column=token.column)
        
        if token.type == TokenType.STRING_LITERAL:
            self.advance()
            return StringLiteral(value=token.value, line=token.line, column=token.column)
        
        if token.type in [TokenType.TRUE, TokenType.FALSE]:
            self.advance()
            return BoolLiteral(value=(token.type == TokenType.TRUE), line=token.line, column=token.column)
        
        # Identifier
        if token.type == TokenType.IDENTIFIER:
            self.advance()
            return Identifier(name=token.value, line=token.line, column=token.column)
        
        # When expression
        if token.type == TokenType.WHEN:
            return self.parse_when_expression()
        
        # Given expression
        if token.type == TokenType.GIVEN:
            return self.parse_given_expression()
        
        # Parenthesized expression
        if token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        
        raise ParseError(f"Unexpected token {token.type} at {token.line}:{token.column}")
    
    def parse_when_expression(self) -> WhenExpression:
        """Parse when/otherwise expression"""
        when_token = self.expect(TokenType.WHEN)
        condition = self.parse_expression()
        self.skip_newlines()
        
        then_block = self.parse_block()
        
        else_block = None
        if self.peek().type == TokenType.OTHERWISE:
            self.advance()
            self.skip_newlines()
            else_block = self.parse_block()
        
        return WhenExpression(
            condition=condition,
            then_block=then_block,
            else_block=else_block,
            line=when_token.line,
            column=when_token.column
        )
    
    def parse_given_expression(self) -> GivenExpression:
        """Parse given (pattern matching) expression"""
        given_token = self.expect(TokenType.GIVEN)
        scrutinee = self.parse_expression()
        self.skip_newlines()
        
        cases = []
        while self.peek().type == TokenType.IDENTIFIER or self.peek().type == TokenType.INTEGER_LITERAL:
            pattern = self.parse_pattern()
            self.expect(TokenType.ARROW)
            expression = self.parse_expression()
            cases.append(PatternCase(pattern=pattern, expression=expression, line=pattern.line, column=pattern.column))
            self.skip_newlines()
        
        return GivenExpression(
            scrutinee=scrutinee,
            cases=cases,
            line=given_token.line,
            column=given_token.column
        )
    
    def parse_pattern(self) -> Pattern:
        """Parse pattern"""
        token = self.peek()
        
        if token.type == TokenType.IDENTIFIER:
            name = self.advance().value
            
            # Constructor pattern
            if self.peek().type == TokenType.LPAREN:
                self.advance()
                params = []
                
                if self.peek().type != TokenType.RPAREN:
                    params.append(self.parse_pattern())
                    
                    while self.peek().type == TokenType.COMMA:
                        self.advance()
                        params.append(self.parse_pattern())
                
                self.expect(TokenType.RPAREN)
                return ConstructorPattern(constructor=name, parameters=params, line=token.line, column=token.column)
            
            # Simple identifier pattern
            return IdentifierPattern(name=name, line=token.line, column=token.column)
        
        # Literal pattern
        if token.type in [TokenType.INTEGER_LITERAL, TokenType.FLOAT_LITERAL, TokenType.STRING_LITERAL]:
            self.advance()
            value = token.value
            if token.type == TokenType.INTEGER_LITERAL:
                value = int(value)
            elif token.type == TokenType.FLOAT_LITERAL:
                value = float(value)
            return LiteralPattern(value=value, line=token.line, column=token.column)
        
        raise ParseError(f"Expected pattern, got {token.type}")
    
    def parse_block(self) -> Block:
        """Parse block of statements"""
        statements = []
        
        if self.peek().type == TokenType.INDENT:
            self.advance()
            
            while self.peek().type not in [TokenType.DEDENT, TokenType.EOF]:
                statements.append(self.parse_statement())
                self.skip_newlines()
            
            if self.peek().type == TokenType.DEDENT:
                self.advance()
        else:
            # Single statement (no indentation)
            statements.append(self.parse_statement())
        
        return Block(statements=statements, line=statements[0].line if statements else 0, column=0)
    
    def parse_statement(self) -> Statement:
        """Parse statement"""
        # Expression statement (default)
        expr = self.parse_expression()
        return ExpressionStatement(expression=expr, line=expr.line, column=expr.column)

class ParseError(Exception):
    """Parser error exception"""
    pass
```

## Usage

```python
lexer = Lexer(source_code)
tokens = lexer.tokenize()

parser = Parser(tokens)
ast = parser.parse()

# Traverse AST
for declaration in ast.declarations:
    if isinstance(declaration, FunctionDeclaration):
        print(f"Function: {declaration.name}")
    elif isinstance(declaration, TypeDeclaration):
        print(f"Type: {declaration.name}")
```

## Error Handling

The parser reports errors for:
- Missing required tokens (parentheses, brackets, etc.)
- Unexpected tokens
- Malformed expressions
- Invalid type annotations
- Missing contracts in appropriate contexts

## Future Enhancements

- Better error messages with context
- Error recovery to continue parsing after errors
- Syntax sugar desugaring
- Macro expansion
- AST validation pass
