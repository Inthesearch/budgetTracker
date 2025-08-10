import React, { useState, useEffect } from 'react';
import { useTransactions } from '../context/TransactionContext.jsx';
import { formatCategoryName, formatSubcategoryName, formatAccountName } from '../utils/formatters.js';
import './TransactionModal.css';

const TransactionModal = ({ transaction, onClose, onSuccess }) => {
  const { 
    categories, 
    subCategories, 
    accounts, 
    addTransaction, 
    updateTransaction,
    addCategory,
    addSubCategory,
    addAccount,
    loadCategories
  } = useTransactions();

  const [formData, setFormData] = useState({
    amount: '',
    category_id: '',
    sub_category_id: '',
    date: new Date().toLocaleDateString('en-CA'),
    account_id: '',
    type: 'expense',
    notes: ''
  });
  const [toAccountId, setToAccountId] = useState('');
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [showNewCategory, setShowNewCategory] = useState(false);
  const [showNewSubCategory, setShowNewSubCategory] = useState(false);
  const [showNewAccount, setShowNewAccount] = useState(false);
  const [newCategory, setNewCategory] = useState('');
  const [newSubCategory, setNewSubCategory] = useState('');
  const [newAccount, setNewAccount] = useState('');

  // Ensure we have a dedicated Transfer category and subcategory; returns their IDs
  const ensureTransferCategoryAndSubcategory = async () => {
    // Find existing transfer category (names are normalized to lowercase in backend)
    let transferCategory = categories.find(c => {
      const name = typeof c === 'string' ? c : c.name;
      return name && name.toLowerCase() === 'transfer';
    });

    let transferCategoryId = transferCategory && (typeof transferCategory === 'string' ? null : transferCategory.id);
    if (!transferCategoryId) {
      const res = await addCategory({ name: 'transfer' });
      if (!res.success) {
        throw new Error(res.error || 'Failed to create Transfer category');
      }
      transferCategoryId = res.id;
    }

    // Find existing transfer subcategory under this category
    let transferSubId = undefined;
    const subs = subCategories[transferCategoryId] || [];
    const existingSub = subs.find(s => {
      const name = typeof s === 'string' ? s : s.name;
      return name && name.toLowerCase() === 'transfer';
    });
    if (existingSub) {
      transferSubId = typeof existingSub === 'string' ? null : existingSub.id;
    } else {
      const subRes = await addSubCategory({ name: 'transfer', category_id: transferCategoryId });
      if (!subRes.success) {
        throw new Error(subRes.error || 'Failed to create Transfer sub-category');
      }
      transferSubId = subRes.id;
    }

    return { categoryId: transferCategoryId, subCategoryId: transferSubId };
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

  // Helper function to get category ID
  const getCategoryId = (category) => {
    if (!category) return null;
    return typeof category === 'string' ? null : category.id;
  };

  // Helper function to get account ID
  const getAccountId = (account) => {
    if (!account) return null;
    return typeof account === 'string' ? null : account.id;
  };

  const isEditing = !!transaction;

  useEffect(() => {
    if (transaction) {
      // Convert UTC date to local date for the date input
      const localDate = new Date(transaction.date).toISOString().split('T')[0];
      
      setFormData({
        amount: transaction.amount.toString(),
        category_id: getCategoryId(transaction.category) || '',
        sub_category_id: getCategoryId(transaction.sub_category) || '',
        date: localDate,
        account_id: getAccountId(transaction.account) || '',
        type: transaction.type || 'expense',
        notes: transaction.notes || ''
      });
    }
  }, [transaction]);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.amount) {
      newErrors.amount = 'Amount is required';
    } else if (isNaN(parseFloat(formData.amount)) || parseFloat(formData.amount) <= 0) {
      newErrors.amount = 'Please enter a valid amount';
    }

    if (!formData.date) {
      newErrors.date = 'Date is required';
    }

    if (!formData.account_id) {
      newErrors.account_id = 'Account is required';
    }

    if (formData.type !== 'transfer' && !formData.category_id) {
      newErrors.category_id = 'Category is required';
    }

    if (formData.type !== 'transfer') {
      if (!formData.sub_category_id) {
        newErrors.sub_category_id = 'Sub-Category is required';
      }
    }

    if (formData.type === 'transfer') {
      if (!toAccountId) {
        newErrors.to_account_id = 'To Account is required';
      } else if (toAccountId && formData.account_id && toAccountId === formData.account_id) {
        newErrors.to_account_id = 'Choose a different account to transfer to';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }

    // Reset sub-category when category changes
    if (name === 'category_id') {
      setFormData(prev => ({
        ...prev,
        category_id: value,
        sub_category_id: ''
      }));
    }

    // When switching to transfer, clear category/sub-category selections
    if (name === 'type') {
      if (value === 'transfer') {
        setFormData(prev => ({
          ...prev,
          category_id: '',
          sub_category_id: ''
        }));
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    console.log('formData', formData);
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // Convert date to local datetime format
      const dateTime = formData.date + 'T00:00:00';

      if (formData.type === 'transfer') {
        // Option B: create two transactions under the hood
        const amount = parseFloat(formData.amount);
        const fromAccountId = parseInt(formData.account_id);
        const toAccId = parseInt(toAccountId);

        // Resolve dedicated transfer category/subcategory
        const { categoryId: transferCategoryId, subCategoryId: transferSubCategoryId } = await ensureTransferCategoryAndSubcategory();

        const base = {
          date: dateTime,
          notes: formData.notes,
          category_id: transferCategoryId,
          sub_category_id: transferSubCategoryId,
        };

        const expenseTx = {
          ...base,
          amount,
          type: 'expense',
          account_id: fromAccountId,
        };

        const incomeTx = {
          ...base,
          amount,
          type: 'income',
          account_id: toAccId,
        };

        const res1 = await addTransaction(expenseTx);
        if (!res1.success) throw new Error(res1.error || 'Failed to create expense transfer leg');

        const res2 = await addTransaction(incomeTx);
        if (!res2.success) throw new Error(res2.error || 'Failed to create income transfer leg');

        onSuccess(isEditing ? 'Transfer updated successfully!' : 'Transfer recorded successfully!');
        return;
      }

      // Non-transfer or editing path (backend handles edit-as-new and balances)
      const transactionData = {
        amount: parseFloat(formData.amount),
        date: dateTime,
        type: formData.type,
        notes: formData.notes,
        category_id: parseInt(formData.category_id),
        sub_category_id: parseInt(formData.sub_category_id),
        account_id: parseInt(formData.account_id)
      };

      let result;
      if (isEditing) {
        result = await updateTransaction(transaction.id, transactionData);
      } else {
        result = await addTransaction(transactionData);
      }

      if (result.success) {
        onSuccess(isEditing ? 'Transaction updated successfully!' : 'Transaction added successfully!');
      } else {
        console.error('Transaction error:', result.error);
      }
    } catch (error) {
      console.error('Error saving transaction:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddCategory = async () => {
    if (!newCategory.trim()) return;

    const result = await addCategory({ name: newCategory.trim() });
    if (result.success) {
      // Reload categories to get the new one with ID
      // For now, we'll just close the form
      setNewCategory('');
      setShowNewCategory(false);
    }
  };

  const handleAddSubCategory = async () => {
    if (!newSubCategory.trim() || !formData.category_id) return;

    const result = await addSubCategory({ 
      name: newSubCategory.trim(),
      category_id: parseInt(formData.category_id)
    });
    if (result.success) {
      setNewSubCategory('');
      setShowNewSubCategory(false);
    }
  };

  const handleAddAccount = async () => {
    if (!newAccount.trim()) return;

    const result = await addAccount({ name: newAccount.trim() });
    if (result.success) {
      setNewAccount('');
      setShowNewAccount(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="transaction-modal">
        <div className="modal-header">
          <h2>{isEditing ? 'Edit Transaction' : 'Add New Transaction'}</h2>
          <button onClick={onClose} className="close-button">×</button>
        </div>

        <form onSubmit={handleSubmit} className="transaction-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="amount">Amount *</label>
              <input
                type="number"
                id="amount"
                name="amount"
                value={formData.amount}
                onChange={handleInputChange}
                placeholder="0.00"
                step="0.01"
                min="0"
                className={errors.amount ? 'error' : ''}
              />
              {errors.amount && <span className="error-message">{errors.amount}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="type">Type</label>
              <select
                id="type"
                name="type"
                value={formData.type}
                onChange={handleInputChange}
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
                <option value="transfer">Transfer</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="date">Date *</label>
              <input
                type="date"
                id="date"
                name="date"
                value={formData.date}
                onChange={handleInputChange}
                className={errors.date ? 'error' : ''}
              />
              {errors.date && <span className="error-message">{errors.date}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="account_id">Account *</label>
              <div className="select-with-add">
                <select
                  id="account_id"
                  name="account_id"
                  value={formData.account_id}
                  onChange={handleInputChange}
                  className={errors.account_id ? 'error' : ''}
                >
                  <option value="">Choose Account</option>
                  {accounts.map(account => (
                    <option key={account.id || account} value={account.id || account}>
                      {getAccountName(account)}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="add-button"
                  onClick={() => setShowNewAccount(true)}
                >
                  +
                </button>
              </div>
              {showNewAccount && (
                <div className="add-new-item">
                  <input
                    type="text"
                    placeholder="New account name"
                    value={newAccount}
                    onChange={(e) => setNewAccount(e.target.value)}
                  />
                  <button type="button" onClick={handleAddAccount}>Add</button>
                  <button type="button" onClick={() => setShowNewAccount(false)}>Cancel</button>
                </div>
              )}
              {errors.account_id && <span className="error-message">{errors.account_id}</span>}
            </div>
          </div>

          {formData.type === 'transfer' && (
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="to_account_id">To Account *</label>
                <select
                  id="to_account_id"
                  name="to_account_id"
                  value={toAccountId}
                  onChange={(e) => setToAccountId(e.target.value)}
                  className={errors.to_account_id ? 'error' : ''}
                >
                  <option value="">Choose To Account</option>
                  {accounts
                    .filter(acc => (acc.id || acc) !== parseInt(formData.account_id || '0'))
                    .map(acc => (
                      <option key={acc.id || acc} value={acc.id || acc}>
                        {getAccountName(acc)}
                      </option>
                    ))}
                </select>
                {errors.to_account_id && <span className="error-message">{errors.to_account_id}</span>}
              </div>
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="category_id">Category *</label>
              <div className="select-with-add">
                 <select
                  id="category_id"
                  name="category_id"
                  value={formData.type === 'transfer' ? '' : formData.category_id}
                  onChange={handleInputChange}
                   className={errors.category_id ? 'error' : ''}
                   disabled={formData.type === 'transfer'}
                >
                  <option value="">Choose Category</option>
                  {categories.map(category => (
                    <option key={category.id || category} value={category.id || category}>
                      {getCategoryName(category)}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="add-button"
                  onClick={() => setShowNewCategory(true)}
                  disabled={formData.type === 'transfer'}
                >
                  +
                </button>
              </div>
              {showNewCategory && (
                <div className="add-new-item">
                  <input
                    type="text"
                    placeholder="New category name"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                  />
                  <button type="button" onClick={handleAddCategory}>Add</button>
                  <button type="button" onClick={() => setShowNewCategory(false)}>Cancel</button>
                </div>
              )}
              {errors.category_id && <span className="error-message">{errors.category_id}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="sub_category_id">Sub-Category *</label>
              <div className="select-with-add">
                <select
                  id="sub_category_id"
                  name="sub_category_id"
                  value={formData.sub_category_id}
                  onChange={handleInputChange}
                  disabled={!formData.category_id || formData.type === 'transfer'}
                  className={errors.sub_category_id ? 'error' : ''}
                >
                  <option value="">Choose Sub-Category</option>
                  {formData.category_id && subCategories[formData.category_id]?.map(subCategory => (
                    <option key={subCategory.id || subCategory} value={subCategory.id || subCategory}>
                      {getSubcategoryName(subCategory)}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="add-button"
                  onClick={() => setShowNewSubCategory(true)}
                  disabled={!formData.category_id || formData.type === 'transfer'}
                >
                  +
                </button>
              </div>
              {formData.category_id && (!subCategories[formData.category_id] || subCategories[formData.category_id].length === 0) && (
                <div style={{fontSize: '12px', color: '#666', marginTop: '5px'}}>
                  No sub-categories available for this category. Click the + button to add one.
                </div>
              )}
              {showNewSubCategory && (
                <div className="add-new-item">
                  <input
                    type="text"
                    placeholder="New sub-category name"
                    value={newSubCategory}
                    onChange={(e) => setNewSubCategory(e.target.value)}
                  />
                  <button type="button" onClick={handleAddSubCategory}>Add</button>
                  <button type="button" onClick={() => setShowNewSubCategory(false)}>Cancel</button>
                </div>
              )}
              {errors.sub_category_id && <span className="error-message">{errors.sub_category_id}</span>}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="notes">Notes</label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              placeholder="Optional notes about this transaction..."
              rows="3"
            />
          </div>

          <div className="form-actions">
            <button type="button" onClick={onClose} className="cancel-button">
              Cancel
            </button>
            <button type="submit" className="submit-button" disabled={isLoading}>
              {isLoading ? 'Saving...' : (isEditing ? 'Update' : 'Add')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TransactionModal; 