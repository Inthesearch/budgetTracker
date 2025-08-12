import React, { useState, useRef, useEffect } from 'react';
import './MultiSelect.css';

const MultiSelect = ({ 
  options, 
  selectedValues, 
  onSelectionChange, 
  placeholder = "Select options...",
  searchable = true,
  maxHeight = "200px"
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const dropdownRef = useRef(null);
  const searchInputRef = useRef(null);

  // Filter options based on search term
  const filteredOptions = options.filter(option =>
    option.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex(prev => 
            prev < filteredOptions.length - 1 ? prev + 1 : prev
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex(prev => prev > 0 ? prev - 1 : -1);
          break;
        case 'Enter':
          e.preventDefault();
          if (highlightedIndex >= 0) {
            handleOptionClick(filteredOptions[highlightedIndex]);
          }
          break;
        case 'Escape':
          setIsOpen(false);
          setSearchTerm('');
          setHighlightedIndex(-1);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, highlightedIndex, filteredOptions]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm('');
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleOptionClick = (option) => {
    const newSelection = selectedValues.includes(option)
      ? selectedValues.filter(item => item !== option)
      : [...selectedValues, option];
    
    onSelectionChange(newSelection);
    setSearchTerm('');
    setHighlightedIndex(-1);
  };

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen && searchable) {
      setTimeout(() => searchInputRef.current?.focus(), 0);
    }
    setSearchTerm('');
    setHighlightedIndex(-1);
  };

  const removeSelected = (option) => {
    const newSelection = selectedValues.filter(item => item !== option);
    onSelectionChange(newSelection);
  };

  const clearAll = () => {
    onSelectionChange([]);
  };

  const getDisplayText = () => {
    if (selectedValues.length === 0) return placeholder;
    if (selectedValues.length === 1) return selectedValues[0];
    return `${selectedValues.length} selected`;
  };

  return (
    <div className="multi-select" ref={dropdownRef}>
      <div 
        className={`multi-select-trigger ${isOpen ? 'open' : ''}`}
        onClick={handleToggle}
      >
        <div className="selected-items">
          {selectedValues.length === 0 ? (
            <span className="placeholder">{placeholder}</span>
          ) : (
            <div className="selected-tags">
              {selectedValues.slice(0, 2).map(option => (
                <span key={option} className="selected-tag">
                  {option}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeSelected(option);
                    }}
                    className="remove-tag"
                  >
                    ×
                  </button>
                </span>
              ))}
              {selectedValues.length > 2 && (
                <span className="more-count">+{selectedValues.length - 2}</span>
              )}
            </div>
          )}
        </div>
        <span className="dropdown-arrow">▼</span>
      </div>

      {isOpen && (
        <div className="multi-select-dropdown" style={{ maxHeight }}>
          {searchable && (
            <div className="search-container">
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          )}

          <div className="options-container">
            {filteredOptions.length === 0 ? (
              <div className="no-options">No options found</div>
            ) : (
              filteredOptions.map((option, index) => (
                <div
                  key={option}
                  className={`option ${selectedValues.includes(option) ? 'selected' : ''} ${index === highlightedIndex ? 'highlighted' : ''}`}
                  onClick={() => handleOptionClick(option)}
                >
                  <input
                    type="checkbox"
                    checked={selectedValues.includes(option)}
                    readOnly
                  />
                  <span>{option}</span>
                </div>
              ))
            )}
          </div>

          {selectedValues.length > 0 && (
            <div className="dropdown-footer">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  clearAll();
                }}
                className="clear-all-btn"
              >
                Clear All
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MultiSelect;
