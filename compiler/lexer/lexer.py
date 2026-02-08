"""VibeLang Lexer - transforms source code into a stream of tokens."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class TokenType(Enum):
    # Keywords
    DEFINE = "define"
    TYPE = "type"
    EXPECT = "expect"
    ENSURE = "ensure"
    INVARIANT = "invariant"
    GIVEN = "given"
    WHEN = "when"
    OTHERWISE = "otherwise"
    IMPORT = "import"
    EXPORT = "export"

    # Literals
    TRUE = "true"
    FALSE = "false"
    SELF = "self"
    OLD = "old"

    # Types
    INT = "Int"
    FLOAT = "Float"
    BOOL = "Bool"
    STRING = "String"
    BYTE = "Byte"
    UNIT = "Unit"
    ARRAY = "Array"
    RESULT = "Result"

    # Identifiers and literals
    IDENTIFIER = "IDENTIFIER"
    INTEGER_LITERAL = "INTEGER_LITERAL"
    FLOAT_LITERAL = "FLOAT_LITERAL"
    STRING_LITERAL = "STRING_LITERAL"

    # Operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    PERCENT = "%"
    EQ = "=="
    NEQ = "!="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    AND = "&&"
    OR = "||"
    NOT = "!"
    ARROW = "->"
    PIPE = "|"
    AMPERSAND = "&"
    QUESTION = "?"

    # Symbols
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    LBRACE = "{"
    RBRACE = "}"
    COMMA = ","
    COLON = ":"
    DOT = "."
    ASSIGN = "="
    ELLIPSIS = "..."

    # Special
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    NEWLINE = "NEWLINE"
    EOF = "EOF"
    COMMENT = "COMMENT"


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    indentation: int


class LexError(Exception):
    """Lexer error exception"""
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]

    def peek(self, offset: int = 0) -> str:
        """Look ahead at character without consuming it."""
        pos = self.position + offset
        if pos < len(self.source):
            return self.source[pos]
        return '\0'

    def advance(self) -> str:
        """Consume and return current character."""
        if self.position >= len(self.source):
            return '\0'

        char = self.source[self.position]
        self.position += 1

        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def skip_whitespace(self):
        """Skip spaces and tabs (but not newlines)."""
        while self.peek() in ' \t':
            self.advance()

    def skip_comment(self):
        """Skip single-line (#) and multi-line (## ... ##) comments."""
        if self.peek() == '#':
            if self.peek(1) == '#':
                # Multi-line comment
                start_line = self.line
                start_column = self.column
                self.advance()  # First #
                self.advance()  # Second #
                while not (self.peek() == '#' and self.peek(1) == '#'):
                    if self.peek() == '\0':
                        raise LexError(
                            f"Unclosed multi-line comment starting at line {start_line}, column {start_column}"
                        )
                    self.advance()
                self.advance()  # First closing #
                self.advance()  # Second closing #
            else:
                # Single-line comment
                while self.peek() != '\n' and self.peek() != '\0':
                    self.advance()

    def read_identifier(self) -> Token:
        """Read identifier or keyword."""
        start_column = self.column
        value = ""

        while self.peek().isalnum() or self.peek() == '_':
            value += self.advance()

        keywords = {
            "define": TokenType.DEFINE,
            "type": TokenType.TYPE,
            "expect": TokenType.EXPECT,
            "ensure": TokenType.ENSURE,
            "invariant": TokenType.INVARIANT,
            "given": TokenType.GIVEN,
            "when": TokenType.WHEN,
            "otherwise": TokenType.OTHERWISE,
            "import": TokenType.IMPORT,
            "export": TokenType.EXPORT,
            "true": TokenType.TRUE,
            "false": TokenType.FALSE,
            "self": TokenType.SELF,
            "old": TokenType.OLD,
            "Int": TokenType.INT,
            "Float": TokenType.FLOAT,
            "Bool": TokenType.BOOL,
            "String": TokenType.STRING,
            "Byte": TokenType.BYTE,
            "Unit": TokenType.UNIT,
            "Array": TokenType.ARRAY,
            "Result": TokenType.RESULT,
        }

        token_type = keywords.get(value, TokenType.IDENTIFIER)
        return Token(token_type, value, self.line, start_column, 0)

    def read_number(self) -> Token:
        """Read integer or float literal."""
        start_column = self.column
        value = ""
        is_float = False

        while self.peek().isdigit():
            value += self.advance()

        # Check for decimal point
        if self.peek() == '.' and self.peek(1).isdigit():
            is_float = True
            value += self.advance()  # Add '.'
            while self.peek().isdigit():
                value += self.advance()

        token_type = TokenType.FLOAT_LITERAL if is_float else TokenType.INTEGER_LITERAL
        return Token(token_type, value, self.line, start_column, 0)

    def read_string(self) -> Token:
        """Read string literal with escape sequence support."""
        start_line = self.line
        start_column = self.column
        self.advance()  # Skip opening quote
        value = ""

        while self.peek() != '"':
            if self.peek() == '\0':
                raise LexError(
                    f"Unclosed string literal starting at line {start_line}, column {start_column}"
                )

            if self.peek() == '\\':
                self.advance()
                escape_char = self.advance()
                escape_map = {
                    'n': '\n',
                    't': '\t',
                    'r': '\r',
                    '"': '"',
                    '\\': '\\'
                }
                value += escape_map.get(escape_char, escape_char)
            else:
                value += self.advance()

        self.advance()  # Skip closing quote
        return Token(TokenType.STRING_LITERAL, value, start_line, start_column, 0)

    def handle_indentation(self, indent_level: int):
        """Generate INDENT/DEDENT tokens based on indentation."""
        if indent_level > self.indent_stack[-1]:
            self.indent_stack.append(indent_level)
            self.tokens.append(Token(TokenType.INDENT, "", self.line, 1, indent_level))
        elif indent_level < self.indent_stack[-1]:
            while self.indent_stack[-1] > indent_level:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, "", self.line, 1, indent_level))

            if self.indent_stack[-1] != indent_level:
                raise LexError(f"Inconsistent indentation at line {self.line}")

    def read_operator_or_symbol(self) -> Optional[Token]:
        """Read operator or symbol token."""
        start_column = self.column
        char = self.peek()

        # Three-character operators
        if char == '.' and self.peek(1) == '.' and self.peek(2) == '.':
            self.advance()
            self.advance()
            self.advance()
            return Token(TokenType.ELLIPSIS, "...", self.line, start_column, 0)

        # Two-character operators
        if char == '-' and self.peek(1) == '>':
            self.advance()
            self.advance()
            return Token(TokenType.ARROW, "->", self.line, start_column, 0)

        if char == '=' and self.peek(1) == '=':
            self.advance()
            self.advance()
            return Token(TokenType.EQ, "==", self.line, start_column, 0)

        if char == '!' and self.peek(1) == '=':
            self.advance()
            self.advance()
            return Token(TokenType.NEQ, "!=", self.line, start_column, 0)

        if char == '<' and self.peek(1) == '=':
            self.advance()
            self.advance()
            return Token(TokenType.LE, "<=", self.line, start_column, 0)

        if char == '>' and self.peek(1) == '=':
            self.advance()
            self.advance()
            return Token(TokenType.GE, ">=", self.line, start_column, 0)

        if char == '&' and self.peek(1) == '&':
            self.advance()
            self.advance()
            return Token(TokenType.AND, "&&", self.line, start_column, 0)

        if char == '|' and self.peek(1) == '|':
            self.advance()
            self.advance()
            return Token(TokenType.OR, "||", self.line, start_column, 0)

        # Single-character operators and symbols
        single_char_tokens = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.STAR,
            '/': TokenType.SLASH,
            '%': TokenType.PERCENT,
            '<': TokenType.LT,
            '>': TokenType.GT,
            '!': TokenType.NOT,
            '|': TokenType.PIPE,
            '&': TokenType.AMPERSAND,
            '?': TokenType.QUESTION,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            ',': TokenType.COMMA,
            ':': TokenType.COLON,
            '.': TokenType.DOT,
            '=': TokenType.ASSIGN,
        }

        if char in single_char_tokens:
            self.advance()
            return Token(single_char_tokens[char], char, self.line, start_column, 0)

        return None

    def tokenize(self) -> List[Token]:
        """Main tokenization loop."""
        at_line_start = True

        while self.position < len(self.source):
            # Handle indentation at line start
            if at_line_start:
                indent_level = 0
                while self.peek() in ' \t':
                    if self.peek() == ' ':
                        indent_level += 1
                    else:  # tab
                        raise LexError("Tabs are not allowed, use 2 spaces for indentation")
                    self.advance()

                # Skip blank lines
                if self.peek() == '\n' or self.peek() == '#':
                    if self.peek() == '#':
                        self.skip_comment()
                    if self.peek() == '\n':
                        self.advance()
                    continue

                # Check indentation (must be multiple of 2)
                if indent_level % 2 != 0:
                    raise LexError(f"Indentation must be multiple of 2 spaces at line {self.line}")

                self.handle_indentation(indent_level // 2)
                at_line_start = False

            self.skip_whitespace()

            char = self.peek()

            if char == '\0':
                break

            # Comments
            if char == '#':
                self.skip_comment()
                continue

            # Newlines
            if char == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, "\\n", self.line, self.column, 0))
                self.advance()
                at_line_start = True
                continue

            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self.tokens.append(self.read_identifier())
                continue

            # Numbers
            if char.isdigit():
                self.tokens.append(self.read_number())
                continue

            # Strings
            if char == '"':
                self.tokens.append(self.read_string())
                continue

            # Operators and symbols
            token = self.read_operator_or_symbol()
            if token:
                self.tokens.append(token)
                continue

            raise LexError(f"Unexpected character '{char}' at line {self.line}, column {self.column}")

        # Handle remaining dedents
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, "", self.line, 1, 0))

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column, 0))

        return self.tokens
