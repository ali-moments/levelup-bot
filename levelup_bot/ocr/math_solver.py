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
        if not text:
            return None
        
        # Handle LaTeX array/matrix notation
        # Pattern: \begin{array} ... \end{array} with numbers
        latex_array_pattern = r'\\begin\{array\}.*?\\end\{array\}'
        if re.search(latex_array_pattern, text, re.DOTALL):
            logger.debug("Detected LaTeX array notation, attempting to parse...")
            # Extract all numbers from the array
            numbers = re.findall(r'\{(\d+)\}', text)
            if numbers:
                # Convert to integers
                nums = [int(n) for n in numbers if n.isdigit()]
                if nums:
                    # For simple arrays, try common operations
                    # If 2 numbers: add them
                    # If 4+ numbers: sum all
                    if len(nums) == 2:
                        result = nums[0] + nums[1]
                        logger.info(f"Solved LaTeX array (2 numbers): {nums[0]} + {nums[1]} = {result}")
                        return float(result)
                    elif len(nums) >= 2:
                        result = sum(nums)
                        logger.info(f"Solved LaTeX array (sum of {len(nums)} numbers): {nums} = {result}")
                        return float(result)
        
        # Clean the text and extract math expression
        # Handle patterns like "12 + 3 = ?" or "12+3=?"
        # Replace Persian/Arabic operators with standard ones
        text = text.replace('×', '*').replace('÷', '/').replace('=', '').replace('?', '')
        text = text.replace('x', '*').replace('X', '*')  # Handle 'x' as multiplication
        # Remove LaTeX markers if present
        text = re.sub(r'\$\$', '', text)  # Remove $$ markers
        text = re.sub(r'\\begin\{array\}.*?\\end\{array\}', '', text, flags=re.DOTALL)  # Remove array blocks
        text = text.strip()
        
        # Remove common OCR artifacts and noise
        # Remove letters that might be OCR mistakes (but keep operators)
        # First, try to find the math expression pattern before cleaning too much
        pattern = r'(\d+(?:\.\d+)?)\s*([+\-*/×÷])\s*(\d+(?:\.\d+)?)'
        match = re.search(pattern, text)
        
        if match:
            num1_str = match.group(1)
            operator = match.group(2)
            num2_str = match.group(3)
            
            # Normalize operator
            operator = operator.replace('×', '*').replace('÷', '/')
            
            try:
                num1 = float(num1_str)
                num2 = float(num2_str)
                
                if operator == '+':
                    result = num1 + num2
                elif operator == '-':
                    result = num1 - num2
                elif operator == '*':
                    result = num1 * num2
                elif operator == '/':
                    if num2 == 0:
                        logger.warning("Division by zero detected")
                        return None
                    result = num1 / num2
                else:
                    return None
                
                logger.info(f"Solved: {num1} {operator} {num2} = {result}")
                return result
            except ValueError:
                logger.warning(f"Could not convert numbers: {num1_str}, {num2_str}")
        
        # If no pattern match, try to extract and evaluate the expression
        # Remove any non-math characters but keep operators and numbers
        cleaned = re.sub(r'[^\d+\-*/.() ]', '', text)
        cleaned = cleaned.strip()
        
        if cleaned:
            # Try to find a valid math expression in the cleaned text
            # Look for patterns like: number operator number
            simple_pattern = r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)'
            simple_match = re.search(simple_pattern, cleaned)
            
            if simple_match:
                try:
                    num1 = float(simple_match.group(1))
                    operator = simple_match.group(2)
                    num2 = float(simple_match.group(3))
                    
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
                    
                    logger.info(f"Solved (from cleaned text): {num1} {operator} {num2} = {result}")
                    return result
                except (ValueError, ZeroDivisionError):
                    pass
            
            # Last resort: try to evaluate the entire cleaned expression
            # This is less safe but might work for simple expressions
            try:
                # Only evaluate if it looks like a simple math expression
                if re.match(r'^[\d+\-*/.() ]+$', cleaned) and any(op in cleaned for op in ['+', '-', '*', '/']):
                    result = eval(cleaned)
                    if isinstance(result, (int, float)):
                        logger.info(f"Solved (via eval): {cleaned} = {result}")
                        return float(result)
            except Exception as e:
                logger.debug(f"Eval failed for '{cleaned}': {e}")
        
        logger.warning(f"Could not parse math expression from text: {text}")
        return None
    except Exception as e:
        logger.error(f"Error parsing math expression: {e}", exc_info=True)
        return None
