# Kliper AI - Video Thumbnail Generation Service

## Overview

This Azure Functions project provides automated thumbnail generation for videos and clips in the Kliper AI platform. It processes video files stored in Azure Blob Storage, extracts frames at specific timestamps, and uploads the generated thumbnails back to Azure Storage.

## Architecture

### Components

1. **Azure Functions (`function_app.py`)**
   - `generate_thumbnail`: Queue-triggered function that processes thumbnail generation requests
   - `initialize_function`: HTTP endpoint for health checks and database initialization

2. **Video IO Service (`modules/video_input_output/video_io_service.py`)**
   - `VideoIOService`: Core service class for video processing
   - Handles video download, thumbnail extraction, and upload operations
   - Manages Azure Storage connections and blob operations

3. **Database Models**
   - `Video`: Stores video metadata and thumbnail URLs
   - `Clip`: Stores clip metadata including timestamps and parent video references
   - `User`: User information for organizing storage paths

### Data Flow

```
Azure Queue → generate_thumbnail() → VideoIOService
                                              ↓
                                    Download video from Azure Storage
                                              ↓
                                    Extract frame using OpenCV
                                              ↓
                                    Upload thumbnail to Azure Storage
                                              ↓
                                    Update database with thumbnail URL
```

### Storage Structure

- **Videos**: `raw-videos/thumbnails/{user_id}/{video_id}_thumbnail.jpg`
- **Clips**: `clips/thumbnails/{user_id}/{video_id}/{clip_id}_thumbnail.jpg`

## Prerequisites

- Python 3.8+
- Azure Functions Core Tools (for local development)
- Azure Storage Account with containers:
  - `raw-videos`
  - `clips`
- PostgreSQL database
- Environment variables configured (see Configuration section)

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

The following environment variables must be set (typically in `.env` file):

- `AZURE_STORAGE_CONNECTION_STRING`: Azure Storage connection string
- `AZURE_STORAGE_ACCOUNT_NAME`: Azure Storage account name
- `AZURE_STORAGE_CONTAINER_NAME`: Default container name
- `DATABASE_URL`: PostgreSQL connection string

## Testing

### Running Tests Locally

The project includes unit tests in `test/test_thumbnail_function.py` that test the thumbnail generation logic directly without requiring the Azure Functions runtime.

#### Test File Structure

The test file (`test/test_thumbnail_function.py`) contains:
- `test_video_thumbnail_processing()`: Tests video thumbnail generation
- `test_clip_thumbnail_processing()`: Tests clip thumbnail generation
- `test_invalid_message()`: Tests error handling for invalid messages

#### How the Tests Work

The test flow is:

1. **`test_thumbnail_function.py`** imports the function directly:
   ```python
   from function_app import generate_thumbnail
   ```

2. Creates mock queue messages with test data:
   ```python
   test_message = create_test_queue_message(
       thumbnail_process=GenerateThumbnailProcess.CLIP_THUMBNAIL,
       entity_id=28
   )
   ```

3. Calls the function directly:
   ```python
   generate_thumbnail(test_message)
   ```

4. The function executes the actual thumbnail generation logic using real database and Azure Storage connections

#### Running Individual Tests

```bash
# Run the test file directly
python test/test_thumbnail_function.py
```

#### Running the Full Test Suite

```bash
# Run all tests using the test runner
python test/run_tests.py
```

The test runner (`test/run_tests.py`) executes test files as separate processes with the correct PYTHONPATH configured.

### Modifying Test Data

To test with different video/clip IDs, edit the `entity_id` parameter in `test/test_thumbnail_function.py`:

```python
test_message = create_test_queue_message(
    thumbnail_process=GenerateThumbnailProcess.CLIP_THUMBNAIL,
    entity_id=YOUR_ID_HERE  # Change this to your test ID
)
```

### Common Test Issues

- **"Could not read frame from video"**: The video file at the specified ID may not exist, be corrupted, or be in an unsupported format
- **Database connection errors**: Verify DATABASE_URL is correctly configured
- **Azure Storage errors**: Verify storage connection string and that the video/clip exists in the storage account

## Running Azure Functions Locally

To run the full Azure Functions runtime locally:

```bash
func start
```

This requires:
- Azure Functions Core Tools installed
- Valid `local.settings.json` configuration
- All environment variables set

## Deployment

To deploy the latest changes to Azure Functions:

1. **Login to Azure:**
   ```bash
   az login
   ```

2. **Select the Azure subscription:**
   ```bash
   az account set --subscription <your-subscription-id>
   ```

3. **List available function apps:**
   ```bash
   az functionapp list --output table
   ```

4. **Deploy to Azure:**
   ```bash
   func azure functionapp publish CreateThumbnail
   ```

This will build and deploy your functions to Azure, typically taking 1-2 minutes.

## API Endpoints

### Health Check
- **Endpoint**: `GET /health`
- **Auth Level**: Anonymous
- **Purpose**: Tests database connectivity and initializes the service

### Queue Trigger
- **Queue**: `generatethumbnailqueue`
- **Message Format**:
  ```json
  {
    "thumbnailProcess": 0,  // 0 = VIDEO_THUMBNAIL, 1 = CLIP_THUMBNAIL
    "entityId": 123
  }
  ```

## Project Structure

```
Functions/
├── function_app.py              # Azure Functions entry point
├── modules/
│   └── video_input_output/
│       └── video_io_service.py  # Video processing logic
├── shared/
│   ├── core/
│   │   ├── config.py           # Configuration settings
│   │   ├── database.py         # Database connection
│   │   └── enums.py            # Enumerations
│   └── models/
│       ├── video.py            # Video model
│       ├── clip.py             # Clip model
│       └── user.py             # User model
├── test/
│   ├── run_tests.py            # Test runner
│   └── test_thumbnail_function.py  # Unit tests
├── requirements.txt            # Python dependencies
├── host.json                   # Azure Functions configuration
└── local.settings.json         # Local settings (gitignored)
```

## Dependencies

- `azure-functions`: Azure Functions runtime
- `sqlalchemy`: Database ORM
- `psycopg2-binary`: PostgreSQL adapter
- `opencv-python`: Video processing
- `azure-storage-blob`: Azure Storage client
- `python-dotenv`: Environment variable management
- `pydantic`: Data validation
- `requests`: HTTP client

## Troubleshooting

### Video Processing Issues
- Ensure video files are in supported formats (MP4, AVI, MOV)
- Check that video files are not corrupted
- Verify OpenCV can read the video format

### Database Issues
- Verify database connection string format
- Ensure database schema is up to date
- Check database user permissions

### Azure Storage Issues
- Verify storage account name and connection string
- Ensure containers exist or can be created
- Check that blob URLs are accessible

## Development Notes

- The service uses temporary files for video processing and cleans them up automatically
- Database connections are opened and closed quickly to avoid connection pool exhaustion
- Thumbnail extraction uses a default timestamp of 1.0 seconds unless specified
- The service handles both video and clip thumbnails with different storage paths
