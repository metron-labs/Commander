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

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from configparser import ConfigParser
from keepercommander.params import KeeperParams
from .file_handler import ConfigFormatHandler
from ..decorators.logging import logger, debug_decorator
from ..util.exceptions import ValidationError
from .models import ServiceConfigData

class ServiceConfig:
    def __init__(self, title: str = 'Commander Service Mode'):
        self.title = title
        
        self.config = ConfigParser()

        home_dir = Path.home()
        keeper_dir = home_dir / ".keeper"
        keeper_dir.mkdir(parents=True, exist_ok=True)  #  Create ~/.keeper if missing

        config_ini_path = keeper_dir / 'config.ini'
        self.config.read(config_ini_path)

        # config_ini_path = Path(__file__).parent / 'config.ini'
        # self.config.read(config_ini_path)
        
        self.messages = self.config['Messages']

        self.validation_messages = self.config['Validation_Messages']

        self.format_handler = ConfigFormatHandler(
            config_dir=keeper_dir,
            messages=self.messages,
            validation_messages=self.validation_messages
        )
        self.config_path = self.format_handler.config_path

        self._validator = None
        self._cli_handler = None
        self._command_validator = None
        self._record_handler = None

    @property
    def validator(self):
        if self._validator is None:
            from .config_validation import ConfigValidator
            self._validator = ConfigValidator()
        return self._validator

    @property
    def cli_handler(self):
        if self._cli_handler is None:
            from .cli_handler import CommandHandler
            self._cli_handler = CommandHandler()
        return self._cli_handler

    @property
    def command_validator(self):
        if self._command_validator is None:
            from .command_validator import CommandValidator
            self._command_validator = CommandValidator()
        return self._command_validator

    @property
    def record_handler(self):
        if self._record_handler is None:
            from .record_handler import RecordHandler
            self._record_handler = RecordHandler()
        return self._record_handler

    @debug_decorator
    def create_default_config(self) -> Dict[str, Any]:
        """Create default configuration structure."""
        config = ServiceConfigData(
            title=self.title,
            port=None,
            ngrok="n",
            ngrok_auth_token="",
            ngrok_public_url="",
            is_advanced_security_enabled="n",
            username="",
            password=None,
            rate_limiting="",
            ip_denied_list="",
            encryption="",
            encryption_private_key="",
            records=[]
        ).__dict__
        return config

    def save_config(self, config_data: Dict[str, Any], save_type: str = None) -> Path:
        """Save configuration to file."""
        self._validate_config_structure(config_data)
        return self.format_handler.save_config(config_data, save_type)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        config = self.format_handler.load_config()
        self._validate_config_structure(config)
        return config

    @debug_decorator
    def _validate_config_structure(self, config: Dict[str, Any]) -> None:
        """Validate the configuration structure."""
        try:
            config_data = ServiceConfigData(**config)
        except TypeError as e:
            raise ValidationError(f"Invalid configuration structure: {str(e)}")

        if config_data.ngrok == 'y':
            logger.debug("Validating ngrok configuration")
            self.validator.validate_ngrok_token(config_data.ngrok_auth_token)

        if config_data.is_advanced_security_enabled == 'y':
            logger.debug("Validating advanced security settings")
            self.validator.validate_rate_limit(config_data.rate_limiting)
            self.validator.validate_ip_list(config_data.ip_denied_list)

        if config_data.encryption == 'y':
            logger.debug("Validating encryption settings")
            self.validator.validate_encryption_key(config_data.encryption_private_key)

    def _get_yes_no_input(self, prompt: str) -> str:
        logger.debug(f"Requesting y/n input with prompt: {prompt}")
        while True:
            if (user_input := input(prompt).lower()) in ['y', 'n']:
                logger.debug(f"Received valid input: {user_input}")
                return user_input
            print(self.validation_messages['invalid_input'])

    def validate_command_list(self, commands: str, params: KeeperParams = None) -> str:
        """Validate command list against available Keeper Commander commands."""
        if not commands:
            raise ValidationError("Command list cannot be empty")
        help_output = self.cli_handler.get_help_output(params)
        valid_commands, command_info = self.command_validator.parse_help_output(help_output)
        validated_commands, invalid_commands = self.command_validator.validate_command_list(commands, valid_commands)
        
        if invalid_commands:
            error_msg = self.command_validator.generate_command_error_message(invalid_commands, command_info)
            raise ValidationError(error_msg)

        return validated_commands

    def _get_validated_commands(self, params: KeeperParams) -> str:
        """Get and validate command list from user input."""
        while True:
            try:
                command_list = input(self.messages['command_list_prompt'])
                return self.validate_command_list(command_list, params)
            except ValidationError as e:
                print(f"\nError: {str(e)}")
                print("\nPlease try again with valid commands.")

    def create_record(self, is_advanced_security_enabled: str, params: KeeperParams, commands: Optional[str] = None) -> Dict[str, Any]:
        """Create a new configuration record."""
        commands = self.validate_command_list(commands, params) if commands else self._get_validated_commands(params)
        return self.record_handler.create_record(is_advanced_security_enabled, commands)

    def update_or_add_record(self, params: KeeperParams) -> None:
        """Update existing record or add new one."""
        self.record_handler.update_or_add_record(params, self.title, self.format_handler.config_path)

    def remove_password_from_service_config(self):
        """Loads `service_config.json` from `~/.keeper/`, removes the stored password, and saves it back."""

        config_path = Path.home() / ".keeper" / "service_config.json"

        if not config_path.exists():
            print(f" Error: {config_path} not found.")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            if "password" in config_data:
                config_data["password"] = None  # or "" if you prefer empty string

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)

            print(f" Password removed from {config_path}")

        except Exception as e:
            print(f" Error modifying {config_path}: {str(e)}")

