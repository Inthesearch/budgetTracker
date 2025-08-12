import React, { useState, useMemo } from 'react';
import { formatCategoryName, formatSubcategoryName, formatAccountName } from '../utils/formatters.js';
import MultiSelect from './MultiSelect.jsx';
import './TransactionList.css';

const TransactionList = ({ transactions, onEdit, onDelete, onView, loading }) => {
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filters, setFilters] = useState({
    types: [],
    categories: [],
    accounts: [],
    dateRange: {
      start: '',
      end: ''
    }
  });

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateString) => {
    // Convert UTC date to local date for display
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Helper function to get category name with proper case
  const getCategoryName = (category) => {
    if (!category) return null;
    const name = typeof category === 'string' ? category : category.name;
    return formatCategoryName(name);
  };

  // Helper function to get subcategory name with proper case
  const getSubcategoryName = (subcategory) => {
    if (!subcategory) return null;
    const name = typeof subcategory === 'string' ? subcategory : subcategory.name;
    return formatSubcategoryName(name);
  };

  // Helper function to get account name with proper case
  const getAccountName = (account) => {
    if (!account) return null;
    const name = typeof account === 'string' ? account : account.name;
    return formatAccountName(name);
  };

  // Get unique values for filters
  const uniqueCategories = [...new Set(
    transactions
      .map(t => getCategoryName(t.category))
      .filter(Boolean)
  )];
  const uniqueAccounts = [...new Set(
    transactions
      .map(t => getAccountName(t.from_account))
      .filter(Boolean)
  )];
  const uniqueTypes = [...new Set(transactions.map(t => t.type))];

  // Filter and sort transactions
  const filteredAndSortedTransactions = useMemo(() => {
    let filtered = transactions.filter(transaction => {
      // Type filter (multi-select)
      if (filters.types.length > 0 && !filters.types.includes(transaction.type)) return false;
      
      // Category filter (multi-select)
      if (filters.categories.length > 0 && !filters.categories.includes(getCategoryName(transaction.category))) return false;
      
      // Account filter (multi-select)
      if (filters.accounts.length > 0 && !filters.accounts.includes(getAccountName(transaction.from_account))) return false;
      
      // Date range filter
      if (filters.dateRange.start || filters.dateRange.end) {
        const transactionDate = new Date(transaction.date).toISOString().split('T')[0];
        if (filters.dateRange.start && transactionDate < filters.dateRange.start) return false;
        if (filters.dateRange.end && transactionDate > filters.dateRange.end) return false;
      }
      
      return true;
    });

    // Sort transactions
    filtered.sort((a, b) => {
      let aValue, bValue;
      
      switch (sortBy) {
        case 'date':
          aValue = new Date(a.date).getTime();
          bValue = new Date(b.date).getTime();
          break;
        case 'amount':
          aValue = a.amount;
          bValue = b.amount;
          break;
        case 'type':
          aValue = a.type;
          bValue = b.type;
          break;
        case 'category':
          aValue = getCategoryName(a.category) || '';
          bValue = getCategoryName(b.category) || '';
          break;
        case 'account':
          aValue = getAccountName(a.from_account) || '';
          bValue = getAccountName(b.from_account) || '';
          break;
        default:
          aValue = a[sortBy];
          bValue = b[sortBy];
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [transactions, filters, sortBy, sortOrder]);

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const handleDateRangeChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      dateRange: {
        ...prev.dateRange,
        [field]: value
      }
    }));
  };

  const clearFilters = () => {
    setFilters({
      types: [],
      categories: [],
      accounts: [],
      dateRange: {
        start: '',
        end: ''
      }
    });
  };

  if (loading) {
    return (
      <div className="transaction-list-container">
        <div className="loading">Loading transactions...</div>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="transaction-list-container">
        <div className="empty-state">
          <p>No transactions yet. Add your first transaction!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="transaction-list-container">
      {/* Filters */}
      <div className="filters-section">
        <div className="filter-group">
          <label>Types:</label>
          <MultiSelect
            options={uniqueTypes}
            selectedValues={filters.types}
            onSelectionChange={(values) => handleFilterChange('types', values)}
            placeholder="Select types..."
            searchable={false}
          />
        </div>

        <div className="filter-group">
          <label>Categories:</label>
          <MultiSelect
            options={uniqueCategories}
            selectedValues={filters.categories}
            onSelectionChange={(values) => handleFilterChange('categories', values)}
            placeholder="Select categories..."
            searchable={true}
          />
        </div>

        <div className="filter-group">
          <label>Accounts:</label>
          <MultiSelect
            options={uniqueAccounts}
            selectedValues={filters.accounts}
            onSelectionChange={(values) => handleFilterChange('accounts', values)}
            placeholder="Select accounts..."
            searchable={true}
          />
        </div>

        <div className="filter-group">
          <label>Date Range:</label>
          <div className="date-range-inputs">
            <input
              type="date"
              value={filters.dateRange.start}
              onChange={(e) => handleDateRangeChange('start', e.target.value)}
              placeholder="Start date"
            />
            <span>to</span>
            <input
              type="date"
              value={filters.dateRange.end}
              onChange={(e) => handleDateRangeChange('end', e.target.value)}
              placeholder="End date"
            />
          </div>
        </div>

        <button onClick={clearFilters} className="clear-filters-btn">
          Clear Filters
        </button>
      </div>

      {/* Transaction Table */}
      <div className="transaction-table-container">
        <table className="transaction-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('date')} className="sortable">
                Date
                {sortBy === 'date' && (
                  <span className="sort-indicator">
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort('type')} className="sortable">
                Type
                {sortBy === 'type' && (
                  <span className="sort-indicator">
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort('account')} className="sortable">
                Account
                {sortBy === 'account' && (
                  <span className="sort-indicator">
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort('category')} className="sortable">
                Category
                {sortBy === 'category' && (
                  <span className="sort-indicator">
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th>To Account</th>
              <th onClick={() => handleSort('amount')} className="sortable">
                Amount
                {sortBy === 'amount' && (
                  <span className="sort-indicator">
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedTransactions.map(transaction => (
              <tr 
                key={transaction.id} 
                className="transaction-row"
                onClick={() => onView(transaction)}
              >
                <td>{formatDate(transaction.date)}</td>
                <td>
                  <span className={`type-badge ${transaction.type}`}>
                    {transaction.type}
                  </span>
                </td>
                <td>{getAccountName(transaction.from_account) || '-'}</td>
                <td>{getCategoryName(transaction.category) || '-'}</td>
                <td>{transaction.type === 'transfer' ? getAccountName(transaction.to_account) || '-' : '-'}</td>
                <td className={`amount ${transaction.type}`}>
                  {transaction.type === 'income' ? '+' : transaction.type === 'transfer' ? '→' : '-'}
                  {formatCurrency(transaction.amount)}
                </td>
                <td className="actions-cell">
                  <div className="action-buttons">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onEdit(transaction);
                      }}
                      className="edit-btn"
                      title="Edit"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(transaction);
                      }}
                      className="delete-btn"
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TransactionList; 