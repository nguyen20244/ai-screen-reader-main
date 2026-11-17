"""
Demo mode for AI Screen Reader - works without API keys
"""
import random
from ai_integration import AIResponse
from question_detector import Question

class DemoAI:
    """Demo AI that provides sample answers without API calls"""
    
    def __init__(self):
        self.demo_answers = {
            'mcq': [
                "The correct answer is C) Paris. Paris is the capital and largest city of France, located in the north-central part of the country.",
                "The correct answer is B) Python. Python is a high-level programming language known for its simplicity and readability.",
                "The correct answer is A) True. This statement is correct based on the given information.",
                "The correct answer is D) All of the above. Each option listed is a valid example of the concept being discussed."
            ],
            'general': [
                "Based on the question, the most accurate answer would be the option that best addresses the core concept being asked about.",
                "This question requires understanding of the fundamental principles involved. The correct approach is to analyze each option systematically.",
                "The answer depends on the specific context and requirements mentioned in the question. Consider the key factors involved.",
                "This is a conceptual question that tests understanding of the underlying theory. The correct answer follows logically from the given premises."
            ]
        }
    
    def answer_question(self, question: Question, provider: str = "demo") -> AIResponse:
        """Generate a demo answer for the question"""
        
        # Simulate processing time
        import time
        processing_time = random.uniform(0.5, 2.0)
        time.sleep(processing_time)
        
        # Choose answer type based on question
        if question.options and len(question.options) >= 2:
            # MCQ question
            answers = self.demo_answers['mcq']
            answer_type = 'mcq'
        else:
            # General question
            answers = self.demo_answers['general']
            answer_type = 'general'
        
        # Select a random demo answer
        demo_answer = random.choice(answers)
        
        # Add question-specific context
        if question.options:
            demo_answer += f"\n\nOptions analyzed:\n"
            for i, option in enumerate(question.options):
                letter = chr(65 + i)  # A, B, C, D
                demo_answer += f"{letter}) {option}\n"
        
        return AIResponse(
            answer=demo_answer,
            provider="demo",
            model="demo-v1.0",
            processing_time=processing_time,
            confidence=0.85
        )
    
    def get_available_providers(self):
        """Return demo provider"""
        return ['demo']
    
    def test_connection(self, provider: str) -> bool:
        """Demo connection always works"""
        return True

# Sample questions for demo
DEMO_QUESTIONS = [
    {
        'text': 'What is the capital of France?',
        'options': ['London', 'Berlin', 'Paris', 'Madrid'],
        'type': 'mcq'
    },
    {
        'text': 'Which of the following is a programming language?',
        'options': ['HTML', 'Python', 'CSS', 'SQL'],
        'type': 'mcq'
    },
    {
        'text': 'What is the primary function of a CPU?',
        'options': ['Store data', 'Process instructions', 'Display graphics', 'Connect to internet'],
        'type': 'mcq'
    },
    {
        'text': 'True or False: Python is an interpreted language.',
        'options': ['True', 'False'],
        'type': 'true_false'
    }
]

def create_demo_question(index=None):
    """Create a demo question for testing"""
    if index is None:
        index = random.randint(0, len(DEMO_QUESTIONS) - 1)
    
    demo_q = DEMO_QUESTIONS[index % len(DEMO_QUESTIONS)]
    
    return Question(
        text=demo_q['text'],
        question_type=demo_q['type'],
        confidence=0.9,
        options=demo_q['options']
    )
