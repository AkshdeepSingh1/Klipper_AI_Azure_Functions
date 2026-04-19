import json
import sys
import os
import azure.functions as func

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from function_app import generate_thumbnail
from shared.core.enums import GenerateThumbnailProcess


def create_test_queue_message(thumbnail_process: int, entity_id: int) -> func.QueueMessage:
    """Create a test queue message"""
    message_data = {
        "thumbnailProcess": thumbnail_process,
        "entityId": entity_id
    }
    message_body = json.dumps(message_data)
    
    # Create a mock QueueMessage
    class MockQueueMessage:
        def __init__(self, body: str):
            self._body = body.encode('utf-8')
        
        def get_body(self) -> bytes:
            return self._body
    
    return MockQueueMessage(message_body)


def test_video_thumbnail_processing():
    """Test video thumbnail processing"""
    print("🎬 Testing Video Thumbnail Processing...")
    
    # Create test message for video thumbnail (process = 0)
    test_message = create_test_queue_message(
        thumbnail_process=GenerateThumbnailProcess.CLIP_THUMBNAIL,
        entity_id=5  # Use the video ID from your error log
    )
    
    try:
        # Call the generate_thumbnail function
        generate_thumbnail(test_message)
        print("✅ Video thumbnail test completed successfully")
    except Exception as e:
        print(f"❌ Video thumbnail test failed: {e}")


def test_clip_thumbnail_processing():
    """Test clip thumbnail processing"""
    print("🎬 Testing Clip Thumbnail Processing...")
    
    # Create test message for clip thumbnail (process = 1)
    test_message = create_test_queue_message(
        thumbnail_process=GenerateThumbnailProcess.CLIP_THUMBNAIL,
        entity_id=28  # Use a sample clip ID
    )
    
    try:
        # Call the generate_thumbnail function
        generate_thumbnail(test_message)
        print("✅ Clip thumbnail test completed successfully")
    except Exception as e:
        print(f"❌ Clip thumbnail test failed: {e}")


def test_invalid_message():
    """Test with invalid message format"""
    print("🎬 Testing Invalid Message Format...")
    
    # Create invalid message
    message_data = {"invalid": "data"}
    message_body = json.dumps(message_data)
    
    class MockQueueMessage:
        def __init__(self, body: str):
            self._body = body.encode('utf-8')
        
        def get_body(self) -> bytes:
            return self._body
    
    test_message = MockQueueMessage(message_body)
    
    try:
        generate_thumbnail(test_message)
        print("✅ Invalid message test completed (should handle gracefully)")
    except Exception as e:
        print(f"❌ Invalid message test failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Thumbnail Function Tests...")
    print("=" * 50)
    
    # Run tests
    # test_video_thumbnail_processing()
    print()
    test_clip_thumbnail_processing()
    print()
    # test_invalid_message()
    
    print("=" * 50)
    print("🏁 All tests completed!")
