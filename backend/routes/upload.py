"""
File upload endpoint with validation and session management
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
import shutil
from pathlib import Path

from backend.config import settings
from backend.models.schemas import UploadResponse, FileMetadata
from backend.services.chunker import chunker

router = APIRouter()

# In-memory session storage (use Redis in production)
active_sessions = {}

@router.post("/", response_model=UploadResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload code files for documentation generation
    
    Returns session_id to track the uploaded files
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Create unique session
    session_id = str(uuid.uuid4())
    session_dir = settings.UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📤 Upload started - Session: {session_id}")
    
    uploaded_files = []
    total_size = 0
    total_tokens = 0
    
    for file in files:
        # Validate extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            print(f"⚠️  Skipping {file.filename} (unsupported extension)")
            continue
        
        # Save file
        file_path = session_dir / file.filename
        
        try:
            # Read and save file
            content = await file.read()
            file_size = len(content)
            
            # Validate size
            if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"File {file.filename} exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
                )
            
            # Save to disk
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Extract metadata
            metadata = chunker.extract_metadata(file_path)
            
            uploaded_files.append(FileMetadata(
                filename=file.filename,
                size=file_size,
                path=str(file_path),
                tokens=metadata.get('tokens', 0),
                functions=metadata.get('functions', []),
                classes=metadata.get('classes', [])
            ))
            
            total_size += file_size
            total_tokens += metadata.get('tokens', 0)
            
            print(f"  ✅ {file.filename} ({file_size} bytes, {metadata.get('tokens', 0)} tokens)")
        
        except Exception as e:
            print(f"  ❌ Error processing {file.filename}: {str(e)}")
            # Clean up on error
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}")
    
    if not uploaded_files:
        # Clean up empty session
        shutil.rmtree(session_dir)
        raise HTTPException(status_code=400, detail="No valid files uploaded")
    
    # Store session info
    active_sessions[session_id] = {
        "session_dir": str(session_dir),
        "files": [f.dict() for f in uploaded_files],
        "total_tokens": total_tokens,
        "status": "uploaded"
    }
    
    print(f"✅ Upload complete - {len(uploaded_files)} files, {total_tokens} tokens")
    
    return UploadResponse(
        session_id=session_id,
        files_uploaded=len(uploaded_files),
        total_size=total_size,
        total_tokens=total_tokens,
        files=uploaded_files
    )


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about an upload session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Clean up a session and its files"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_info = active_sessions[session_id]
    session_dir = Path(session_info["session_dir"])
    
    # Delete files
    if session_dir.exists():
        shutil.rmtree(session_dir)
    
    # Remove from active sessions
    del active_sessions[session_id]
    
    print(f"🗑️  Session {session_id} cleaned up")
    
    return {"message": "Session deleted successfully"}
