"""
This module contains exceptions specific to SimpleAGI.
"""

class InvalidLLMResponseError(Exception):
    """Exception raised when the LLM response can't be parsed.
    
    Attributes:
        None
    """
