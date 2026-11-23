"""Translate CSV-like UVM source into an intermediate form and bytes."""

import csv
from pathlib import Path

from .isa import encode, field_values


def _parse_integer(value, line_number):
    """Parse an integer and report its source line on failure."""
    try:
        return int(value.strip(), 0)
    except ValueError as error:
        message = f"line {line_number}: invalid integer {value!r}"
        raise ValueError(message) from error


def parse_source(source):
    """Parse source lines into opcode, fields, and encoded byte records."""
    program = []
    for line_number, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            columns = next(csv.reader([line], skipinitialspace=True))
        except csv.Error as error:
            raise ValueError(f"line {line_number}: invalid CSV") from error
        if len(columns) < 2:
            message = f"line {line_number}: expected opcode and operands"
            raise ValueError(message)
        opcode = _parse_integer(columns[0], line_number)
        operands = tuple(
            _parse_integer(value, line_number) for value in columns[1:]
        )
        try:
            instruction, values = field_values(opcode, operands)
            machine_code = encode(opcode, operands)
        except ValueError as error:
            raise ValueError(f"line {line_number}: {error}") from error
        program.append({
            "line": line_number,
            "name": instruction.name,
            "opcode": opcode,
            "fields": values,
            "bytes": machine_code,
        })
    if not program:
        raise ValueError("source contains no instructions")
    return program


def assemble_source(source):
    """Translate source text into a byte string."""
    return b"".join(item["bytes"] for item in parse_source(source))


def assemble_file(source_path, output_path):
    """Assemble UTF-8 source file and write the binary result."""
    source = Path(source_path).read_text(encoding="utf-8")
    result = assemble_source(source)
    Path(output_path).write_bytes(result)
    return result


def describe_program(program):
    """Format intermediate fields and encoded bytes for test mode."""
    rows = []
    for item in program:
        fields = ", ".join(
            f"{key}={value}" for key, value in item["fields"].items()
        )
        byte_values = ", ".join(f"0x{value:02X}" for value in item["bytes"])
        rows.append(f"{item['name']} ({fields})\n{byte_values}")
    return "\n".join(rows)
