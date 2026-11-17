"""
Question detection system for the AI Screen Reader
"""
import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from config import config

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
        """
        Detect questions from text
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of detected Question objects
        """
        if not text:
            return []
        
        questions = []
        lines = text.split('\n')
        
        # Process each line
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check each question pattern
            for q_type, pattern_info in self.question_patterns.items():
                matches = re.findall(pattern_info['pattern'], line)
                if matches:
                    for match in matches:
                        question_text = match if isinstance(match, str) else match[0]
                        
                        # Get context (surrounding lines)
                        context = self._get_context(lines, i, 2)
                        
                        # Detect options if it's an MCQ
                        options = self._detect_mcq_options(lines, i)
                        
                        question = Question(
                            text=question_text.strip(),
                            question_type=q_type,
                            confidence=pattern_info['confidence'],
                            options=options,
                            context=context,
                            line_number=i
                        )
                        
                        questions.append(question)
                        self.logger.debug(f"Detected {q_type}: {question_text[:50]}...")
        
        # Remove duplicates and sort by confidence
        questions = self._remove_duplicates(questions)
        questions.sort(key=lambda q: q.confidence, reverse=True)
        
        self.logger.info(f"Detected {len(questions)} questions")
        return questions
    
    def _detect_mcq_options(self, lines: List[str], question_line: int) -> Optional[List[str]]:
        """
        Detect MCQ options following a question
        
        Args:
            lines: All text lines
            question_line: Index of the question line
            
        Returns:
            List of option texts or None
        """
        options = []
        
        # Look for options in the next few lines
        for i in range(question_line + 1, min(question_line + 6, len(lines))):
            line = lines[i].strip()
            if not line:
                continue
                
            # Check if line matches any MCQ option pattern
            for pattern in self.mcq_option_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    option_text = match.group(1).strip()
                    options.append(option_text)
                    break
            else:
                # If line doesn't match option pattern, stop looking
                if options:  # Only stop if we already found some options
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
        """
        Remove duplicate questions based on text similarity
        
        Args:
            questions: List of Question objects
            
        Returns:
            List with duplicates removed
        """
        unique_questions = []
        seen_texts = set()
        
        for question in questions:
            # Normalize text for comparison
            normalized = re.sub(r'\s+', ' ', question.text.lower().strip())
            
            if normalized not in seen_texts:
                seen_texts.add(normalized)
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
