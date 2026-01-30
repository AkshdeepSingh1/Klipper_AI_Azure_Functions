import azure.functions as func
import datetime
import json
import logging
from shared.core.database import init_db, cleanup_db
from shared.core.enums import GenerateThumbnailProcess
from modules.video_input_output.video_io_service import video_service

app = func.FunctionApp()


@app.function_name("initialize")
@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def initialize_function(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint that also initializes database"""
    try:
        init_db()
        logging.info("🚀 Kliper AI Functions started successfully with database connection")
        return func.HttpResponse("✅ Database connected successfully", status_code=200)
    except Exception as e:
        logging.error(f"❌ Failed to initialize database: {e}")
        return func.HttpResponse(f"❌ Database connection failed: {e}", status_code=500)


@app.queue_trigger(arg_name="azqueue", queue_name="generatethumbnailqueue",
                               connection="AzureWebJobsStorage") 
def generate_thumbnail(azqueue: func.QueueMessage):
    """Generate thumbnails based on queue message"""
    try:
        # Initialize database connection
        init_db()
        
        # Parse queue message
        message_body = azqueue.get_body().decode('utf-8')
        message_data = json.loads(message_body)
        
        thumbnail_process = message_data.get('thumbnailProcess')
        entity_id = message_data.get('entityId')
        
        if thumbnail_process is None or entity_id is None:
            logging.error("❌ Invalid queue message format. Missing thumbnailProcess or entityId")
            return
        
        # Convert enum value
        process_type = GenerateThumbnailProcess(thumbnail_process)
        
        logging.info(f"🎬 Processing thumbnail for {process_type.name} with ID: {entity_id}")
        
        # Route to appropriate processing function
        if process_type == GenerateThumbnailProcess.VIDEO_THUMBNAIL:
            thumbnail_url = video_service.process_video_thumbnail(entity_id)
            logging.info(f"✅ Video thumbnail generated: {thumbnail_url}")
            
        elif process_type == GenerateThumbnailProcess.CLIP_THUMBNAIL:
            thumbnail_url = video_service.process_clip_thumbnail(entity_id)
            logging.info(f"✅ Clip thumbnail generated: {thumbnail_url}")
            
        else:
            logging.error(f"❌ Unknown thumbnail process: {thumbnail_process}")
            
    except Exception as e:
        logging.error(f"❌ Failed to process queue message: {e}")
        raise
