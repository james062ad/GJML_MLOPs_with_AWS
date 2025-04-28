# TODO: confirm I can remove this.
import os
import yaml
from typing import Any, Optional


#----current code ----
class ConfigLoader:
    _config = None

    @classmethod
    def load_config(cls, config_name: str):
        """
        Loads the configuration file from the config/ directory.
        This method caches the configuration to avoid reloading multiple times.
        """
        if cls._config is None:
            # Determine the base path of the configuration directory
            config_path = os.path.join(
                os.path.dirname(__file__), "../config", f"{config_name}.yaml"
            )

            # Load the YAML config file
            with open(config_path, "r") as file:
                cls._config = yaml.safe_load(file)

        return cls._config

    @classmethod
    def get_config_value(cls, key: str, default: Any = None) -> Optional[Any]:
        """
        Retrieve a specific config value from the loaded configuration.
        """
        if cls._config is None:
            raise ValueError("Configuration not loaded. Please call load_config first.")

        return cls._config.get(key, default)

#----AWS code ----
# class ConfigLoader:
#     _config = None
# 
#     @classmethod
#     def load_config(cls, config_name: str):
#         """
#         Loads the configuration file from the config/ directory and handles Bedrock settings.
#         """
#         if cls._config is None:
#             config_path = os.path.join(
#                 os.path.dirname(__file__), "../config", f"{config_name}.yaml"
#             )
# 
#             with open(config_path, "r") as file:
#                 cls._config = yaml.safe_load(file)
# 
#             # Handle Bedrock configuration
#             if cls._config.get("generation", {}).get("model") == "bedrock":
#                 from server.src.config import settings
#                 gen_config = cls._config.get("generation", {})
#                 
#                 # Update Bedrock settings
#                 if hasattr(settings, "bedrock_model_id"):
#                     settings.bedrock_model_id = gen_config.get("bedrock_model_id")
#                 if hasattr(settings, "aws_region"):
#                     settings.aws_region = gen_config.get("aws_region")
# 
#         return cls._config
# 
#     @classmethod
#     def get_config_value(cls, key: str, default: Any = None) -> Optional[Any]:
#         """
#         Retrieve config values with special handling for Bedrock settings.
#         """
#         if cls._config is None:
#             raise ValueError("Configuration not loaded. Please call load_config first.")
# 
#         # Handle Bedrock-specific keys
#         if key in ["bedrock_model_id", "aws_region"]:
#             return cls._config.get("generation", {}).get(key, default)
#         elif key == "model_type":
#             return cls._config.get("generation", {}).get("model", default)
# 
#         return cls._config.get(key, default)
# 
#     @classmethod
#     def is_using_bedrock(cls) -> bool:
#         """Check if AWS Bedrock is enabled in config."""
#         if cls._config is None:
#             raise ValueError("Configuration not loaded. Please call load_config first.")
#         return cls._config.get("generation", {}).get("model") == "bedrock"
