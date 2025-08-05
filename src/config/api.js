// API Configuration
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Environment detection
export const isDevelopment = process.env.NODE_ENV === 'development';
export const isProduction = process.env.NODE_ENV === 'production';

// API endpoints
export const API_ENDPOINTS = {
  // Auth endpoints
  LOGIN: '/api/v1/login',
  REGISTER: '/api/v1/register',
  FORGOT_PASSWORD: '/api/v1/forgotPass',
  
  // Transaction endpoints
  GET_TRANSACTIONS: '/api/v1/transaction/getTransactionRecord',
  ADD_TRANSACTION: '/api/v1/transaction/addTransaction',
  UPDATE_TRANSACTION: '/api/v1/transaction/editTransaction',
  DELETE_TRANSACTION: '/api/v1/transaction/deleteTransaction',
  
  // Category endpoints
  GET_CATEGORIES: '/api/v1/category/list',
  ADD_CATEGORY: '/api/v1/category/addCategory',
  
  // Subcategory endpoints
  GET_SUBCATEGORIES: '/api/v1/subcategory/list',
  ADD_SUBCATEGORY: '/api/v1/subcategory/addSubCategory',
  
  // Account endpoints
  GET_ACCOUNTS: '/api/v1/account/list',
  ADD_ACCOUNT: '/api/v1/account/addAccount',
}; 