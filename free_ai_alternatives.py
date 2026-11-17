"""
Free AI alternatives for the Screen Reader
"""
import requests
import json
import logging
from typing import Optional
from dataclasses import dataclass
from question_detector import Question
from ai_integration import AIResponse

class OllamaAI:
    """Local AI using Ollama (completely free)"""
    
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.model = "llama3.2:1b"  # Lightweight model
    
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def answer_question(self, question: Question) -> AIResponse:
        """Answer question using Ollama"""
        import time
        start_time = time.time()
        
        try:
            prompt = self._format_prompt(question)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', 'No response generated')
                
                return AIResponse(
                    answer=answer,
                    provider="ollama",
                    model=self.model,
                    processing_time=time.time() - start_time
                )
            else:
                return AIResponse(
                    answer=f"Ollama error: {response.status_code}",
                    provider="ollama",
                    model=self.model,
                    error=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            return AIResponse(
                answer=f"Ollama connection error: {str(e)}",
                provider="ollama",
                model=self.model,
                error=str(e)
            )
    
    def _format_prompt(self, question: Question) -> str:
        """Format question for Ollama"""
        prompt = f"Answer this question clearly and concisely:\n\n{question.text}\n"
        
        if question.options:
            prompt += "\nOptions:\n"
            for i, option in enumerate(question.options):
                letter = chr(65 + i)
                prompt += f"{letter}) {option}\n"
            prompt += "\nProvide the correct letter and explain why."
        
        return prompt

class HuggingFaceAI:
    """Free Hugging Face API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key  # Optional - has free tier without key
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api-inference.huggingface.co/models"
        self.model = "microsoft/DialoGPT-medium"
    
    def answer_question(self, question: Question) -> AIResponse:
        """Answer question using Hugging Face"""
        import time
        start_time = time.time()
        
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            prompt = self._format_prompt(question)
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 200,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(
                f"{self.base_url}/{self.model}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    answer = result[0].get('generated_text', 'No answer generated')
                else:
                    answer = str(result)
                
                return AIResponse(
                    answer=answer,
                    provider="huggingface",
                    model=self.model,
                    processing_time=time.time() - start_time
                )
            else:
                return AIResponse(
                    answer=f"HuggingFace error: {response.status_code}",
                    provider="huggingface",
                    model=self.model,
                    error=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            return AIResponse(
                answer=f"HuggingFace error: {str(e)}",
                provider="huggingface",
                model=self.model,
                error=str(e)
            )
    
    def _format_prompt(self, question: Question) -> str:
        """Format question for HuggingFace"""
        return f"Q: {question.text}\nA:"

class GeminiAI:
    """Google Gemini free tier"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    def answer_question(self, question: Question) -> AIResponse:
        """Answer question using Gemini"""
        import time
        start_time = time.time()
        
        try:
            prompt = self._format_prompt(question)
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                candidates = result.get('candidates', [])
                if candidates:
                    content = candidates[0].get('content', {})
                    parts = content.get('parts', [])
                    if parts:
                        answer = parts[0].get('text', 'No answer generated')
                    else:
                        answer = 'No answer in response'
                else:
                    answer = 'No candidates in response'
                
                return AIResponse(
                    answer=answer,
                    provider="gemini",
                    model="gemini-pro",
                    processing_time=time.time() - start_time
                )
            else:
                return AIResponse(
                    answer=f"Gemini error: {response.status_code}",
                    provider="gemini",
                    model="gemini-pro",
                    error=f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            return AIResponse(
                answer=f"Gemini error: {str(e)}",
                provider="gemini",
                model="gemini-pro",
                error=str(e)
            )
    
    def _format_prompt(self, question: Question) -> str:
        """Format question for Gemini"""
        prompt = f"Answer this question:\n\n{question.text}\n"
        
        if question.options:
            prompt += "\nOptions:\n"
            for i, option in enumerate(question.options):
                letter = chr(65 + i)
                prompt += f"{letter}) {option}\n"
            prompt += "\nProvide the correct answer and explanation."
        
        return prompt

class FreeAIManager:
    """Manages multiple free AI providers"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available free providers"""
        from config import config

        # Ollama (local AI)
        ollama = OllamaAI()
        if ollama.is_available():
            self.providers['ollama'] = ollama
            self.logger.info("Ollama local AI available")

        # Hugging Face (free tier)
        self.providers['huggingface'] = HuggingFaceAI()

        # Add Gemini if API key is provided
        if config.gemini_api_key:
            self.providers['gemini'] = GeminiAI(config.gemini_api_key)
            self.logger.info("Google Gemini available")
    
    def get_available_providers(self) -> list:
        """Get list of available free providers"""
        return list(self.providers.keys())
    
    def answer_question(self, question: Question, provider: str = None) -> AIResponse:
        """Answer question using specified or best available provider"""
        if not self.providers:
            return AIResponse(
                answer="No free AI providers available",
                provider="none",
                model="none",
                error="No providers configured"
            )
        
        if provider and provider in self.providers:
            return self.providers[provider].answer_question(question)
        
        # Try providers in order of preference
        for provider_name in ['ollama', 'huggingface', 'gemini']:
            if provider_name in self.providers:
                try:
                    response = self.providers[provider_name].answer_question(question)
                    if not response.error:
                        return response
                except Exception as e:
                    self.logger.warning(f"Provider {provider_name} failed: {e}")
                    continue
        
        return AIResponse(
            answer="All free AI providers failed",
            provider="none",
            model="none",
            error="All providers failed"
        )
