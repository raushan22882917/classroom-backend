"""Video management endpoints"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import logging
from supabase import Client

from app.models.content import Video, VideoCreate, Timestamp
from app.models.base import Subject
from app.services.youtube_service import youtube_service
from app.services.embedding_service import embedding_service
from app.services.vector_db_service import vector_db_service
from app.config import settings
from app.utils.exceptions import APIException
from supabase import create_client

logger = logging.getLogger(__name__)

router = APIRouter()


def get_supabase() -> Client:
    """Get Supabase client"""
    return create_client(settings.supabase_url, settings.supabase_service_key)


@router.post("/curate", response_model=Video, status_code=201)
async def curate_video(
    video_data: VideoCreate,
    background_tasks: BackgroundTasks,
    supabase: Client = Depends(get_supabase)
):
    """
    Curate a YouTube video by adding it to the platform (Admin only)
    
    This endpoint:
    1. Fetches video metadata from YouTube API
    2. Fetches video transcript/captions
    3. Stores video in database
    4. Indexes transcript into RAG pipeline (background task)
    
    Args:
        video_data: Video creation data with youtube_id and topic associations
        background_tasks: FastAPI background tasks
        supabase: Supabase client
        
    Returns:
        Created video object
    """
    try:
        youtube_id = video_data.youtube_id
        
        # Check if video already exists
        existing = supabase.table('videos').select('*').eq('youtube_id', youtube_id).execute()
        if existing.data:
            raise APIException(
                code="VIDEO_ALREADY_EXISTS",
                message=f"Video with YouTube ID {youtube_id} already exists",
                status_code=409
            )
        
        # Fetch video metadata from YouTube
        logger.info(f"Fetching metadata for video {youtube_id}")
        metadata = await youtube_service.get_video_metadata(youtube_id)
        
        # Fetch transcript
        logger.info(f"Fetching transcript for video {youtube_id}")
        transcript = await youtube_service.get_video_transcript(youtube_id)
        
        # Prepare video data
        video_record = {
            'youtube_id': youtube_id,
            'title': video_data.title or metadata['title'],
            'transcript': transcript,
            'timestamps': [ts.dict() if isinstance(ts, Timestamp) else ts for ts in video_data.timestamps],
            'topic_ids': video_data.topic_ids,
            'subject': video_data.subject.value if video_data.subject else None,
            'duration_seconds': video_data.duration_seconds or metadata['duration_seconds'],
            'channel_name': video_data.channel_name or metadata['channel_name'],
            'metadata': {
                **video_data.metadata,
                'description': metadata.get('description', ''),
                'published_at': metadata.get('published_at', ''),
                'thumbnail_url': metadata.get('thumbnail_url', ''),
                'view_count': metadata.get('view_count', 0),
                'like_count': metadata.get('like_count', 0)
            }
        }
        
        # Insert into database
        result = supabase.table('videos').insert(video_record).execute()
        
        if not result.data:
            raise APIException(
                code="DATABASE_ERROR",
                message="Failed to insert video into database",
                status_code=500
            )
        
        video = result.data[0]
        
        # Index transcript into RAG pipeline in background
        if transcript:
            background_tasks.add_task(
                index_video_transcript,
                video_id=video['id'],
                youtube_id=youtube_id,
                transcript=transcript,
                metadata={
                    'title': video['title'],
                    'subject': video['subject'],
                    'topic_ids': video['topic_ids'],
                    'type': 'video'
                }
            )
        
        logger.info(f"Successfully curated video {youtube_id}")
        
        # Convert to Video model
        return Video(
            id=video['id'],
            youtube_id=video['youtube_id'],
            title=video['title'],
            transcript=video.get('transcript'),
            timestamps=video.get('timestamps', []),
            topic_ids=video.get('topic_ids', []),
            subject=Subject(video['subject']) if video.get('subject') else None,
            duration_seconds=video.get('duration_seconds'),
            channel_name=video.get('channel_name'),
            metadata=video.get('metadata', {}),
            created_at=datetime.fromisoformat(video['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(video['updated_at'].replace('Z', '+00:00'))
        )
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error curating video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to curate video: {str(e)}")


@router.get("/topic/{topic_id}", response_model=List[Video])
async def get_videos_by_topic(
    topic_id: str,
    limit: int = 10,
    supabase: Client = Depends(get_supabase)
):
    """
    Get videos associated with a specific topic
    
    Args:
        topic_id: Topic UUID
        limit: Maximum number of videos to return
        supabase: Supabase client
        
    Returns:
        List of videos for the topic
    """
    try:
        # Query videos where topic_id is in the topic_ids array
        result = supabase.table('videos').select('*').contains('topic_ids', [topic_id]).limit(limit).execute()
        
        if not result.data:
            return []
        
        videos = []
        for video in result.data:
            videos.append(Video(
                id=video['id'],
                youtube_id=video['youtube_id'],
                title=video['title'],
                transcript=video.get('transcript'),
                timestamps=video.get('timestamps', []),
                topic_ids=video.get('topic_ids', []),
                subject=Subject(video['subject']) if video.get('subject') else None,
                duration_seconds=video.get('duration_seconds'),
                channel_name=video.get('channel_name'),
                metadata=video.get('metadata', {}),
                created_at=datetime.fromisoformat(video['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(video['updated_at'].replace('Z', '+00:00'))
            ))
        
        return videos
        
    except Exception as e:
        logger.error(f"Error fetching videos for topic {topic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch videos: {str(e)}")


@router.get("/subject/{subject}", response_model=List[Video])
async def get_videos_by_subject(
    subject: Subject,
    limit: int = 20,
    supabase: Client = Depends(get_supabase)
):
    """
    Get videos for a specific subject
    
    Args:
        subject: Subject enum value
        limit: Maximum number of videos to return
        supabase: Supabase client
        
    Returns:
        List of videos for the subject
    """
    try:
        result = supabase.table('videos').select('*').eq('subject', subject.value).limit(limit).execute()
        
        if not result.data:
            return []
        
        videos = []
        for video in result.data:
            videos.append(Video(
                id=video['id'],
                youtube_id=video['youtube_id'],
                title=video['title'],
                transcript=video.get('transcript'),
                timestamps=video.get('timestamps', []),
                topic_ids=video.get('topic_ids', []),
                subject=Subject(video['subject']) if video.get('subject') else None,
                duration_seconds=video.get('duration_seconds'),
                channel_name=video.get('channel_name'),
                metadata=video.get('metadata', {}),
                created_at=datetime.fromisoformat(video['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(video['updated_at'].replace('Z', '+00:00'))
            ))
        
        return videos
        
    except Exception as e:
        logger.error(f"Error fetching videos for subject {subject}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch videos: {str(e)}")


@router.get("/{video_id}", response_model=Video)
async def get_video(
    video_id: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get a specific video by ID
    
    Args:
        video_id: Video UUID
        supabase: Supabase client
        
    Returns:
        Video object
    """
    try:
        result = supabase.table('videos').select('*').eq('id', video_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Video not found")
        
        video = result.data[0]
        
        return Video(
            id=video['id'],
            youtube_id=video['youtube_id'],
            title=video['title'],
            transcript=video.get('transcript'),
            timestamps=video.get('timestamps', []),
            topic_ids=video.get('topic_ids', []),
            subject=Subject(video['subject']) if video.get('subject') else None,
            duration_seconds=video.get('duration_seconds'),
            channel_name=video.get('channel_name'),
            metadata=video.get('metadata', {}),
            created_at=datetime.fromisoformat(video['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(video['updated_at'].replace('Z', '+00:00'))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch video: {str(e)}")


@router.get("/youtube/{youtube_id}", response_model=Video)
async def get_video_by_youtube_id(
    youtube_id: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Get a video by YouTube ID
    
    Args:
        youtube_id: YouTube video ID
        supabase: Supabase client
        
    Returns:
        Video object
    """
    try:
        result = supabase.table('videos').select('*').eq('youtube_id', youtube_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Video not found")
        
        video = result.data[0]
        
        return Video(
            id=video['id'],
            youtube_id=video['youtube_id'],
            title=video['title'],
            transcript=video.get('transcript'),
            timestamps=video.get('timestamps', []),
            topic_ids=video.get('topic_ids', []),
            subject=Subject(video['subject']) if video.get('subject') else None,
            duration_seconds=video.get('duration_seconds'),
            channel_name=video.get('channel_name'),
            metadata=video.get('metadata', {}),
            created_at=datetime.fromisoformat(video['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(video['updated_at'].replace('Z', '+00:00'))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching video by YouTube ID {youtube_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch video: {str(e)}")


@router.get("/search/youtube", response_model=List[dict])
async def search_youtube_videos(
    query: str,
    max_results: int = 10
):
    """
    Search for videos on YouTube
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10, max: 50)
    
    Returns:
        List of video metadata dictionaries
    """
    try:
        if max_results > 50:
            max_results = 50
        
        videos = await youtube_service.search_videos(
            query=query,
            max_results=max_results,
            order='relevance'
        )
        
        return videos
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error searching YouTube videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search videos: {str(e)}")


async def index_video_transcript(
    video_id: str,
    youtube_id: str,
    transcript: str,
    metadata: dict
):
    """
    Background task to index video transcript into RAG pipeline
    
    Args:
        video_id: Video UUID
        youtube_id: YouTube video ID
        transcript: Video transcript text
        metadata: Video metadata
    """
    try:
        logger.info(f"Indexing transcript for video {youtube_id}")
        
        # Chunk the transcript (use smaller chunks for video content)
        from app.services.chunking_service import chunking_service
        chunks = await chunking_service.chunk_text(
            text=transcript,
            chunk_size=300,  # Smaller chunks for video transcripts
            chunk_overlap=50
        )
        
        # Generate embeddings for each chunk
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding
                embedding = await embedding_service.generate_embedding(chunk)
                
                # Create metadata for this chunk
                chunk_metadata = {
                    **metadata,
                    'video_id': video_id,
                    'youtube_id': youtube_id,
                    'chunk_index': i,
                    'chunk_text': chunk[:200]  # Store preview
                }
                
                # Index in vector database
                embedding_id = f"video_{video_id}_chunk_{i}"
                await vector_db_service.upsert_vector(
                    vector_id=embedding_id,
                    embedding=embedding,
                    metadata=chunk_metadata
                )
                
            except Exception as e:
                logger.error(f"Error indexing chunk {i} for video {youtube_id}: {str(e)}")
                continue
        
        logger.info(f"Successfully indexed {len(chunks)} chunks for video {youtube_id}")
        
    except Exception as e:
        logger.error(f"Error in background indexing task for video {youtube_id}: {str(e)}")
