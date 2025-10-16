# Enneagram Team Assessment

**🌐 Live App:** https://enneagram-app-w34l2h6gva-uc.a.run.app

A stateless web application for conducting Enneagram personality assessments within teams. Built with FastAPI and Google Sheets integration for privacy and simplicity.

## Features

**Quiz Experience**
- Progressive question flow (3 questions per page)
- Question randomization for fresh assessment experience
- 54 comprehensive questions for accurate assessment (or 9 for development)
- Mobile-responsive interface with modern UI
- Real-time progress tracking
- Optional team affiliation input

**Results & Visualization**
- Interactive spider chart showing personality profile
- SVG icons for each personality type
- Wing analysis (highest wing displayed)
- One-time result display (completely stateless)
- Direct link to team results (when team specified)

**Team Analytics**
- Team-based assessment aggregation
- Team composition analysis and statistics
- Balance scoring and insights
- Public team dashboard at `/team/{team-name}`
- Smart caching with development override

**Types Reference**
- Comprehensive overview of all 9 Enneagram types
- Interactive expand/collapse for detailed information
- Type strengths and growth areas
- Professional iconography and descriptions

**Privacy & Security**
- **100% stateless** - no server-side data storage
- Results displayed once and not retained locally
- Input sanitization and validation
- Content Security Policy protection
- Real-time logging to Google Sheets for admin review

**Data Management**
- Automatic logging to Google Sheets with team information
- Real-time result collection for administrators
- No local database or user data storage
- GDPR-friendly architecture

**Developer Experience**
- Dual question sets (54 full / 9 debug questions)
- Interactive API documentation (`/docs`, `/redoc`)
- Environment-based configuration
- Fast development testing mode
- Comprehensive logging and health checks

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Google Cloud account (for Google Sheets integration)

### Google Sheets Setup

1. **Create a Google Sheets spreadsheet** for collecting results

2. **Set up Google Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Sheets API
   - Create service account credentials
   - Download the JSON key file

3. **Share your spreadsheet:**
   - Share the Google Sheet with the service account email
   - Grant "Editor" permissions

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

4. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your Google Sheets configuration
   ```

5. **Run the application**
   ```bash
   cd app
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the application**
   - Main app: http://localhost:8000
   - Types overview: http://localhost:8000/types
   - API documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health
   - Team analytics: http://localhost:8000/team/{team-name}

## Configuration

Create a `.env` file in the root directory:

```env
# Google Sheets Integration (REQUIRED)
GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/your/service-account.json
GOOGLE_SHEETS_ID=your_spreadsheet_id_here
GOOGLE_SHEETS_RANGE=Sheet1!A:Z

# Application Settings
DEBUG=false
APP_TITLE=Enneagram Team Assessment
QUESTIONS_FILE=questions.json
BLURBS_FILE=type_blurbs.json
NAME_MAX_LENGTH=100

# Team Features
DISABLE_CACHING=false  # Set to true in development for immediate team updates

# Development Settings
# QUESTIONS_FILE=questions_short.json  # Uncomment for 9-question testing mode
```

## Usage

**For Participants**
1. Enter your name and optionally specify a team name (3-20 characters, letters/numbers only)
2. Take the randomized 54-question assessment (questions appear in different order each time)
3. View results showing your primary type, wing analysis, and interactive spider chart
4. If you specified a team, click the team link to see aggregated team results
5. Results are displayed once and not stored on the server

**For Teams**
1. All team members use the same team name during assessment
2. Visit `/team/{team-name}` to view team composition and analytics
3. See type distribution, balance scores, and team insights
4. Team pages are publicly accessible but show only aggregated, anonymous data

**For Administrators**
1. Results are automatically logged to your Google Sheets in real-time with team information
2. Access the spreadsheet to view and analyze all individual assessment data
3. Use spreadsheet features for filtering, sorting, and exporting data
4. Team column allows grouping and analysis by organizational unit

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

# Disable team caching for immediate updates during development
DISABLE_CACHING=true uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Combined development settings
DEBUG=true QUESTIONS_FILE=questions_short.json DISABLE_CACHING=true uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Google Sheets Testing

For development, you can:
1. Use the same Google Sheets setup as production
2. Create a separate test spreadsheet
3. Run without Google Sheets (app will log warnings but continue to work)

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

### Local Production

For local production deployment:

1. Configure Google Sheets integration in `.env`
2. Set `DEBUG=false`
3. Use a production WSGI server:

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

Build and run with Docker:

```bash
# Build the image
docker build -t enneagram-app .

# Run the container with Google Sheets credentials
docker run -p 8080:8080 \
  -e GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}' \
  -e GOOGLE_SHEETS_ID=your_spreadsheet_id \
  -e DEBUG=false \
  enneagram-app

# Or mount the service account file
docker run -p 8080:8080 \
  -v /path/to/service-account.json:/app/service-account.json \
  -e GOOGLE_SERVICE_ACCOUNT_JSON=/app/service-account.json \
  -e GOOGLE_SHEETS_ID=your_spreadsheet_id \
  -e DEBUG=false \
  enneagram-app
```

### Google Cloud Run

**🔗 URL Generation:** Cloud Run generates unique URLs with random suffixes (e.g., `w34l2h6gva-uc`). The deployment script will automatically retrieve and display the actual service URL after deployment.

#### Prerequisites

1. Install [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
2. Authenticate: `gcloud auth login`
3. Set your project: `gcloud config set project YOUR_PROJECT_ID`
4. Set up Google Sheets integration with service account

#### Automated Deployment

Use the provided deployment script:

```bash
# Make script executable (if not already)
chmod +x deploy.sh

# Deploy to Cloud Run
./deploy.sh [YOUR_PROJECT_ID]
```

The script will:
- Create Google Sheets service account secrets in Secret Manager
- Enable necessary APIs (Cloud Run, Cloud Build, Secret Manager, Sheets API)
- Set up IAM permissions
- Build and deploy using Cloud Build
- Automatically retrieve and display the actual service URL

#### Manual Deployment

1. **Create secrets in Secret Manager:**

```bash
# Create Google service account secret
gcloud secrets create google-service-account --data-file=path/to/service-account.json

# Create Google Sheets ID secret
echo "your_spreadsheet_id" | gcloud secrets create google-sheets-id --data-file=-
```

2. **Enable required APIs:**

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sheets.googleapis.com
```

3. **Deploy with Cloud Build:**

```bash
gcloud builds submit --config cloudbuild.yaml
```

#### Configuration

The Cloud Run deployment uses:
- **Container Port:** 8080 (automatically set by Cloud Run's PORT environment variable)
- **Memory:** 1 GiB (default)
- **CPU:** 1 vCPU (default)
- **Concurrency:** 80 requests per instance (default)
- **Min instances:** 0 (scales to zero when not in use)
- **Max instances:** 10 (configurable)

Environment variables are managed through Google Secret Manager for security.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.