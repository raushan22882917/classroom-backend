"""YouTube API integration service"""

from typing import List, Optional, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from app.config import settings
from app.utils.exceptions import APIException

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for interacting with YouTube Data API v3"""
    
    def __init__(self):
        """Initialize YouTube API client"""
        self.youtube = build('youtube', 'v3', developerKey=settings.youtube_api_key)
        self._quota_exceeded = False
        self._quota_reset_time: Optional[datetime] = None
    
    def _check_quota_status(self) -> bool:
        """
        Check if quota is currently exceeded and if it should be reset.
        
        Returns:
            True if quota is exceeded and hasn't reset yet, False otherwise
        """
        if not self._quota_exceeded:
            return False
        
        # If we have a reset time, check if we've passed it
        if self._quota_reset_time:
            now = datetime.now(timezone.utc)
            if now >= self._quota_reset_time:
                logger.info("YouTube API quota reset time has passed. Resetting quota status.")
                self._quota_exceeded = False
                self._quota_reset_time = None
                return False
        
        return True
    
    def _calculate_quota_reset_time(self) -> datetime:
        """
        Calculate when the YouTube API quota should reset (midnight PST).
        
        Returns:
            Datetime when quota resets (midnight PST as UTC)
        """
        # Get current time in PST
        pst_tz = ZoneInfo('America/Los_Angeles')
        now_pst = datetime.now(pst_tz)
        
        # Calculate next midnight PST
        if now_pst.hour == 0 and now_pst.minute == 0:
            # Already at midnight, reset happens today
            reset_time_pst = now_pst.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Next midnight
            reset_time_pst = (now_pst + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Convert to UTC
        reset_time_utc = reset_time_pst.astimezone(timezone.utc)
        return reset_time_utc
    
    async def get_video_metadata(self, youtube_id: str) -> Dict[str, Any]:
        """
        Fetch video metadata from YouTube API
        
        Args:
            youtube_id: YouTube video ID
            
        Returns:
            Dictionary containing video metadata
            
        Raises:
            APIException: If video not found or API error occurs
        """
        # Check quota status before making API call
        if self._check_quota_status():
            reset_time_str = self._quota_reset_time.strftime('%Y-%m-%d %H:%M:%S UTC') if self._quota_reset_time else "midnight PST"
            logger.debug(f"YouTube API quota already exceeded. Skipping API call for video {youtube_id}. Quota resets at {reset_time_str}.")
            raise APIException(
                code="YOUTUBE_QUOTA_EXCEEDED",
                message="YouTube API quota exceeded. The daily quota has been reached. Videos will be available again after the quota resets (typically at midnight PST).",
                status_code=503,
                retryable=True
            )
        
        try:
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=youtube_id
            )
            response = request.execute()
            
            if not response.get('items'):
                raise APIException(
                    code="VIDEO_NOT_FOUND",
                    message=f"Video with ID {youtube_id} not found",
                    status_code=404
                )
            
            video = response['items'][0]
            snippet = video.get('snippet', {})
            content_details = video.get('contentDetails', {})
            
            # Parse duration from ISO 8601 format (PT#H#M#S)
            duration_seconds = self._parse_duration(content_details.get('duration', 'PT0S'))
            
            return {
                'title': snippet.get('title', ''),
                'channel_name': snippet.get('channelTitle', ''),
                'duration_seconds': duration_seconds,
                'description': snippet.get('description', ''),
                'published_at': snippet.get('publishedAt', ''),
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'view_count': int(video.get('statistics', {}).get('viewCount', 0)),
                'like_count': int(video.get('statistics', {}).get('likeCount', 0))
            }
            
        except HttpError as e:
            logger.error(f"YouTube API error for video {youtube_id}: {str(e)}")
            error_message = str(e)
            error_details = ""
            
            # Try to extract error details
            try:
                error_details = e.error_details if hasattr(e, 'error_details') else str(e.content) if hasattr(e, 'content') else ""
            except:
                pass
            
            # Check for specific error types
            if "API key expired" in error_message or "API key not valid" in error_message:
                raise APIException(
                    code="YOUTUBE_API_KEY_ERROR",
                    message="YouTube API key has expired. Please contact administrator.",
                    status_code=503,
                    retryable=False
                )
            elif "quota" in error_message.lower() or "quotaExceeded" in error_message or "quotaExceeded" in str(error_details):
                # Set quota exceeded flag and calculate reset time
                self._quota_exceeded = True
                self._quota_reset_time = self._calculate_quota_reset_time()
                reset_time_str = self._quota_reset_time.strftime('%Y-%m-%d %H:%M:%S UTC')
                logger.warning(f"YouTube API quota exceeded for video {youtube_id}. Quota resets at {reset_time_str}. Error: {error_message}")
                raise APIException(
                    code="YOUTUBE_QUOTA_EXCEEDED",
                    message="YouTube API quota exceeded. The daily quota has been reached. Videos will be available again after the quota resets (typically at midnight PST).",
                    status_code=503,
                    retryable=True
                )
            else:
                raise APIException(
                    code="YOUTUBE_API_ERROR",
                    message="Failed to fetch video metadata from YouTube.",
                    status_code=500,
                    retryable=True
                )
        except Exception as e:
            logger.error(f"Unexpected error fetching video metadata: {str(e)}")
            raise APIException(
                code="YOUTUBE_SERVICE_ERROR",
                message=f"Unexpected error: {str(e)}",
                status_code=500
            )
    
    async def get_video_transcript(self, youtube_id: str, languages: List[str] = None) -> Optional[str]:
        """
        Fetch video transcript/captions using youtube-transcript-api
        
        Args:
            youtube_id: YouTube video ID
            languages: List of language codes to try (default: ['en', 'hi'])
            
        Returns:
            Transcript text as a single string, or None if not available
        """
        if languages is None:
            languages = ['en', 'hi']  # English and Hindi
        
        try:
            # Try to get transcript in preferred languages
            transcript_list = YouTubeTranscriptApi.list_transcripts(youtube_id)
            
            # Try manual captions first
            try:
                transcript = transcript_list.find_manually_created_transcript(languages)
            except NoTranscriptFound:
                # Fall back to auto-generated captions
                try:
                    transcript = transcript_list.find_generated_transcript(languages)
                except NoTranscriptFound:
                    logger.warning(f"No transcript found for video {youtube_id} in languages {languages}")
                    return None
            
            # Fetch and format transcript
            transcript_data = transcript.fetch()
            transcript_text = ' '.join([entry['text'] for entry in transcript_data])
            
            return transcript_text
            
        except TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for video {youtube_id}")
            return None
        except VideoUnavailable:
            logger.error(f"Video {youtube_id} is unavailable")
            raise APIException(
                code="VIDEO_UNAVAILABLE",
                message=f"Video {youtube_id} is unavailable",
                status_code=404
            )
        except Exception as e:
            logger.error(f"Error fetching transcript for video {youtube_id}: {str(e)}")
            return None
    
    async def get_transcript_with_timestamps(
        self, 
        youtube_id: str, 
        languages: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch video transcript with timestamps
        
        Args:
            youtube_id: YouTube video ID
            languages: List of language codes to try
            
        Returns:
            List of transcript entries with timestamps
        """
        if languages is None:
            languages = ['en', 'hi']
        
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(youtube_id)
            
            # Try manual captions first
            try:
                transcript = transcript_list.find_manually_created_transcript(languages)
            except NoTranscriptFound:
                try:
                    transcript = transcript_list.find_generated_transcript(languages)
                except NoTranscriptFound:
                    logger.warning(f"No transcript found for video {youtube_id}")
                    return []
            
            # Fetch transcript with timestamps
            transcript_data = transcript.fetch()
            
            # Format: [{'time': seconds, 'text': 'transcript text', 'duration': seconds}]
            formatted_transcript = [
                {
                    'time': int(entry['start']),
                    'text': entry['text'],
                    'duration': entry['duration']
                }
                for entry in transcript_data
            ]
            
            return formatted_transcript
            
        except Exception as e:
            logger.error(f"Error fetching transcript with timestamps: {str(e)}")
            return []
    
    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration format (PT#H#M#S) to seconds
        
        Args:
            duration_str: Duration string in ISO 8601 format
            
        Returns:
            Duration in seconds
        """
        import re
        
        # Remove PT prefix
        duration_str = duration_str.replace('PT', '')
        
        # Extract hours, minutes, seconds
        hours = 0
        minutes = 0
        seconds = 0
        
        hours_match = re.search(r'(\d+)H', duration_str)
        if hours_match:
            hours = int(hours_match.group(1))
        
        minutes_match = re.search(r'(\d+)M', duration_str)
        if minutes_match:
            minutes = int(minutes_match.group(1))
        
        seconds_match = re.search(r'(\d+)S', duration_str)
        if seconds_match:
            seconds = int(seconds_match.group(1))
        
        return hours * 3600 + minutes * 60 + seconds
    
    async def search_videos(
        self, 
        query: str, 
        max_results: int = 10,
        order: str = 'relevance'
    ) -> List[Dict[str, Any]]:
        """
        Search for educational videos on YouTube
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            order: Sort order (relevance, date, rating, viewCount)
            
        Returns:
            List of video metadata dictionaries (educational videos only)
        """
        # Check quota status before making API call
        if self._check_quota_status():
            reset_time_str = self._quota_reset_time.strftime('%Y-%m-%d %H:%M:%S UTC') if self._quota_reset_time else "midnight PST"
            logger.debug(f"YouTube API quota already exceeded. Skipping API call for query '{query[:50]}...'. Quota resets at {reset_time_str}.")
            raise APIException(
                code="YOUTUBE_QUOTA_EXCEEDED",
                message="YouTube API quota exceeded. The daily quota has been reached. Videos will be available again after the quota resets (typically at midnight PST).",
                status_code=503,
                retryable=True
            )
        
        try:
            # Enhance query with educational keywords to filter for educational content
            educational_keywords = ['tutorial', 'lecture', 'lesson', 'course', 'education', 'learn', 'study', 'explained']
            
            # Check if query already contains educational terms
            query_lower = query.lower()
            has_educational_term = any(keyword in query_lower for keyword in educational_keywords)
            
            # Add educational context if not present
            if not has_educational_term:
                enhanced_query = f"{query} tutorial lecture educational"
            else:
                enhanced_query = query
            
            # Build search request with educational filtering
            request = self.youtube.search().list(
                part='snippet',
                q=enhanced_query,
                type='video',
                maxResults=max_results * 2,  # Fetch more to filter educational ones
                order=order,
                relevanceLanguage='en',
                safeSearch='strict',
                videoCategoryId='27'  # Education category (27 = Education)
            )
            response = request.execute()
            
            videos = []
            educational_terms = ['tutorial', 'lecture', 'lesson', 'course', 'education', 'learn', 'study', 
                              'explained', 'class', 'teaching', 'academic', 'curriculum', 'syllabus',
                              'concept', 'topic', 'subject', 'mathematics', 'physics', 'chemistry', 
                              'biology', 'science', 'math', 'physics', 'chemistry']
            
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                
                title = snippet.get('title', '').lower()
                description = snippet.get('description', '').lower()
                channel_title = snippet.get('channelTitle', '').lower()
                
                # Filter for educational content
                is_educational = False
                
                # Check title and description for educational terms
                text_to_check = f"{title} {description} {channel_title}"
                educational_matches = sum(1 for term in educational_terms if term in text_to_check)
                
                # Exclude non-educational content
                exclude_terms = ['music', 'song', 'movie', 'trailer', 'game', 'gaming', 'entertainment',
                               'comedy', 'funny', 'prank', 'vlog', 'lifestyle', 'cooking', 'recipe']
                has_exclude_term = any(term in text_to_check for term in exclude_terms)
                
                # Consider it educational if:
                # 1. Has educational terms in title/description/channel
                # 2. Doesn't have exclude terms
                # 3. Or is from known educational channels (can be expanded)
                if educational_matches >= 1 and not has_exclude_term:
                    is_educational = True
                elif any(edu_term in channel_title for edu_term in ['education', 'academy', 'university', 'college', 'school', 'tutor', 'learn']):
                    is_educational = True
                
                if is_educational:
                    # Get video duration
                    duration_seconds = None
                    try:
                        video_details = self.youtube.videos().list(
                            part='contentDetails',
                            id=video_id
                        ).execute()
                        
                        if video_details.get('items'):
                            duration_str = video_details['items'][0]['contentDetails'].get('duration', '')
                            duration_seconds = self._parse_duration(duration_str)
                    except Exception as e:
                        logger.warning(f"Could not fetch duration for video {video_id}: {str(e)}")
                    
                    videos.append({
                        'youtube_id': video_id,
                        'title': snippet.get('title', ''),
                        'channel_name': snippet.get('channelTitle', ''),
                        'description': snippet.get('description', ''),
                        'published_at': snippet.get('publishedAt', ''),
                        'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                        'duration_seconds': duration_seconds
                    })
                    
                    # Stop when we have enough educational videos
                    if len(videos) >= max_results:
                        break
            
            return videos
            
        except HttpError as e:
            error_message = str(e)
            error_details = ""
            
            # Try to extract error details from the HTTP error
            try:
                error_details = e.error_details if hasattr(e, 'error_details') else str(e.content) if hasattr(e, 'content') else ""
            except:
                pass
            
            # Check for specific error types
            if "API key expired" in error_message or "API key not valid" in error_message:
                logger.warning(f"YouTube API key error for query '{query[:50]}...': {error_message}")
                raise APIException(
                    code="YOUTUBE_API_KEY_ERROR",
                    message="YouTube API key has expired. Please contact administrator to renew it.",
                    status_code=503,
                    retryable=False
                )
            elif "quota" in error_message.lower() or "quotaExceeded" in error_message or "quotaExceeded" in str(error_details):
                # Set quota exceeded flag and calculate reset time
                self._quota_exceeded = True
                self._quota_reset_time = self._calculate_quota_reset_time()
                reset_time_str = self._quota_reset_time.strftime('%Y-%m-%d %H:%M:%S UTC')
                logger.warning(f"YouTube API quota exceeded for query '{query[:50]}...'. Quota resets at {reset_time_str}. Error: {error_message}")
                raise APIException(
                    code="YOUTUBE_QUOTA_EXCEEDED",
                    message="YouTube API quota exceeded. The daily quota has been reached. Videos will be available again after the quota resets (typically at midnight PST).",
                    status_code=503,
                    retryable=True
                )
            else:
                logger.error(f"YouTube search error for query '{query[:50]}...': {error_message}. Details: {error_details}")
                raise APIException(
                    code="YOUTUBE_SEARCH_ERROR",
                    message="Failed to search YouTube videos. Please try again later.",
                    status_code=500,
                    retryable=True
                )


# Global service instance
youtube_service = YouTubeService()
