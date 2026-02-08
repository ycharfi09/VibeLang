"""VibeLang Parser - transforms tokens into an Abstract Syntax Tree."""

from typing import List, Union

from compiler.lexer.lexer import Token, TokenType
from .ast_nodes import (
    ASTNode, Program, ImportStatement,
    TypeDeclaration, SimpleType, SumType, Variant, RefinedType,
    FunctionDeclaration, Parameter,
    Type, PrimitiveType, ArrayType, ResultType, FunctionType, NamedType,
    Expression, IntegerLiteral, FloatLiteral, StringLiteral, BoolLiteral,
    Identifier, BinaryOp, UnaryOp, FunctionCall, MemberAccess,
    ArrayLiteral, RecordLiteral, WhenExpression, GivenExpression, PatternCase,
    Pattern, ConstructorPattern, IdentifierPattern, LiteralPattern, WildcardPattern,
    Statement, Block, LetBinding, Assignment, ExpressionStatement,
)


class ParseError(Exception):
    """Parser error exception."""
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------

    def peek(self, offset: int = 0) -> Token:
        """Look ahead at token without consuming it."""
        pos = self.position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]  # Return EOF

    def advance(self) -> Token:
        """Consume and return current token."""
        token = self.peek()
        if token.type != TokenType.EOF:
            self.position += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        """Consume token of expected type or raise error."""
        token = self.peek()
        if token.type != token_type:
            raise ParseError(
                f"Expected {token_type}, got {token.type} at {token.line}:{token.column}"
            )
        return self.advance()

    def skip_newlines(self):
        """Skip newline tokens."""
        while self.peek().type == TokenType.NEWLINE:
            self.advance()

    # ------------------------------------------------------------------
    # Top-level
    # ------------------------------------------------------------------

    def parse(self) -> Program:
        """Parse entire program."""
        imports: List[ImportStatement] = []
        declarations: List[Union[TypeDeclaration, FunctionDeclaration]] = []

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

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def parse_import(self) -> ImportStatement:
        """Parse import statement."""
        import_token = self.expect(TokenType.IMPORT)

        path_parts = [self.expect(TokenType.IDENTIFIER).value]

        while self.peek().type == TokenType.DOT:
            self.advance()
            path_parts.append(self.expect(TokenType.IDENTIFIER).value)

        module_path = ".".join(path_parts)
        return ImportStatement(
            module_path=module_path,
            line=import_token.line,
            column=import_token.column,
        )

    # ------------------------------------------------------------------
    # Type declarations
    # ------------------------------------------------------------------

    def parse_type_declaration(self) -> TypeDeclaration:
        """Parse type declaration."""
        type_token = self.expect(TokenType.TYPE)

        # The type name may be a keyword like Result or Array
        name_token = self.peek()
        if name_token.type == TokenType.IDENTIFIER:
            name = self.advance().value
        elif name_token.type in (
            TokenType.RESULT, TokenType.ARRAY,
            TokenType.INT, TokenType.FLOAT, TokenType.BOOL,
            TokenType.STRING, TokenType.BYTE, TokenType.UNIT,
        ):
            name = self.advance().value
        else:
            raise ParseError(
                f"Expected type name, got {name_token.type} at {name_token.line}:{name_token.column}"
            )

        # Optional type parameters  e.g. [T, E]
        type_params: List[str] = []
        if self.peek().type == TokenType.LBRACKET:
            self.advance()
            type_params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.peek().type == TokenType.COMMA:
                self.advance()
                type_params.append(self.expect(TokenType.IDENTIFIER).value)
            self.expect(TokenType.RBRACKET)

        self.expect(TokenType.ASSIGN)

        # Parse type definition body
        definition = self.parse_type_definition()

        # Parse invariants (may be indented)
        invariants: List[Expression] = []
        self.skip_newlines()
        has_indent = False
        if self.peek().type == TokenType.INDENT:
            self.advance()
            has_indent = True
        while self.peek().type == TokenType.INVARIANT:
            self.advance()
            invariants.append(self.parse_expression())
            self.skip_newlines()
        if has_indent and self.peek().type == TokenType.DEDENT:
            self.advance()

        return TypeDeclaration(
            name=name,
            type_params=type_params,
            definition=definition,
            invariants=invariants,
            line=type_token.line,
            column=type_token.column,
        )

    def parse_type_definition(self) -> Union[SumType, SimpleType]:
        """Parse the right-hand side of a type declaration after '='.

        Handles:
          - Sum types:  | Variant1(T) | Variant2(T)
          - Record types: { field: Type, ... }  (represented as SimpleType)
          - Simple named types with optional type args
        """
        self.skip_newlines()

        # Type definition body may be wrapped in INDENT/DEDENT
        has_indent = False
        if self.peek().type == TokenType.INDENT:
            self.advance()
            has_indent = True

        result = self._parse_type_definition_inner()

        self.skip_newlines()
        if has_indent and self.peek().type == TokenType.DEDENT:
            self.advance()

        return result

    def _parse_type_definition_inner(self) -> Union[SumType, SimpleType]:
        """Parse the actual type definition content."""
        # Sum type: starts with '|'
        if self.peek().type == TokenType.PIPE:
            return self._parse_sum_type()

        # Record type: starts with '{'
        if self.peek().type == TokenType.LBRACE:
            return self._parse_record_type_definition()

        # Simple type reference (identifier with optional type args)
        token = self.peek()
        if token.type == TokenType.IDENTIFIER:
            name = self.advance().value
            type_args: List[Type] = []
            if self.peek().type == TokenType.LBRACKET:
                self.advance()
                type_args.append(self.parse_type())
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    type_args.append(self.parse_type())
                self.expect(TokenType.RBRACKET)
            return SimpleType(
                name=name,
                type_args=type_args,
                line=token.line,
                column=token.column,
            )

        # Also allow primitive-keyword based type definitions
        if token.type in (
            TokenType.INT, TokenType.FLOAT, TokenType.BOOL,
            TokenType.STRING, TokenType.BYTE, TokenType.UNIT,
            TokenType.ARRAY, TokenType.RESULT,
        ):
            self.advance()
            return SimpleType(
                name=token.value,
                type_args=[],
                line=token.line,
                column=token.column,
            )

        raise ParseError(
            f"Expected type definition, got {token.type} at {token.line}:{token.column}"
        )

    def _parse_sum_type(self) -> SumType:
        """Parse sum type variants:  | A(T) | B(T, U) ..."""
        first_pipe = self.peek()
        variants: List[Variant] = []

        while self.peek().type == TokenType.PIPE:
            self.advance()  # consume '|'
            self.skip_newlines()
            variant_token = self.expect(TokenType.IDENTIFIER)
            params: List[Type] = []

            if self.peek().type == TokenType.LPAREN:
                self.advance()
                if self.peek().type != TokenType.RPAREN:
                    params.append(self.parse_type())
                    while self.peek().type == TokenType.COMMA:
                        self.advance()
                        params.append(self.parse_type())
                self.expect(TokenType.RPAREN)

            variants.append(Variant(
                name=variant_token.value,
                parameters=params,
                line=variant_token.line,
                column=variant_token.column,
            ))
            self.skip_newlines()

        return SumType(
            variants=variants,
            line=first_pipe.line,
            column=first_pipe.column,
        )

    def _parse_record_type_definition(self) -> SimpleType:
        """Parse record-style type definition: { field: Type, ... }

        Represented as a SimpleType with name='Record' for now.
        """
        lbrace = self.expect(TokenType.LBRACE)
        self.skip_newlines()

        # We store field types as type_args (minimal representation)
        type_args: List[Type] = []
        while self.peek().type != TokenType.RBRACE:
            self.expect(TokenType.IDENTIFIER)  # field name
            self.expect(TokenType.COLON)
            type_args.append(self.parse_type())
            self.skip_newlines()
            if self.peek().type == TokenType.COMMA:
                self.advance()
                self.skip_newlines()

        self.expect(TokenType.RBRACE)
        return SimpleType(
            name="Record",
            type_args=type_args,
            line=lbrace.line,
            column=lbrace.column,
        )

    # ------------------------------------------------------------------
    # Function declarations
    # ------------------------------------------------------------------

    def parse_function_declaration(self) -> FunctionDeclaration:
        """Parse function declaration."""
        define_token = self.expect(TokenType.DEFINE)
        name = self.expect(TokenType.IDENTIFIER).value

        # Parameters
        self.expect(TokenType.LPAREN)
        parameters: List[Parameter] = []

        if self.peek().type != TokenType.RPAREN:
            parameters.append(self.parse_parameter())
            while self.peek().type == TokenType.COMMA:
                self.advance()
                parameters.append(self.parse_parameter())

        self.expect(TokenType.RPAREN)

        # Return type
        self.expect(TokenType.ARROW)
        return_type = self.parse_type()

        self.skip_newlines()

        # The function body (contracts + given block) is typically indented
        has_outer_indent = False
        if self.peek().type == TokenType.INDENT:
            self.advance()
            has_outer_indent = True

        # Contracts
        preconditions: List[Expression] = []
        postconditions: List[Expression] = []

        while self.peek().type in (TokenType.EXPECT, TokenType.ENSURE):
            if self.peek().type == TokenType.EXPECT:
                self.advance()
                preconditions.append(self.parse_expression())
            else:
                self.advance()
                postconditions.append(self.parse_expression())
            self.skip_newlines()

        # Close the outer indent that wrapped the contracts
        if has_outer_indent and self.peek().type == TokenType.DEDENT:
            self.advance()
            has_outer_indent = False

        self.skip_newlines()

        # Body
        self.expect(TokenType.GIVEN)
        self.skip_newlines()
        body = self.parse_block()

        if has_outer_indent and self.peek().type == TokenType.DEDENT:
            self.advance()

        return FunctionDeclaration(
            name=name,
            parameters=parameters,
            return_type=return_type,
            preconditions=preconditions,
            postconditions=postconditions,
            body=body,
            line=define_token.line,
            column=define_token.column,
        )

    def parse_parameter(self) -> Parameter:
        """Parse function parameter."""
        name_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.COLON)
        type_annotation = self.parse_type()
        return Parameter(
            name=name_token.value,
            type_annotation=type_annotation,
            line=name_token.line,
            column=name_token.column,
        )

    # ------------------------------------------------------------------
    # Types
    # ------------------------------------------------------------------

    def parse_type(self) -> Type:
        """Parse type annotation."""
        token = self.peek()

        # Primitive types
        if token.type in (
            TokenType.INT, TokenType.FLOAT, TokenType.BOOL,
            TokenType.STRING, TokenType.BYTE, TokenType.UNIT,
        ):
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
                column=token.column,
            )

        # Named type
        if token.type == TokenType.IDENTIFIER:
            name = self.advance().value
            type_args: List[Type] = []

            if self.peek().type == TokenType.LBRACKET:
                self.advance()
                type_args.append(self.parse_type())
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    type_args.append(self.parse_type())
                self.expect(TokenType.RBRACKET)

            return NamedType(name=name, type_args=type_args, line=token.line, column=token.column)

        raise ParseError(f"Expected type, got {token.type} at {token.line}:{token.column}")

    # ------------------------------------------------------------------
    # Expressions — operator precedence (lowest → highest)
    # ------------------------------------------------------------------

    def parse_expression(self) -> Expression:
        """Parse expression (entry point for precedence climbing)."""
        return self.parse_logical_or()

    def parse_logical_or(self) -> Expression:
        left = self.parse_logical_and()

        while self.peek().type == TokenType.OR:
            op_token = self.advance()
            right = self.parse_logical_and()
            left = BinaryOp(
                left=left, operator="||", right=right,
                line=op_token.line, column=op_token.column,
            )
        return left

    def parse_logical_and(self) -> Expression:
        left = self.parse_equality()

        while self.peek().type == TokenType.AND:
            op_token = self.advance()
            right = self.parse_equality()
            left = BinaryOp(
                left=left, operator="&&", right=right,
                line=op_token.line, column=op_token.column,
            )
        return left

    def parse_equality(self) -> Expression:
        left = self.parse_comparison()

        while self.peek().type in (TokenType.EQ, TokenType.NEQ):
            op_token = self.advance()
            right = self.parse_comparison()
            left = BinaryOp(
                left=left, operator=op_token.value, right=right,
                line=op_token.line, column=op_token.column,
            )
        return left

    def parse_comparison(self) -> Expression:
        left = self.parse_additive()

        while self.peek().type in (TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE):
            op_token = self.advance()
            right = self.parse_additive()
            left = BinaryOp(
                left=left, operator=op_token.value, right=right,
                line=op_token.line, column=op_token.column,
            )
        return left

    def parse_additive(self) -> Expression:
        left = self.parse_multiplicative()

        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(
                left=left, operator=op_token.value, right=right,
                line=op_token.line, column=op_token.column,
            )
        return left

    def parse_multiplicative(self) -> Expression:
        left = self.parse_unary()

        while self.peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_token = self.advance()
            right = self.parse_unary()
            left = BinaryOp(
                left=left, operator=op_token.value, right=right,
                line=op_token.line, column=op_token.column,
            )
        return left

    def parse_unary(self) -> Expression:
        if self.peek().type in (TokenType.NOT, TokenType.MINUS):
            op_token = self.advance()
            operand = self.parse_unary()
            return UnaryOp(
                operator=op_token.value, operand=operand,
                line=op_token.line, column=op_token.column,
            )
        return self.parse_postfix()

    # ------------------------------------------------------------------
    # Postfix / Primary
    # ------------------------------------------------------------------

    def parse_postfix(self) -> Expression:
        """Parse postfix expressions (function calls, member access)."""
        expr = self.parse_primary()

        while True:
            if self.peek().type == TokenType.LPAREN:
                self.advance()
                arguments: List[Expression] = []

                if self.peek().type != TokenType.RPAREN:
                    arguments.append(self.parse_expression())
                    while self.peek().type == TokenType.COMMA:
                        self.advance()
                        arguments.append(self.parse_expression())

                self.expect(TokenType.RPAREN)
                expr = FunctionCall(
                    function=expr, arguments=arguments,
                    line=expr.line, column=expr.column,
                )
            elif self.peek().type == TokenType.DOT:
                self.advance()
                member_token = self.expect(TokenType.IDENTIFIER)
                expr = MemberAccess(
                    obj=expr, member=member_token.value,
                    line=expr.line, column=expr.column,
                )
            else:
                break

        return expr

    def parse_primary(self) -> Expression:
        """Parse primary expression."""
        token = self.peek()

        # Integer literal
        if token.type == TokenType.INTEGER_LITERAL:
            self.advance()
            return IntegerLiteral(value=int(token.value), line=token.line, column=token.column)

        # Float literal
        if token.type == TokenType.FLOAT_LITERAL:
            self.advance()
            return FloatLiteral(value=float(token.value), line=token.line, column=token.column)

        # String literal
        if token.type == TokenType.STRING_LITERAL:
            self.advance()
            return StringLiteral(value=token.value, line=token.line, column=token.column)

        # Boolean literals
        if token.type in (TokenType.TRUE, TokenType.FALSE):
            self.advance()
            return BoolLiteral(
                value=(token.type == TokenType.TRUE),
                line=token.line, column=token.column,
            )

        # Identifier
        if token.type == TokenType.IDENTIFIER:
            self.advance()
            return Identifier(name=token.value, line=token.line, column=token.column)

        # When expression
        if token.type == TokenType.WHEN:
            return self.parse_when_expression()

        # Given expression (pattern matching inside expressions)
        if token.type == TokenType.GIVEN:
            return self.parse_given_expression()

        # Array literal  [a, b, c]
        if token.type == TokenType.LBRACKET:
            return self._parse_array_literal()

        # Record literal  { field: expr, ... }
        if token.type == TokenType.LBRACE:
            return self._parse_record_literal()

        # Parenthesized expression
        if token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        raise ParseError(f"Unexpected token {token.type} at {token.line}:{token.column}")

    def _parse_array_literal(self) -> ArrayLiteral:
        lbracket = self.expect(TokenType.LBRACKET)
        elements: List[Expression] = []

        if self.peek().type != TokenType.RBRACKET:
            elements.append(self.parse_expression())
            while self.peek().type == TokenType.COMMA:
                self.advance()
                elements.append(self.parse_expression())

        self.expect(TokenType.RBRACKET)
        return ArrayLiteral(
            elements=elements, line=lbracket.line, column=lbracket.column,
        )

    def _parse_record_literal(self) -> RecordLiteral:
        lbrace = self.expect(TokenType.LBRACE)
        fields: List[tuple] = []

        self.skip_newlines()
        while self.peek().type != TokenType.RBRACE:
            name = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.COLON)
            value = self.parse_expression()
            fields.append((name, value))
            self.skip_newlines()
            if self.peek().type == TokenType.COMMA:
                self.advance()
                self.skip_newlines()

        self.expect(TokenType.RBRACE)
        return RecordLiteral(
            fields=fields, line=lbrace.line, column=lbrace.column,
        )

    # ------------------------------------------------------------------
    # When / Given
    # ------------------------------------------------------------------

    def parse_when_expression(self) -> WhenExpression:
        """Parse when/otherwise expression."""
        when_token = self.expect(TokenType.WHEN)
        condition = self.parse_expression()
        self.skip_newlines()

        then_block = self.parse_block()

        else_block = None
        self.skip_newlines()
        if self.peek().type == TokenType.OTHERWISE:
            self.advance()
            self.skip_newlines()
            else_block = self.parse_block()

        return WhenExpression(
            condition=condition,
            then_block=then_block,
            else_block=else_block,
            line=when_token.line,
            column=when_token.column,
        )

    def parse_given_expression(self) -> GivenExpression:
        """Parse given (pattern matching) expression."""
        given_token = self.expect(TokenType.GIVEN)
        scrutinee = self.parse_expression()
        self.skip_newlines()

        cases: List[PatternCase] = []
        while self.peek().type in (
            TokenType.IDENTIFIER, TokenType.INTEGER_LITERAL,
            TokenType.FLOAT_LITERAL, TokenType.STRING_LITERAL,
            TokenType.TRUE, TokenType.FALSE,
        ):
            pattern = self.parse_pattern()
            self.expect(TokenType.ARROW)
            expression = self.parse_expression()
            cases.append(PatternCase(
                pattern=pattern, expression=expression,
                line=pattern.line, column=pattern.column,
            ))
            self.skip_newlines()

        return GivenExpression(
            scrutinee=scrutinee, cases=cases,
            line=given_token.line, column=given_token.column,
        )

    # ------------------------------------------------------------------
    # Patterns
    # ------------------------------------------------------------------

    def parse_pattern(self) -> Pattern:
        """Parse pattern."""
        token = self.peek()

        if token.type == TokenType.IDENTIFIER:
            name = self.advance().value

            # Constructor pattern  e.g. Some(x)
            if self.peek().type == TokenType.LPAREN:
                self.advance()
                params: List[Pattern] = []
                if self.peek().type != TokenType.RPAREN:
                    params.append(self.parse_pattern())
                    while self.peek().type == TokenType.COMMA:
                        self.advance()
                        params.append(self.parse_pattern())
                self.expect(TokenType.RPAREN)
                return ConstructorPattern(
                    constructor=name, parameters=params,
                    line=token.line, column=token.column,
                )

            # Wildcard pattern (conventionally "_")
            if name == "_":
                return WildcardPattern(line=token.line, column=token.column)

            return IdentifierPattern(name=name, line=token.line, column=token.column)

        # Literal patterns
        if token.type in (
            TokenType.INTEGER_LITERAL, TokenType.FLOAT_LITERAL, TokenType.STRING_LITERAL,
        ):
            self.advance()
            value = token.value
            if token.type == TokenType.INTEGER_LITERAL:
                value = int(value)
            elif token.type == TokenType.FLOAT_LITERAL:
                value = float(value)
            return LiteralPattern(value=value, line=token.line, column=token.column)

        if token.type in (TokenType.TRUE, TokenType.FALSE):
            self.advance()
            return LiteralPattern(
                value=(token.type == TokenType.TRUE),
                line=token.line, column=token.column,
            )

        raise ParseError(f"Expected pattern, got {token.type} at {token.line}:{token.column}")

    # ------------------------------------------------------------------
    # Block / Statements
    # ------------------------------------------------------------------

    def parse_block(self) -> Block:
        """Parse block of statements."""
        statements: List[Statement] = []

        if self.peek().type == TokenType.INDENT:
            self.advance()

            while self.peek().type not in (TokenType.DEDENT, TokenType.EOF):
                statements.append(self.parse_statement())
                self.skip_newlines()

            if self.peek().type == TokenType.DEDENT:
                self.advance()
        else:
            # Single statement (no indentation block)
            statements.append(self.parse_statement())

        line = statements[0].line if statements else 0
        column = statements[0].column if statements else 0
        return Block(statements=statements, line=line, column=column)

    def parse_statement(self) -> Statement:
        """Parse a single statement."""
        expr = self.parse_expression()
        return ExpressionStatement(expression=expr, line=expr.line, column=expr.column)
