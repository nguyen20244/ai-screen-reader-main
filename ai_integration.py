"""
AI integration module for the AI Screen Reader
Supports both OpenAI (ChatGPT) and Anthropic (Claude) APIs
"""
import openai
import anthropic
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
from config import config
from question_detector import Question

SYSTEM_PROMPT = "You are an expert assistant that provides ONE definitive answer to each question. Never say 'it could be' or list multiple possibilities. For multiple choice questions, state ONLY the correct letter (A, B, C, or D) followed by a brief explanation. Be decisive and confident in your answer."

@dataclass
class AIResponse:
    """Data class for AI responses"""
    answer: str
    provider: str
    model: str
    confidence: float = 0.0
    processing_time: float = 0.0
    error: Optional[str] = None

class AIIntegration:
    """Handles AI API integrations for answering questions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize API clients
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_api_key = None
        
        self._initialize_clients()
        
        # Model configurations
        self.models = {
            'openai': {
                'default': 'gpt-3.5-turbo',
                'advanced': 'gpt-4',
                'max_tokens': 1000,
                'temperature': 0.1
            },
            'claude': {
                'default': 'claude-3-haiku-20240307',
                'advanced': 'claude-3-sonnet-20240229',
                'max_tokens': 1000,
                'temperature': 0.1
            },
            'gemini': {
                'default': 'gemini-1.5-flash',
                'advanced': 'gemini-1.5-flash',
                'max_tokens': 1000,
                'temperature': 0.1
            }
        }
    
    def _initialize_clients(self):
        """Initialize API clients based on available keys"""
        try:
            if config.openai_api_key:
                self.openai_client = openai.OpenAI(api_key=config.openai_api_key)
                self.logger.info("OpenAI client initialized")
            else:
                self.logger.warning("OpenAI API key not found")
                
            if config.anthropic_api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=config.anthropic_api_key)
                self.logger.info("Anthropic client initialized")
            else:
                self.logger.warning("Anthropic API key not found")

            if config.gemini_api_key:
                self.gemini_api_key = config.gemini_api_key
                self.logger.info("Google Gemini initialized")
            else:
                self.logger.warning("Gemini API key not found")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize AI clients: {e}")
    
    def answer_question(self, question: Question, provider: str = None) -> AIResponse:
        """
        Get AI answer for a question
        
        Args:
            question: Question object to answer
            provider: AI provider ('openai' or 'claude'), uses default if None
            
        Returns:
            AIResponse object with the answer
        """
        if not provider:
            provider = config.default_ai_provider
        
        # Format question for AI
        formatted_question = self._format_question_prompt(question)
        
        try:
            if provider == 'openai' and self.openai_client:
                return self._query_openai(formatted_question, question)
            elif provider == 'claude' and self.anthropic_client:
                return self._query_claude(formatted_question, question)
            elif provider == 'gemini' and self.gemini_api_key:
                return self._query_gemini(formatted_question, question)
            else:
                return AIResponse(
                    answer="AI provider not available or not configured",
                    provider=provider,
                    model="none",
                    error=f"Provider {provider} not available"
                )
                
        except Exception as e:
            self.logger.error(f"AI query failed: {e}")
            return AIResponse(
                answer=f"Error getting AI response: {str(e)}",
                provider=provider,
                model="error",
                error=str(e)
            )
    
    def _query_openai(self, prompt: str, question: Question) -> AIResponse:
        """Query OpenAI API"""
        import time
        start_time = time.time()
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.models['openai']['default'],
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.models['openai']['max_tokens'],
                temperature=0.1  # Lower temperature for more consistent answers
            )
            
            processing_time = time.time() - start_time
            answer = response.choices[0].message.content.strip()
            
            return AIResponse(
                answer=answer,
                provider='openai',
                model=self.models['openai']['default'],
                processing_time=processing_time
            )
            
        except Exception as e:
            return AIResponse(
                answer=f"OpenAI API error: {str(e)}",
                provider='openai',
                model=self.models['openai']['default'],
                error=str(e)
            )
    
    def _query_claude(self, prompt: str, question: Question) -> AIResponse:
        """Query Anthropic Claude API"""
        import time
        start_time = time.time()
        
        try:
            response = self.anthropic_client.messages.create(
                system=SYSTEM_PROMPT,
                model=self.models['claude']['default'],
                max_tokens=self.models['claude']['max_tokens'],
                temperature=0.1,  # Lower temperature for more consistent answers
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            processing_time = time.time() - start_time
            answer = response.content[0].text.strip()
            
            return AIResponse(
                answer=answer,
                provider='claude',
                model=self.models['claude']['default'],
                processing_time=processing_time
            )
            
        except Exception as e:
            return AIResponse(
                answer=f"Claude API error: {str(e)}",
                provider='claude',
                model=self.models['claude']['default'],
                error=str(e)
            )

    def _query_gemini(self, prompt: str, question: Question) -> AIResponse:
        """Query Google Gemini API"""
        import time
        import requests
        start_time = time.time()

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.models['gemini']['default']}:generateContent"

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }

            response = requests.post(url, json=payload, headers={"x-goog-api-key": self.gemini_api_key}, timeout=30)

            if response.status_code == 200:
                result = response.json()
                candidates = result.get('candidates', [])
                if candidates:
                    content = candidates[0].get('content', {})
                    parts = content.get('parts', [])
                    if parts:
                        answer = parts[0].get('text', 'No answer generated').strip()
                    else:
                        answer = 'No answer in response'
                else:
                    answer = 'No candidates in response'

                processing_time = time.time() - start_time

                return AIResponse(
                    answer=answer,
                    provider='gemini',
                    model=self.models['gemini']['default'],
                    processing_time=processing_time
                )
            else:
                if response.status_code == 429:
                    # Rate limit exceeded - provide helpful message
                    self.logger.warning("Gemini rate limit exceeded (429). Switch to Claude or OpenAI.")
                    return AIResponse(
                        answer="⚠️ Gemini rate limit exceeded. Please switch to 'claude' or 'openai' provider, or wait a few minutes before trying again.",
                        provider='gemini',
                        model=self.models['gemini']['default'],
                        error="Rate limit exceeded"
                    )
                else:
                    return AIResponse(
                        answer=f"Gemini API error: HTTP {response.status_code}",
                        provider='gemini',
                        model=self.models['gemini']['default'],
                        error=f"HTTP {response.status_code}"
                    )

        except Exception as e:
            return AIResponse(
                answer=f"Gemini API error: {str(e)}",
                provider='gemini',
                model=self.models['gemini']['default'],
                error=str(e)
            )

    def _format_question_prompt(self, question: Question) -> str:
        """Format question into a proper prompt for AI"""
        prompt = f"Answer this question with ONE definitive answer only:\n\n{question.text}\n"

        if question.options:
            prompt += "\nOptions:\n"
            for i, option in enumerate(question.options):
                letter = chr(65 + i)  # A, B, C, D
                prompt += f"{letter}) {option}\n"
            prompt += "\nIMPORTANT: Provide ONLY the correct answer letter (A, B, C, or D) followed by a brief explanation. Do not mention other possibilities or say 'it could be'. Give me the ONE correct answer.\n"
        else:
            prompt += "\nIMPORTANT: Provide ONE clear, definitive answer. Do not list multiple possibilities. Give me the single correct answer.\n"
        
        if question.context and question.context != question.text:
            prompt += f"\nAdditional context:\n{question.context}\n"
        
        return prompt
    
    def batch_answer_questions(self, questions: List[Question], provider: str = None) -> List[AIResponse]:
        """
        Answer multiple questions in batch
        
        Args:
            questions: List of Question objects
            provider: AI provider to use
            
        Returns:
            List of AIResponse objects
        """
        responses = []
        
        for question in questions:
            response = self.answer_question(question, provider)
            responses.append(response)

            # Add delay to avoid rate limiting (longer for Gemini)
            import time
            if provider == 'gemini':
                time.sleep(2.0)  # 2 second delay for Gemini
            else:
                time.sleep(0.5)  # 0.5 second delay for others
        
        return responses
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers"""
        providers = []

        if self.openai_client:
            providers.append('openai')
        if self.anthropic_client:
            providers.append('claude')
        if self.gemini_api_key:
            providers.append('gemini')

        return providers
    
    def test_connection(self, provider: str) -> bool:
        """Test connection to AI provider"""
        try:
            test_question = Question(
                text="What is 2+2?",
                question_type="test",
                confidence=1.0
            )
            
            response = self.answer_question(test_question, provider)
            return response.error is None
            
        except Exception as e:
            self.logger.error(f"Connection test failed for {provider}: {e}")
            return False
