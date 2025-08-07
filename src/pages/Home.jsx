import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext.jsx';
import { useTransactions } from '../context/TransactionContext.jsx';
import { toast } from 'react-toastify';
import TransactionModal from '../components/TransactionModal.jsx';
import TransactionList from '../components/TransactionList.jsx';
import BudgetGraph from '../components/BudgetGraph.jsx';
import { formatCategoryName, formatSubcategoryName, formatAccountName } from '../utils/formatters.js';

import './Home.css';

const Home = () => {
  const { user, logout } = useAuth();
  const { transactions, loading, deleteTransaction } = useTransactions();
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(null);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [deleting, setDeleting] = useState(false);

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

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
  };

  const handleAddTransaction = () => {
    setShowAddModal(true);
    setEditingTransaction(null);
  };

  const handleEditTransaction = (transaction) => {
    setEditingTransaction(transaction);
    setShowAddModal(true);
  };

  const handleDeleteTransaction = (transaction) => {
    setShowDeleteModal(transaction);
  };

  const handleViewTransaction = (transaction) => {
    setSelectedTransaction(transaction);
  };

  const handleCloseModals = () => {
    setShowAddModal(false);
    setEditingTransaction(null);
    setShowDeleteModal(null);
    setSelectedTransaction(null);
  };

  const handleTransactionSuccess = (message) => {
    toast.success(message);
    handleCloseModals();
  };

  const handleConfirmDelete = async () => {
    if (!showDeleteModal) return;
    
    setDeleting(true);
    try {
      const result = await deleteTransaction(showDeleteModal.id);
      if (result.success) {
        toast.success('Transaction deleted successfully');
        handleCloseModals();
      } else {
        toast.error(result.error || 'Failed to delete transaction');
      }
    } catch (error) {
      console.error('Error deleting transaction:', error);
      toast.error('An error occurred while deleting the transaction');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="home-container">
      {/* Header */}
      <header className="home-header">
        <div className="header-left">
          <h1>💰 Budget Tracker</h1>
        </div>
        <div className="header-right">
          <span className="user-info">Welcome, {user?.name || user?.email}</span>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="home-content">
        {/* Left Side - Graph */}
        <div className="home-left">
          <BudgetGraph />
        </div>

        {/* Right Side - Add Transaction Button and Transaction List */}
        <div className="home-right">
          {/* Add Transaction Button */}
          <div className="add-transaction-section">
            <button 
              onClick={handleAddTransaction}
              className="add-transaction-button"
            >
              Add +
            </button>
          </div>

          {/* Transaction List */}
          <div className="transaction-list-section">
            <TransactionList
              transactions={transactions}
              onEdit={handleEditTransaction}
              onDelete={handleDeleteTransaction}
              onView={handleViewTransaction}
              loading={loading}
            />
          </div>
        </div>
      </div>

      {/* Modals */}
      {showAddModal && (
        <TransactionModal
          transaction={editingTransaction}
          onClose={handleCloseModals}
          onSuccess={handleTransactionSuccess}
        />
      )}

      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="delete-modal">
            <h3>Delete Transaction</h3>
            <p>Are you sure you want to delete this transaction?</p>
            <div className="modal-actions">
              <button 
                onClick={handleCloseModals}
                className="cancel-button"
                disabled={deleting}
              >
                Cancel
              </button>
              <button 
                onClick={handleConfirmDelete}
                className="delete-button"
                disabled={deleting}
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedTransaction && (
        <div className="modal-overlay">
          <div className="transaction-info-modal">
            <h3>Transaction Details</h3>
            <div className="transaction-info">
              <div className="info-row">
                <span className="label">Date:</span>
                <span>{new Date(selectedTransaction.date).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}</span>
              </div>
              <div className="info-row">
                <span className="label">Type:</span>
                <span className={`type ${selectedTransaction.type}`}>
                  {selectedTransaction.type}
                </span>
              </div>
              <div className="info-row">
                <span className="label">Amount:</span>
                <span className="amount">
                  ${selectedTransaction.amount.toFixed(2)}
                </span>
              </div>
              <div className="info-row">
                <span className="label">Category:</span>
                <span>{getCategoryName(selectedTransaction.category) || '-'}</span>
              </div>
              {selectedTransaction.sub_category && (
                <div className="info-row">
                  <span className="label">Sub-Category:</span>
                  <span>{getSubcategoryName(selectedTransaction.sub_category) || '-'}</span>
                </div>
              )}
              <div className="info-row">
                <span className="label">Account:</span>
                <span>{getAccountName(selectedTransaction.account) || '-'}</span>
              </div>
              {selectedTransaction.notes && (
                <div className="info-row">
                  <span className="label">Notes:</span>
                  <span>{selectedTransaction.notes}</span>
                </div>
              )}
            </div>
            <button onClick={handleCloseModals} className="close-button">
              Close
            </button>
          </div>
        </div>
      )}


    </div>
  );
};

export default Home; 