from google.cloud import storage
import os
import shutil
from abc import ABC, abstractmethod
from pdf2image import convert_from_path

class StorageBackend(ABC):
    @abstractmethod
    def upload_file(self, source_file_path, destination_blob_name=None):
        """
        Upload a file to storage and return its public URL.
        Handles any necessary cleanup of source files.
        
        Args:
            source_file_path (str): Path to the local file to upload
            destination_blob_name (str, optional): Name to give the file in storage.
                                                If None, uses the filename from source_file_path
        
        Returns:
            str: Public URL or path of the uploaded file
        """
        pass

    @abstractmethod
    def delete_file(self, file_name):
        """Delete a file from storage."""
        pass

class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir='local_storage'):
        """Initialize local storage with a base directory."""
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def upload_file(self, source_file_path, destination_blob_name=None):
        """
        Store a file in local storage and return its relative path.
        For local storage, we move the file instead of copying to handle cleanup automatically.
        
        Args:
            source_file_path (str): Path to the local file to store
            destination_blob_name (str, optional): Name to give the file in storage.
                                                If None, uses the filename from source_file_path
        
        Returns:
            str: Full URL path to the stored file
        """
        if destination_blob_name is None:
            destination_blob_name = os.path.basename(source_file_path)

        # If this is a PDF, convert to JPG with high quality settings
        jpg_path = None
        if source_file_path.lower().endswith('.pdf'):
            # Convert PDF to JPG with high DPI
            images = convert_from_path(source_file_path, dpi=300)
            
            # Save as JPG with maximum quality
            jpg_path = source_file_path.rsplit('.', 1)[0] + '.jpg'
            images[0].save(jpg_path, 'JPEG', quality=100, dpi=(300, 300))
            
            # Clean up the original PDF since we'll use the JPG
            os.remove(source_file_path)
            
            # Update source path to the JPG
            source_file_path = jpg_path
            destination_blob_name = destination_blob_name.rsplit('.', 1)[0] + '.jpg'

        try:
            dest_path = os.path.join(self.base_dir, destination_blob_name)
            # Move the file instead of copying to handle cleanup
            shutil.move(source_file_path, dest_path)
            
            # Get server host and port from environment or use defaults
            host = os.environ.get('SERVER_HOST', 'localhost')
            port = os.environ.get('PORT', '8080')
            
            # Return full URL including scheme, host, and port
            return f'http://{host}:{port}/files/{destination_blob_name}'
        except Exception as e:
            # Clean up any temporary files if something goes wrong
            if jpg_path and os.path.exists(jpg_path):
                os.remove(jpg_path)
            raise e

    def delete_file(self, file_name):
        """Delete a file from local storage."""
        file_path = os.path.join(self.base_dir, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

class CloudStorageClient(StorageBackend):
    def __init__(self, bucket_name):
        """Initialize the cloud storage client with a bucket name."""
        self.storage_client = storage.Client()
        self.bucket_name = bucket_name
        self.bucket = self.storage_client.bucket(bucket_name)

    def upload_file(self, source_file_path, destination_blob_name=None):
        """
        Upload a file to Google Cloud Storage and clean up the local file.
        
        Args:
            source_file_path (str): Path to the local file to upload
            destination_blob_name (str, optional): Name to give the file in GCS.
                                                If None, uses the filename from source_file_path
        
        Returns:
            str: Public URL of the uploaded file
        """
        if destination_blob_name is None:
            destination_blob_name = os.path.basename(source_file_path)

        jpg_path = None
        try:
            # If this is a PDF, convert to JPG with high quality settings
            if source_file_path.lower().endswith('.pdf'):
                # Convert PDF to JPG with high DPI
                images = convert_from_path(source_file_path, dpi=300)
                
                # Save as JPG with maximum quality
                jpg_path = source_file_path.rsplit('.', 1)[0] + '.jpg'
                images[0].save(jpg_path, 'JPEG', quality=100, dpi=(300, 300))
                
                # Clean up the original PDF since we'll use the JPG
                os.remove(source_file_path)
                
                # Update source path to the JPG
                source_file_path = jpg_path
                destination_blob_name = destination_blob_name.rsplit('.', 1)[0] + '.jpg'

            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_path)
            
            # Make the blob publicly readable
            blob.make_public()
            
            # Clean up the local file after successful upload
            os.remove(source_file_path)
            
            return blob.public_url
            
        except Exception as e:
            # Clean up any temporary files if something goes wrong
            if jpg_path and os.path.exists(jpg_path):
                os.remove(jpg_path)
            if os.path.exists(source_file_path):
                os.remove(source_file_path)
            raise e

    def delete_file(self, blob_name):
        """Delete a file from Google Cloud Storage."""
        blob = self.bucket.blob(blob_name)
        blob.delete()

def get_storage_backend():
    """Factory function to get the appropriate storage backend based on environment."""
    if os.environ.get('USE_LOCAL_STORAGE', 'false').lower() == 'true':
        return LocalStorageBackend()
    else:
        bucket_name = os.environ.get('STORAGE_BUCKET', 'cmt-renders-benchmark-eval-2024')
        return CloudStorageClient(bucket_name) 