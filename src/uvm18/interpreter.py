"""Execute UVM variant 18 code with isolated code and data memory."""

import xml.etree.ElementTree as ElementTree
from pathlib import Path

from .isa import COMMAND_SIZE, INSTRUCTIONS, MEMORY_SIZE, WORD_MASK, decode


def _read(memory, address):
    """Read a checked 32-bit word from virtual data memory."""
    if not 0 <= address < MEMORY_SIZE:
        raise ValueError(f"data address out of range: {address}")
    return memory.get(address, 0)


def _write(memory, address, value):
    """Write a checked 32-bit word to virtual data memory."""
    if not 0 <= address < MEMORY_SIZE:
        raise ValueError(f"data address out of range: {address}")
    memory[address] = value & WORD_MASK


def execute(machine_code, memory=None):
    """Execute binary commands and return resulting sparse data memory."""
    if len(machine_code) % COMMAND_SIZE:
        raise ValueError("binary program size must be a multiple of 11 bytes")
    data_memory = memory if memory is not None else {}
    code_memory = [
        machine_code[index:index + COMMAND_SIZE]
        for index in range(0, len(machine_code), COMMAND_SIZE)
    ]
    for address, command in enumerate(code_memory):
        opcode, operands = decode(command)
        fields = dict(zip(
            (field.name for field in INSTRUCTIONS[opcode].fields), operands
        ))
        if opcode == 2:
            _write(data_memory, fields["B"], fields["C"])
        elif opcode == 7:
            pointer = _read(data_memory, fields["C"])
            target = pointer + fields["B"]
            _write(data_memory, fields["D"], _read(data_memory, target))
        elif opcode == 6:
            source = _read(data_memory, fields["B"])
            pointer = _read(data_memory, fields["C"])
            _write(data_memory, pointer + fields["D"], source)
        elif opcode == 3:
            left = _read(data_memory, fields["D"])
            right = _read(data_memory, fields["B"])
            destination = _read(data_memory, fields["C"])
            _write(data_memory, destination, left & right)
        else:
            raise ValueError(f"unsupported opcode at command {address}")
    return data_memory


def load_xml_memory(path):
    """Load sparse initial memory from XML memory elements."""
    root = ElementTree.parse(path).getroot()
    memory = {}
    for element in root.findall("memory"):
        address = int(element.attrib["address"], 0)
        value = int(element.attrib["value"], 0)
        _write(memory, address, value)
    return memory


def write_memory_dump(memory, path, start, end):
    """Write the inclusive address range to an XML dump file."""
    if start < 0 or end < start or end >= MEMORY_SIZE:
        raise ValueError("invalid memory dump address range")
    root = ElementTree.Element("memoryDump", start=str(start), end=str(end))
    for address in range(start, end + 1):
        element = ElementTree.SubElement(root, "memory")
        element.set("address", str(address))
        element.set("value", str(memory.get(address, 0)))
    ElementTree.indent(root, space="  ")
    tree = ElementTree.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def interpret_file(binary_path, dump_path, start, end, input_path=None):
    """Run a binary program and write an XML dump of virtual memory."""
    memory = load_xml_memory(input_path) if input_path else {}
    machine_code = Path(binary_path).read_bytes()
    result = execute(machine_code, memory)
    write_memory_dump(result, dump_path, start, end)
    return result
