"""VibeLang CLI - entry point for the compiler toolchain."""

import argparse
import sys

from compiler.lexer import Lexer, LexError
from compiler.parser import Parser, ParseError
from compiler.parser.ast_nodes import FunctionDeclaration, TypeDeclaration


def lex_command(args):
    """Lex a .vbl file and print tokens."""
    source = _read_file(args.file)
    if source is None:
        return 1
    try:
        tokens = Lexer(source).tokenize()
        for token in tokens:
            print(f"{token.line}:{token.column}  {token.type.name:<20} {token.value!r}")
        return 0
    except LexError as e:
        print(f"Lex error: {e}", file=sys.stderr)
        return 1


def parse_command(args):
    """Parse a .vbl file and print an AST summary."""
    source = _read_file(args.file)
    if source is None:
        return 1
    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()

        print(f"Imports: {len(program.imports)}")
        for imp in program.imports:
            print(f"  - {imp.module_path}")

        print(f"Declarations: {len(program.declarations)}")
        for decl in program.declarations:
            if isinstance(decl, TypeDeclaration):
                print(f"  type {decl.name} ({len(decl.invariants)} invariants)")
            elif isinstance(decl, FunctionDeclaration):
                params = ", ".join(p.name for p in decl.parameters)
                print(f"  define {decl.name}({params}) -> {decl.return_type}")
                print(f"    preconditions: {len(decl.preconditions)}")
                print(f"    postconditions: {len(decl.postconditions)}")
        return 0
    except (LexError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _read_file(path: str):
    """Read source file, returning contents or None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        return None
    except OSError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        prog="vibelang",
        description="VibeLang compiler toolchain",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    lex_parser = subparsers.add_parser("lex", help="Lex a .vbl file and print tokens")
    lex_parser.add_argument("file", help="Path to .vbl source file")
    lex_parser.set_defaults(func=lex_command)

    parse_parser = subparsers.add_parser("parse", help="Parse a .vbl file and print AST summary")
    parse_parser.add_argument("file", help="Path to .vbl source file")
    parse_parser.set_defaults(func=parse_command)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
