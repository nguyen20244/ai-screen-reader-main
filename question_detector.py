"""
Question detection system for the AI Screen Reader
"""
import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from config import config

# MCQ option line patterns
LETTER_OPTION_RE = re.compile(r'^\(?[A-Da-d][.)]\s*\S')
LETTER_OPTION_PATTERNS = [r'^[A-D]\)\s*(.+)', r'^[A-D]\.\s*(.+)', r'^\([A-D]\)\s*(.+)']
NUMBER_OPTION_PATTERNS = [r'^[1-4]\)\s*(.+)', r'^[1-4]\.\s*(.+)']
# Pattern types that must not produce a question on their own
SKIP_AS_QUESTION = {'mcq_options', 'true_false'}

@dataclass
class Question:
    """Data class for detected questions"""
    text: str
    question_type: str
    confidence: float
    options: List[str] = None
    context: str = ""
    line_number: int = 0

class QuestionDetector:
    """Detects questions and MCQs from extracted text"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Question type patterns with confidence weights
        self.question_patterns = {
            'mcq_options': {
                'pattern': r'(?i)^[A-D]\)\s*(.+)',
                'confidence': 0.9,
                'description': 'Multiple choice options (A, B, C, D)'
            },
            'numbered_question': {
                'pattern': r'(?i)^(\d+\.?\s*(.+\?.*))$',
                'confidence': 0.8,
                'description': 'Numbered questions ending with ?'
            },
            'direct_question': {
                'pattern': r'(.+\?)',
                'confidence': 0.7,
                'description': 'Direct questions ending with ?'
            },
            'what_question': {
                'pattern': r'(?i)(what\s+is\s+.+\??)',
                'confidence': 0.8,
                'description': 'What is questions'
            },
            'which_question': {
                'pattern': r'(?i)(which\s+of\s+.+\??)',
                'confidence': 0.8,
                'description': 'Which of questions'
            },
            'choose_question': {
                'pattern': r'(?i)(choose\s+the\s+.+\??)',
                'confidence': 0.7,
                'description': 'Choose the questions'
            },
            'select_question': {
                'pattern': r'(?i)(select\s+the\s+.+\??)',
                'confidence': 0.7,
                'description': 'Select the questions'
            },
            'true_false': {
                'pattern': r'(?i)(.+\s+(true|false)\s*\??)',
                'confidence': 0.6,
                'description': 'True/False questions'
            }
        }
        
        # MCQ option patterns
        self.mcq_option_patterns = [
            r'^[A-D]\)\s*(.+)',  # A) option
            r'^[A-D]\.\s*(.+)',  # A. option
            r'^\([A-D]\)\s*(.+)',  # (A) option
            r'^[1-4]\)\s*(.+)',  # 1) option
            r'^[1-4]\.\s*(.+)',  # 1. option
        ]
    
    def detect_questions(self, text: str) -> List[Question]:
        """Detect questions line by line. Each line yields at most one question."""
        if not text:
            return []
        lines = [line.strip() for line in text.split('\n')]
        questions = []
        for i, line in enumerate(lines):
            # Option lines (A) B) C) D)) are answers, not questions
            if not line or LETTER_OPTION_RE.match(line):
                continue
            for q_type, info in self.question_patterns.items():
                if q_type in SKIP_AS_QUESTION:
                    continue
                m = re.search(info['pattern'], line)
                if not m:
                    continue
                if q_type == 'numbered_question':
                    raw = m.group(2)  # text after the "1." prefix
                else:
                    raw = m.group(1) if m.groups() else m.group(0)
                q_text = raw.strip()
                if not q_text:
                    continue
                questions.append(Question(
                    text=q_text,
                    question_type=q_type,
                    confidence=info['confidence'],
                    options=self._detect_mcq_options(lines, i),
                    context=self._get_context(lines, i, 2),
                    line_number=i,
                ))
                break  # one question per line
        questions = self._remove_duplicates(questions)
        questions.sort(key=lambda q: q.confidence, reverse=True)
        self.logger.info(f"Detected {len(questions)} questions")
        return questions

    def _detect_mcq_options(self, lines: List[str], question_line: int) -> Optional[List[str]]:
        """Collect A)-D) options after a question. Numeric 1)-4) options are only used for unnumbered questions."""
        patterns = list(LETTER_OPTION_PATTERNS)
        if not re.match(r'^\d+[.)]\s', lines[question_line]):
            patterns += NUMBER_OPTION_PATTERNS
        options = []
        for line in lines[question_line + 1: question_line + 6]:
            if not line:
                continue
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    options.append(match.group(1).strip())
                    break
            else:
                if options:  # stop once the option block ends
                    break
        return options if len(options) >= 2 else None

    def _get_context(self, lines: List[str], line_index: int, context_size: int = 2) -> str:
        """
        Get context around a specific line
        
        Args:
            lines: All text lines
            line_index: Index of the target line
            context_size: Number of lines before and after to include
            
        Returns:
            Context string
        """
        start = max(0, line_index - context_size)
        end = min(len(lines), line_index + context_size + 1)
        
        context_lines = lines[start:end]
        return '\n'.join(context_lines)
    
    def _remove_duplicates(self, questions: List[Question]) -> List[Question]:
        """Drop repeated questions. Ignores case, extra spaces, trailing punctuation and leading numbering."""
        unique_questions = []
        seen = set()
        for question in questions:
            key = re.sub(r'^\d+[.)]\s+', '', question.text.lower())
            key = re.sub(r'[\s?.!:]+$', '', re.sub(r'\s+', ' ', key)).strip()
            if key and key not in seen:
                seen.add(key)
                unique_questions.append(question)
        return unique_questions

    def format_question_for_ai(self, question: Question) -> str:
        """
        Format a question for AI processing
        
        Args:
            question: Question object to format
            
        Returns:
            Formatted question string
        """
        formatted = f"Question: {question.text}\n"
        
        if question.options:
            formatted += "Options:\n"
            for i, option in enumerate(question.options):
                letter = chr(65 + i)  # A, B, C, D
                formatted += f"{letter}) {option}\n"
        
        if question.context and question.context != question.text:
            formatted += f"\nContext: {question.context}\n"
        
        return formatted.strip()
    
    def is_likely_question(self, text: str, threshold: float = 0.5) -> bool:
        """
        Quick check if text likely contains questions
        
        Args:
            text: Text to check
            threshold: Confidence threshold
            
        Returns:
            True if likely contains questions
        """
        questions = self.detect_questions(text)
        return any(q.confidence >= threshold for q in questions)
