"""Math expression parsing and solving."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def parse_and_solve_math(text: str) -> Optional[float]:
    """Parse math expression from text and solve it.
    
    Args:
        text: Text containing a math expression
        
    Returns:
        The solution as a float, or None if parsing fails
    """
    try:
        # Clean the text and extract math expression
        # Handle patterns like "12 + 3 = ?" or "12+3=?"
        # Replace Persian operators with standard ones
        text = text.replace('×', '*').replace('÷', '/').replace('=', '').replace('?', '').strip()
        
        # Try to find math expression pattern
        # Match patterns like: number operator number
        pattern = r'(\d+)\s*([+\-*/])\s*(\d+)'
        match = re.search(pattern, text)
        
        if match:
            num1 = float(match.group(1))
            operator = match.group(2)
            num2 = float(match.group(3))
            
            if operator == '+':
                result = num1 + num2
            elif operator == '-':
                result = num1 - num2
            elif operator == '*':
                result = num1 * num2
            elif operator == '/':
                if num2 == 0:
                    return None
                result = num1 / num2
            else:
                return None
            
            return result
        
        # If no pattern match, try to evaluate the entire expression safely
        # Remove any non-math characters
        cleaned = re.sub(r'[^\d+\-*/.() ]', '', text)
        if cleaned:
            try:
                result = eval(cleaned)
                return float(result) if isinstance(result, (int, float)) else None
            except:
                pass
        
        return None
    except Exception as e:
        logger.error(f"Error parsing math expression: {e}")
        return None
