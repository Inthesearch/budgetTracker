import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext.jsx';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api.js';

const TransactionContext = createContext();

export const useTransactions = () => {
  const context = useContext(TransactionContext);
  if (!context) {
    throw new Error('useTransactions must be used within a TransactionProvider');
  }
  return context;
};

export const TransactionProvider = ({ children }) => {
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [subCategories, setSubCategories] = useState({});
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();



  // Get auth token
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  };

  // Load data only when user is authenticated
  useEffect(() => {
    if (user && localStorage.getItem('token')) {
      loadTransactions();
      loadCategories();
      loadAccounts();
    } else {
      // Clear data when user is not authenticated
      setTransactions([]);
      setCategories([]);
      setAccounts([]);
    }
  }, [user]);

  const loadTransactions = async () => {
    if (!user || !localStorage.getItem('token')) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.GET_TRANSACTIONS}`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const data = await response.json();
        setTransactions(data);
      } else if (response.status === 401) {
        // Token expired or invalid
        console.error('Authentication failed, redirecting to login');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      } else {
        console.error('Failed to load transactions:', response.status);
      }
    } catch (error) {
      console.error('Error loading transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    if (!user || !localStorage.getItem('token')) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.GET_CATEGORIES}`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const data = await response.json();
        setCategories(data);
        // Load subcategories for each category
        await loadSubCategories(data);
      } else if (response.status === 401) {
        console.error('Authentication failed, redirecting to login');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      } else {
        console.error('Failed to load categories:', response.status);
      }
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadSubCategories = async (categoriesList) => {
    if (!user || !localStorage.getItem('token')) return;
    
    try {
      const subCategoriesMap = {};
      
      // Load subcategories for each category
      for (const category of categoriesList) {
        const categoryId = typeof category === 'string' ? null : category.id;
        if (categoryId) {
          const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.GET_SUBCATEGORIES}/${categoryId}`, {
            method: 'GET',
            headers: getAuthHeaders(),
          });

          if (response.ok) {
            const data = await response.json();
            subCategoriesMap[categoryId] = data;
          }
        }
      }
      
      setSubCategories(subCategoriesMap);
    } catch (error) {
      console.error('Error loading subcategories:', error);
    }
  };

  const loadAccounts = async () => {
    if (!user || !localStorage.getItem('token')) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.GET_ACCOUNTS}`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const data = await response.json();
        setAccounts(data);
      } else if (response.status === 401) {
        console.error('Authentication failed, redirecting to login');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      } else {
        console.error('Failed to load accounts:', response.status);
      }
    } catch (error) {
      console.error('Error loading accounts:', error);
    }
  };

  const addTransaction = async (transactionData) => {
    if (!user || !localStorage.getItem('token')) {
      return { success: false, error: 'Not authenticated' };
    }
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.ADD_TRANSACTION}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(transactionData),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // Reload transactions to get the updated list
          await loadTransactions();
          return { success: true, transaction: result.data };
        } else {
          return { success: false, error: result.message };
        }
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return { success: false, error: 'Authentication failed' };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Failed to add transaction' };
      }
    } catch (error) {
      console.error('Error adding transaction:', error);
      return { success: false, error: 'Network error. Please try again.' };
    } finally {
      setLoading(false);
    }
  };

  const updateTransaction = async (id, transactionData) => {
    if (!user || !localStorage.getItem('token')) {
      return { success: false, error: 'Not authenticated' };
    }
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.UPDATE_TRANSACTION}/${id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(transactionData),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // Reload transactions to get the updated list
          await loadTransactions();
          return { success: true };
        } else {
          return { success: false, error: result.message };
        }
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return { success: false, error: 'Authentication failed' };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Failed to update transaction' };
      }
    } catch (error) {
      console.error('Error updating transaction:', error);
      return { success: false, error: 'Network error. Please try again.' };
    } finally {
      setLoading(false);
    }
  };

  const deleteTransaction = async (id) => {
    if (!user || !localStorage.getItem('token')) {
      return { success: false, error: 'Not authenticated' };
    }
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.DELETE_TRANSACTION}/${id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // Reload transactions to get the updated list
          await loadTransactions();
          return { success: true };
        } else {
          return { success: false, error: result.message };
        }
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return { success: false, error: 'Authentication failed' };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Failed to delete transaction' };
      }
    } catch (error) {
      console.error('Error deleting transaction:', error);
      return { success: false, error: 'Network error. Please try again.' };
    } finally {
      setLoading(false);
    }
  };

  const getTransactions = async (filters = {}) => {
    if (!user || !localStorage.getItem('token')) {
      return { success: false, error: 'Not authenticated' };
    }
    
    setLoading(true);
    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.transaction_type) params.append('transaction_type', filters.transaction_type);
      if (filters.category_id) params.append('category_id', filters.category_id);
      if (filters.sub_category_id) params.append('sub_category_id', filters.sub_category_id);
      if (filters.account_id) params.append('account_id', filters.account_id);
      if (filters.min_amount) params.append('min_amount', filters.min_amount);
      if (filters.max_amount) params.append('max_amount', filters.max_amount);
      if (filters.page) params.append('page', filters.page);
      if (filters.size) params.append('size', filters.size);

      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.GET_TRANSACTIONS}?${params}`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const data = await response.json();
        setTransactions(data);
        return { success: true, transactions: data };
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return { success: false, error: 'Authentication failed' };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Failed to get transactions' };
      }
    } catch (error) {
      console.error('Error getting transactions:', error);
      return { success: false, error: 'Network error. Please try again.' };
    } finally {
      setLoading(false);
    }
  };

  const addCategory = async (categoryData) => {
    if (!user || !localStorage.getItem('token')) {
      return { success: false, error: 'Not authenticated' };
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.ADD_CATEGORY}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(categoryData),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          await loadCategories();
          return { success: true };
        } else {
          return { success: false, error: result.message };
        }
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return { success: false, error: 'Authentication failed' };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Failed to add category' };
      }
    } catch (error) {
      console.error('Error adding category:', error);
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const addSubCategory = async (subCategoryData) => {
    if (!user || !localStorage.getItem('token')) {
      return { success: false, error: 'Not authenticated' };
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.ADD_SUBCATEGORY}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(subCategoryData),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // Reload categories to get updated sub-categories
          await loadCategories();
          return { success: true };
        } else {
          return { success: false, error: result.message };
        }
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return { success: false, error: 'Authentication failed' };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Failed to add sub-category' };
      }
    } catch (error) {
      console.error('Error adding sub-category:', error);
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const addAccount = async (accountData) => {
    if (!user || !localStorage.getItem('token')) {
      return { success: false, error: 'Not authenticated' };
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.ADD_ACCOUNT}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(accountData),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          await loadAccounts();
          return { success: true };
        } else {
          return { success: false, error: result.message };
        }
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return { success: false, error: 'Authentication failed' };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Failed to add account' };
      }
    } catch (error) {
      console.error('Error adding account:', error);
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const value = {
    transactions,
    categories,
    subCategories,
    accounts,
    loading,
    addTransaction,
    updateTransaction,
    deleteTransaction,
    getTransactions,
    addCategory,
    addSubCategory,
    addAccount,
    loadTransactions,
    loadCategories,
    loadAccounts,
  };

  return (
    <TransactionContext.Provider value={value}>
      {children}
    </TransactionContext.Provider>
  );
}; 