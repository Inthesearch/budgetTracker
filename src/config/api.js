// API Configuration
const API_CONFIG = {
  // Development
  development: {
    baseUrl: 'http://localhost:8000'
  },
  // Production
  production: {
    baseUrl: 'https://budgettracker-yiw5.onrender.com'
  }
};

// Get current environment
const isDevelopment = process.env.NODE_ENV === 'development';
const currentConfig = isDevelopment ? API_CONFIG.development : API_CONFIG.production;

export const API_BASE_URL = currentConfig.baseUrl;

// Helper function to get full API URL
export const getApiUrl = (endpoint) => {
  return `${API_BASE_URL}/api/v1${endpoint}`;
};

export default API_CONFIG; 