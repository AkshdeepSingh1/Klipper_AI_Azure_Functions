import cv2
import numpy as np
import requests
from azure.storage.blob import BlobServiceClient
from io import BytesIO
from shared.core.config import settings
from shared.core.database import SessionLocal
from shared.models.video import Video
from shared.models.clip import Clip
from shared.models.user import User
from shared.models.processing_job import ProcessingJob
import logging

logger = logging.getLogger(__name__)


class VideoIOService:
    """Service for video processing and thumbnail generation"""
    
    def __init__(self):
        # Check if Azure Storage configuration is available
        if not settings.AZURE_STORAGE_CONNECTION_STRING:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is not configured")
        if not settings.AZURE_STORAGE_ACCOUNT_NAME:
            raise ValueError("AZURE_STORAGE_ACCOUNT_NAME is not configured")
        if not settings.AZURE_STORAGE_CONTAINER_NAME:
            raise ValueError("AZURE_STORAGE_CONTAINER_NAME is not configured")
        
        logger.info(f"Initializing Azure Storage for account: {settings.AZURE_STORAGE_ACCOUNT_NAME}")
        logger.info(f"Using container: {settings.AZURE_STORAGE_CONTAINER_NAME}")
        
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
            self.container_client = self.blob_service_client.get_container_client(
                settings.AZURE_STORAGE_CONTAINER_NAME
            )
            
            # Test connection by checking if container exists
            if not self.container_client.exists():
                logger.warning(f"Container '{settings.AZURE_STORAGE_CONTAINER_NAME}' does not exist. Creating it...")
                self.container_client.create_container()
                logger.info(f"Container '{settings.AZURE_STORAGE_CONTAINER_NAME}' created successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure Storage: {e}")
            raise
    
    def download_video_from_blob(self, blob_url: str) -> bytes:
        """Download video from blob URL to memory"""
        try:
            # Extract blob name from URL or use direct URL
            if blob_url.startswith('http'):
                response = requests.get(blob_url)
                response.raise_for_status()
                return response.content
            else:
                # If it's a blob name, download from Azure Storage
                blob_client = self.container_client.get_blob_client(blob_url)
                return blob_client.download_blob().readall()
        except Exception as e:
            logger.error(f"Failed to download video from {blob_url}: {e}")
            raise
    
    def extract_thumbnail_from_video(self, video_bytes: bytes, timestamp_sec: float = 1.0) -> bytes:
        """Extract a frame from video and convert to JPEG"""
        try:
            # Write video bytes to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(video_bytes)
                temp_file_path = temp_file.name
            
            try:
                # Read video using OpenCV
                cap = cv2.VideoCapture(temp_file_path)
                
                if not cap.isOpened():
                    raise ValueError("Could not open video file")
                
                # Seek to the specified timestamp
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps > 0:
                    frame_number = int(timestamp_sec * fps)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                
                # Read frame
                ret, frame = cap.read()
                
                # If seeking failed, try reading first frame
                if not ret:
                    logger.warning(f"Could not read frame at timestamp {timestamp_sec}s, using first frame instead")
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                
                if not ret:
                    raise ValueError("Could not read frame from video")
                
                # Convert frame to JPEG
                _, jpeg_bytes = cv2.imencode('.jpg', frame)
                thumbnail_bytes = jpeg_bytes.tobytes()
                
                cap.release()
                return thumbnail_bytes
                
            finally:
                # Clean up temporary file
                import os
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            logger.error(f"Failed to extract thumbnail: {e}")
            raise
    
    def upload_thumbnail_to_blob(self, thumbnail_bytes: bytes, entity_id: int, entity_type: str, user_id: int = None, video_id: int = None) -> str:
        """Upload thumbnail to Azure Storage and return URL"""
        try:
            # Validate thumbnail bytes
            if not thumbnail_bytes:
                raise ValueError("Thumbnail bytes are empty")
            
            logger.info(f"Uploading thumbnail for {entity_type} ID {entity_id}, size: {len(thumbnail_bytes)} bytes")
            
            if entity_type == "video":
                # Video structure: raw-videos/thumbnails/{user_id}/{entity_id}_thumbnail.jpg
                if not user_id:
                    raise ValueError("user_id is required for video thumbnails")
                
                container_name = "raw-videos"
                thumbnail_name = f"thumbnails/{user_id}/{entity_id}_thumbnail.jpg"
                container_client = self.blob_service_client.get_container_client(container_name)
                
            elif entity_type == "clip":
                # Clip structure: clips/thumbnails/{user_id}/{video_id}/{entity_id}_thumbnail.jpg
                if not user_id or not video_id:
                    raise ValueError("user_id and video_id are required for clip thumbnails")
                
                container_name = "clips"
                thumbnail_name = f"thumbnails/{user_id}/{video_id}/{entity_id}_thumbnail.jpg"
                container_client = self.blob_service_client.get_container_client(container_name)
                
            else:
                raise ValueError(f"Unknown entity type: {entity_type}")
            
            # Upload to blob storage
            blob_client = container_client.get_blob_client(thumbnail_name)
            logger.info(f"Uploading to blob: {thumbnail_name} in container: {container_name}")
            
            blob_client.upload_blob(thumbnail_bytes, overwrite=True)
            logger.info("Thumbnail uploaded successfully to blob storage")
            
            # Generate URL
            thumbnail_url = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{container_name}/{thumbnail_name}"
            logger.info(f"Generated thumbnail URL: {thumbnail_url}")
            
            return thumbnail_url
            
        except Exception as e:
            logger.error(f"Failed to upload thumbnail: {e}")
            logger.error(f"Azure Storage Account: {settings.AZURE_STORAGE_ACCOUNT_NAME}")
            logger.error(f"Entity Type: {entity_type}, Entity ID: {entity_id}")
            logger.error(f"User ID: {user_id}, Video ID: {video_id}")
            raise
    
    def process_video_thumbnail(self, video_id: int) -> str:
        """Process thumbnail for a video"""
        # First, get video info quickly and close connection
        db = SessionLocal()
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise ValueError(f"Video with id {video_id} not found")
            
            # Store video info and close database connection
            blob_url = video.blob_url
            user_id = video.user_id
            logger.info(f"Found video {video_id} with blob URL: {blob_url}, user_id: {user_id}")
            
        finally:
            db.close()
        
        # Process video and generate thumbnail (no database connection)
        try:
            # Download video
            logger.info(f"Downloading video from {blob_url}")
            video_bytes = self.download_video_from_blob(blob_url)
            
            # Extract thumbnail (use 1 second timestamp)
            logger.info("Extracting thumbnail from video")
            thumbnail_bytes = self.extract_thumbnail_from_video(video_bytes, 1.0)
            
            # Upload thumbnail with user_id
            logger.info("Uploading thumbnail to Azure Storage")
            thumbnail_url = self.upload_thumbnail_to_blob(thumbnail_bytes, video_id, "video", user_id=user_id)
            
            # Quick database update with just the thumbnail URL
            db = SessionLocal()
            try:
                video = db.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.thumbnail_url = thumbnail_url
                    db.commit()
                    logger.info(f"Updated video {video_id} with thumbnail URL")
                else:
                    logger.warning(f"Video {video_id} not found during update")
                    
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to update video thumbnail URL: {e}")
                raise
            finally:
                db.close()
            
            logger.info(f"Successfully generated thumbnail for video {video_id}")
            return thumbnail_url
            
        except Exception as e:
            logger.error(f"Failed to process video thumbnail for {video_id}: {e}")
            raise
    
    def process_clip_thumbnail(self, clip_id: int) -> str:
        """Process thumbnail for a clip"""
        # First, get clip info quickly and close connection
        db = SessionLocal()
        try:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            if not clip:
                raise ValueError(f"Clip with id {clip_id} not found")
            
            # Store clip info and close database connection
            clip_url = clip.clip_url
            timestamp = clip.start_time_sec if clip.start_time_sec and clip.start_time_sec > 0 else 1.0
            video_id = clip.video_id
            
            # Get user_id from the video
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise ValueError(f"Video with id {video_id} not found for clip {clip_id}")
            user_id = video.user_id
            
            logger.info(f"Found clip {clip_id} with URL: {clip_url}, timestamp: {timestamp}, video_id: {video_id}, user_id: {user_id}")
            
        finally:
            db.close()
        
        # Process clip and generate thumbnail (no database connection)
        try:
            # Download clip video
            logger.info(f"Downloading clip from {clip_url}")
            video_bytes = self.download_video_from_blob(clip_url)
            
            # Extract thumbnail
            logger.info("Extracting thumbnail from clip")
            thumbnail_bytes = self.extract_thumbnail_from_video(video_bytes, timestamp)
            
            # Upload thumbnail with user_id and video_id
            logger.info("Uploading thumbnail to Azure Storage")
            thumbnail_url = self.upload_thumbnail_to_blob(thumbnail_bytes, clip_id, "clip", user_id=user_id, video_id=video_id)
            
            # Quick database update with just the thumbnail URL
            db = SessionLocal()
            try:
                clip = db.query(Clip).filter(Clip.id == clip_id).first()
                if clip:
                    clip.thumbnail_url = thumbnail_url
                    db.commit()
                    logger.info(f"Updated clip {clip_id} with thumbnail URL")
                else:
                    logger.warning(f"Clip {clip_id} not found during update")
                    
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to update clip thumbnail URL: {e}")
                raise
            finally:
                db.close()
            
            logger.info(f"Successfully generated thumbnail for clip {clip_id}")
            return thumbnail_url
            
        except Exception as e:
            logger.error(f"Failed to process clip thumbnail for {clip_id}: {e}")
            raise


# Create service instance
video_service = VideoIOService()