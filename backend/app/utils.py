import re

def to_proper_case(text: str) -> str:
    """
    Convert a lowercase string to proper case (first letter of each word capitalized).
    Handles common abbreviations and special cases.
    """
    if not text:
        return text
    
    # Common abbreviations that should remain uppercase
    abbreviations = {
        'atm', 'tv', 'pc', 'dvd', 'cd', 'usb', 'wifi', 'gps', 'covid', 'covid-19',
        'id', 'usa', 'uk', 'eu', 'un', 'nato', 'fbi', 'cia', 'irs', 'fda', 'epa',
        'ceo', 'cfo', 'cto', 'hr', 'it', 'qa', 'ui', 'ux', 'api', 'url', 'html',
        'css', 'js', 'php', 'sql', 'aws', 'api', 'sdk', 'ios', 'android', 'mac',
        'pc', 'laptop', 'smartphone', 'tablet', 'wifi', 'bluetooth', '4g', '5g'
    }
    
    # Split by spaces and hyphens
    words = re.split(r'[\s\-]+', text.lower())
    
    def capitalize_word(word):
        if word in abbreviations:
            return word.upper()
        elif word.startswith('mc') and len(word) > 2:
            # Handle names like "McDonald"
            return word[:2] + word[2:].capitalize()
        elif word.startswith('mac') and len(word) > 3:
            # Handle names like "MacDonald"
            return word[:3] + word[3:].capitalize()
        else:
            return word.capitalize()
    
    # Capitalize each word
    proper_words = [capitalize_word(word) for word in words if word]
    
    # Join with spaces (preserve original spacing/hyphenation)
    if '-' in text:
        return '-'.join(proper_words)
    else:
        return ' '.join(proper_words)

def format_category_name(name: str) -> str:
    """
    Format a category name for display with proper case.
    """
    return to_proper_case(name)

def format_subcategory_name(name: str) -> str:
    """
    Format a subcategory name for display with proper case.
    """
    return to_proper_case(name)

def format_account_name(name: str) -> str:
    """
    Format an account name for display with proper case.
    """
    return to_proper_case(name)
