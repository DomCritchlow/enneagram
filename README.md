# Enneagram Team Assessment

A modern, clean web application for conducting Enneagram personality assessments within teams. Built with FastAPI and designed for simplicity, privacy, and professional use.

![Enneagram Assessment](https://via.placeholder.com/800x400/4F46E5/FFFFFF?text=Enneagram+Team+Assessment)

## ✨ Features

### 🎯 **Progressive Quiz Experience**
- Clean, minimal interface with calming design
- Progressive question flow (3 questions per page)
- Real-time progress tracking
- Mobile-responsive design

### 📊 **Rich Results Visualization**
- Interactive spider chart showing personality profile
- Prominent main type display with professional SVG icons
- Wing analysis (highest wing displayed)
- Professional personality insights

### 🔒 **Privacy & Security**
- Secure delete tokens for result removal
- No duplicate name restrictions - full privacy
- Bcrypt password hashing for admin functions
- CSRF protection and input sanitization

### 🎨 **Modern UI/UX**
- Beautiful SVG icons for each personality type
- Responsive design for all devices
- Dark/light theme ready
- Smooth animations and transitions

### 📈 **Administrative Features**
- CSV export of all results
- Comprehensive logging system
- Admin dashboard with analytics
- Secure authentication

### 🔧 **Developer Features**
- Dual question sets (54 full / 9 debug questions)
- Environment-based configuration switching
- Fast development testing mode
- Comprehensive error handling and logging

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd enneagram
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv enn_venv
   source enn_venv/bin/activate  # On Windows: enn_venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment (optional)**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

5. **Run the application**
   ```bash
   cd app
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the application**
   - Main app: http://localhost:8000
   - Types overview: http://localhost:8000/types
   - Admin (default): http://localhost:8000/admin (admin/change-me-please)

## 📁 Project Structure

```
enneagram/
├── app/                    # Main application directory
│   ├── api/               # FastAPI route handlers
│   │   ├── admin.py       # Admin dashboard and CSV export
│   │   └── quiz.py        # Quiz flow and results
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration management
│   │   ├── logging.py     # Centralized logging
│   │   └── security.py    # Security utilities
│   ├── models/            # Data models
│   │   ├── database.py    # SQLAlchemy models
│   │   └── schemas.py     # Pydantic schemas
│   ├── services/          # Business logic
│   │   └── quiz_service.py # Quiz processing and scoring
│   ├── static/            # Static assets
│   │   └── style.css      # Application styles
│   ├── templates/         # Jinja2 templates
│   │   ├── base.html      # Base template
│   │   ├── index.html     # Quiz interface
│   │   ├── results.html   # Results display
│   │   └── types.html     # Types overview
│   ├── questions.json     # Full Enneagram questions (54 questions)
│   ├── questions_short.json # Debug questions (9 questions)
│   ├── type_blurbs.json   # Type descriptions and SVG icons
│   └── main.py           # FastAPI application entry point
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md            # This file
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Security
ADMIN_USER=admin
ADMIN_PASS=your-secure-password
SECRET_KEY=your-secret-key

# Application
DEBUG=false
APP_TITLE=Enneagram Team Assessment

# Database
DATABASE_URL=sqlite:///app/results.sqlite
```

### Security Notes

- **Change the default admin password** before deployment
- The application will refuse to start in production with the default password
- All user inputs are sanitized and validated
- Delete tokens use cryptographically secure random generation

## 🎯 Usage

### For Participants

1. **Take the Assessment**
   - Enter your name (no duplicates required)
   - Answer questions honestly on a 1-5 scale
   - Progress through 3 questions per page

2. **View Results**
   - See your primary Enneagram type
   - Explore your personality profile via spider chart
   - Review wing analysis
   - Save your unique delete link for privacy

3. **Manage Your Data**
   - Use the delete token to remove results anytime
   - All deletions are permanent and logged

### For Administrators

1. **Access Admin Panel**
   ```
   http://localhost:8006/admin
   ```

2. **Export Data**
   - Download CSV with all results
   - Includes type scores and metadata
   - Excludes personal identifiers for privacy

3. **Monitor Activity**
   - View application logs
   - Track quiz completions
   - Monitor system health

## 🧠 About the Enneagram

The Enneagram is a powerful personality typing system that describes nine distinct personality types. Each type represents a different pattern of thinking, feeling, and behaving.

### The Nine Types

1. **Reformer** - Principled, purposeful, self-controlled
2. **Helper** - Empathic, interpersonal, people-pleasing
3. **Achiever** - Adaptable, driven, image-conscious
4. **Individualist** - Expressive, dramatic, self-absorbed
5. **Investigator** - Intense, cerebral, perceptive
6. **Loyalist** - Engaging, responsible, anxious
7. **Enthusiast** - Spontaneous, versatile, acquisitive
8. **Challenger** - Self-confident, decisive, willful
9. **Peacemaker** - Receptive, reassuring, complacent

## 🛠️ Development

### Running in Development

```bash
# Start with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run with debug logging
DEBUG=true uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Use short question set for fast debugging (9 questions vs 54)
QUESTIONS_FILE=questions_short.json uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Database Management

```bash
# The database is created automatically on first run
# To reset the database, simply delete the SQLite file:
rm app/results.sqlite
```

### Question Sets

The application supports two question sets for different use cases:

**Production Assessment (`questions.json`)**:
- **54 comprehensive questions** (6 per type)
- Provides accurate, reliable personality assessment
- Used by default for all assessments

**Development Testing (`questions_short.json`)**:
- **9 quick questions** (1 per type)  
- Fast testing during development
- Enable with: `QUESTIONS_FILE=questions_short.json`

Edit either file to modify questions:

```json
{
  "id": 1,
  "text": "I hold myself to very high standards.",
  "type": 1,
  "reverse": false
}
```

## 📋 API Endpoints

### Public Endpoints
- `GET /` - Quiz interface
- `GET /types` - Enneagram types overview
- `GET /results` - Results display (requires token)
- `POST /submit` - Submit quiz responses
- `GET /delete/{token}` - Delete results by token

### Admin Endpoints
- `GET /admin` - Admin dashboard
- `POST /admin/login` - Admin authentication
- `GET /admin/export` - CSV export

### API Endpoints
- `GET /api/questions` - Get quiz questions
- `GET /api/health` - Application health check

## 🔧 Deployment

### Production Checklist

- [ ] Set strong admin password in environment
- [ ] Configure secure secret key
- [ ] Set `DEBUG=false`
- [ ] Set up proper database (PostgreSQL recommended for production)
- [ ] Configure HTTPS
- [ ] Set up log rotation
- [ ] Configure backup strategy

### Example Production Command

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Enneagram Institute for the personality type system
- FastAPI team for the excellent web framework
- The open source community for the tools and libraries used

## 🚀 What's Next?

- [ ] Team comparison analytics  
- [ ] PDF report generation
- [ ] Integration with HR systems
- [ ] Multi-language support
- [ ] Advanced personality insights
- [ ] Question validation and psychometric testing
- [ ] Custom question sets for different contexts


