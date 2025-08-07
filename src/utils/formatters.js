/**
 * Convert a lowercase string to proper case (first letter of each word capitalized).
 * Handles common abbreviations and special cases.
 */
export const toProperCase = (text) => {
  if (!text) return text;
  
  // Common abbreviations that should remain uppercase
  const abbreviations = new Set([
    'atm', 'tv', 'pc', 'dvd', 'cd', 'usb', 'wifi', 'gps', 'covid', 'covid-19',
    'id', 'usa', 'uk', 'eu', 'un', 'nato', 'fbi', 'cia', 'irs', 'fda', 'epa',
    'ceo', 'cfo', 'cto', 'hr', 'it', 'qa', 'ui', 'ux', 'api', 'url', 'html',
    'css', 'js', 'php', 'sql', 'aws', 'api', 'sdk', 'ios', 'android', 'mac',
    'pc', 'laptop', 'smartphone', 'tablet', 'wifi', 'bluetooth', '4g', '5g'
  ]);
  
  // Split by spaces and hyphens
  const words = text.toLowerCase().split(/[\s\-]+/);
  
  const capitalizeWord = (word) => {
    if (abbreviations.has(word)) {
      return word.toUpperCase();
    } else if (word.startsWith('mc') && word.length > 2) {
      // Handle names like "McDonald"
      return word.slice(0, 2) + word.slice(2).charAt(0).toUpperCase() + word.slice(3);
    } else if (word.startsWith('mac') && word.length > 3) {
      // Handle names like "MacDonald"
      return word.slice(0, 3) + word.slice(3).charAt(0).toUpperCase() + word.slice(4);
    } else {
      return word.charAt(0).toUpperCase() + word.slice(1);
    }
  };
  
  // Capitalize each word
  const properWords = words.filter(word => word).map(capitalizeWord);
  
  // Join with spaces (preserve original spacing/hyphenation)
  if (text.includes('-')) {
    return properWords.join('-');
  } else {
    return properWords.join(' ');
  }
};

/**
 * Format a category name for display with proper case.
 */
export const formatCategoryName = (name) => {
  return toProperCase(name);
};

/**
 * Format a subcategory name for display with proper case.
 */
export const formatSubcategoryName = (name) => {
  return toProperCase(name);
};

/**
 * Format an account name for display with proper case.
 */
export const formatAccountName = (name) => {
  return toProperCase(name);
};

/**
 * Format any name for display with proper case.
 */
export const formatName = (name) => {
  return toProperCase(name);
};
