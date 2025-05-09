#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys

from jsonschema import validate, ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
from ruamel.yaml.scanner import ScannerError


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description='Validate configuration files against a schema.')
    parser.add_argument('config_file', help='Path to the configuration file (JSON or YAML).')
    parser.add_argument('schema_file', help='Path to the schema file (JSON or YAML).')
    parser.add_argument('--config_type', choices=['json', 'yaml'], help='Specify config file type (JSON or YAML).  If not specified, it will try to guess from extension.')
    parser.add_argument('--schema_type', choices=['json', 'yaml'], help='Specify schema file type (JSON or YAML).  If not specified, it will try to guess from extension.')
    parser.add_argument('--log_level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Set the logging level.')

    return parser

def load_json(file_path):
    """
    Loads JSON data from a file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: The loaded JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {file_path}: {e}")
        raise

def load_yaml(file_path):
    """
    Loads YAML data from a file.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict: The loaded YAML data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ruamel.yaml.parser.ParserError: If the file contains invalid YAML.
        ruamel.yaml.scanner.ScannerError: If the file contains invalid YAML.
    """
    yaml = YAML(typ='safe') # Use safe load to prevent arbitrary code execution
    try:
        with open(file_path, 'r') as f:
            data = yaml.load(f)
        return data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except (ParserError, ScannerError) as e:
        logging.error(f"Invalid YAML in {file_path}: {e}")
        raise

def validate_config(config_data, schema_data):
    """
    Validates a configuration against a schema using jsonschema.

    Args:
        config_data (dict): The configuration data.
        schema_data (dict): The schema data.

    Returns:
        bool: True if the configuration is valid, False otherwise.

    Raises:
        jsonschema.exceptions.ValidationError: If the configuration is invalid according to the schema.
    """
    try:
        validate(instance=config_data, schema=schema_data)
        logging.info("Configuration is valid according to the schema.")
        return True
    except ValidationError as e:
        logging.error(f"Configuration is invalid: {e}")
        raise

def determine_file_type(file_path, arg_type=None):
    """
    Determines the file type (JSON or YAML) based on the file extension or argument.

    Args:
        file_path (str): The path to the file.
        arg_type (str, optional): File type specified as a CLI argument. Defaults to None.

    Returns:
        str: 'json' or 'yaml'

    Raises:
        ValueError: If the file type cannot be determined.
    """
    if arg_type:
        return arg_type
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.json']:
        return 'json'
    elif ext in ['.yaml', '.yml']:
        return 'yaml'
    else:
        raise ValueError(f"Could not determine file type for {file_path}.  Specify with --config_type or --schema_type.")

def main():
    """
    Main function to parse arguments, load files, and validate the configuration.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    try:
        # Determine file types
        try:
            config_type = determine_file_type(args.config_file, args.config_type)
        except ValueError as e:
            logging.error(e)
            sys.exit(1)

        try:
            schema_type = determine_file_type(args.schema_file, args.schema_type)
        except ValueError as e:
            logging.error(e)
            sys.exit(1)

        # Load configuration and schema files
        if config_type == 'json':
            config_data = load_json(args.config_file)
        elif config_type == 'yaml':
            config_data = load_yaml(args.config_file)
        else:
            logging.error("Invalid config file type.")
            sys.exit(1)

        if schema_type == 'json':
            schema_data = load_json(args.schema_file)
        elif schema_type == 'yaml':
            schema_data = load_yaml(args.schema_file)
        else:
            logging.error("Invalid schema file type.")
            sys.exit(1)

        # Validate the configuration
        validate_config(config_data, schema_data)
        logging.info("Validation successful.")
        sys.exit(0)

    except FileNotFoundError:
        sys.exit(1)
    except (json.JSONDecodeError, ParserError, ScannerError):
        sys.exit(1)
    except ValidationError:
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()