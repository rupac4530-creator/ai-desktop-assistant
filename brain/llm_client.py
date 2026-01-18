import os
import ollama

class LLMClient:
    def __init__(self, model=None):
        # Use model from env or default
        self.model = model or os.getenv('OLLAMA_MODEL', 'llama3')
        
        # Load default system prompt
        prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.default_system_prompt = f.read()
        else:
            self.default_system_prompt = "You are a helpful AI desktop assistant."
        
        # Conversation history for context
        self.history = []
        self.max_history = 10

    def get_response(self, user_input, system_prompt=None):
        """
        Get response from Ollama LLM.
        
        Args:
            user_input: User's message
            system_prompt: Optional custom system prompt (for planner, etc.)
        
        Returns:
            LLM response text
        """
        messages = [
            {"role": "system", "content": system_prompt or self.default_system_prompt}
        ]
        
        # Add history for context (skip if custom system prompt)
        if not system_prompt:
            messages.extend(self.history[-self.max_history:])
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            
            reply = response['message']['content']
            
            # Add to history (only for default conversations)
            if not system_prompt:
                self.history.append({"role": "user", "content": user_input})
                self.history.append({"role": "assistant", "content": reply})
            
            return reply
            
        except Exception as e:
            print(f"[LLM] Error: {e}")
            return f"I'm having trouble connecting to the AI. Error: {str(e)[:100]}"
    
    def clear_history(self):
        """Clear conversation history."""
        self.history = []
    
    def set_model(self, model):
        """Change the active model."""
        self.model = model
        print(f"[LLM] Switched to model: {model}")
