# Budget Tracker Backend

A robust FastAPI backend for the Budget Tracker application with comprehensive user management, transaction tracking, and financial analytics.

## Features

- **Authentication & Authorization**: JWT-based authentication with password reset functionality
- **User Management**: Registration, login, and profile management
- **Category Management**: Hierarchical categories with sub-categories
- **Transaction Tracking**: Full CRUD operations with filtering and pagination
- **Account Management**: Multiple account types (bank, credit, cash, investment)
- **Database Migrations**: Alembic for schema versioning
- **API Documentation**: Auto-generated with FastAPI
- **CORS Support**: Cross-origin resource sharing for frontend integration

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool
- **PostgreSQL/SQLite**: Database support
- **JWT**: JSON Web Tokens for authentication
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server

## Prerequisites

- Python 3.8+
- PostgreSQL (optional, SQLite for development)
- pip

## Installation

1. **Clone the repository and navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database:**
   ```bash
   # For SQLite (development)
   python -c "from app.main import app; from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
   
   # For PostgreSQL (production)
   alembic upgrade head
   ```

## Configuration

Create a `.env` file with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/budget_tracker
# or for SQLite: DATABASE_URL=sqlite:///./budget_tracker.db

# JWT Configuration
SECRET_KEY=your-secret-key-here-make-it-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration (for password reset)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Application Configuration
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

## Running the Application

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/forgotPass` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password with token

### Categories
- `POST /api/v1/category/addCategory` - Add new category
- `PUT /api/v1/category/editCategory/{category_id}` - Edit category
- `PUT /api/v1/category/deleteCategory/{category_id}` - Delete category
- `GET /api/v1/category/list` - List user categories

### Sub-Categories
- `POST /api/v1/subCategory/addSubCategory` - Add new sub-category
- `PUT /api/v1/subCategory/deleteSubCategory/{sub_category_id}` - Delete sub-category
- `PUT /api/v1/subCategory/changeCategory/{sub_category_id}` - Change sub-category category
- `GET /api/v1/subCategory/list/{category_id}` - List sub-categories for category

### Transactions
- `POST /api/v1/transaction/addTransaction` - Add new transaction
- `PUT /api/v1/transaction/editTransaction/{transaction_id}` - Edit transaction
- `PUT /api/v1/transaction/deleteTransaction/{transaction_id}` - Delete transaction
- `GET /api/v1/transaction/getTransactionRecord` - Get transaction records with filtering
- `GET /api/v1/transaction/{transaction_id}` - Get transaction details

### Accounts
- `POST /api/v1/account/addAccount` - Add new account
- `PUT /api/v1/account/editAccount/{account_id}` - Edit account
- `PUT /api/v1/account/deleteAccount/{account_id}` - Delete account
- `GET /api/v1/account/list` - List user accounts
- `GET /api/v1/account/{account_id}` - Get account details

## Database Migrations

### Initialize Alembic (first time only)
```bash
alembic init alembic
```

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

## Testing

Run tests with pytest:
```bash
pytest
```

## Development

### Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Authentication utilities
│   └── routers/             # API route handlers
│       ├── __init__.py
│       ├── auth.py          # Authentication routes
│       ├── category.py      # Category routes
│       ├── subcategory.py   # Sub-category routes
│       ├── transaction.py   # Transaction routes
│       └── account.py       # Account routes
├── alembic/                 # Database migrations
├── requirements.txt          # Python dependencies
├── alembic.ini             # Alembic configuration
├── env.example             # Environment variables template
└── README.md               # This file
```

### Adding New Features

1. **Models**: Add new SQLAlchemy models in `app/models.py`
2. **Schemas**: Add Pydantic schemas in `app/schemas.py`
3. **Routes**: Create new router files in `app/routers/`
4. **Migrations**: Generate and apply database migrations
5. **Documentation**: Update this README and API docs

## Security Features

- **Password Hashing**: Bcrypt for secure password storage
- **JWT Tokens**: Secure authentication with configurable expiration
- **Input Validation**: Pydantic schemas for request validation
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Configurable cross-origin resource sharing

## Performance Optimizations

- **Database Indexing**: Proper indexes on frequently queried fields
- **Pagination**: Efficient pagination for large datasets
- **Connection Pooling**: Database connection pooling for better performance
- **Async Support**: FastAPI's async capabilities for better concurrency

## Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production
```env
DATABASE_URL=postgresql://user:password@host:port/dbname
SECRET_KEY=your-production-secret-key
DEBUG=False
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 