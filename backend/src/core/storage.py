from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.identity import DefaultAzureCredential
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import uuid
import hashlib
from pathlib import Path
import json

from .config import settings

logger = logging.getLogger(__name__)

class AzureBlobStorage:
    """
    Cliente mejorado de Azure Blob Storage para sistema RAG
    Incluye funcionalidades específicas para procesamiento de documentos
    """
    
    def __init__(self):
        """Inicializar cliente con manejo robusto de errores"""
        self.blob_service_client = None
        self.container_name = settings.azure_storage_container_name
        
        try:
            self._initialize_client()
            self._ensure_container_exists()
            logger.info(f"✅ Azure Blob Storage inicializado - Container: {self.container_name}")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Azure Blob Storage: {str(e)}")
            logger.error(f"   - Connection String presente: {bool(settings.azure_storage_connection_string)}")
            logger.error(f"   - Account Name: {settings.azure_storage_account_name}")
            logger.error(f"   - Container: {self.container_name}")
            raise
    
    def _initialize_client(self):
        """Inicializar cliente con múltiples métodos de autenticación"""
        if settings.azure_storage_connection_string:
            # Método preferido: Connection String
            self.blob_service_client = BlobServiceClient.from_connection_string(
                settings.azure_storage_connection_string
            )
            logger.info("🔐 Autenticación: Connection String")
            
        elif settings.azure_storage_account_name:
            # Método alternativo: Managed Identity
            account_url = f"https://{settings.azure_storage_account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=DefaultAzureCredential()
            )
            logger.info("🔐 Autenticación: Managed Identity")
            
        else:
            raise ValueError(
                "Se requiere AZURE_STORAGE_CONNECTION_STRING o AZURE_STORAGE_ACCOUNT_NAME"
            )
    
    def _ensure_container_exists(self):
        """Asegurar que el container existe"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            if not container_client.exists():
                container_client.create_container(
                    metadata={
                        "purpose": "rag-documents",
                        "created": datetime.utcnow().isoformat(),
                        "version": "2.0"
                    }
                )
                logger.info(f"📁 Container creado: {self.container_name}")
            else:
                logger.info(f"📁 Container existente: {self.container_name}")
                
        except Exception as e:
            logger.error(f"❌ Error con container {self.container_name}: {str(e)}")
            raise
    
    async def upload_document(
        self, 
        file_name: str, 
        content: bytes, 
        content_type: str = None,
        metadata: Dict[str, str] = None
    ) -> str:
        """
        Subir documento con metadata enriquecida para RAG
        """
        try:
            # Generar nombre único de blob
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(file_name).suffix.lower()
            content_hash = hashlib.md5(content).hexdigest()[:8]
            blob_name = f"{timestamp}_{content_hash}_{uuid.uuid4().hex[:8]}{file_extension}"
            
            # Crear metadata enriquecida
            enhanced_metadata = {
                "original_name": file_name,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "file_type": file_extension[1:] if file_extension else "unknown",
                "size": str(len(content)),
                "content_hash": content_hash,
                "rag_status": "uploaded",
                "processing_status": "pending",
                "version": "2.0"
            }
            
            # Añadir metadata adicional si se proporciona
            if metadata:
                enhanced_metadata.update(metadata)
            
            # Subir blob
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(
                data=content,
                overwrite=True,
                content_settings={
                    "content_type": content_type or "application/octet-stream",
                    "content_encoding": "utf-8" if file_extension in ['.txt', '.md'] else None
                },
                metadata=enhanced_metadata,
                tags={
                    "file_type": file_extension[1:] if file_extension else "unknown",
                    "rag_ready": str(file_extension in ['.pdf', '.docx', '.txt']).lower(),
                    "upload_date": datetime.utcnow().strftime("%Y-%m-%d")
                }
            )
            
            logger.info(f"📄 Documento subido: {blob_name} ({len(content)} bytes)")
            return blob_name
            
        except Exception as e:
            logger.error(f"❌ Error subiendo {file_name}: {str(e)}")
            raise
    
    async def list_documents(self, include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        Listar documentos con información enriquecida para RAG
        """
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            documents = []
            
            include_fields = ['metadata', 'tags'] if include_metadata else []
            
            for blob in container_client.list_blobs(include=include_fields):
                doc_info = {
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None,
                    "original_name": blob.metadata.get("original_name", blob.name) if blob.metadata else blob.name
                }
                
                if include_metadata and blob.metadata:
                    doc_info.update({
                        "metadata": blob.metadata,
                        "file_type": blob.metadata.get("file_type", "unknown"),
                        "rag_status": blob.metadata.get("rag_status", "unknown"),
                        "processing_status": blob.metadata.get("processing_status", "unknown"),
                        "content_hash": blob.metadata.get("content_hash"),
                        "upload_timestamp": blob.metadata.get("upload_timestamp")
                    })
                
                if hasattr(blob, 'tags') and blob.tags:
                    doc_info["tags"] = blob.tags
                    doc_info["rag_ready"] = blob.tags.get("rag_ready") == "true"
                
                documents.append(doc_info)
            
            # Ordenar por fecha de modificación, más reciente primero
            documents.sort(
                key=lambda x: x.get("last_modified", ""), 
                reverse=True
            )
            
            logger.info(f"📋 Listados {len(documents)} documentos")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Error listando documentos: {str(e)}")
            raise
    
    async def get_document(self, blob_name: str) -> bytes:
        """Descargar contenido de documento"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            download_stream = blob_client.download_blob()
            content = download_stream.readall()
            
            logger.info(f"📥 Descargado: {blob_name} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            logger.error(f"❌ Error descargando {blob_name}: {str(e)}")
            raise
    
    async def delete_document(self, blob_name: str) -> bool:
        """Eliminar documento"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            logger.info(f"🗑️ Eliminado: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando {blob_name}: {str(e)}")
            raise
    
    async def update_processing_status(
        self, 
        blob_name: str, 
        status: str, 
        metadata_updates: Dict[str, str] = None
    ) -> bool:
        """
        Actualizar estado de procesamiento para RAG
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Obtener metadata existente
            properties = blob_client.get_blob_properties()
            current_metadata = properties.metadata or {}
            
            # Actualizar metadata
            current_metadata["processing_status"] = status
            current_metadata["last_updated"] = datetime.utcnow().isoformat()
            
            if metadata_updates:
                current_metadata.update(metadata_updates)
            
            # Aplicar cambios
            blob_client.set_blob_metadata(metadata=current_metadata)
            
            logger.info(f"🔄 Estado actualizado para {blob_name}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando estado {blob_name}: {str(e)}")
            raise
    
    async def get_documents_for_processing(self, status: str = "pending") -> List[Dict[str, Any]]:
        """
        Obtener documentos listos para procesamiento RAG
        """
        try:
            all_documents = await self.list_documents(include_metadata=True)
            
            # Filtrar por estado y compatibilidad RAG
            processing_documents = [
                doc for doc in all_documents
                if doc.get("metadata", {}).get("processing_status") == status
                and doc.get("file_type") in ["pdf", "docx", "txt", "md"]
            ]
            
            logger.info(f"🔍 {len(processing_documents)} documentos listos para procesamiento")
            return processing_documents
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo documentos para procesamiento: {str(e)}")
            raise
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Obtener información de conexión para debugging"""
        return {
            "container_name": self.container_name,
            "account_name": settings.azure_storage_account_name,
            "has_connection_string": bool(settings.azure_storage_connection_string),
            "client_initialized": self.blob_service_client is not None
        }