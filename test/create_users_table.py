"""
Create a simple users table to fix foreign key constraints
"""
import logging
from shared.core.database import engine, SessionLocal
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_users_table():
    """Create a simple users table and processing_jobs table"""
    db = SessionLocal()
    
    try:
        # Check if users table exists
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'users'
        """))
        
        if not result.fetchone():
            logger.info("Creating users table...")
            db.execute(text("""
                CREATE TABLE users (
                    id BIGSERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Insert a sample user
            db.execute(text("""
                INSERT INTO users (id) VALUES (1)
            """))
            
            logger.info("✅ Users table created successfully")
        else:
            logger.info("✅ Users table already exists")
        
        # Check if processing_jobs table exists
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'processing_jobs'
        """))
        
        if not result.fetchone():
            logger.info("Creating processing_jobs table...")
            db.execute(text("""
                CREATE TABLE processing_jobs (
                    id BIGSERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Insert a sample job
            db.execute(text("""
                INSERT INTO processing_jobs (id) VALUES (1)
            """))
            
            logger.info("✅ Processing jobs table created successfully")
        else:
            logger.info("✅ Processing jobs table already exists")
        
        db.commit()
            
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create tables: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🚀 Creating users table...")
    create_users_table()
    logger.info("🏁 Users table creation completed!")
