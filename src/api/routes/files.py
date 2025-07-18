from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from ..models.schemas import FileUploadResponse, FileInfo
from typing import List
from datetime import datetime
import uuid
import os

router = APIRouter()

# Temporary storage for uploaded files (in production, use proper storage)
uploaded_files_store = {}

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a document file"""
    # Validate file type
    allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.md']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_extension} not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (10MB limit)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit"
        )
    
    # Generate file ID and store
    file_id = str(uuid.uuid4())
    file_info = {
        "file_id": file_id,
        "filename": file.filename,
        "content": file_content,
        "size": len(file_content),
        "content_type": file.content_type,
        "uploaded_at": datetime.now().isoformat(),
        "processed": False
    }
    
    uploaded_files_store[file_id] = file_info
    
    return FileUploadResponse(
        file_id=file_id,
        filename=file.filename,
        size=len(file_content),
        content_type=file.content_type,
        uploaded_at=datetime.now().isoformat()
    )

@router.get("/", response_model=List[FileInfo])
async def get_uploaded_files():
    """Get list of uploaded files"""
    return [
        FileInfo(
            file_id=info["file_id"],
            filename=info["filename"],
            size=info["size"],
            content_type=info["content_type"],
            uploaded_at=info["uploaded_at"],
            processed=info["processed"]
        )
        for info in uploaded_files_store.values()
    ]

@router.get("/{file_id}", response_model=FileInfo)
async def get_file_info(file_id: str):
    """Get information about a specific file"""
    if file_id not in uploaded_files_store:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    info = uploaded_files_store[file_id]
    return FileInfo(
        file_id=info["file_id"],
        filename=info["filename"],
        size=info["size"],
        content_type=info["content_type"],
        uploaded_at=info["uploaded_at"],
        processed=info["processed"]
    )

@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete an uploaded file"""
    if file_id not in uploaded_files_store:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    del uploaded_files_store[file_id]
    return {"message": "File deleted successfully"}

@router.get("/{file_id}/preview")
async def preview_file(file_id: str):
    """Get a preview of the file content"""
    if file_id not in uploaded_files_store:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    info = uploaded_files_store[file_id]
    
    # If file is already processed, return the content
    if info.get("processed") and info.get("text_content"):
        from ..services.file_processor import FileProcessor
        processor = FileProcessor()
        preview = processor.get_file_preview(info["text_content"])
        summary = processor.get_content_summary(info["text_content"])
        
        return {
            "file_id": file_id,
            "filename": info["filename"],
            "preview": preview,
            "content_type": info["content_type"],
            "processed": True,
            "summary": summary
        }
    
    # If not processed, try to process it now
    from ..services.file_processor import FileProcessor
    processor = FileProcessor()
    
    try:
        processed_content = await processor.process_file(file_id)
        if processed_content:
            preview = processor.get_file_preview(processed_content["content"])
            summary = processor.get_content_summary(processed_content["content"])
            
            return {
                "file_id": file_id,
                "filename": info["filename"],
                "preview": preview,
                "content_type": info["content_type"],
                "processed": True,
                "summary": summary
            }
    except Exception as e:
        pass
    
    # If processing failed, return basic info
    return {
        "file_id": file_id,
        "filename": info["filename"],
        "preview": "File content could not be extracted",
        "content_type": info["content_type"],
        "processed": False
    }

@router.post("/{file_id}/process")
async def process_file(file_id: str):
    """Process a file to extract its content"""
    if file_id not in uploaded_files_store:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    from ..services.file_processor import FileProcessor
    processor = FileProcessor()
    
    try:
        processed_content = await processor.process_file(file_id)
        if processed_content:
            return {
                "file_id": file_id,
                "processed": True,
                "content_length": len(processed_content["content"]),
                "metadata": processed_content["metadata"]
            }
        else:
            return {
                "file_id": file_id,
                "processed": False,
                "error": "Failed to extract content from file"
            }
    except Exception as e:
        return {
            "file_id": file_id,
            "processed": False,
            "error": str(e)
        }