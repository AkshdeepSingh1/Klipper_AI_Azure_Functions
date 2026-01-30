"""
Create sample video and clip data for testing
"""
import logging
from shared.core.database import SessionLocal
from shared.models.video import Video
from shared.models.clip import Clip
from shared.models.processing_job import ProcessingJob
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_data():
    """Create sample video and clip data"""
    db = SessionLocal()
    
    try:
        # Check if video with ID 26 exists
        video = db.query(Video).filter(Video.id == 26).first()
        if not video:
            logger.info("Creating sample video with ID 26...")
            # Create a sample video record
            video = Video(
                id=26,
                user_id=1,
                blob_url="https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",  # Sample video URL
                duration_seconds=30
            )
            db.add(video)
            logger.info("✅ Sample video created")
        else:
            logger.info("✅ Video with ID 26 already exists")
        
        # Check if clip with ID 1 exists
        clip = db.query(Clip).filter(Clip.id == 1).first()
        if not clip:
            logger.info("Creating sample clip with ID 1...")
            # Create a sample clip record
            clip = Clip(
                id=1,
                job_id=1,
                video_id=26,
                clip_url="https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",  # Sample video URL
                start_time_sec=5.0,
                end_time_sec=15.0,
                duration_sec=10.0
            )
            db.add(clip)
            logger.info("✅ Sample clip created")
        else:
            logger.info("✅ Clip with ID 1 already exists")
        
        db.commit()
        logger.info("🎉 Sample data creation completed!")
        
        # Print current data
        logger.info("Current videos:")
        videos = db.query(Video).all()
        for v in videos:
            logger.info(f"  Video ID: {v.id}, User ID: {v.user_id}, Blob URL: {v.blob_url}")
        
        logger.info("Current clips:")
        clips = db.query(Clip).all()
        for c in clips:
            logger.info(f"  Clip ID: {c.id}, Video ID: {c.video_id}, Clip URL: {c.clip_url}")
            
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create sample data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🚀 Creating sample data...")
    create_sample_data()
    logger.info("🏁 Sample data creation completed!")
