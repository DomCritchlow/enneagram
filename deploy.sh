#!/bin/bash

# Deployment script for Google Cloud Run
# Usage: ./deploy.sh [PROJECT_ID]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project ID from argument or gcloud config
PROJECT_ID=${1:-$(gcloud config get-value project)}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No project ID provided and none set in gcloud config${NC}"
    echo "Usage: $0 [PROJECT_ID]"
    exit 1
fi

echo -e "${GREEN}Deploying Stateless Enneagram App to Google Cloud Run...${NC}"
echo -e "${YELLOW}Project ID: $PROJECT_ID${NC}"

# Enable required APIs first
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID --quiet
gcloud services enable run.googleapis.com --project=$PROJECT_ID --quiet
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID --quiet
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID --quiet
gcloud services enable sheets.googleapis.com --project=$PROJECT_ID --quiet

# Wait a moment for APIs to be fully enabled
echo -e "${YELLOW}Waiting for APIs to be ready...${NC}"
sleep 10

# Check if required secrets exist, if not create them
echo -e "${YELLOW}Checking Google Sheets integration secrets...${NC}"

# Check Google service account secret
echo -e "${YELLOW}Checking google-service-account secret...${NC}"
if ! gcloud secrets describe google-service-account --project=$PROJECT_ID --quiet 2>/dev/null; then
    echo -e "${YELLOW}Creating google-service-account secret...${NC}"
    read -p "Enter path to Google service account JSON file: " SERVICE_ACCOUNT_PATH
    if [ -z "$SERVICE_ACCOUNT_PATH" ] || [ ! -f "$SERVICE_ACCOUNT_PATH" ]; then
        echo -e "${RED}Error: Service account JSON file not found${NC}"
        exit 1
    fi
    gcloud secrets create google-service-account --data-file="$SERVICE_ACCOUNT_PATH" --project=$PROJECT_ID --quiet
    echo -e "${GREEN}google-service-account secret created${NC}"
else
    echo -e "${GREEN}google-service-account secret exists${NC}"
fi

# Check Google Sheets ID secret
echo -e "${YELLOW}Checking google-sheets-id secret...${NC}"
if ! gcloud secrets describe google-sheets-id --project=$PROJECT_ID --quiet 2>/dev/null; then
    echo -e "${YELLOW}Creating google-sheets-id secret...${NC}"
    read -p "Enter Google Sheets ID: " SHEETS_ID
    if [ -z "$SHEETS_ID" ]; then
        echo -e "${RED}Error: Google Sheets ID cannot be empty${NC}"
        exit 1
    fi
    echo "$SHEETS_ID" | gcloud secrets create google-sheets-id --data-file=- --project=$PROJECT_ID --quiet
    echo -e "${GREEN}google-sheets-id secret created${NC}"
else
    echo -e "${GREEN}google-sheets-id secret exists${NC}"
fi

# Set up all required IAM permissions
echo -e "${YELLOW}Setting up IAM permissions...${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Enable Artifact Registry API (needed for container storage)
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID --quiet

# Create Artifact Registry repository if it doesn't exist
if ! gcloud artifacts repositories describe enneagram-app --location=us-central1 --project=$PROJECT_ID --quiet 2>/dev/null; then
    echo -e "${YELLOW}Creating Artifact Registry repository...${NC}"
    gcloud artifacts repositories create enneagram-app --repository-format=docker --location=us-central1 --project=$PROJECT_ID --quiet
fi

# Create dedicated service account for Cloud Run if it doesn't exist
if ! gcloud iam service-accounts describe enneagram-run@$PROJECT_ID.iam.gserviceaccount.com --project=$PROJECT_ID --quiet 2>/dev/null; then
    echo -e "${YELLOW}Creating Cloud Run service account...${NC}"
    gcloud iam service-accounts create enneagram-run --display-name="Enneagram Stateless Cloud Run Service" --project=$PROJECT_ID --quiet
fi

# Grant necessary permissions to Cloud Build service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/artifactregistry.writer" --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/run.developer" --quiet

# Grant permissions to the dedicated Cloud Run service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:enneagram-run@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" --quiet

# Allow Cloud Build to act as the Cloud Run service account
gcloud iam service-accounts add-iam-policy-binding enneagram-run@$PROJECT_ID.iam.gserviceaccount.com \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser" --project=$PROJECT_ID --quiet

# Deploy using Cloud Build
echo -e "${YELLOW}Starting deployment...${NC}"
gcloud builds submit --config cloudbuild.yaml --project=$PROJECT_ID

echo -e "${GREEN}Deployment completed!${NC}"

# Get the actual service URL
SERVICE_URL=$(gcloud run services describe enneagram-app --region=us-central1 --project=$PROJECT_ID --format="value(status.url)" 2>/dev/null || echo "")
if [ -n "$SERVICE_URL" ]; then
    echo -e "${GREEN}🌐 Your app is live at: $SERVICE_URL${NC}"
    echo -e "${YELLOW}📋 Service Details:${NC}"
    echo "   • Project: $PROJECT_ID"
    echo "   • Region: us-central1"
    echo "   • Service: enneagram-app"
else
    echo -e "${RED}❌ Could not retrieve service URL. Check deployment status manually.${NC}"
    echo "   Run: gcloud run services list --project=$PROJECT_ID"
fi
