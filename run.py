"""Command-line entry point for UVM variant 18 tools."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from uvm18.assembler import assemble_file, describe_program, parse_source
from uvm18.interpreter import interpret_file


def _assembler_command(arguments):
    """Assemble source and show diagnostics or output size."""
    source_text = Path(arguments.source).read_text(encoding="utf-8")
    program = parse_source(source_text)
    result = assemble_file(arguments.source, arguments.output)
    if arguments.test:
        print(describe_program(program))
    print(f"Размер бинарного файла: {len(result)} байт")
    return 0


def _interpreter_command(arguments):
    """Interpret a binary file and write selected XML memory range."""
    interpret_file(
        arguments.binary,
        arguments.dump,
        arguments.start,
        arguments.end,
        arguments.input,
    )
    print(f"Дамп памяти записан: {arguments.dump}")
    return 0


def create_parser():
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="УВМ, вариант 18")
    commands = parser.add_subparsers(dest="command", required=True)
    assembler = commands.add_parser("assemble", help="ассемблировать CSV-файл")
    assembler.add_argument("source", help="путь к исходному файлу")
    assembler.add_argument("output", help="путь к бинарному результату")
    assembler.add_argument("--test", action="store_true", help="показать поля")
    assembler.set_defaults(handler=_assembler_command)
    interpreter = commands.add_parser("interpret", help="исполнить программу")
    interpreter.add_argument("binary", help="путь к бинарной программе")
    interpreter.add_argument("dump", help="путь к XML-дампу памяти")
    interpreter.add_argument("start", type=int, help="первый адрес дампа")
    interpreter.add_argument("end", type=int, help="последний адрес дампа")
    interpreter.add_argument("--input", help="XML с начальной памятью")
    interpreter.set_defaults(handler=_interpreter_command)
    return parser


def main():
    """Run the selected command and show expected errors cleanly."""
    parser = create_parser()
    arguments = parser.parse_args()
    try:
        return arguments.handler(arguments)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
