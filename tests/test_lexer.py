import pytest
from compiler.lexer import Lexer, Token, TokenType, LexError


class TestLexerKeywords:
    def test_define_keyword(self):
        tokens = Lexer("define").tokenize()
        assert tokens[0].type == TokenType.DEFINE

    def test_all_keywords(self):
        source = "define type expect ensure invariant given when otherwise import export"
        tokens = Lexer(source).tokenize()
        expected = [TokenType.DEFINE, TokenType.TYPE, TokenType.EXPECT, TokenType.ENSURE,
                    TokenType.INVARIANT, TokenType.GIVEN, TokenType.WHEN, TokenType.OTHERWISE,
                    TokenType.IMPORT, TokenType.EXPORT]
        for i, exp in enumerate(expected):
            assert tokens[i].type == exp

    def test_literal_keywords(self):
        tokens = Lexer("true false self old").tokenize()
        assert tokens[0].type == TokenType.TRUE
        assert tokens[1].type == TokenType.FALSE
        assert tokens[2].type == TokenType.SELF
        assert tokens[3].type == TokenType.OLD

    def test_type_keywords(self):
        source = "Int Float Bool String Byte Unit Array Result"
        tokens = Lexer(source).tokenize()
        expected = [TokenType.INT, TokenType.FLOAT, TokenType.BOOL, TokenType.STRING,
                    TokenType.BYTE, TokenType.UNIT, TokenType.ARRAY, TokenType.RESULT]
        for i, exp in enumerate(expected):
            assert tokens[i].type == exp


class TestLexerIdentifiers:
    def test_simple_identifier(self):
        tokens = Lexer("myVar").tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "myVar"

    def test_identifier_with_underscore(self):
        tokens = Lexer("my_var_2").tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "my_var_2"

    def test_identifier_starting_with_underscore(self):
        tokens = Lexer("_private").tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "_private"


class TestLexerLiterals:
    def test_integer_literal(self):
        tokens = Lexer("42").tokenize()
        assert tokens[0].type == TokenType.INTEGER_LITERAL
        assert tokens[0].value == "42"

    def test_float_literal(self):
        tokens = Lexer("3.14").tokenize()
        assert tokens[0].type == TokenType.FLOAT_LITERAL
        assert tokens[0].value == "3.14"

    def test_string_literal(self):
        tokens = Lexer('"hello world"').tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].value == "hello world"

    def test_string_with_escape_sequences(self):
        tokens = Lexer('"hello\\nworld\\t!"').tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].value == "hello\nworld\t!"

    def test_string_with_escaped_quote(self):
        tokens = Lexer('"say \\"hi\\""').tokenize()
        assert tokens[0].type == TokenType.STRING_LITERAL
        assert tokens[0].value == 'say "hi"'


class TestLexerOperators:
    def test_arithmetic_operators(self):
        tokens = Lexer("+ - * / %").tokenize()
        expected = [TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT]
        for i, exp in enumerate(expected):
            assert tokens[i].type == exp

    def test_comparison_operators(self):
        tokens = Lexer("== != < > <= >=").tokenize()
        expected = [TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE]
        for i, exp in enumerate(expected):
            assert tokens[i].type == exp

    def test_logical_operators(self):
        tokens = Lexer("&& || !").tokenize()
        assert tokens[0].type == TokenType.AND
        assert tokens[1].type == TokenType.OR
        assert tokens[2].type == TokenType.NOT

    def test_arrow_operator(self):
        tokens = Lexer("->").tokenize()
        assert tokens[0].type == TokenType.ARROW

    def test_ellipsis(self):
        tokens = Lexer("...").tokenize()
        assert tokens[0].type == TokenType.ELLIPSIS


class TestLexerSymbols:
    def test_parentheses(self):
        tokens = Lexer("()").tokenize()
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].type == TokenType.RPAREN

    def test_brackets(self):
        tokens = Lexer("[]").tokenize()
        assert tokens[0].type == TokenType.LBRACKET
        assert tokens[1].type == TokenType.RBRACKET

    def test_braces(self):
        tokens = Lexer("{}").tokenize()
        assert tokens[0].type == TokenType.LBRACE
        assert tokens[1].type == TokenType.RBRACE

    def test_comma_colon_dot(self):
        tokens = Lexer(", : .").tokenize()
        assert tokens[0].type == TokenType.COMMA
        assert tokens[1].type == TokenType.COLON
        assert tokens[2].type == TokenType.DOT

    def test_assign(self):
        tokens = Lexer("=").tokenize()
        assert tokens[0].type == TokenType.ASSIGN


class TestLexerComments:
    def test_single_line_comment(self):
        tokens = Lexer("x # this is a comment\ny").tokenize()
        types = [t.type for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
        assert TokenType.COMMENT not in types
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "x"

    def test_multiline_comment(self):
        tokens = Lexer("x ## this is\na comment ## y").tokenize()
        id_tokens = [t for t in tokens if t.type == TokenType.IDENTIFIER]
        assert len(id_tokens) == 2
        assert id_tokens[0].value == "x"
        assert id_tokens[1].value == "y"


class TestLexerIndentation:
    def test_indent_dedent(self):
        source = "x\n  y\nz"
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens]
        assert TokenType.INDENT in types
        assert TokenType.DEDENT in types

    def test_tab_raises_error(self):
        with pytest.raises(LexError, match="[Tt]ab"):
            Lexer("\tx").tokenize()

    def test_odd_indentation_raises_error(self):
        with pytest.raises(LexError, match="[Ii]ndentation"):
            Lexer("x\n   y").tokenize()

    def test_nested_indentation(self):
        source = "a\n  b\n    c\n  d\ne"
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens]
        assert types.count(TokenType.INDENT) == 2
        assert types.count(TokenType.DEDENT) >= 2


class TestLexerLineTracking:
    def test_line_numbers(self):
        tokens = Lexer("x\ny\nz").tokenize()
        id_tokens = [t for t in tokens if t.type == TokenType.IDENTIFIER]
        assert id_tokens[0].line == 1
        assert id_tokens[1].line == 2
        assert id_tokens[2].line == 3

    def test_column_numbers(self):
        tokens = Lexer("abc def").tokenize()
        assert tokens[0].column == 1
        assert tokens[1].column == 5


class TestLexerErrors:
    def test_unclosed_string(self):
        with pytest.raises(LexError, match="[Uu]nclosed"):
            Lexer('"hello').tokenize()

    def test_unclosed_multiline_comment(self):
        with pytest.raises(LexError, match="[Uu]nclosed"):
            Lexer("## unclosed comment").tokenize()


class TestLexerEOF:
    def test_eof_token(self):
        tokens = Lexer("x").tokenize()
        assert tokens[-1].type == TokenType.EOF

    def test_empty_source(self):
        tokens = Lexer("").tokenize()
        assert tokens[-1].type == TokenType.EOF


class TestLexerFunctionSignature:
    def test_function_definition(self):
        source = "define add(x: Int, y: Int) -> Int"
        tokens = Lexer(source).tokenize()
        expected_types = [
            TokenType.DEFINE, TokenType.IDENTIFIER, TokenType.LPAREN,
            TokenType.IDENTIFIER, TokenType.COLON, TokenType.INT, TokenType.COMMA,
            TokenType.IDENTIFIER, TokenType.COLON, TokenType.INT, TokenType.RPAREN,
            TokenType.ARROW, TokenType.INT, TokenType.EOF
        ]
        assert [t.type for t in tokens] == expected_types
