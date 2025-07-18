import pytest
import os
import tempfile
import requests
from tests.utils.api_client import APIClient

class TestFileUpload:
    """Test file upload functionality."""
    
    def test_upload_markdown_file(self, api_client: APIClient, test_files, cleanup_uploaded_files):
        """Test uploading a markdown file."""
        file_path = test_files["requirements.md"]
        
        response = api_client.upload_file(file_path)
        cleanup_uploaded_files(response["file_id"])
        
        assert "file_id" in response
        assert response["filename"] == "requirements.md"
        assert response["size"] > 0
        assert response["content_type"] in ["text/markdown", "application/octet-stream"]
        assert "uploaded_at" in response
    
    def test_upload_text_file(self, api_client: APIClient, test_files, cleanup_uploaded_files):
        """Test uploading a text file."""
        file_path = test_files["test_document.txt"]
        
        response = api_client.upload_file(file_path)
        cleanup_uploaded_files(response["file_id"])
        
        assert "file_id" in response
        assert response["filename"] == "test_document.txt"
        assert response["size"] > 0
        assert response["content_type"] in ["text/plain", "application/octet-stream"]
    
    def test_upload_with_custom_filename(self, api_client: APIClient, test_files, cleanup_uploaded_files):
        """Test uploading file with custom filename."""
        file_path = test_files["requirements.md"]
        custom_filename = "custom_requirements.md"
        
        response = api_client.upload_file(file_path, custom_filename)
        cleanup_uploaded_files(response["file_id"])
        
        assert response["filename"] == custom_filename
    
    def test_upload_large_file(self, api_client: APIClient, cleanup_uploaded_files):
        """Test uploading a large file (within limits)."""
        # Create a temporary large file (1MB)
        large_content = "x" * (1024 * 1024)  # 1MB
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_content)
            temp_file = f.name
        
        try:
            response = api_client.upload_file(temp_file)
            cleanup_uploaded_files(response["file_id"])
            
            assert response["size"] == 1024 * 1024
            assert "file_id" in response
        finally:
            os.unlink(temp_file)
    
    def test_upload_unsupported_file_type(self, api_client: APIClient):
        """Test uploading unsupported file type."""
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            with pytest.raises(requests.exceptions.HTTPError) as exc_info:
                api_client.upload_file(temp_file)
            
            assert exc_info.value.response.status_code == 400
            error_response = exc_info.value.response.json()
            assert "not supported" in error_response["detail"]
        finally:
            os.unlink(temp_file)
    
    def test_upload_oversized_file(self, api_client: APIClient):
        """Test uploading file that exceeds size limit."""
        # Create a temporary file that exceeds 10MB limit
        oversized_content = "x" * (11 * 1024 * 1024)  # 11MB
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(oversized_content)
            temp_file = f.name
        
        try:
            with pytest.raises(requests.exceptions.HTTPError) as exc_info:
                api_client.upload_file(temp_file)
            
            assert exc_info.value.response.status_code == 400
            error_response = exc_info.value.response.json()
            assert "exceeds" in error_response["detail"]
        finally:
            os.unlink(temp_file)
    
    def test_upload_nonexistent_file(self, api_client: APIClient):
        """Test uploading non-existent file."""
        with pytest.raises(FileNotFoundError):
            api_client.upload_file("/nonexistent/file.txt")

class TestFileOperations:
    """Test file operations after upload."""
    
    def test_get_uploaded_files(self, api_client: APIClient, test_files, cleanup_uploaded_files):
        """Test getting list of uploaded files."""
        # Upload a file first
        file_path = test_files["requirements.md"]
        upload_response = api_client.upload_file(file_path)
        cleanup_uploaded_files(upload_response["file_id"])
        
        # Get files list
        files = api_client.get_files()
        
        assert isinstance(files, list)
        assert len(files) > 0
        
        # Find our uploaded file
        uploaded_file = next((f for f in files if f["file_id"] == upload_response["file_id"]), None)
        assert uploaded_file is not None
        assert uploaded_file["filename"] == "requirements.md"
        assert uploaded_file["processed"] is False
    
    def test_get_file_info(self, api_client: APIClient, test_files, cleanup_uploaded_files):
        """Test getting specific file information."""
        # Upload a file first
        file_path = test_files["requirements.md"]
        upload_response = api_client.upload_file(file_path)
        file_id = upload_response["file_id"]
        cleanup_uploaded_files(file_id)
        
        # Get file info
        file_info = api_client.get_file_info(file_id)
        
        assert file_info["file_id"] == file_id
        assert file_info["filename"] == "requirements.md"
        assert file_info["size"] > 0
        assert "uploaded_at" in file_info
        assert file_info["processed"] is False
    
    def test_get_nonexistent_file_info(self, api_client: APIClient):
        """Test getting info for non-existent file."""
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.get_file_info("nonexistent-file-id")
        
        assert exc_info.value.response.status_code == 404
    
    def test_delete_file(self, api_client: APIClient, test_files):
        """Test deleting a file."""
        # Upload a file first
        file_path = test_files["requirements.md"]
        upload_response = api_client.upload_file(file_path)
        file_id = upload_response["file_id"]
        
        # Delete the file
        delete_response = api_client.delete_file(file_id)
        assert "deleted successfully" in delete_response["message"]
        
        # Verify it's gone
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.get_file_info(file_id)
        
        assert exc_info.value.response.status_code == 404
    
    def test_delete_nonexistent_file(self, api_client: APIClient):
        """Test deleting non-existent file."""
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.delete_file("nonexistent-file-id")
        
        assert exc_info.value.response.status_code == 404

class TestFileProcessing:
    """Test file content processing."""
    
    def test_preview_markdown_file(self, api_client: APIClient, test_files, cleanup_uploaded_files):
        """Test previewing markdown file content."""
        # Upload a file first
        file_path = test_files["requirements.md"]
        upload_response = api_client.upload_file(file_path)
        file_id = upload_response["file_id"]
        cleanup_uploaded_files(file_id)
        
        # Get file preview
        preview = api_client.preview_file(file_id)
        
        assert preview["file_id"] == file_id
        assert preview["filename"] == "requirements.md"
        assert preview["processed"] is True
        assert "preview" in preview
        assert "summary" in preview
        
        # Check that content was extracted
        assert "Emergency Communication System" in preview["preview"]
        assert preview["summary"]["character_count"] > 0
        assert preview["summary"]["word_count"] > 0
    
    def test_preview_text_file(self, api_client: APIClient, test_files, cleanup_uploaded_files):
        """Test previewing text file content."""
        # Upload a file first
        file_path = test_files["test_document.txt"]
        upload_response = api_client.upload_file(file_path)
        file_id = upload_response["file_id"]
        cleanup_uploaded_files(file_id)
        
        # Get file preview
        preview = api_client.preview_file(file_id)
        
        assert preview["file_id"] == file_id
        assert preview["filename"] == "test_document.txt"
        assert preview["processed"] is True
        assert "simple text document" in preview["preview"]
    
    def test_process_file_explicitly(self, api_client: APIClient, test_files, cleanup_uploaded_files):
        """Test explicit file processing."""
        # Upload a file first
        file_path = test_files["requirements.md"]
        upload_response = api_client.upload_file(file_path)
        file_id = upload_response["file_id"]
        cleanup_uploaded_files(file_id)
        
        # Process the file
        process_response = api_client.process_file(file_id)
        
        assert process_response["file_id"] == file_id
        assert process_response["processed"] is True
        assert "content_length" in process_response
        assert process_response["content_length"] > 0
        assert "metadata" in process_response
        
        # Check metadata
        metadata = process_response["metadata"]
        assert metadata["file_type"] == ".md"
        assert metadata["original_size"] > 0
        assert metadata["extracted_size"] > 0
    
    def test_process_nonexistent_file(self, api_client: APIClient):
        """Test processing non-existent file."""
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.process_file("nonexistent-file-id")
        
        assert exc_info.value.response.status_code == 404
    
    def test_preview_nonexistent_file(self, api_client: APIClient):
        """Test previewing non-existent file."""
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.preview_file("nonexistent-file-id")
        
        assert exc_info.value.response.status_code == 404

class TestFileContentValidation:
    """Test file content validation and extraction."""
    
    def test_markdown_content_extraction(self, api_client: APIClient, test_files, cleanup_uploaded_files):
        """Test that markdown content is properly extracted."""
        # Upload requirements document
        file_path = test_files["requirements.md"]
        upload_response = api_client.upload_file(file_path)
        file_id = upload_response["file_id"]
        cleanup_uploaded_files(file_id)
        
        # Get preview
        preview = api_client.preview_file(file_id)
        content = preview["preview"]
        
        # Check that specific requirements are extracted
        assert "FR-001" in content
        assert "NFR-001" in content
        assert "Real-time Communication" in content
        assert "Performance" in content
        
        # Check summary statistics
        summary = preview["summary"]
        assert summary["character_count"] > 1000
        assert summary["word_count"] > 100
        assert summary["line_count"] > 10
    
    def test_text_content_extraction(self, api_client: APIClient, test_files, cleanup_uploaded_files):
        """Test that text content is properly extracted."""
        # Upload text document
        file_path = test_files["test_document.txt"]
        upload_response = api_client.upload_file(file_path)
        file_id = upload_response["file_id"]
        cleanup_uploaded_files(file_id)
        
        # Get preview
        preview = api_client.preview_file(file_id)
        content = preview["preview"]
        
        # Check that content is extracted
        assert "simple text document" in content
        assert "file processing" in content
        assert "multiple lines" in content
    
    def test_empty_file_handling(self, api_client: APIClient, cleanup_uploaded_files):
        """Test handling of empty files."""
        # Create empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_file = f.name
        
        try:
            # Upload empty file
            upload_response = api_client.upload_file(temp_file)
            file_id = upload_response["file_id"]
            cleanup_uploaded_files(file_id)
            
            assert upload_response["size"] == 0
            
            # Try to preview empty file
            preview = api_client.preview_file(file_id)
            assert preview["summary"]["character_count"] == 0
            assert preview["summary"]["word_count"] == 0
            
        finally:
            os.unlink(temp_file)

class TestFileWorkflow:
    """Test complete file workflow."""
    
    def test_upload_process_preview_delete_workflow(self, api_client: APIClient, test_files):
        """Test complete file workflow."""
        # 1. Upload file
        file_path = test_files["requirements.md"]
        upload_response = api_client.upload_file(file_path)
        file_id = upload_response["file_id"]
        
        assert "file_id" in upload_response
        assert upload_response["filename"] == "requirements.md"
        
        # 2. Verify it appears in file list
        files = api_client.get_files()
        uploaded_file = next((f for f in files if f["file_id"] == file_id), None)
        assert uploaded_file is not None
        
        # 3. Get file info
        file_info = api_client.get_file_info(file_id)
        assert file_info["file_id"] == file_id
        
        # 4. Process file
        process_response = api_client.process_file(file_id)
        assert process_response["processed"] is True
        
        # 5. Preview file content
        preview = api_client.preview_file(file_id)
        assert preview["processed"] is True
        assert len(preview["preview"]) > 0
        
        # 6. Delete file
        delete_response = api_client.delete_file(file_id)
        assert "deleted successfully" in delete_response["message"]
        
        # 7. Verify it's gone
        with pytest.raises(requests.exceptions.HTTPError):
            api_client.get_file_info(file_id)
    
    def test_multiple_file_upload(self, api_client: APIClient, test_files):
        """Test uploading multiple files."""
        file_ids = []
        
        try:
            # Upload multiple files
            for filename in ["requirements.md", "test_document.txt"]:
                if filename in test_files:
                    file_path = test_files[filename]
                    upload_response = api_client.upload_file(file_path)
                    file_ids.append(upload_response["file_id"])
            
            # Verify all files are listed
            files = api_client.get_files()
            uploaded_files = [f for f in files if f["file_id"] in file_ids]
            assert len(uploaded_files) == len(file_ids)
            
            # Process all files
            for file_id in file_ids:
                process_response = api_client.process_file(file_id)
                assert process_response["processed"] is True
            
        finally:
            # Cleanup
            for file_id in file_ids:
                try:
                    api_client.delete_file(file_id)
                except:
                    pass