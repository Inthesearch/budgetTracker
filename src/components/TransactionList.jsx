import React, { useState, useMemo } from 'react';
import { formatCategoryName, formatSubcategoryName, formatAccountName } from '../utils/formatters.js';
import './TransactionList.css';

const TransactionList = ({ transactions, onEdit, onDelete, onView, loading }) => {
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filters, setFilters] = useState({
    type: '',
    category: '',
    account: ''
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
      .map(t => getAccountName(t.account))
      .filter(Boolean)
  )];
  const uniqueTypes = [...new Set(transactions.map(t => t.type))];

  // Filter and sort transactions
  const filteredAndSortedTransactions = useMemo(() => {
    let filtered = transactions.filter(transaction => {
      if (filters.type && transaction.type !== filters.type) return false;
      if (filters.category && getCategoryName(transaction.category) !== filters.category) return false;
      if (filters.account && getAccountName(transaction.account) !== filters.account) return false;
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
          aValue = getAccountName(a.account) || '';
          bValue = getAccountName(b.account) || '';
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

  const clearFilters = () => {
    setFilters({
      type: '',
      category: '',
      account: ''
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
          <label>Type:</label>
          <select
            value={filters.type}
            onChange={(e) => handleFilterChange('type', e.target.value)}
          >
            <option value="">All Types</option>
            {uniqueTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Category:</label>
          <select
            value={filters.category}
            onChange={(e) => handleFilterChange('category', e.target.value)}
          >
            <option value="">All Categories</option>
            {uniqueCategories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Account:</label>
          <select
            value={filters.account}
            onChange={(e) => handleFilterChange('account', e.target.value)}
          >
            <option value="">All Accounts</option>
            {uniqueAccounts.map(account => (
              <option key={account} value={account}>{account}</option>
            ))}
          </select>
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
                <td>{getAccountName(transaction.account) || '-'}</td>
                <td>{getCategoryName(transaction.category) || '-'}</td>
                <td className={`amount ${transaction.type}`}>
                  {transaction.type === 'income' ? '+' : '-'}
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