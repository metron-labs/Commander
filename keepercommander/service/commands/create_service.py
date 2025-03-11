#  _  __
# | |/ /___ ___ _ __  ___ _ _ ®
# | ' </ -_) -_) '_ \/ -_) '_|
# |_|\_\___\___| .__/\___|_|
#              |_|
#
# Keeper Commander
# Copyright 2024 Keeper Security Inc.
# Contact: ops@keepersecurity.com
#

import argparse
from typing import Dict, Any
from keepercommander.params import KeeperParams
from keepercommander.commands.base import report_output_parser, Command
from ..config.config_validation import ValidationError
from ..decorators.logging import logger, debug_decorator
from dataclasses import dataclass
from typing import Optional

@dataclass
class StreamlineArgs:
    port: Optional[int]
    commands: Optional[str]
    ngrok: Optional[str]   
    username: Optional[str]
    password: Optional[str]

class CreateService(Command):
    """Command to create a new service configuration."""
    
    def __init__(self):
        from keepercommander.service.config.service_config import ServiceConfig
        self.service_config = ServiceConfig()
        self._config_handler = None
        self._security_handler = None

    @property
    def config_handler(self):
        if self._config_handler is None:
            from .service_config_handlers import ServiceConfigHandler
            self._config_handler = ServiceConfigHandler(self.service_config)
        return self._config_handler

    @property
    def security_handler(self):
        if self._security_handler is None:
            from .security_config_handler import SecurityConfigHandler
            self._security_handler = SecurityConfigHandler(self.service_config)
        return self._security_handler

    @debug_decorator
    def get_parser(self):
        parser = argparse.ArgumentParser(prog='service-create', parents=[report_output_parser], description='Creates and initializes the Commander API service.')
        parser.add_argument('-p', '--port', type=int, help='port number for the service (required)')
        parser.add_argument('-c', '--commands', type=str, help='command list for policy')
        parser.add_argument('-ng', '--ngrok', type=str, help='ngrok auth token to generate public URL (optional)')

        #  New arguments for username and password
        parser.add_argument('-u', '--username', type=str, help='Username for authentication')
        parser.add_argument('-pw', '--password', type=str, help='Password for authentication')
        return parser
    
    def execute(self, params: KeeperParams, **kwargs) -> None:
        try:
            from ..core.service_manager import ServiceManager
            if ServiceManager.get_status().startswith("Commander Service is Running"):
                print("Error: Commander Service is already running.")
                return

            from ..core.globals import init_globals
            init_globals(params)

            config_data = self.service_config.create_default_config()

            filtered_kwargs = {k: v for k, v in kwargs.items() if k in ['port', 'commands', 'ngrok', 'username', 'password']}
            args = StreamlineArgs(**filtered_kwargs)

            
            self._handle_configuration(config_data, params, args)
            self._create_and_save_record(config_data, params, args)
            self._upload_and_start_service(params, args, config_data)

        except ValidationError as e:
            print(f"Validation Error: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
    
    @debug_decorator
    def _handle_configuration(self, config_data: Dict[str, Any], params: KeeperParams, args: StreamlineArgs) -> None:       
        if args.port is not None:
            logger.debug("Entering streamlined configuration")
            self.config_handler.handle_streamlined_config(config_data, args, params)
        else:
            logger.debug("Entering interactive configuration")
            self.config_handler.handle_interactive_config(config_data, params)
            self.security_handler.configure_security(config_data)
    
    def _create_and_save_record(self, config_data: Dict[str, Any], params: KeeperParams, args: StreamlineArgs) -> None:
        record = self.service_config.create_record(config_data["is_advanced_security_enabled"], params, args.commands)
        config_data["records"] = [record]
        self.service_config.save_config(config_data, 'create')
        
    def _upload_and_start_service(self, params: KeeperParams, args: StreamlineArgs, config_data: Dict[str, Any]) -> None:


        print("Saved config file successfully in the .keeper folder")
        self.service_config.update_or_add_record(params)
        from ..core.service_manager import ServiceManager
        if config_data:
            print("Config data before sending it start service", config_data)
            ServiceManager.start_service(config_data)  # Pass `config_data` as fallback
        else:
            ServiceManager.start_service(args)
        