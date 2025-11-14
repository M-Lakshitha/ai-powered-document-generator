"""
File download endpoint
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from backend.config import settings

router = APIRouter()


@router.get("/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    """Download generated documentation file"""
    
    file_path = settings.OUTPUT_DIR / session_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="text/markdown"
    )


@router.get("/zip/{session_id}")
async def download_all_as_zip(session_id: str):
    """Download all generated files as ZIP"""
    import zipfile
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    output_dir = settings.OUTPUT_DIR / session_id
    
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Session output not found")
    
    # Create ZIP in memory
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in output_dir.glob('*.md'):
            zip_file.write(file_path, arcname=file_path.name)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=documentation_{session_id}.zip"}
    )
