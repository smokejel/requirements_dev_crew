import pytest
import asyncio
import time
from tests.utils.api_client import APIClient
from tests.utils.websocket_client import WebSocketTestClient

@pytest.mark.integration
class TestCompleteWorkflow:
    """Test complete end-to-end workflow."""
    
    def test_complete_workflow_without_websocket(self, api_client: APIClient, test_files, test_config):
        """Test complete workflow: upload -> configure -> execute -> monitor."""
        # 1. Upload files
        file_ids = api_client.upload_test_files(test_files)
        assert len(file_ids) > 0
        
        # 2. Set up API keys
        api_client.setup_test_api_keys(test_config)
        
        # 3. Configure agents
        for agent_name, config in test_config["test_agent_configs"].items():
            api_client.update_agent_config(agent_name, config)
        
        # 4. Execute crew
        execution_request = {
            "prompt": "Complete workflow test: analyze the uploaded documents",
            "uploaded_files": list(file_ids.values()),
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # 5. Monitor execution
        final_status = api_client.wait_for_execution(execution_id, timeout=15)
        
        # 6. Verify completion (should fail with test keys)
        assert final_status["status"] == "failed"
        assert "error" in final_status
        assert final_status["progress"] == 1.0
        
        # 7. Check execution history
        history = api_client.get_execution_history()
        execution_in_history = next((ex for ex in history if ex["execution_id"] == execution_id), None)
        assert execution_in_history is not None
        
        # 8. Cleanup files
        for file_id in file_ids.values():
            api_client.delete_file(file_id)
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_websocket(self, api_client: APIClient, websocket_client: WebSocketTestClient, test_files, test_config):
        """Test complete workflow with WebSocket streaming."""
        # 1. Upload files
        file_ids = api_client.upload_test_files(test_files)
        assert len(file_ids) > 0
        
        # 2. Set up API keys
        api_client.setup_test_api_keys(test_config)
        
        # 3. Execute crew
        execution_request = {
            "prompt": "WebSocket workflow test: analyze the uploaded documents and provide insights",
            "uploaded_files": list(file_ids.values()),
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # 4. Subscribe to WebSocket updates
        await websocket_client.subscribe(execution_id)
        
        # 5. Monitor via WebSocket
        progress_updates = []
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < 10.0:
            await asyncio.sleep(0.5)
            
            # Get execution messages
            messages = websocket_client.get_execution_messages(execution_id)
            for msg in messages:
                if msg.get("data", {}).get("progress") is not None:
                    progress_updates.append(msg["data"]["progress"])
                
                # Check for completion
                if msg.get("data", {}).get("type") == "completion":
                    break
        
        # 6. Verify streaming worked
        assert len(progress_updates) > 0
        
        # 7. Verify final status via API
        final_status = api_client.get_execution_status(execution_id)
        assert final_status["status"] in ["completed", "failed"]
        assert final_status["progress"] == 1.0
        
        # 8. Cleanup
        for file_id in file_ids.values():
            api_client.delete_file(file_id)
    
    def test_workflow_with_file_processing(self, api_client: APIClient, test_files, test_config):
        """Test workflow with explicit file processing."""
        # 1. Upload and process files
        file_ids = []
        for name, path in test_files.items():
            if not name.endswith('.json'):
                # Upload file
                upload_response = api_client.upload_file(path, name)
                file_id = upload_response["file_id"]
                file_ids.append(file_id)
                
                # Process file
                process_response = api_client.process_file(file_id)
                assert process_response["processed"] is True
                
                # Verify preview
                preview = api_client.preview_file(file_id)
                assert preview["processed"] is True
                assert len(preview["preview"]) > 0
        
        # 2. Set up and execute
        api_client.setup_test_api_keys(test_config)
        
        execution_request = {
            "prompt": "Analyze the processed documents",
            "uploaded_files": file_ids,
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # 3. Wait for completion
        final_status = api_client.wait_for_execution(execution_id, timeout=10)
        assert final_status["status"] in ["completed", "failed"]
        
        # 4. Cleanup
        for file_id in file_ids:
            api_client.delete_file(file_id)

@pytest.mark.integration
class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    def test_recovery_from_api_key_error(self, api_client: APIClient, test_config):
        """Test recovery from API key errors."""
        # 1. Start execution without API key
        execution_request = {
            "prompt": "Test recovery from API key error",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response1 = api_client.execute_crew(execution_request)
        execution_id1 = response1["execution_id"]
        
        # Should fail
        final_status1 = api_client.wait_for_execution(execution_id1, timeout=10)
        assert final_status1["status"] == "failed"
        assert "key" in final_status1["error"].lower()
        
        # 2. Set up API key and retry
        api_client.setup_test_api_keys(test_config)
        
        response2 = api_client.execute_crew(execution_request)
        execution_id2 = response2["execution_id"]
        
        # Should still fail but with different error (test key)
        final_status2 = api_client.wait_for_execution(execution_id2, timeout=10)
        assert final_status2["status"] == "failed"
        assert "AuthenticationError" in final_status2["error"]
        
        # Different error messages indicate the API key was found
        assert final_status1["error"] != final_status2["error"]
    
    def test_recovery_from_file_error(self, api_client: APIClient, test_config):
        """Test recovery from file errors."""
        # 1. Execute with invalid file ID
        api_client.setup_test_api_keys(test_config)
        
        execution_request = {
            "prompt": "Test with invalid file",
            "uploaded_files": ["invalid-file-id"],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # Should handle gracefully
        final_status = api_client.wait_for_execution(execution_id, timeout=10)
        assert final_status["status"] == "failed"
        assert "error" in final_status
    
    @pytest.mark.asyncio
    async def test_websocket_reconnection_during_execution(self, api_client: APIClient, ws_url, test_config):
        """Test WebSocket reconnection during execution."""
        # 1. Start execution
        api_client.setup_test_api_keys(test_config)
        
        execution_request = {
            "prompt": "Test WebSocket reconnection",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # 2. Connect WebSocket and subscribe
        client1 = WebSocketTestClient(ws_url)
        await client1.connect()
        await client1.subscribe(execution_id)
        
        # 3. Wait for some updates
        await asyncio.sleep(2)
        messages1 = client1.get_execution_messages(execution_id)
        
        # 4. Disconnect and reconnect
        await client1.disconnect()
        
        client2 = WebSocketTestClient(ws_url)
        await client2.connect()
        await client2.subscribe(execution_id)
        
        # 5. Wait for more updates
        await asyncio.sleep(2)
        messages2 = client2.get_execution_messages(execution_id)
        
        # 6. Should have received messages on both connections
        assert len(messages1) > 0 or len(messages2) > 0
        
        # 7. Cleanup
        await client2.disconnect()
        try:
            api_client.cancel_execution(execution_id)
        except:
            pass

@pytest.mark.integration
class TestConcurrentOperations:
    """Test concurrent operations."""
    
    def test_concurrent_file_uploads(self, api_client: APIClient, test_files):
        """Test concurrent file uploads."""
        import threading
        
        results = []
        errors = []
        
        def upload_file(file_path, filename):
            try:
                response = api_client.upload_file(file_path, filename)
                results.append(response)
            except Exception as e:
                errors.append(e)
        
        # Start multiple uploads concurrently
        threads = []
        for i, (name, path) in enumerate(test_files.items()):
            if not name.endswith('.json'):
                thread = threading.Thread(
                    target=upload_file,
                    args=(path, f"concurrent_{i}_{name}")
                )
                threads.append(thread)
                thread.start()
        
        # Wait for all uploads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Upload errors: {errors}"
        assert len(results) > 0
        
        # Cleanup
        for result in results:
            try:
                api_client.delete_file(result["file_id"])
            except:
                pass
    
    def test_concurrent_executions(self, api_client: APIClient, test_config):
        """Test concurrent crew executions."""
        import threading
        
        api_client.setup_test_api_keys(test_config)
        
        results = []
        errors = []
        
        def execute_crew(prompt_suffix):
            try:
                execution_request = {
                    "prompt": f"Concurrent execution test {prompt_suffix}",
                    "uploaded_files": [],
                    "agent_configs": test_config["test_agent_configs"],
                    "execution_mode": "run"
                }
                
                response = api_client.execute_crew(execution_request)
                results.append(response)
            except Exception as e:
                errors.append(e)
        
        # Start multiple executions concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=execute_crew, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all executions to start
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Execution errors: {errors}"
        assert len(results) == 3
        
        # Wait for all executions to complete
        for result in results:
            try:
                api_client.wait_for_execution(result["execution_id"], timeout=15)
            except:
                pass
    
    @pytest.mark.asyncio
    async def test_concurrent_websocket_subscriptions(self, api_client: APIClient, ws_url, test_config):
        """Test concurrent WebSocket subscriptions."""
        # Start execution
        api_client.setup_test_api_keys(test_config)
        
        execution_request = {
            "prompt": "Concurrent WebSocket test",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # Create multiple WebSocket clients
        clients = []
        for i in range(3):
            client = WebSocketTestClient(ws_url)
            await client.connect(f"concurrent-client-{i}")
            await client.subscribe(execution_id)
            clients.append(client)
        
        # Wait for updates
        await asyncio.sleep(3)
        
        # All clients should receive messages
        for client in clients:
            messages = client.get_execution_messages(execution_id)
            assert len(messages) > 0
        
        # Cleanup
        for client in clients:
            await client.disconnect()
        
        try:
            api_client.cancel_execution(execution_id)
        except:
            pass

@pytest.mark.integration
@pytest.mark.slow
class TestSystemLimits:
    """Test system limits and boundaries."""
    
    def test_maximum_file_uploads(self, api_client: APIClient, test_files):
        """Test uploading maximum allowed files."""
        # Upload files up to limit (simulate with smaller number)
        file_ids = []
        max_files = 5  # Reduced for testing
        
        try:
            for i in range(max_files):
                # Use the requirements file repeatedly
                file_path = test_files["requirements.md"]
                response = api_client.upload_file(file_path, f"test_file_{i}.md")
                file_ids.append(response["file_id"])
            
            # Verify all files are listed
            files = api_client.get_files()
            uploaded_count = len([f for f in files if f["file_id"] in file_ids])
            assert uploaded_count == max_files
        
        finally:
            # Cleanup
            for file_id in file_ids:
                try:
                    api_client.delete_file(file_id)
                except:
                    pass
    
    def test_large_prompt_handling(self, api_client: APIClient, test_config):
        """Test handling of large prompts."""
        # Create a large prompt
        large_prompt = "Analyze this system: " + "x" * 5000  # 5KB prompt
        
        api_client.setup_test_api_keys(test_config)
        
        execution_request = {
            "prompt": large_prompt,
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # Should handle large prompt
        assert "execution_id" in response
        assert response["status"] == "pending"
        
        # Wait for completion
        final_status = api_client.wait_for_execution(execution_id, timeout=10)
        assert final_status["status"] in ["completed", "failed"]
    
    @pytest.mark.asyncio
    async def test_websocket_message_limits(self, websocket_client: WebSocketTestClient):
        """Test WebSocket message handling limits."""
        # Send many messages rapidly
        num_messages = 50
        
        for i in range(num_messages):
            await websocket_client.ping()
            await asyncio.sleep(0.01)  # Very short delay
        
        # Wait for all responses
        await asyncio.sleep(5)
        
        # Should handle all messages
        pong_messages = websocket_client.get_messages("pong")
        assert len(pong_messages) == num_messages

@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency across operations."""
    
    def test_file_consistency_across_operations(self, api_client: APIClient, test_files):
        """Test file data consistency."""
        # Upload file
        file_path = test_files["requirements.md"]
        upload_response = api_client.upload_file(file_path)
        file_id = upload_response["file_id"]
        
        try:
            # Get file info multiple times
            info1 = api_client.get_file_info(file_id)
            info2 = api_client.get_file_info(file_id)
            
            # Should be consistent
            assert info1["file_id"] == info2["file_id"]
            assert info1["filename"] == info2["filename"]
            assert info1["size"] == info2["size"]
            assert info1["uploaded_at"] == info2["uploaded_at"]
            
            # Process file
            process_response = api_client.process_file(file_id)
            assert process_response["processed"] is True
            
            # File info should now show processed
            info3 = api_client.get_file_info(file_id)
            # Note: The actual processed status might be in preview, not file info
            
            # Preview should show processed content
            preview = api_client.preview_file(file_id)
            assert preview["processed"] is True
        
        finally:
            api_client.delete_file(file_id)
    
    def test_execution_state_consistency(self, api_client: APIClient, test_config):
        """Test execution state consistency."""
        api_client.setup_test_api_keys(test_config)
        
        execution_request = {
            "prompt": "Test state consistency",
            "uploaded_files": [],
            "agent_configs": test_config["test_agent_configs"],
            "execution_mode": "run"
        }
        
        response = api_client.execute_crew(execution_request)
        execution_id = response["execution_id"]
        
        # Check status multiple times
        status1 = api_client.get_execution_status(execution_id)
        time.sleep(0.5)
        status2 = api_client.get_execution_status(execution_id)
        
        # Execution ID should be consistent
        assert status1["execution_id"] == status2["execution_id"]
        assert status1["execution_id"] == execution_id
        
        # Progress should not decrease
        assert status2["progress"] >= status1["progress"]
        
        # If completed, should stay completed
        if status1["status"] in ["completed", "failed", "cancelled"]:
            assert status2["status"] == status1["status"]
        
        # Final status check
        final_status = api_client.wait_for_execution(execution_id, timeout=10)
        assert final_status["execution_id"] == execution_id
        assert final_status["progress"] == 1.0