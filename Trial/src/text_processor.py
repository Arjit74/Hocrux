"""
Text Processing Module

This module handles the conversion of recognized gestures to text,
including text formatting, grammar correction, and context management.
"""

import re
from typing import Dict, Any, List, Optional

class TextProcessor:
    def __init__(self, config: Dict[str, Any]):
        """Initialize the text processor with configuration."""
        self.config = config
        self.context = {
            'last_gesture': None,
            'last_text': '',
            'word_buffer': [],
            'sentence_buffer': []
        }
        
        # Initialize gesture to text mappings
        self.gesture_to_text = {
            'hello': 'Hello',
            'thank_you': 'Thank you',
            'yes': 'Yes',
            'no': 'No',
            'help': 'Help',
            'please': 'Please',
            'goodbye': 'Goodbye',
            'i_love_you': 'I love you',
            'sorry': 'I\'m sorry',
            'name': 'My name is',
            'nice_to_meet_you': 'Nice to meet you',
            'how_are_you': 'How are you?',
            'i_am_fine': 'I am fine, thank you',
            'what_time': 'What time is it?',
            'where_bathroom': 'Where is the bathroom?',
            'water': 'Water',
            'food': 'Food',
            'help_me': 'Help me',
            'understand': 'I understand',
            'dont_understand': 'I don\'t understand'
        }
        
        # Update with any custom mappings from config
        if 'gesture_mappings' in config.get('text_processor', {}):
            self.gesture_to_text.update(config['text_processor']['gesture_mappings'])
    
    def gesture_to_text(self, gesture_data: Dict[str, Any]) -> str:
        """
        Convert a recognized gesture to text.
        
        Args:
            gesture_data: Dictionary containing gesture information
                - 'gesture': The recognized gesture label
                - 'confidence': Confidence score (0-1)
                - 'landmarks': Optional hand landmarks
                
        Returns:
            Formatted text representation of the gesture
        """
        if not gesture_data or 'gesture' not in gesture_data:
            return ''
            
        gesture = gesture_data['gesture']
        confidence = gesture_data.get('confidence', 0.0)
        
        # Skip if confidence is too low
        min_confidence = self.config.get('text_processor', {}).get('min_confidence', 0.5)
        if confidence < min_confidence:
            return ''
        
        # Map gesture to text
        text = self.gesture_to_text.get(gesture, '')
        
        # Update context
        self.context['last_gesture'] = gesture
        
        # Process the text with formatting and context
        processed_text = self._process_text(text, gesture_data)
        
        # Update last text
        self.context['last_text'] = processed_text
        
        return processed_text
    
    def _process_text(self, text: str, gesture_data: Dict[str, Any]) -> str:
        """Process and format the text based on context and rules."""
        if not text:
            return ''
            
        # Apply text formatting rules
        text = self._apply_formatting_rules(text)
        
        # Handle sentence structure if needed
        if self.config.get('text_processor', {}).get('enable_grammar_correction', True):
            text = self._correct_grammar(text)
        
        return text
    
    def _apply_formatting_rules(self, text: str) -> str:
        """Apply formatting rules to the text."""
        # Capitalize first letter of each sentence
        if not text:
            return text
            
        # Remove any extra whitespace
        text = ' '.join(text.split())
        
        # Ensure proper punctuation
        if not text.endswith(('.', '!', '?')):
            # Add period if it's a statement, question mark if it's a question
            if any(q_word in text.lower() for q_word in ['who', 'what', 'when', 'where', 'why', 'how', '?']):
                text += '?'
            else:
                text += '.'
                
        # Capitalize first letter
        text = text[0].upper() + text[1:]
        
        return text
    
    def _correct_grammar(self, text: str) -> str:
        """Apply basic grammar correction rules."""
        # Common contractions
        contractions = {
            "i am": "I'm",
            "i will": "I'll",
            "i have": "I've",
            "i would": "I'd",
            "you are": "you're",
            "you will": "you'll",
            "you have": "you've",
            "he is": "he's",
            "she is": "she's",
            "it is": "it's",
            "we are": "we're",
            "they are": "they're",
            "cannot": "can't",
            "do not": "don't",
            "does not": "doesn't",
            "did not": "didn't",
            "is not": "isn't",
            "are not": "aren't",
            "was not": "wasn't",
            "were not": "weren't",
            "have not": "haven't",
            "has not": "hasn't",
            "had not": "hadn't",
            "will not": "won't",
            "would not": "wouldn't",
            "should not": "shouldn't",
            "could not": "couldn't",
            "might not": "mightn't",
            "must not": "mustn't"
        }
        
        # Apply contractions
        for full, contraction in contractions.items():
            text = re.sub(rf'\b{re.escape(full)}\b', contraction, text, flags=re.IGNORECASE)
        
        # Fix common issues
        text = re.sub(r'\bi\b', 'I', text)  # Capitalize single 'i'
        
        return text
    
    def reset_context(self):
        """Reset the processing context."""
        self.context = {
            'last_gesture': None,
            'last_text': '',
            'word_buffer': [],
            'sentence_buffer': []
        }
    
    def get_context(self) -> Dict[str, Any]:
        """Get the current processing context."""
        return self.context.copy()
    
    def set_context(self, context: Dict[str, Any]):
        """Set the processing context."""
        self.context.update(context)

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'text_processor': {
            'min_confidence': 0.5,
            'enable_grammar_correction': True,
            'gesture_mappings': {
                'custom_gesture': 'Custom text'
            }
        }
    }
    
    processor = TextProcessor(config)
    
    # Example gesture data
    gesture_data = {
        'gesture': 'hello',
        'confidence': 0.9,
        'landmarks': None
    }
    
    # Convert gesture to text
    text = processor.gesture_to_text(gesture_data)
    print(f"Converted text: {text}")
    
    # Get current context
    print(f"Context: {processor.get_context()}")
