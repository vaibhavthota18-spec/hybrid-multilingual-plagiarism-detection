"""
Lexical Detection Engine Package
Exports Tokenizer, RollingHash, WinnowingEngine, BM25Index, PassageAligner, and CoverageCalculator.
"""

from plagiarism.services.lexical.aligner import AlignedFinding, PassageAligner
from plagiarism.services.lexical.bm25 import BM25Index
from plagiarism.services.lexical.coverage import CoverageCalculator, SourceCoverageSummary
from plagiarism.services.lexical.rolling_hash import RollingHash, compute_kgram_hash, fnv1a_64
from plagiarism.services.lexical.tokenizer import LexicalToken, LexicalTokenizer
from plagiarism.services.lexical.winnowing import Fingerprint, WinnowingEngine

__all__ = [
    "LexicalToken",
    "LexicalTokenizer",
    "RollingHash",
    "fnv1a_64",
    "compute_kgram_hash",
    "Fingerprint",
    "WinnowingEngine",
    "BM25Index",
    "AlignedFinding",
    "PassageAligner",
    "CoverageCalculator",
    "SourceCoverageSummary",
]
