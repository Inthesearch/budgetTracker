// Test script to debug API response
const API_BASE_URL = 'http://localhost:8000';

async function testAPI() {
  try {
    // Test health endpoint
    const healthResponse = await fetch(`${API_BASE_URL}/health`);
    console.log('Health check:', await healthResponse.json());
    
    // Test transactions endpoint (this will fail without auth, but let's see the error)
    const transactionsResponse = await fetch(`${API_BASE_URL}/api/v1/transaction/getTransactionRecord`);
    console.log('Transactions response status:', transactionsResponse.status);
    
    if (transactionsResponse.ok) {
      const transactions = await transactionsResponse.json();
      console.log('Transactions data:', transactions);
      if (transactions.length > 0) {
        console.log('First transaction structure:', transactions[0]);
        console.log('Category field type:', typeof transactions[0].category);
        console.log('Category field value:', transactions[0].category);
      }
    } else {
      const error = await transactionsResponse.text();
      console.log('Error response:', error);
    }
    
  } catch (error) {
    console.error('API test error:', error);
  }
}

testAPI(); 