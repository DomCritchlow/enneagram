"""
Google Sheets integration service for logging quiz results.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.config import settings
from core.logging import app_logger
from models.schemas import EnneagramResult


class SheetsService:
    """Service for Google Sheets integration."""
    
    def __init__(self):
        self._service = None
        self._credentials = None
    
    def _get_credentials(self) -> Optional[Credentials]:
        """Get Google Sheets API credentials."""
        if self._credentials and self._credentials.valid:
            return self._credentials
        
        try:
            # Try service account credentials from environment variable
            if settings.google_service_account_json:
                if os.path.isfile(settings.google_service_account_json):
                    # From file path
                    self._credentials = Credentials.from_service_account_file(
                        settings.google_service_account_json,
                        scopes=settings.google_sheets_scopes
                    )
                else:
                    # From JSON string
                    service_account_info = json.loads(settings.google_service_account_json)
                    self._credentials = Credentials.from_service_account_info(
                        service_account_info,
                        scopes=settings.google_sheets_scopes
                    )
            else:
                app_logger.error("No Google service account credentials configured")
                return None
                
            if self._credentials and not self._credentials.valid:
                if self._credentials.expired and self._credentials.refresh_token:
                    self._credentials.refresh(Request())
                    
            return self._credentials
            
        except Exception as e:
            app_logger.error(f"Failed to get Google Sheets credentials: {e}")
            return None
    
    def _get_service(self):
        """Get Google Sheets API service."""
        if self._service:
            return self._service
            
        credentials = self._get_credentials()
        if not credentials:
            return None
            
        try:
            self._service = build('sheets', 'v4', credentials=credentials)
            return self._service
        except Exception as e:
            app_logger.error(f"Failed to build Google Sheets service: {e}")
            return None
    
    def log_quiz_result(self, result: EnneagramResult) -> bool:
        """
        Log quiz result to Google Sheets.
        
        Args:
            result: EnneagramResult to log
            
        Returns:
            True if successful, False otherwise
        """
        service = self._get_service()
        if not service:
            app_logger.error("Google Sheets service not available")
            return False
        
        try:
            # Prepare row data
            timestamp = datetime.utcnow().isoformat()
            scores_dict = result.scores.to_dict()
            
            # Create row: timestamp, name, team, top_type, type1_score, type2_score, ..., type9_score, validity_mean, validity_sd
            row_data = [
                timestamp,
                result.name,
                result.team or "NA",  # Use "NA" if no team specified
                result.top_type,
            ]
            
            # Add type scores (1-9)
            for i in range(1, 10):
                row_data.append(scores_dict.get(i, 0))
            
            # Add validity stats
            row_data.extend([
                round(result.validity.mean, 2),
                round(result.validity.sd, 2)
            ])
            
            # Add tied types if any
            tied_types_str = json.dumps(result.tied_types) if result.tied_types else ""
            row_data.append(tied_types_str)
            
            # Append to sheet
            body = {
                'values': [row_data]
            }
            
            service.spreadsheets().values().append(
                spreadsheetId=settings.google_sheets_id,
                range=settings.google_sheets_range,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            app_logger.info(f"Successfully logged quiz result for {result.name} to Google Sheets")
            return True
            
        except HttpError as e:
            app_logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            app_logger.error(f"Failed to log quiz result to Google Sheets: {e}")
            return False
    
    def initialize_sheet_headers(self) -> bool:
        """
        Initialize the Google Sheet with headers if it's empty.
        
        Returns:
            True if successful, False otherwise
        """
        service = self._get_service()
        if not service:
            return False
        
        try:
            # Check if sheet already has data
            result = service.spreadsheets().values().get(
                spreadsheetId=settings.google_sheets_id,
                range='A1:Z1'
            ).execute()
            
            values = result.get('values', [])
            if values:
                # Sheet already has headers
                return True
            
            # Add headers
            headers = [
                'Timestamp (UTC)',
                'Name',
                'Team',
                'Top Type',
                'Type 1 Score',
                'Type 2 Score', 
                'Type 3 Score',
                'Type 4 Score',
                'Type 5 Score',
                'Type 6 Score',
                'Type 7 Score',
                'Type 8 Score',
                'Type 9 Score',
                'Validity Mean',
                'Validity SD',
                'Tied Types'
            ]
            
            body = {
                'values': [headers]
            }
            
            service.spreadsheets().values().update(
                spreadsheetId=settings.google_sheets_id,
                range='A1:P1',  # Extended to P1 to include Team column
                valueInputOption='RAW',
                body=body
            ).execute()
            
            app_logger.info("Successfully initialized Google Sheets headers")
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to initialize Google Sheets headers: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test Google Sheets connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        service = self._get_service()
        if not service:
            return False
            
        try:
            # Try to read the sheet metadata
            service.spreadsheets().get(
                spreadsheetId=settings.google_sheets_id
            ).execute()
            
            app_logger.info("Google Sheets connection test successful")
            return True
            
        except Exception as e:
            app_logger.error(f"Google Sheets connection test failed: {e}")
            return False
    
    def get_team_data(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Get all data for a specific team.
        
        Args:
            team_name: Name of the team to get data for
            
        Returns:
            List of dictionaries containing team member data
        """
        service = self._get_service()
        if not service:
            app_logger.error("Google Sheets service not available")
            return []
        
        try:
            # Get all data from the sheet
            result = service.spreadsheets().values().get(
                spreadsheetId=settings.google_sheets_id,
                range=settings.google_sheets_range
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return []
            
            # First row should be headers
            headers = values[0]
            team_data = []
            
            # Find team column index
            team_col_index = None
            try:
                team_col_index = headers.index('Team')
            except ValueError:
                app_logger.error("Team column not found in spreadsheet")
                return []
            
            # Process data rows
            for row in values[1:]:  # Skip header row
                if len(row) > team_col_index and row[team_col_index].lower() == team_name.lower():
                    # Create dictionary from row data
                    row_dict = {}
                    for i, header in enumerate(headers):
                        row_dict[header] = row[i] if i < len(row) else ''
                    team_data.append(row_dict)
            
            app_logger.info(f"Retrieved {len(team_data)} records for team {team_name}")
            return team_data
            
        except Exception as e:
            app_logger.error(f"Failed to get team data: {e}")
            return []
    
    def migrate_existing_entries(self) -> bool:
        """
        Add 'NA' to the Team column for existing entries that don't have it.
        This is a one-time migration function.
        
        Returns:
            True if successful, False otherwise
        """
        service = self._get_service()
        if not service:
            app_logger.error("Google Sheets service not available")
            return False
        
        try:
            # Get all data from the sheet
            result = service.spreadsheets().values().get(
                spreadsheetId=settings.google_sheets_id,
                range=settings.google_sheets_range
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return True  # No data to migrate
            
            headers = values[0]
            
            # Check if Team column already exists
            if 'Team' in headers:
                app_logger.info("Team column already exists, no migration needed")
                return True
            
            # Insert Team column after Name column
            name_col_index = headers.index('Name') if 'Name' in headers else 1
            team_col_index = name_col_index + 1
            
            # Update headers
            headers.insert(team_col_index, 'Team')
            
            # Update all data rows to include 'NA' in team column
            for i, row in enumerate(values[1:], start=1):
                while len(row) < team_col_index:
                    row.append('')
                row.insert(team_col_index, 'NA')
            
            # Update the entire sheet with migrated data
            body = {
                'values': values
            }
            
            service.spreadsheets().values().update(
                spreadsheetId=settings.google_sheets_id,
                range=settings.google_sheets_range,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            app_logger.info("Successfully migrated existing entries with Team column")
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to migrate existing entries: {e}")
            return False


# Global service instance
sheets_service = SheetsService()
