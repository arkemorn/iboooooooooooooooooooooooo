"""Instruction layout and bit-level encoding for UVM variant 18."""

from dataclasses import dataclass

COMMAND_SIZE = 11
WORD_MASK = (1 << 32) - 1
MEMORY_SIZE = 1 << 28


@dataclass(frozen=True)
class Field:
    """A named unsigned field in an instruction word."""

    name: str
    width: int


@dataclass(frozen=True)
class Instruction:
    """An instruction opcode and its operand layout."""

    name: str
    opcode: int
    fields: tuple[Field, ...]


INSTRUCTIONS = {
    2: Instruction("LOAD", 2, (Field("B", 28), Field("C", 32))),
    7: Instruction(
        "READ", 7,
        (Field("B", 9), Field("C", 28), Field("D", 28)),
    ),
    6: Instruction(
        "WRITE", 6,
        (Field("B", 28), Field("C", 28), Field("D", 9)),
    ),
    3: Instruction(
        "AND", 3,
        (Field("B", 28), Field("C", 28), Field("D", 28)),
    ),
}


def field_values(opcode, operands):
    """Return an instruction and its fields as a name-value mapping."""
    instruction = INSTRUCTIONS.get(opcode)
    if instruction is None:
        raise ValueError(f"unknown opcode: {opcode}")
    if len(operands) != len(instruction.fields):
        expected = len(instruction.fields)
        raise ValueError(f"{instruction.name} expects {expected} fields")
    names = (field.name for field in instruction.fields)
    return instruction, dict(zip(names, operands))


def encode(opcode, operands):
    """Encode one instruction using its 11-byte little-endian bit stream."""
    instruction, values = field_values(opcode, operands)
    packed = opcode
    offset = 3
    for field in instruction.fields:
        value = values[field.name]
        if value < 0 or value >= 1 << field.width:
            message = f"field {field.name} does not fit {field.width} bits"
            raise ValueError(message)
        packed |= value << offset
        offset += field.width
    return packed.to_bytes(COMMAND_SIZE, "little")


def decode(data):
    """Decode one 11-byte instruction into opcode and operand tuple."""
    if len(data) != COMMAND_SIZE:
        raise ValueError("instruction must contain exactly 11 bytes")
    packed = int.from_bytes(data, "little")
    opcode = packed & 0b111
    instruction = INSTRUCTIONS.get(opcode)
    if instruction is None:
        raise ValueError(f"unknown opcode: {opcode}")
    offset = 3
    operands = []
    for field in instruction.fields:
        mask = (1 << field.width) - 1
        operands.append((packed >> offset) & mask)
        offset += field.width
    return opcode, tuple(operands)
