import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import logging

from core.storage import AzureBlobStorage
from core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Document Upload API",
    description="API for uploading documents to Azure Blob Storage",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage
storage = AzureBlobStorage()

# Serve static files (frontend)
static_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RAG Document Upload"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to Azure Blob Storage
    
    Supported formats: PDF, Word, Excel, PowerPoint
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt'}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Upload to blob storage
        blob_name = await storage.upload_document(
            file_name=file.filename,
            content=content,
            content_type=file.content_type
        )
        
        logger.info(f"Successfully uploaded file: {blob_name}")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "File uploaded successfully",
                "file_name": file.filename,
                "blob_name": blob_name,
                "size": len(content)
            }
        )
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def list_documents():
    """List all documents in the storage"""
    try:
        documents = await storage.list_documents()
        return {
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{blob_name}")
async def delete_document(blob_name: str):
    """Delete a document from storage"""
    try:
        await storage.delete_document(blob_name)
        return {"message": f"Document {blob_name} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)