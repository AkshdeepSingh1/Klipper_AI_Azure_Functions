"""
Database migration script to add thumbnail_url columns to existing tables
Run this script to update your database schema
"""
import logging
from shared.core.database import engine, SessionLocal
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_thumbnail_columns():
    """Add thumbnail_url columns to videos and clips tables"""
    db = SessionLocal()
    
    try:
        # Check if thumbnail_url column exists in videos table
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'videos' AND column_name = 'thumbnail_url'
        """))
        
        if not result.fetchone():
            logger.info("Adding thumbnail_url column to videos table...")
            db.execute(text("""
                ALTER TABLE videos 
                ADD COLUMN thumbnail_url TEXT
            """))
            db.commit()
            logger.info("✅ Added thumbnail_url column to videos table")
        else:
            logger.info("✅ thumbnail_url column already exists in videos table")
        
        # Check if thumbnail_url column exists in clips table
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clips' AND column_name = 'thumbnail_url'
        """))
        
        if not result.fetchone():
            logger.info("Adding thumbnail_url column to clips table...")
            db.execute(text("""
                ALTER TABLE clips 
                ADD COLUMN thumbnail_url TEXT
            """))
            db.commit()
            logger.info("✅ Added thumbnail_url column to clips table")
        else:
            logger.info("✅ thumbnail_url column already exists in clips table")
            
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to add thumbnail columns: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🚀 Starting database migration...")
    add_thumbnail_columns()
    logger.info("🏁 Database migration completed!")
