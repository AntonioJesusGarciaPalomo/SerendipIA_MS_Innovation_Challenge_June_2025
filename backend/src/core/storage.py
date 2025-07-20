from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.identity import DefaultAzureCredential
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import uuid
from pathlib import Path

from .config import settings

logger = logging.getLogger(__name__)

class AzureBlobStorage:
    """Azure Blob Storage handler for document management"""
    
    def __init__(self):
        """Initialize Azure Blob Storage client"""
        try:
            if settings.azure_storage_connection_string:
                # Use connection string if available
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    settings.azure_storage_connection_string
                )
            else:
                # Use DefaultAzureCredential for managed identity
                account_url = f"https://{settings.azure_storage_account_name}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=DefaultAzureCredential()
                )
            
            self.container_name = settings.azure_storage_container_name
            self._ensure_container_exists()
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob Storage: {str(e)}")
            raise
    
    def _ensure_container_exists(self):
        """Ensure the container exists, create if it doesn't"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Created container: {self.container_name}")
        except Exception as e:
            logger.error(f"Error ensuring container exists: {str(e)}")
            raise
    
    async def upload_document(self, file_name: str, content: bytes, content_type: str = None) -> str:
        """
        Upload a document to Azure Blob Storage
        
        Args:
            file_name: Original file name
            content: File content as bytes
            content_type: MIME type of the file
            
        Returns:
            str: Blob name (unique identifier)
        """
        try:
            # Generate unique blob name
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(file_name).suffix
            blob_name = f"{timestamp}_{uuid.uuid4().hex[:8]}{file_extension}"
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Upload with metadata
            metadata = {
                "original_name": file_name,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "file_type": file_extension[1:] if file_extension else "unknown"
            }
            
            blob_client.upload_blob(
                data=content,
                overwrite=True,
                content_settings={"content_type": content_type} if content_type else None,
                metadata=metadata
            )
            
            logger.info(f"Successfully uploaded document: {blob_name}")
            return blob_name
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the container
        
        Returns:
            List of document metadata
        """
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            documents = []
            
            for blob in container_client.list_blobs(include=['metadata']):
                documents.append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None,
                    "metadata": blob.metadata or {},
                    "original_name": blob.metadata.get("original_name", blob.name) if blob.metadata else blob.name
                })
            
            # Sort by last modified date, newest first
            documents.sort(key=lambda x: x["last_modified"] or "", reverse=True)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise
    
    async def get_document(self, blob_name: str) -> bytes:
        """
        Download a document from Azure Blob Storage
        
        Args:
            blob_name: The blob name to download
            
        Returns:
            bytes: Document content
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            download_stream = blob_client.download_blob()
            return download_stream.readall()
            
        except Exception as e:
            logger.error(f"Error downloading document: {str(e)}")
            raise
    
    async def delete_document(self, blob_name: str) -> bool:
        """
        Delete a document from Azure Blob Storage
        
        Args:
            blob_name: The blob name to delete
            
        Returns:
            bool: True if successful
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            logger.info(f"Successfully deleted document: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise
    
    async def get_document_metadata(self, blob_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific document
        
        Args:
            blob_name: The blob name
            
        Returns:
            Dict containing document metadata
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            properties = blob_client.get_blob_properties()
            
            return {
                "name": blob_name,
                "size": properties.size,
                "last_modified": properties.last_modified.isoformat() if properties.last_modified else None,
                "content_type": properties.content_settings.content_type if properties.content_settings else None,
                "metadata": properties.metadata or {},
                "etag": properties.etag,
                "created_on": properties.created_on.isoformat() if hasattr(properties, 'created_on') and properties.created_on else None
            }
            
        except Exception as e:
            logger.error(f"Error getting document metadata: {str(e)}")
            raise