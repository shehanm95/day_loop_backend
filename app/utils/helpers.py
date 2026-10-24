import os
import uuid
from fastapi import UploadFile, HTTPException, status

UPLOAD_DIR = "static/uploads"

def save_upload_file(upload_file: UploadFile, subfolder: str) -> str:
    """
    Saves an uploaded file to the specified subfolder under static/uploads/
    and returns the relative URL path string.
    """
    if not upload_file or not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded or filename is empty."
        )
    
    # Optional: Validate file extension (e.g., images only)
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
    file_ext = os.path.splitext(upload_file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{file_ext}'. Allowed: {list(allowed_extensions)}"
        )

    # Generate unique filename to prevent collisions
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Construct destination directory
    destination_folder = os.path.join(UPLOAD_DIR, subfolder)
    os.makedirs(destination_folder, exist_ok=True)
    
    file_path = os.path.join(destination_folder, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            content = upload_file.file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save uploaded file: {str(e)}"
        )
        
    # Return relative URL path to store in DB (e.g., /static/uploads/categories/icons/filename.png)
    return f"/{destination_folder}/{unique_filename}".replace("\\", "/")