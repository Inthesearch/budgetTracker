import React, { useMemo, useState } from 'react';
import { useTransactions } from '../context/TransactionContext.jsx';
import './AccountsManagerModal.css';

const AccountsManagerModal = ({ onClose }) => {
  const { accounts, addAccount, updateAccount, deleteAccount } = useTransactions();
  const [newAccount, setNewAccount] = useState({ name: '', balance: '' });
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);

  const sorted = useMemo(() => {
    return [...accounts].sort((a, b) => a.name.localeCompare(b.name));
  }, [accounts]);

  const handleAdd = async () => {
    if (!newAccount.name.trim()) return;
    setSaving(true);
    const payload = { name: newAccount.name.trim(), type: 'bank', balance: parseFloat(newAccount.balance || '0') || 0, currency: 'USD' };
    const res = await addAccount(payload);
    setSaving(false);
    if (res.success) setNewAccount({ name: '', balance: '' });
  };

  const handleSaveEdit = async () => {
    if (!editing) return;
    setSaving(true);
    const payload = {};
    if (editing.name) payload.name = editing.name;
    if (editing.balance !== undefined && editing.balance !== null && editing.balance !== '') payload.balance = parseFloat(editing.balance) || 0;
    const res = await updateAccount(editing.id, payload);
    setSaving(false);
    if (res.success) setEditing(null);
  };

  const handleDelete = async (id) => {
    setSaving(true);
    await deleteAccount(id);
    setSaving(false);
  };

  return (
    <div className="modal-overlay">
      <div className="accounts-manager-modal">
        <div className="amm-header">
          <h3>Manage Accounts</h3>
          <button className="amm-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        <div className="amm-section">
          <div className="amm-subtitle">Add new account</div>
          <div className="amm-add-row">
            <input
              type="text"
              placeholder="Account name"
              value={newAccount.name}
              onChange={(e) => setNewAccount(a => ({ ...a, name: e.target.value }))}
            />
            <input
              type="number"
              placeholder="Initial amount (optional)"
              value={newAccount.balance}
              onChange={(e) => setNewAccount(a => ({ ...a, balance: e.target.value }))}
            />
            <button className="amm-btn" onClick={handleAdd} disabled={saving || !newAccount.name.trim()}>Add</button>
          </div>
        </div>

        <div className="amm-section">
          <div className="amm-subtitle">Your accounts</div>
          <div className="amm-list">
            {sorted.map(acc => (
              <div className="amm-row" key={acc.id}>
                {editing?.id === acc.id ? (
                  <>
                    <input
                      type="text"
                      value={editing.name}
                      onChange={(e) => setEditing(prev => ({ ...prev, name: e.target.value }))}
                    />
                    <input
                      type="number"
                      value={editing.balance}
                      onChange={(e) => setEditing(prev => ({ ...prev, balance: e.target.value }))}
                    />
                    <button className="amm-btn" onClick={handleSaveEdit} disabled={saving}>Save</button>
                    <button className="amm-btn secondary" onClick={() => setEditing(null)} disabled={saving}>Cancel</button>
                  </>
                ) : (
                  <>
                    <div className="amm-name">{acc.name}</div>
                    <div className="amm-balance">{(acc.balance ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                    <button className="amm-btn" onClick={() => setEditing({ id: acc.id, name: acc.name, balance: acc.balance ?? 0 })} disabled={saving}>Edit</button>
                    <button className="amm-btn danger" onClick={() => handleDelete(acc.id)} disabled={saving}>Delete</button>
                  </>
                )}
              </div>
            ))}
            {sorted.length === 0 && <div className="amm-empty">No accounts yet.</div>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccountsManagerModal;


