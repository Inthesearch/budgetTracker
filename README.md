# Budget Tracker Web App

A modern, responsive web application built with React and TypeScript for tracking personal income and expenses.

## Features

- 💰 **Track Income & Expenses**: Add and categorize your financial transactions
- 📊 **Real-time Summary**: View your current balance, total income, and total expenses
- 📱 **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- 💾 **Local Storage**: Your data is automatically saved to your browser
- 🎨 **Modern UI**: Clean and intuitive interface with beautiful gradients
- ⚡ **Fast Performance**: Built with React 18 and optimized for speed

## Getting Started

### Prerequisites

- Node.js (version 14 or higher)
- npm or yarn

### Installation

1. Clone the repository or navigate to the project directory
2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) to view it in the browser

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App (one-way operation)

## Usage

### Adding Transactions

1. Fill in the transaction form with:
   - **Description**: What the transaction was for
   - **Amount**: The dollar amount
   - **Type**: Income or Expense
   - **Category**: Choose from predefined categories
   - **Date**: When the transaction occurred

2. Click "Add Transaction" to save

### Managing Transactions

- View all transactions in the "Recent Transactions" section
- Transactions are automatically sorted by date (newest first)
- Delete transactions by clicking the "Delete" button
- Your data is automatically saved to localStorage

### Budget Summary

The app automatically calculates and displays:
- **Balance**: Total income minus total expenses
- **Income**: Sum of all income transactions
- **Expenses**: Sum of all expense transactions

## Technology Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe JavaScript
- **CSS3** - Modern styling with gradients and responsive design
- **Local Storage** - Client-side data persistence
- **Create React App** - Zero-configuration build tool

## Project Structure

```
src/
├── components/
│   ├── BudgetSummary.tsx    # Balance, income, expenses display
│   ├── TransactionForm.tsx  # Form for adding new transactions
│   └── TransactionList.tsx  # List of all transactions
├── App.tsx                  # Main application component
├── App.css                  # App-specific styles
├── index.tsx                # Application entry point
├── index.css                # Global styles
└── reportWebVitals.ts       # Performance monitoring
```

## Features to Come

- [ ] Data export functionality
- [ ] Charts and graphs
- [ ] Budget goals and alerts
- [ ] Multiple currency support
- [ ] Cloud sync (optional)
- [ ] Dark mode toggle

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

If you encounter any issues or have questions, please open an issue on GitHub. 