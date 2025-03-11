import sys
import unittest
from unittest.mock import Mock, patch
from flask import Flask
from pathlib import Path
from keepercommander.service.util.command_util import CommandExecutor
from keepercommander.service.util.exceptions import CommandExecutionError
from keepercommander.service.util.parse_keeper_response import parse_keeper_response

class TestCommandAPI(unittest.TestCase):
    def setUp(self):
        """Set up Flask test client."""
        self.app = Flask(__name__)
        self.client = self.app.test_client()

        @self.app.route('/api/v1/executecommand', methods=['POST'])
        def execute_command():
            command = "ls"
            user_info = {"password": "test_pass"}  #  Ensure password is always present
            response, status_code = CommandExecutor.execute(command, user_info)
            return {'response': response}, status_code

    def test_validate_command(self):
        """Test command validation."""
        result, status_code = CommandExecutor.validate_command("")
        self.assertIsNotNone(result)
        self.assertEqual(status_code, 400)
        self.assertEqual(result["error"], "No command provided.")

        result = CommandExecutor.validate_command("ls")
        self.assertIsNone(result)

    def test_validate_session(self):
        """Test session validation."""
        with patch('keepercommander.service.util.command_util.get_current_params', return_value=None):
            result, status_code = CommandExecutor.validate_session()
            self.assertEqual(status_code, 401)
            self.assertIn("No active session", result["error"])

        with patch('keepercommander.service.util.command_util.get_current_params', return_value={"session": "active"}):
            result = CommandExecutor.validate_session()
            self.assertIsNone(result)

    def test_command_execution_success(self):
        """Test successful command execution."""
        mock_params = {"session": "active"}
        test_command = "ls"
        expected_output = "Folder1\nFolder2\n"
        user_info = {"password": "test_pass"}

        with patch('keepercommander.service.util.command_util.get_current_params', return_value=mock_params), \
            patch('keepercommander.cli.do_command', return_value=expected_output), \
            patch('keepercommander.service.util.command_util.ConfigReader.read_config', return_value=None), \
            patch('keepercommander.service.util.command_util.LoginCommand.execute') as mock_login:
            
            mock_login.return_value = None  #  Prevents password prompt

            response, status_code = CommandExecutor.execute(test_command, user_info)
            self.assertEqual(status_code, 200)
            self.assertIsNotNone(response)

    def test_command_execution_failure(self):
        """Test command execution failure."""
        mock_params = {"session": "active"}
        test_command = "invalid_command"
        user_info = {"password": "test_pass"}

        with patch('keepercommander.service.util.command_util.get_current_params', return_value=mock_params), \
            patch('keepercommander.cli.do_command', side_effect=Exception("Command failed")), \
            patch('keepercommander.service.util.command_util.LoginCommand.execute') as mock_login:
            
            mock_login.return_value = None  #  Prevents password prompt

            with self.assertRaises(CommandExecutionError):
                CommandExecutor.execute(test_command, user_info)

    def test_response_encryption(self):
        """Test response encryption when key is present."""
        test_response = {"status": "success", "data": "test"}
        mock_key = "0" * 32

        with patch('keepercommander.service.util.command_util.ConfigReader.read_config', return_value=mock_key):
            encrypted_response = CommandExecutor.encrypt_response(test_response)
            self.assertIsInstance(encrypted_response, bytes)
            self.assertGreater(len(encrypted_response), 0)

    def test_response_parsing(self):
        """Test response parsing for different commands."""
        ls_response = "# Folder UID\n1 folder1_uid folder1 rw\n# Record UID\n1 record1_uid login record1"
        parsed = parse_keeper_response("ls", ls_response)
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["command"], "ls")
        self.assertIn("folders", parsed["data"])
        self.assertIn("records", parsed["data"])

        tree_response = "Root\n  Folder1\n    SubFolder1"
        parsed = parse_keeper_response("tree", tree_response)
        self.assertEqual(parsed["command"], "tree")
        self.assertIsInstance(parsed["data"], list)

    def test_capture_output(self):
        """Test command output capture."""
        test_command = "ls"
        expected_output = "test output"
        mock_params = {"session": "active"}

        with patch('keepercommander.cli.do_command', return_value=expected_output):
            return_value, output = CommandExecutor.capture_output(mock_params, test_command)
            self.assertEqual(return_value, expected_output)

    def test_integration_command_flow(self):
        """Test the complete command execution flow."""
        test_command = "ls"
        mock_params = {"session": "active"}
        user_info = {"password": "test_pass"}
        expected_output = "# Folder UID\n1 folder1_uid folder1 rw"

        with patch('keepercommander.service.util.command_util.get_current_params', return_value=mock_params), \
            patch('keepercommander.cli.do_command', return_value=expected_output), \
            patch('keepercommander.service.util.command_util.ConfigReader.read_config', return_value=None), \
            patch('keepercommander.service.util.command_util.LoginCommand.execute') as mock_login:
            
            mock_login.return_value = None  #  Prevents password prompt

            response, status_code = CommandExecutor.execute(test_command, user_info)
            self.assertEqual(status_code, 200)
            self.assertIsNotNone(response)

if __name__ == '__main__':
    unittest.main()
