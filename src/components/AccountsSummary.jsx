import React, { useMemo } from 'react';
import { formatAccountName } from '../utils/formatters.js';
import './AccountsSummary.css';

const formatCurrency = (amount, currency = 'USD') => {
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount || 0);
  } catch (e) {
    return `$${(amount || 0).toFixed(2)}`;
  }
};

const AccountsSummary = ({ accounts = [], onManage }) => {
  const { maxBalance, totalBalance } = useMemo(() => {
    const balances = accounts.map(a => a.balance || 0);
    return {
      maxBalance: Math.max(1, ...balances),
      totalBalance: balances.reduce((s, v) => s + v, 0),
    };
  }, [accounts]);


  return (
    <div className="accounts-summary">
      <div className="accounts-summary__header">
        <div className="accounts-summary__title">
          <div className="accounts-summary__subtitle">Available funds</div>
          <div className="accounts-summary__total">{formatCurrency(totalBalance)}</div>
        </div>
        <button className="accounts-summary__manage" onClick={onManage} title="Manage accounts" aria-label="Manage accounts">
          ⚙️
        </button>
      </div>

      <div className="accounts-summary__list">
        {accounts.map(account => {
          const percent = Math.max(0, Math.min(100, ((account.balance || 0) / maxBalance) * 100));
          return (
            <div className="accounts-summary__row" key={account.id}>
              <div className="accounts-summary__name" title={formatAccountName(account.name)}>{formatAccountName(account.name)}</div>
              <div className="accounts-summary__bar">
                <div className="accounts-summary__bar-fill" style={{ width: `${percent}%` }} />
              </div>
              <div className="accounts-summary__balance">{formatCurrency(account.balance, account.currency)}</div>
            </div>
          );
        })}
        {accounts.length === 0 && (
          <div className="accounts-summary__empty">No accounts yet. Add one from the manager.</div>
        )}
      </div>
    </div>
  );
};

export default AccountsSummary;


