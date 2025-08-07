import React, { useState, useMemo, useEffect  } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTransactions } from '../context/TransactionContext.jsx';
import { formatCategoryName, formatSubcategoryName } from '../utils/formatters.js';
import './BudgetGraph.css';

const BudgetGraph = () => {
  const { transactions, categories } = useTransactions();
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toLocaleDateString('en-CA'),
    end: new Date().toLocaleDateString('en-CA')
  });
  const [selectedCategories, setSelectedCategories] = useState([]);


  // Helper function to get category name with proper case
  const getCategoryName = (category) => {
    if (!category) return null;
    
    let name;
    
    // If category is a number (ID), we need to look it up from categories
    if (typeof category === 'number') {
      const categoryObj = categories.find(cat => cat.id === category);
      name = categoryObj ? categoryObj.name : `Category ${category}`;
    }
    // If category is a string, use it directly
    else if (typeof category === 'string') {
      name = category;
    }
    // If category is an object with name property
    else if (category && typeof category === 'object' && category.name) {
      name = category.name;
    }
    // Fallback
    else {
      name = `Category ${category}`;
    }
    
    return formatCategoryName(name);
  };

  // Helper function to get subcategory name with proper case
  const getSubcategoryName = (subcategory) => {
    if (!subcategory) return null;
    
    let name;
    
    // If subcategory is a number (ID), we need to look it up from subcategories
    if (typeof subcategory === 'number') {
      // For now, we'll use a fallback since we don't have subcategories in context
      name = `Subcategory ${subcategory}`;
    }
    // If subcategory is a string, use it directly
    else if (typeof subcategory === 'string') {
      name = subcategory;
    }
    // If subcategory is an object with name property
    else if (subcategory && typeof subcategory === 'object' && subcategory.name) {
      name = subcategory.name;
    }
    // Fallback
    else {
      name = `Subcategory ${subcategory}`;
    }
    
    return formatSubcategoryName(name);
  };

  // Get unique categories for filter
  const uniqueCategories = useMemo(() => {
    return [...new Set(
      transactions
        .map(t => getCategoryName(t.category))
        .filter(Boolean)
    )];
  }, [transactions]);

  // Filter transactions based on date range and selected categories
  const filteredTransactions = useMemo(() => {
    const filtered = transactions.filter(transaction => {
      const transactionDate = new Date(transaction.date);
      const startDate = new Date(dateRange.start);
      const endDate = new Date(dateRange.end);  
      
      // Date filter
      if (transactionDate < startDate || transactionDate > endDate) {
        return false;
      }
      
      // Category filter
      if (selectedCategories.length > 0 && !selectedCategories.includes(getCategoryName(transaction.category))) {
        return false;
      }
      
      return true;
    });
    
    return filtered;
  }, [transactions, dateRange, selectedCategories, categories]);



  // Calculate category totals
  const categoryData = useMemo(() => {
    const categoryTotals = {};
    
    filteredTransactions.forEach(transaction => {
      const categoryName = getCategoryName(transaction.category);
      
      if (categoryName) {
        if (!categoryTotals[categoryName]) {
          categoryTotals[categoryName] = 0;
        }
        
        if (transaction.type === 'expense') {
          categoryTotals[categoryName] += transaction.amount;
        } else if (transaction.type === 'income') {
          categoryTotals[categoryName] -= transaction.amount;
        }
      }
    });

    // Convert to array and sort by amount (descending)
    return Object.entries(categoryTotals)
      .map(([category, amount]) => ({
        category,
        amount: Math.abs(amount),
        isExpense: amount > 0
      }))
      .sort((a, b) => b.amount - a.amount);
  }, [filteredTransactions, categories]);

  // Calculate sub-category data for selected category
  const subCategoryData = useMemo(() => {
    if (!selectedCategory) return [];

    const subCategoryTotals = {};


    
    filteredTransactions
      .filter(t => getCategoryName(t.category) === selectedCategory)
      .forEach(transaction => {
        const subCategoryName = getSubcategoryName(transaction.sub_category);
        if (subCategoryName) {
          if (!subCategoryTotals[subCategoryName]) {
            subCategoryTotals[subCategoryName] = 0;
          }
          
          if (transaction.type === 'expense') {
            subCategoryTotals[subCategoryName] += transaction.amount;
          } else if (transaction.type === 'income') {
            subCategoryTotals[subCategoryName] -= transaction.amount;
          }
        }
      });

    return Object.entries(subCategoryTotals)
      .map(([subCategory, amount]) => ({
        category: subCategory,
        amount: Math.abs(amount),
        isExpense: amount > 0
      }))
      .sort((a, b) => b.amount - a.amount);
  }, [filteredTransactions, selectedCategory, transactions]);


  

  const handleCategoryClick = (data) => {
    if (selectedCategory === data.category) {
      setSelectedCategory(null);
    } else {
      setSelectedCategory(data.category);
    }
  };

  const handleCategoryFilterChange = (category) => {
    setSelectedCategories(prev => {
      if (prev.includes(category)) {
        return prev.filter(c => c !== category);
      } else {
        return [...prev, category];
      }
    });
  };

  const clearFilters = () => {
    setDateRange({
      start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toLocaleDateString('en-CA'),
      end: new Date().toLocaleDateString('en-CA')
    });
    setSelectedCategories([]);
    setSelectedCategory(null);
  };

  const displayData = selectedCategory ? subCategoryData : categoryData;
  const displayTitle = selectedCategory 
    ? `Sub-Categories for ${selectedCategory}`
    : 'Category Spending';
  


  return (
    <div className="budget-graph-container">
      <div className="graph-header">
        <h3>{displayTitle}</h3>
        {selectedCategory && (
          <button 
            onClick={() => setSelectedCategory(null)}
            className="back-button"
          >
            ← Back to Categories
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="graph-filters">
        <div className="filter-group">
          <label>Date Range:</label>
          <div className="date-inputs">
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
            />
            <span>to</span>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
            />
          </div>
        </div>

        {!selectedCategory && (
          <div className="filter-group">
            <label>Categories:</label>
            <div className="category-filters">
              {uniqueCategories.map(category => (
                <label key={category} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedCategories.includes(category)}
                    onChange={() => handleCategoryFilterChange(category)}
                  />
                  {category}
                </label>
              ))}
            </div>
          </div>
        )}

               <button onClick={clearFilters} className="clear-filters-btn">
         Clear Filters
       </button>
     </div>

     {/* Chart */}
      <div className="chart-container">
        {displayData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={displayData}
              layout="vertical"
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis 
                type="category" 
                dataKey="category" 
                width={100}
                tick={{ fontSize: 12 }}
              />
              <Tooltip 
                formatter={(value, name) => [`$${value.toFixed(2)}`, 'Amount']}
                labelFormatter={(label) => `Category: ${label}`}
              />
              <Bar 
                dataKey="amount" 
                fill="#667eea"
                onClick={!selectedCategory ? handleCategoryClick : undefined}
                style={{ cursor: !selectedCategory ? 'pointer' : 'default' }}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="no-data">
            <p>No data available for the selected filters.</p>
          </div>
        )}
      </div>

      {/* Summary */}
      {displayData.length > 0 && (
        <div className="graph-summary">
          <div className="summary-item">
            <span className="label">Total Categories:</span>
            <span className="value">{displayData.length}</span>
          </div>
          <div className="summary-item">
            <span className="label">Total Amount:</span>
            <span className="value">
              ${displayData.reduce((sum, item) => sum + item.amount, 0).toFixed(2)}
            </span>
          </div>
          <div className="summary-item">
            <span className="label">Average:</span>
            <span className="value">
              ${(displayData.reduce((sum, item) => sum + item.amount, 0) / displayData.length).toFixed(2)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default BudgetGraph; 