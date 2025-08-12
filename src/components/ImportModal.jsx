import React, { useState, useRef } from 'react';
import { useTransactions } from '../context/TransactionContext.jsx';
import './ImportModal.css';

const ImportModal = ({ onClose }) => {
  const { importTransactions } = useTransactions();
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (file) => {
    if (!file) return;
    
    // Validate file type
    const validTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
      'application/vnd.ms-excel', // .xls
      'text/csv', // .csv
      'application/csv'
    ];
    
    if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
      alert('Please select a valid Excel (.xlsx, .xls) or CSV file.');
      return;
    }
    
    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB.');
      return;
    }
    
    setSelectedFile(file);
    setUploadResult(null);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const downloadSampleFile = () => {
    // Create sample data
    const sampleData = [
      {
        'Date (dd/mm/yy)': '15/01/2024',
        'Account': 'Bank Account',
        'Entry Type': 'income',
        'Category': 'Salary',
        'Sub Category': 'Monthly',
        'Amount': '5000.00',
        'To Account': '',
        'Notes': 'January salary payment'
      },
      {
        'Date (dd/mm/yy)': '16/01/2024',
        'Account': 'Credit Card',
        'Entry Type': 'expense',
        'Category': 'Food',
        'Sub Category': 'Groceries',
        'Amount': '150.50',
        'To Account': '',
        'Notes': 'Weekly grocery shopping'
      },
      {
        'Date (dd/mm/yy)': '17/01/2024',
        'Account': 'Bank Account',
        'Entry Type': 'transfer',
        'Category': '',
        'Sub Category': '',
        'Amount': '1000.00',
        'To Account': 'Savings Account',
        'Notes': 'Transfer to savings account'
      }
    ];

    // Convert to CSV
    const headers = Object.keys(sampleData[0]);
    const csvContent = [
      headers.join(','),
      ...sampleData.map(row => 
        headers.map(header => `"${row[header]}"`).join(',')
      )
    ].join('\n');

    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample_transactions.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setProgress(0);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const result = await importTransactions(formData, (progressPercent) => {
        setProgress(progressPercent);
      });

      setUploadResult(result);
    } catch (error) {
      setUploadResult({
        success: false,
        error: 'Upload failed. Please try again.'
      });
    } finally {
      setIsUploading(false);
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setProgress(0);
    setUploadResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="modal-overlay">
      <div className="import-modal">
        <div className="import-modal-header">
          <h3>📥 Import Transactions</h3>
          <button onClick={onClose} className="close-button">×</button>
        </div>

        <div className="import-modal-content">
          {/* Important Notice */}
          <div className="import-notice">
            <h4>⚠️ Important:</h4>
            <ul>
              <li>You are responsible for ensuring no duplicate transactions</li>
              <li>Transfer transactions must have empty category and subcategory fields</li>
              <li>Transfer transactions must specify a 'To Account' for the destination</li>
              <li>Please verify account balances after import</li>
              <li>Maximum file size: 5MB</li>
            </ul>
          </div>

          {/* Validation Rules */}
          <div className="validation-rules">
            <h4>📋 Validation Rules:</h4>
            <ul>
              <li>Date format: dd/mm/yy</li>
              <li>Entry types: income, expense, transfer</li>
              <li>Transfer transactions: category and subcategory must be empty</li>
              <li>Transfer transactions: 'To Account' field is required</li>
              <li>Account names: will be created if they don't exist</li>
              <li>Categories: will be created if they don't exist</li>
              <li>Subcategories: will be created if they don't exist</li>
            </ul>
          </div>

          {/* Sample File Download */}
          <div className="sample-file-section">
            <button 
              onClick={downloadSampleFile}
              className="download-sample-btn"
              disabled={isUploading}
            >
              📄 Download Sample File
            </button>
          </div>

          {/* File Upload Area */}
          <div className="file-upload-section">
            <div 
              className={`file-drop-zone ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'file-selected' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={handleFileInput}
                style={{ display: 'none' }}
              />
              
              {selectedFile ? (
                <div className="file-info">
                  <div className="file-name">📎 {selectedFile.name}</div>
                  <div className="file-size">({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)</div>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      resetForm();
                    }}
                    className="remove-file-btn"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className="upload-prompt">
                  <div className="upload-icon">📁</div>
                  <div className="upload-text">
                    <strong>Click to select file</strong> or drag and drop
                  </div>
                  <div className="upload-hint">
                    Supports .xlsx, .xls, .csv files (max 5MB)
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          {isUploading && (
            <div className="progress-section">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <div className="progress-text">{Math.round(progress)}%</div>
            </div>
          )}

          {/* Upload Result */}
          {uploadResult && (
            <div className={`upload-result ${uploadResult.success ? 'success' : 'error'}`}>
              <h4>{uploadResult.success ? '✅ Import Complete' : '❌ Import Failed'}</h4>
              {uploadResult.success ? (
                <div>
                  <p>Successfully imported {uploadResult.importedCount} transactions</p>
                  {uploadResult.createdAccounts > 0 && (
                    <p>Created {uploadResult.createdAccounts} new accounts</p>
                  )}
                  {uploadResult.createdCategories > 0 && (
                    <p>Created {uploadResult.createdCategories} new categories</p>
                  )}
                  {uploadResult.createdSubcategories > 0 && (
                    <p>Created {uploadResult.createdSubcategories} new subcategories</p>
                  )}
                </div>
              ) : (
                <div>
                  <p>{uploadResult.error}</p>
                  {uploadResult.validationErrors && uploadResult.validationErrors.length > 0 && (
                    <div className="validation-errors">
                      <h5>Validation Errors:</h5>
                      <ul>
                        {uploadResult.validationErrors.map((error, index) => (
                          <li key={index}>Row {error.row}: {error.message}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="import-actions">
            <button 
              onClick={onClose} 
              className="cancel-btn"
              disabled={isUploading}
            >
              Cancel
            </button>
            <button 
              onClick={handleUpload}
              className="upload-btn"
              disabled={!selectedFile || isUploading}
            >
              {isUploading ? 'Uploading...' : 'Upload & Import'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImportModal;
