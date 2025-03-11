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

import getpass
from typing import Dict, Any
from keepercommander.api import login
from keepercommander.params import KeeperParams
from configparser import ConfigParser
from pathlib import Path

from keepercommander.service.config.service_config import ServiceConfig
# from ..config.service_config import ServiceConfig
from ..decorators.logging import logger, debug_decorator
from ..util.exceptions import ValidationError

class ServiceConfigHandler:
    def __init__(self, service_config: ServiceConfig):
        self.service_config = service_config
        self.config = ConfigParser()
        # config_path = Path(__file__).parent.parent / 'config' / 'config.ini'
        home_dir = Path.home()
        keeper_dir = home_dir / ".keeper"
        keeper_dir.mkdir(parents=True, exist_ok=True)  #  Create ~/.keeper if missing

        config_ini_path = keeper_dir / 'config.ini'

        self.config.read(config_ini_path)
        self.messages = self.config['Messages']
        self.validation_messages = self.config['Validation_Messages']
        self.params  = None

    @debug_decorator
    def handle_streamlined_config(self, config_data: Dict[str, Any], args, params: KeeperParams) -> None:
        config_data.update({
            "port": self.service_config.validator.validate_port(args.port),
            "ngrok": "y" if args.ngrok else "n",
            "ngrok_auth_token": (
                self.service_config.validator.validate_ngrok_token(args.ngrok)
                if args.ngrok else ""
            ),
            "username": self.service_config.validator.validate_username(args.username, params),
            "password": args.password
        })

    @debug_decorator
    def handle_interactive_config(self, config_data: Dict[str, Any], params: KeeperParams) -> None:
        self.params = params
        self._configure_port(config_data)
        self._configure_ngrok(config_data)
        self._configure_username(config_data, params)
        self._configure_password(config_data)
        
    def _configure_port(self, config_data: Dict[str, Any]) -> None:
        while True:
            try:
                port = input(self.messages['port_prompt'])
                logger.debug(f"Validating port: {port}")
                config_data["port"] = self.service_config.validator.validate_port(port)
                break
            except ValidationError as e:
                print(f"{self.validation_messages['invalid_port']} {str(e)}")

    def _configure_ngrok(self, config_data: Dict[str, Any]) -> None:
        config_data["ngrok"] = self.service_config._get_yes_no_input(self.messages['ngrok_prompt'])
        
        if config_data["ngrok"] == "y":
            while True:
                try:
                    token = input(self.messages['ngrok_token_prompt'])
                    config_data["ngrok_auth_token"] = self.service_config.validator.validate_ngrok_token(token)
                    break
                except ValidationError as e:
                    print(f"{self.validation_messages['invalid_ngrok_token']} {str(e)}")
        else:
            config_data["ngrok_auth_token"] = ""

    def _configure_username(self, config_data: Dict[str, Any], params) -> None:
        while True:
            try:
                username = input(self.messages['username'])
                logger.debug(f"Validating username: {username}")
                config_data["username"] = self.service_config.validator.validate_username(username, params)
                break
            except ValidationError as e:
                print(f"{self.validation_messages['invalid_username']} {str(e)}")

    def _configure_password(self, config_data: Dict[str, Any]) -> None:
        while True:
            try:
                # password = input(self.messages['password'])
                password = getpass.getpass(prompt="Enter Password: ")
                logger.debug(f"Validating password: {password}")

                if not password:  #  Check if input is empty
                    print("Error: Password cannot be empty. Please enter a valid password.")
                    continue  # Ask for input again
                config_data["password"] = password
                break
            except ValidationError as e:
                print(f"{self.validation_messages['invalid_password']} {str(e)}")