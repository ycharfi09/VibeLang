"""VibeLang CLI - entry point for the compiler toolchain."""

import argparse
import sys

from compiler.lexer import Lexer, LexError
from compiler.parser import Parser, ParseError
from compiler.parser.ast_nodes import FunctionDeclaration, TypeDeclaration


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


def _lex_and_parse(source: str):
    """Lex and parse source code, returning (program, None) or (None, error)."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


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
        program = _lex_and_parse(source)

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


def check_command(args):
    """Type-check a .vbl file."""
    from compiler.typechecker import TypeChecker

    source = _read_file(args.file)
    if source is None:
        return 1
    try:
        program = _lex_and_parse(source)
        checker = TypeChecker()
        errors = checker.check(program)
        if errors:
            for err in errors:
                print(f"{err}", file=sys.stderr)
            print(f"\n{len(errors)} type error(s) found.", file=sys.stderr)
            return 1
        print("Type check passed.")
        return 0
    except (LexError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def compile_command(args):
    """Compile a .vbl file to Python."""
    from compiler.codegen import CodeGenerator

    source = _read_file(args.file)
    if source is None:
        return 1
    try:
        program = _lex_and_parse(source)
        generator = CodeGenerator()
        output = generator.generate(program)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Compiled to {args.output}")
        else:
            print(output)
        return 0
    except (LexError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def verify_command(args):
    """Verify contracts in a .vbl file."""
    from compiler.verifier import Verifier, VerificationStatus

    source = _read_file(args.file)
    if source is None:
        return 1
    try:
        program = _lex_and_parse(source)
        verifier = Verifier()
        results = verifier.verify(program)

        proven = sum(1 for r in results if r.status == VerificationStatus.PROVEN)
        unproven = sum(1 for r in results if r.status == VerificationStatus.UNPROVEN)
        violated = sum(1 for r in results if r.status == VerificationStatus.VIOLATED)

        for r in results:
            icon = {"proven": "✓", "unproven": "?", "violated": "✗"}[r.status.value]
            print(f"  [{icon}] {r.function_name}: {r.contract_type} at {r.line}:{r.column} - {r.message}")

        print(f"\nVerification: {proven} proven, {unproven} unproven, {violated} violated")
        return 1 if violated > 0 else 0
    except (LexError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def optimize_command(args):
    """Optimize a .vbl file and print the optimized AST."""
    from compiler.optimizer import Optimizer
    from compiler.formatter import Formatter

    source = _read_file(args.file)
    if source is None:
        return 1
    try:
        program = _lex_and_parse(source)
        optimizer = Optimizer()
        optimized = optimizer.optimize(program)
        formatted = Formatter().format(optimized)

        print(formatted)
        print(f"# {optimizer.optimizations_applied} optimization(s) applied", file=sys.stderr)
        return 0
    except (LexError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def fmt_command(args):
    """Format a .vbl file."""
    from compiler.formatter import Formatter

    source = _read_file(args.file)
    if source is None:
        return 1
    try:
        program = _lex_and_parse(source)
        formatted = Formatter().format(program)

        if args.write:
            with open(args.file, "w", encoding="utf-8") as f:
                f.write(formatted)
            print(f"Formatted {args.file}")
        else:
            print(formatted, end="")
        return 0
    except (LexError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        prog="vibelang",
        description="VibeLang compiler toolchain",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # lex
    lex_parser = subparsers.add_parser("lex", help="Lex a .vbl file and print tokens")
    lex_parser.add_argument("file", help="Path to .vbl source file")
    lex_parser.set_defaults(func=lex_command)

    # parse
    parse_parser = subparsers.add_parser("parse", help="Parse a .vbl file and print AST summary")
    parse_parser.add_argument("file", help="Path to .vbl source file")
    parse_parser.set_defaults(func=parse_command)

    # check (type-check)
    check_parser = subparsers.add_parser("check", help="Type-check a .vbl file")
    check_parser.add_argument("file", help="Path to .vbl source file")
    check_parser.set_defaults(func=check_command)

    # compile (code generation)
    compile_parser = subparsers.add_parser("compile", help="Compile a .vbl file to Python")
    compile_parser.add_argument("file", help="Path to .vbl source file")
    compile_parser.add_argument("-o", "--output", help="Output file path")
    compile_parser.set_defaults(func=compile_command)

    # verify (contract verification)
    verify_parser = subparsers.add_parser("verify", help="Verify contracts in a .vbl file")
    verify_parser.add_argument("file", help="Path to .vbl source file")
    verify_parser.set_defaults(func=verify_command)

    # optimize
    opt_parser = subparsers.add_parser("optimize", help="Optimize a .vbl file")
    opt_parser.add_argument("file", help="Path to .vbl source file")
    opt_parser.set_defaults(func=optimize_command)

    # fmt (formatter)
    fmt_parser = subparsers.add_parser("fmt", help="Format a .vbl file")
    fmt_parser.add_argument("file", help="Path to .vbl source file")
    fmt_parser.add_argument("-w", "--write", action="store_true",
                            help="Write result back to source file")
    fmt_parser.set_defaults(func=fmt_command)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
