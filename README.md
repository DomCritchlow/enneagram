# Enneagram Team Assessment

A web application for conducting Enneagram personality assessments within teams. Built with FastAPI for simplicity and professional use.

## Features

**Quiz Experience**
- Progressive question flow (3 questions per page)
- 54 comprehensive questions for accurate assessment
- Mobile-responsive interface
- Real-time progress tracking

**Results & Visualization**
- Interactive spider chart showing personality profile
- SVG icons for each personality type
- Wing analysis (highest wing displayed)
- Individual result pages with delete tokens

**Privacy & Security**
- Secure delete tokens for result removal
- Bcrypt password hashing for admin functions
- Input sanitization and validation
- Local data storage

**Administration**
- CSV export of all results
- Admin dashboard with secure authentication
- Comprehensive logging system

**Development**
- Dual question sets (54 full / 9 debug questions)
- Environment-based configuration
- Fast development testing mode

## Quick Start

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

4. **Run the application**
   ```bash
   cd app
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the application**
   - Main app: http://localhost:8000
   - Types overview: http://localhost:8000/types
   - Admin: http://localhost:8000/admin (admin/change-me-please)

## Configuration

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

**Important**: Change the default admin password before deployment. The application will refuse to start in production with the default password.

## Usage

**For Participants**
1. Enter your name and take the 54-question assessment
2. View results showing your primary type, wing analysis, and spider chart
3. Use the provided delete token to remove your data anytime

**For Administrators**
1. Access admin panel at http://localhost:8000/admin
2. Export CSV data with all results and type scores
3. Monitor application logs and quiz completions

## About the Enneagram

The Enneagram describes nine personality types, each representing different patterns of thinking, feeling, and behaving:

1. **Reformer** - Principled, purposeful, self-controlled
2. **Helper** - Empathic, interpersonal, people-pleasing
3. **Achiever** - Adaptable, driven, image-conscious
4. **Individualist** - Expressive, dramatic, self-absorbed
5. **Investigator** - Intense, cerebral, perceptive
6. **Loyalist** - Engaging, responsible, anxious
7. **Enthusiast** - Spontaneous, versatile, acquisitive
8. **Challenger** - Self-confident, decisive, willful
9. **Peacemaker** - Receptive, reassuring, complacent

## Development

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

## Deployment

For production deployment:

1. Set strong admin password in environment
2. Configure secure secret key  
3. Set `DEBUG=false`
4. Use a production WSGI server:

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.