from typing import List, Dict, Any
import streamlit as st
from retrieval import Retriever
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from typing import List, Dict, Any
import streamlit as st
from retrieval import Retriever
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage



class LMMentorBot:
    def __init__(self):
        self.chat = ChatOpenAI(
            temperature=0.7,
            model_name="gpt-4",
            openai_api_key=st.secrets["OPENAI_KEY"]
        )
        self.retriever = Retriever()
        self.conversation_history = []
        self.reflection_mode = False
        
    def generate_reflection_prompt(self, topic: str) -> str:
        """Generate a reflection prompt based on the topic."""
        reflection_templates = {
            "search": "Before we dive into searching algorithms, could you share what you already know about them?",
            "sort": "Before we discuss sorting, what experience do you have with organizing data?",
            "default": f"Before we explore this topic, could you share what you already know about {topic}?"
        }
        
        # Determine which template to use
        for key in reflection_templates:
            if key in topic.lower():
                return reflection_templates[key]
        return reflection_templates["default"]

    def generate_follow_up_prompts(self, topic: str, user_response: str) -> List[str]:
        """Generate contextual follow-up prompts based on the topic and user's response."""
        system_prompt = f"""
        Based on the user's response about {topic}, generate 2 engaging follow-up questions that:
        1. Connect to their personal experience
        2. Encourage deeper technical understanding
        Keep each question concise and conversational.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_response)
        ]
        
        response = self.chat(messages)
        # Split the response into individual questions
        follow_ups = [q.strip() for q in response.content.split('\n') if q.strip()]
        return follow_ups[:2]  # Return maximum 2 questions

    def get_response(self, user_input: str) -> str:
        """Process user input and generate appropriate response."""
        # Initialize conversation if it's empty
        if not self.conversation_history:
            # Check if this is a topic-based question
            if "what is" in user_input.lower() or "how does" in user_input.lower():
                self.reflection_mode = True
                reflection_prompt = self.generate_reflection_prompt(user_input)
                self.conversation_history.append({"role": "assistant", "content": reflection_prompt})
                return reflection_prompt

        if self.reflection_mode:
            # Generate follow-up questions based on user's reflection
            follow_ups = self.generate_follow_up_prompts(
                self.conversation_history[0]["content"], 
                user_input
            )
            
            # Construct response with follow-ups
            response = "Thank you for sharing that! " + follow_ups[0]
            self.reflection_mode = False  # Exit reflection mode
            
            # Store the interaction
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return response

        # Regular conversation flow
        messages = [
            SystemMessage(content="""You are a mentor helping students learn computer science concepts. 
            Be encouraging and use the Socratic method to guide students to understanding.""")
        ]
        
        # Add conversation history
        for message in self.conversation_history:
            if message["role"] == "user":
                messages.append(HumanMessage(content=message["content"]))
            else:
                messages.append(AIMessage(content=message["content"]))
        
        # Add current user input
        messages.append(HumanMessage(content=user_input))
        
        # Get response
        response = self.chat(messages)
        
        # Store the interaction
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response.content})
        
        return response.content

    def reset(self):
        """Reset the conversation history."""
        self.conversation_history = []
        self.reflection_mode = False