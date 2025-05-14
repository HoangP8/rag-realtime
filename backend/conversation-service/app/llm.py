"""
LLM service for OpenAI integration
"""
import logging
from typing import List

import openai
from openai import OpenAI

from app.config import settings
from app.models import MessageResponse


class LLMService:
    """Service for LLM operations"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)
        
        # Default model
        self.model = "gpt-4o-mini"
    
    async def generate_response(self, conversation_history: List[MessageResponse], user_message: str) -> str:
        """Generate a response from the LLM"""
        try:
            # Format conversation history for OpenAI
            messages = []
            
            # Add system message if not present in history
            has_system_message = any(msg.role == "system" for msg in conversation_history)
            if not has_system_message:
                messages.append({
                    "role": "system",
                    "content": "You are a helpful medical assistant. Provide accurate and helpful information about medical topics. If you're unsure about something, acknowledge the limitations of your knowledge and suggest consulting with a healthcare professional."
                })
            
            # Add conversation history
            for msg in conversation_history:
                if msg.role in ["user", "assistant", "system"]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Add the new user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract and return the response text
            return response.choices[0].message.content
        
        except Exception as e:
            self.logger.error(f"Error generating LLM response: {str(e)}")
            # Return a fallback response in case of error
            return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
