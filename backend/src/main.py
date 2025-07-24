import os
import sys
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import List, Optional
import logging
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding

from core.storage import AzureBlobStorage
from core.config import settings

# Configurar logging para Azure App Service
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando aplicación RAG Document Upload")
    logger.info(f"📁 Directorio actual: {os.getcwd()}")
    logger.info(f"📁 Contenido directorio: {os.listdir('.')}")
    logger.info(f"⚙️ Python path: {sys.path}")
    
    # Inicializar Semantic Kernel para futuro procesamiento RAG
    try:
        app.state.kernel = sk.Kernel()
        logger.info("✅ Semantic Kernel inicializado")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo inicializar Semantic Kernel: {e}")
        app.state.kernel = None
    
    # Inicializar Azure Blob Storage
    try:
        app.state.storage = AzureBlobStorage()
        logger.info("✅ Azure Blob Storage conectado")
    except Exception as e:
        logger.error(f"❌ Error conectando Azure Blob Storage: {e}")
        app.state.storage = None
    
    yield
    
    logger.info("🛑 Cerrando aplicación")

# Crear aplicación FastAPI
app = FastAPI(
    title="RAG Document Upload API",
    description="Sistema de carga de documentos para RAG con Semantic Kernel",
    version="2.0.0",
    lifespan=lifespan
)

# Middleware CORS mejorado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests"""
    logger.info(f"📝 {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"📤 Response: {response.status_code}")
    return response

# Montar archivos estáticos con manejo robusto
static_paths = [
    Path("static"),
    Path("src/static"),
    Path("frontend/dist"),
    Path("../frontend/dist")
]

static_dir = None
for path in static_paths:
    if path.exists() and path.is_dir():
        static_dir = path
        logger.info(f"📁 Encontrado directorio estático: {static_dir}")
        break

if static_dir:
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"✅ Archivos estáticos montados desde {static_dir}")
else:
    logger.warning("⚠️ No se encontró directorio de archivos estáticos")

@app.get("/")
async def root():
    """Endpoint raíz - sirve index.html o información de API"""
    try:
        # Intentar servir index.html
        if static_dir and (static_dir / "index.html").exists():
            return FileResponse(static_dir / "index.html")
        else:
            return {
                "message": "RAG Document Upload API",
                "version": "2.0.0",
                "status": "running",
                "endpoints": {
                    "health": "/api/health",
                    "upload": "/api/upload",
                    "documents": "/api/documents",
                    "docs": "/docs"
                }
            }
    except Exception as e:
        logger.error(f"❌ Error en endpoint raíz: {e}")
        return {"error": str(e), "message": "API en funcionamiento, interfaz no disponible"}

@app.get("/api/health")
async def health_check():
    """Health check mejorado con información del sistema"""
    try:
        storage_status = "ok" if app.state.storage else "error"
        kernel_status = "ok" if app.state.kernel else "not_initialized"
        
        return {
            "status": "healthy",
            "service": "RAG Document Upload API v2.0",
            "storage": storage_status,
            "semantic_kernel": kernel_status,
            "environment": {
                "python_version": sys.version,
                "cwd": os.getcwd(),
                "static_dir": str(static_dir) if static_dir else None
            }
        }
    except Exception as e:
        logger.error(f"❌ Error en health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload de archivos con preparación para procesamiento RAG
    """
    try:
        if not app.state.storage:
            raise HTTPException(
                status_code=503, 
                detail="Servicio de almacenamiento no disponible"
            )
        
        # Validar tipo de archivo
        allowed_extensions = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt'}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de archivo no soportado. Permitidos: {', '.join(allowed_extensions)}"
            )
        
        # Validar tamaño (máximo 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="Archivo demasiado grande. Máximo 10MB"
            )
        
        # Subir a Azure Blob Storage
        blob_name = await app.state.storage.upload_document(
            file_name=file.filename,
            content=content,
            content_type=file.content_type
        )
        
        logger.info(f"✅ Archivo subido exitosamente: {blob_name}")
        
        # Respuesta con información para procesamiento futuro
        return JSONResponse(
            status_code=200,
            content={
                "message": "Archivo cargado exitosamente",
                "file_name": file.filename,
                "blob_name": blob_name,
                "size": len(content),
                "type": file_extension,
                "ready_for_processing": True,
                "next_steps": "Documento listo para indexación en vector store"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error subiendo archivo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/api/documents")
async def list_documents():
    """Listar documentos con información para RAG"""
    try:
        if not app.state.storage:
            raise HTTPException(
                status_code=503, 
                detail="Servicio de almacenamiento no disponible"
            )
        
        documents = await app.state.storage.list_documents()
        
        # Enriquecer información para procesamiento RAG
        for doc in documents:
            doc["processing_status"] = "ready_for_indexing"
            doc["supported_for_rag"] = doc.get("metadata", {}).get("file_type", "").lower() in ["pdf", "docx", "txt"]
        
        return {
            "documents": documents,
            "count": len(documents),
            "rag_ready": sum(1 for doc in documents if doc.get("supported_for_rag", False))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listando documentos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{blob_name}")
async def delete_document(blob_name: str):
    """Eliminar documento del almacenamiento"""
    try:
        if not app.state.storage:
            raise HTTPException(
                status_code=503, 
                detail="Servicio de almacenamiento no disponible"
            )
        
        await app.state.storage.delete_document(blob_name)
        logger.info(f"🗑️ Documento eliminado: {blob_name}")
        
        return {"message": f"Documento {blob_name} eliminado exitosamente"}
    except Exception as e:
        logger.error(f"❌ Error eliminando documento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/process/{blob_name}")
async def process_document_for_rag(blob_name: str):
    """Endpoint futuro para procesar documentos con Semantic Kernel"""
    try:
        if not app.state.kernel:
            return {
                "message": "Semantic Kernel no disponible",
                "blob_name": blob_name,
                "status": "pending_implementation"
            }
        
        # Aquí irá la lógica de procesamiento con Semantic Kernel
        # - Extraer texto del documento
        # - Crear embeddings
        # - Almacenar en vector store (Chroma/Azure Cognitive Search)
        
        return {
            "message": "Procesamiento preparado para implementación",
            "blob_name": blob_name,
            "status": "ready_for_semantic_kernel_processing",
            "next_implementation": [
                "Extraer texto con librerías apropiadas",
                "Crear embeddings con Azure OpenAI",
                "Almacenar en vector store",
                "Configurar para búsqueda semántica"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error procesando documento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Manejo de rutas catch-all para SPA
@app.get("/{full_path:path}")
async def catch_all(full_path: str, request: Request):
    """Manejo de rutas SPA"""
    try:
        # Si es una ruta de API, devolver 404
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint no encontrado")
        
        # Para otras rutas, intentar servir index.html (SPA)
        if static_dir and (static_dir / "index.html").exists():
            return FileResponse(static_dir / "index.html")
        
        # Si no hay frontend, mostrar información de API
        return {
            "message": "RAG Document Upload API - Frontend no disponible",
            "api_docs": f"{request.base_url}docs",
            "available_endpoints": [
                "/api/health",
                "/api/upload",
                "/api/documents"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en catch-all: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Iniciando servidor en {host}:{port}")
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=False,
        log_level="info"
    )