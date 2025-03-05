from typing import Dict, List, Any, Optional
import openai
import json
import logging
import os
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for ReAct agents using ChatGPT"""
    
    def __init__(self, model: str = "gpt-4"):
        """Initialize the base agent
        
        Args:
            model: GPT model to use (default: gpt-4)
        """
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        openai.api_key = self.openai_api_key
        self.model = model
        self.conversation_history = []
    
    def _call_llm(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Make an API call to ChatGPT
        
        Args:
            prompt: The user prompt
            system_message: Optional system message to set context/behavior
            
        Returns:
            Model's response text
        """
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})
            
        # Add conversation history
        messages.extend(self.conversation_history)
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
    
    def _parse_react_output(self, output: str) -> Dict[str, Any]:
        """Parse the ReAct output from the LLM
        
        The expected format is:
        Thought: [reasoning about what to do]
        Action: [tool name]
        Action Input: [input for the tool in JSON format]
        
        or
        
        Thought: [reasoning about what to do]
        Final Answer: [final response to the query]
        
        Args:
            output: The LLM's response text
            
        Returns:
            Dictionary containing parsed components
        """
        lines = output.strip().split('\n')
        result = {}
        
        for line in lines:
            if line.startswith('Thought:'):
                result['thought'] = line[8:].strip()
            elif line.startswith('Action:'):
                result['action'] = line[7:].strip()
            elif line.startswith('Action Input:'):
                try:
                    # Try to parse as JSON
                    input_str = line[13:].strip()
                    result['action_input'] = json.loads(input_str)
                except json.JSONDecodeError:
                    # If not JSON, store as string
                    result['action_input'] = input_str
            elif line.startswith('Final Answer:'):
                result['final_answer'] = line[13:].strip()
                
        return result
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent type
        
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    def _get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools for this agent
        
        Returns:
            List of tool descriptions
        """
        pass
    
    def _format_tool_description(self) -> str:
        """Format the tool descriptions for the prompt
        
        Returns:
            Formatted tool description string
        """
        tools = self._get_available_tools()
        tool_str = "Available tools:\n\n"
        for tool in tools:
            tool_str += f"Tool: {tool['name']}\n"
            tool_str += f"Description: {tool['description']}\n"
            if 'parameters' in tool:
                tool_str += f"Parameters: {json.dumps(tool['parameters'], indent=2)}\n"
            tool_str += "\n"
        return tool_str
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
