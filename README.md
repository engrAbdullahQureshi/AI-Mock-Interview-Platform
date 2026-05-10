# AI Mock Interview Platform

A comprehensive AI-powered platform designed to help users practice and improve their job interview skills through realistic mock interviews with intelligent AI interviewers.

## 🚀 Overview

The AI Mock Interview Platform is a FastAPI-based backend system that enables users to:
- Upload and parse resumes (PDF, DOCX support)
- Generate personalized interview questions based on resume content
- Conduct real-time mock interviews with AI-powered interviewers
- Receive detailed feedback and performance analytics
- Practice various interview scenarios with adaptive questioning

The platform integrates Google Gemini AI for intelligent question generation, feedback analysis, and conversational interview simulation.

## ✨ Features

### Core Functionality
- **Resume Parsing**: Intelligent extraction of skills, experience, and qualifications from uploaded resumes
- **AI Question Generation**: Context-aware interview questions tailored to user's background and target role
- **Real-time Interviews**: WebSocket-based live interview sessions with streaming AI responses
- **Performance Analytics**: Detailed scoring and feedback on interview performance
- **User Authentication**: Secure JWT-based authentication system
- **Rate Limiting**: Built-in protection against API abuse

### Technical Features
- **Async Architecture**: Modern async/await patterns throughout for high performance
- **Cloud Database**: MongoDB Atlas integration for scalable data storage
- **Caching Layer**: Redis-based caching for improved response times
- **File Upload**: Secure handling of resume documents with validation
- **Error Handling**: Comprehensive exception handling and logging
- **Health Monitoring**: Built-in health checks for all services

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server for production deployment
- **Python 3.10+** - Core programming language

### Database & Storage
- **MongoDB Atlas** - Cloud-hosted NoSQL database
- **Motor** - Async MongoDB driver
- **Redis** - In-memory caching and rate limiting

### AI & ML
- **Google Gemini AI** - Advanced AI for question generation and feedback

### Security & Authentication
- **JWT (JSON Web Tokens)** - Secure token-based authentication
- **bcrypt** - Password hashing for user security
- **CORS** - Cross-origin resource sharing configuration

### File Processing
- **PyPDF2** - PDF text extraction and parsing
- **aiofiles** - Async file operations

### Development Tools
- **Pydantic** - Data validation and settings management
- **httpx** - Async HTTP client
- **python-dotenv** - Environment variable management

## 📁 Project Structure

```
AI-MOCK-INTERVIEW/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Application settings and configuration
│   ├── main.py                  # FastAPI app initialization and root endpoints
│   ├── database.py              # MongoDB connection management
│   ├── redis_client.py          # Redis connection and caching logic
│   ├── middleware/              # Custom middleware (prepared for future use)
│   │   └── __init__.py
│   ├── models/                  # Pydantic data models (prepared for implementation)
│   │   └── __init__.py
│   ├── routers/                 # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication routes (login, register, token refresh)
│   │   ├── resumes.py           # Resume upload/parsing routes (planned)
│   │   ├── interviews.py        # Interview management routes (planned)
│   │   └── websocket.py         # WebSocket chat routes (planned)
│   └── services/                # Business logic layer
│       └── __init__.py
│       └── ai_service.py        # AI integration service (planned)
│
├── frontend/                     # Frontend application directory (not yet implemented)
│
├── uploads/                      # Directory for uploaded resume files
│
├── requirements.txt              # Python dependencies
├── .env                         # Environment configuration file
├── .gitignore                   # Git ignore rules
├── README.md                    # Project documentation (this file)
├── app.log                      # Application log file
└── venv/                        # Virtual environment (not committed)
```

### Key Components

| Component | Purpose | Status |
|-----------|---------|--------|
| `config.py` | Centralized configuration management | ✅ Complete |
| `main.py` | Application entry point and setup | ✅ Complete |
| `database.py` | MongoDB connection and indexing | ✅ Complete |
| `redis_client.py` | Caching and rate limiting | ✅ Complete |
| `routers/auth.py` | Authentication endpoints | ⏳ Planned |
| `services/ai_service.py` | AI integration logic | ⏳ Planned |
| `frontend/` | User interface | ⏳ Not Started |

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or higher
- MongoDB Atlas account (cloud database)
- Google Gemini API key
- Redis (optional, for caching)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AI-MOCK-INTERVIEW
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory:

```env
# Application Settings
APP_NAME="AI Interview Platform"
DEBUG=True
API_VERSION="v1"

# Security (JWT Tokens)
SECRET_KEY="your-32-character-secret-key-here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# MongoDB Atlas Cloud Database
MONGODB_URL="mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster"
MONGODB_DB_NAME="ai_interview_db"

# Google Gemini AI Integration
GEMINI_API_KEY="your-gemini-api-key-here"

# File Upload Configuration
UPLOAD_DIR="./uploads"
MAX_UPLOAD_SIZE=10485760

# Rate Limiting (100 requests per hour)
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=3600

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# Redis Configuration (Optional)
REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_DB=0
```

### 5. Database Setup
The application will automatically create the required database collections and indexes on startup.

### 6. Run the Application
```bash
# Development mode
python app/main.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📖 Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
Once running, visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## 🔌 API Endpoints

### Current Endpoints
- `GET /` - Basic API information
- `GET /health` - Service health status
- `GET /api/v1/info` - API capabilities

### Planned Endpoints

#### Authentication
```
POST /api/v1/auth/register     # User registration
POST /api/v1/auth/login        # User login
POST /api/v1/auth/refresh      # Token refresh
POST /api/v1/auth/logout       # User logout
```

#### Resume Management
```
POST /api/v1/resumes/upload    # Upload resume
GET  /api/v1/resumes           # List user resumes
GET  /api/v1/resumes/{id}      # Get resume details
DELETE /api/v1/resumes/{id}    # Delete resume
```

#### Interview Management
```
POST /api/v1/interviews         # Create interview
GET  /api/v1/interviews         # List interviews
GET  /api/v1/interviews/{id}    # Get interview details
PUT  /api/v1/interviews/{id}    # Update interview
```

#### Real-time Chat
```
WebSocket /ws/chat/{interview_id}  # Live interview session
```

## 🗄️ Database Schema

### Collections

#### Users
```javascript
{
  _id: ObjectId,
  email: String (unique),
  username: String,
  password_hash: String,
  created_at: DateTime,
  updated_at: DateTime
}
```

#### Resumes
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  file_name: String,
  content: String,  // Extracted text
  file_path: String,
  uploaded_at: DateTime,
  parsed_data: Object  // Structured resume data
}
```

#### Interviews
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  title: String,
  job_title: String,
  questions: Array,
  status: String,  // active, completed, paused
  created_at: DateTime,
  completed_at: DateTime
}
```

#### Sessions
```javascript
{
  _id: ObjectId,
  interview_id: ObjectId,
  user_id: ObjectId,
  messages: Array,  // Chat history
  feedback: String,
  score: Number,
  created_at: DateTime
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | JWT signing key (32+ chars) | Yes | - |
| `MONGODB_URL` | MongoDB Atlas connection string | Yes | - |
| `GEMINI_API_KEY` | Google Gemini API key | Yes | - |
| `DEBUG` | Enable debug mode | No | False |
| `REDIS_HOST` | Redis server host | No | localhost |
| `RATE_LIMIT_REQUESTS` | Requests per period | No | 100 |
| `MAX_UPLOAD_SIZE` | Max file size in bytes | No | 10485760 |

### File Upload Settings
- **Supported formats**: PDF, DOCX, TXT
- **Maximum size**: 10MB (configurable)
- **Storage**: Local filesystem (`./uploads/`)

## 🚀 Deployment

### Production Deployment
```bash
# Using uvicorn with production settings
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment (Planned)
```dockerfile
# Dockerfile will be added for containerized deployment
```

## 🧪 Testing

### Running Tests
```bash
# Unit tests (when implemented)
pytest

# API testing with curl
curl -X GET "http://localhost:8000/health"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Add type hints for function parameters
- Write unit tests for new features
- Update documentation for API changes

## 📝 Current Implementation Status

### ✅ Completed
- FastAPI application setup with async architecture
- MongoDB Atlas database integration with indexing
- Redis caching and rate limiting system
- JWT-based authentication framework
- File upload infrastructure
- Comprehensive configuration management
- Error handling and logging
- Health check endpoints
- CORS and security middleware

### ⏳ In Progress / Planned
- User authentication routes implementation
- Resume parsing and AI question generation
- Interview management endpoints
- WebSocket real-time chat functionality
- Frontend user interface
- Performance analytics and scoring
- Production deployment configuration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

For questions or support:
- Check the API documentation at `/docs`
- Review the health endpoint at `/health`
- Check application logs in `app.log`

## 🔄 Future Enhancements

- [ ] Frontend application (React/Vue)
- [ ] Advanced AI feedback analysis
- [ ] Interview recording and playback
- [ ] Multi-language support
- [ ] Integration with job boards
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Video interview capabilities
- [ ] Integration with LinkedIn/Resume databases</content>
<parameter name="filePath">g:\AI-MOCK-INTERVIEW\README.md