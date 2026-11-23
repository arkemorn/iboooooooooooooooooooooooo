"""Assembler and interpreter for educational virtual machine variant 18."""

from .assembler import assemble_file, assemble_source
from .interpreter import execute

__all__ = ["assemble_file", "assemble_source", "execute"]
