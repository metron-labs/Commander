import sys
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch
from pathlib import Path

from keepercommander.params import KeeperParams
from keepercommander.service.core.service_manager import ServiceManager
from keepercommander.service.core.process_info import ProcessInfo
from keepercommander.service.commands.handle_service import StartService, StopService, ServiceStatus


class TestServiceManagement(unittest.TestCase):
    def setUp(self):
        self.params = mock.Mock(spec=KeeperParams)
        ProcessInfo._env_file = Path(__file__).parent / ".test_service.env"

        if ProcessInfo._env_file.exists():
            ProcessInfo._env_file.unlink()

    def tearDown(self):
        if ProcessInfo._env_file.exists():
            ProcessInfo._env_file.unlink()

    @patch("os.getpid", return_value=225104)
    @patch("psutil.Process")
    @patch("builtins.print")  #  Capture printed output
    def test_start_service_when_already_running(self, mock_print, mock_process, mock_pid):
        """Test starting service when another instance is already running"""
        ProcessInfo.save(pid=mock_pid.return_value, is_running=True)  #  Use mock PID
        mock_process.return_value.is_running.return_value = True

        start_cmd = StartService()
        start_cmd.execute(self.params)

        #  Debug print output
        print(f"Captured Print Calls: {mock_print.call_args_list}")

        expected_message = f"Error: Commander Service is already running (PID: {mock_pid.return_value})"
        mock_print.assert_any_call(expected_message)  #  Check if the expected message is in the print calls


    @patch("os.getpid", return_value=9999)
    @patch("keepercommander.service.core.terminal_handler.TerminalHandler.get_terminal_info", return_value="/dev/pts/0")
    @patch("psutil.Process")
    def test_stop_service_when_running(self, mock_process, mock_terminal, mock_pid):
        """Test stopping a running service"""
        ProcessInfo.save(pid=9999, is_running=True)
        mock_process.return_value.is_running.return_value = True
        mock_process.return_value.terminate = MagicMock()

        stop_cmd = StopService()

        #  Corrected: Patch stop_service, not stop()
        with patch.object(ServiceManager, "stop_service") as mock_stop:
            stop_cmd.execute(self.params)
            mock_stop.assert_called_once()

        self.assertTrue(ProcessInfo._env_file.exists())

    @patch("builtins.print")
    def test_stop_service_when_not_running(self, mock_print):
        """Test stopping service when no service is running"""
        stop_cmd = StopService()
        stop_cmd.execute(self.params)
        mock_print.assert_called_with("Error: No running service found to stop")

    @patch("os.getpid", return_value=225104)
    @patch("psutil.Process")
    @patch("keepercommander.service.core.terminal_handler.TerminalHandler.get_terminal_info", return_value="/dev/pts/13")  #  Use actual terminal value
    @patch("builtins.print")  #  Patch print to capture the output
    def test_service_status_when_running(self, mock_print, mock_terminal, mock_process, mock_pid):
        """Test getting status of running service"""
        ProcessInfo.save(pid=mock_pid.return_value, is_running=True)  #  Use mock PID
        mock_process.return_value.is_running.return_value = True

        status_cmd = ServiceStatus()
        status_cmd.execute(self.params)

        print(f"Captured Print Calls: {mock_print.call_args_list}")

        expected_status = f"Current status: Commander Service is Running (PID: {mock_pid.return_value}, Terminal: {mock_terminal.return_value})"

        mock_print.assert_any_call(expected_status)  #  Ensure expected print output matches the actual one



    @patch("builtins.print")
    def test_service_status_when_not_running(self, mock_print):
        """Test getting status when no service is running"""
        status_cmd = ServiceStatus()
        status_cmd.execute(self.params)
        mock_print.assert_called_with("Current status: Commander Service is Stopped")

    @patch("os.getpid", return_value=225104)
    def test_process_info_save_load(self, mock_pid):
        """Test ProcessInfo save and load operations"""
        ProcessInfo.save(pid=mock_pid.return_value, is_running=True)  #  Use mocked PID

        loaded_info = ProcessInfo.load()
        print(f"🚀 Loaded Process Info: {loaded_info.pid}")  #  Debugging line

        self.assertEqual(loaded_info.pid, mock_pid.return_value)  #  Compare with mock
        self.assertTrue(loaded_info.is_running)



    def test_handle_shutdown(self):
        """Test service shutdown handler"""
        ServiceManager._is_running = True
        ServiceManager._flask_app = MagicMock()

        ProcessInfo.save(pid=225104, is_running=True)

        ServiceManager._handle_shutdown()

        self.assertFalse(ServiceManager._is_running)
        self.assertIsNone(ServiceManager._flask_app)
        self.assertFalse(ProcessInfo._env_file.exists())

    @patch("keepercommander.service.config.service_config.ServiceConfig")
    @patch("keepercommander.service.app.create_app")
    @patch("builtins.print")
    def test_start_service_with_missing_config(self, mock_print, mock_create_app, mock_service_config):
        """Test starting service with missing configuration file"""
        mock_service_config.return_value.load_config.side_effect = FileNotFoundError()

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        start_cmd = StartService()
        start_cmd.execute(self.params)

        mock_print.assert_called_with(
            "Error: Service configuration file not found. Please use 'service-create' command to create a service_config file."
        )

    @patch("keepercommander.service.config.service_config.ServiceConfig")
    @patch("keepercommander.service.app.create_app")
    @patch("builtins.print")
    def test_start_service_with_missing_port(self, mock_print, mock_create_app, mock_service_config):
        """Test starting service with missing port in configuration"""
        mock_service_config.return_value.load_config.return_value = {}

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        start_cmd = StartService()
        start_cmd.execute(self.params)

        mock_print.assert_called_with(
            "Error: Service configuration is incomplete. Please configure the service port in service_config"
        )


if __name__ == "__main__":
    unittest.main()
