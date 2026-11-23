"""Specification and behavior tests for UVM variant 18."""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from uvm18.assembler import assemble_source, parse_source
from uvm18.interpreter import execute, load_xml_memory
from uvm18.isa import decode, encode


class EncodingTests(unittest.TestCase):
    """Check instruction encodings against assignment examples."""

    def test_load_example_bytes(self):
        actual = encode(2, (817, 472))
        expected = bytes.fromhex("8A 19 00 00 EC 00 00 00 00 00 00")
        self.assertEqual(actual, expected)

    def test_read_example_bytes(self):
        actual = encode(7, (287, 225, 609))
        expected = bytes.fromhex("FF 18 0E 00 00 61 02 00 00 00 00")
        self.assertEqual(actual, expected)

    def test_write_example_bytes(self):
        actual = encode(6, (816, 778, 464))
        expected = bytes.fromhex("86 19 00 00 85 01 00 80 0E 00 00")
        self.assertEqual(actual, expected)

    def test_and_example_bytes(self):
        actual = encode(3, (816, 778, 464))
        expected = bytes.fromhex("83 19 00 00 85 01 00 80 0E 00 00")
        self.assertEqual(actual, expected)

    def test_and_round_trip(self):
        expected = (3, (816, 778, 464))
        self.assertEqual(decode(encode(*expected)), expected)


class ExecutionTests(unittest.TestCase):
    """Check source parsing and virtual memory behavior."""

    def test_source_comments_and_hex_values(self):
        result = assemble_source("# example\n2, 0x10, 0xAB\n")
        self.assertEqual(len(result), 11)

    def test_and_task_vector(self):
        values = [255, 170, 85, 240, 15, 128]
        memory = {10: 155}
        memory.update({100 + i: value for i, value in enumerate(values)})
        source = "".join(
            f"2, 11, {100 + i}\n2, 12, {200 + i}\n"
            f"3, 10, 12, {100 + i}\n"
            for i in range(len(values))
        )
        result = execute(assemble_source(source), memory)
        actual = [result[200 + i] for i in range(len(values))]
        self.assertEqual(actual, [value & 155 for value in values])

    def test_three_demonstration_programs(self):
        project = Path(__file__).resolve().parents[1]
        examples = (
            ("and.csv", "input.xml", 155),
            ("and-high-bits.csv", "input-high-bits.xml", 0xFF00FF00),
            ("and-sparse.csv", "input-sparse.xml", 42),
        )
        for program_name, input_name, mask in examples:
            source_path = project / "examples" / program_name
            input_path = project / "examples" / input_name
            source = source_path.read_text(encoding="utf-8")
            memory = load_xml_memory(input_path)
            result = execute(assemble_source(source), memory)
            actual = [result[200 + index] for index in range(6)]
            expected = [memory[100 + index] & mask for index in range(6)]
            self.assertEqual(actual, expected, program_name)

    def test_indirect_copy(self):
        source = "2, 10, 100\n2, 20, 3\n7, 0, 10, 30\n"
        result = execute(assemble_source(source), {100: 22})
        self.assertEqual(result[30], 22)

    def test_indirect_write(self):
        source = "2, 30, 42\n2, 10, 100\n6, 30, 10, 1\n"
        result = execute(assemble_source(source))
        self.assertEqual(result[101], 42)

    def test_rejects_wrong_operand_count(self):
        with self.assertRaisesRegex(ValueError, "expects"):
            parse_source("2, 1\n")

    def test_rejects_out_of_range_address(self):
        source = "2, 10, 268435455\n7, 1, 10, 20\n"
        program = assemble_source(source)
        with self.assertRaisesRegex(ValueError, "out of range"):
            execute(program)


if __name__ == "__main__":
    unittest.main()
