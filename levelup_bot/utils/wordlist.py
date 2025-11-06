"""Wordlist loading utility."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_wordlist(filename: str = "data/wordlist.txt") -> list[str]:
    """Load words from wordlist.txt file.
    
    Args:
        filename: Path to the wordlist file
        
    Returns:
        List of words from the file
    """
    try:
        # Try data/wordlist.txt first, then fallback to wordlist.txt in root
        wordlist_path = Path(filename)
        if not wordlist_path.exists():
            # Fallback to root directory for backward compatibility
            wordlist_path = Path("wordlist.txt")
        
        with open(wordlist_path, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(words)} words from {wordlist_path}")
        return words
    except FileNotFoundError:
        logger.error(f"Wordlist file '{wordlist_path}' not found!")
        return []
    except Exception as e:
        logger.error(f"Error loading wordlist: {e}")
        return []

