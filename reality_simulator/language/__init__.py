"""
Language System Module

Contains language learning, vocabulary management, and communication components.

NEW: Atomic Language System for Butterfly Engine integration
- LinguisticAtom: Trackable linguistic unit (like traits for language)
- AtomicLanguageSystem: Per-organism atomic language representation
- DialectAnalyzer: Population-level dialect emergence analysis
"""

from .language_teacher import LanguageTeacher, create_language_teacher
from .butterfly_chat import ButterflyChatRouter
from .atomic_language import AtomicLanguageSystem, LinguisticAtom, DialectAnalyzer

__all__ = [
    'LanguageTeacher',
    'create_language_teacher',
    'ButterflyChatRouter',
    # Atomic language system
    'AtomicLanguageSystem',
    'LinguisticAtom', 
    'DialectAnalyzer'
]

