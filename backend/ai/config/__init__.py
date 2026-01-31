"""
AI Configuration Module
=======================
Centralized configuration management for all AI models.
Load hyperparameters from YAML files instead of hardcoding.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Config directory
CONFIG_DIR = Path(__file__).parent
HYPERPARAMS_FILE = CONFIG_DIR / "hyperparameters.yaml"


class ConfigManager:
    """
    Centralized configuration manager for AI models.
    
    Usage:
        from ai.config import config
        
        # Get intent classifier config
        lr = config.get("intent_classifier.training.learning_rate")
        
        # Get with default
        epochs = config.get("intent_classifier.training.epochs", default=10)
        
        # Get entire section
        training_config = config.get_section("intent_classifier.training")
    """
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            if HYPERPARAMS_FILE.exists():
                with open(HYPERPARAMS_FILE, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                logger.info(f"Loaded config from {HYPERPARAMS_FILE}")
            else:
                logger.warning(f"Config file not found: {HYPERPARAMS_FILE}")
                self._config = {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = {}
    
    def reload(self):
        """Reload configuration from file"""
        self._load_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Dot-separated key (e.g., "intent_classifier.training.learning_rate")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Dot-separated section path
            
        Returns:
            Dictionary of section config
        """
        result = self.get(section, {})
        return result if isinstance(result, dict) else {}
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        Get complete configuration for a model.
        
        Args:
            model_name: Name of the model (e.g., "intent_classifier")
            
        Returns:
            Complete model configuration
        """
        return self.get_section(model_name)
    
    def get_training_config(self, model_name: str) -> Dict[str, Any]:
        """Get training configuration for a model"""
        return self.get_section(f"{model_name}.training")
    
    def get_optimizer_config(self, model_name: str) -> Dict[str, Any]:
        """Get optimizer configuration for a model"""
        return self.get_section(f"{model_name}.optimizer")
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value (runtime only, not persisted).
        
        Args:
            key: Dot-separated key
            value: Value to set
        """
        keys = key.split(".")
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, filepath: Optional[str] = None):
        """
        Save current configuration to YAML file.
        
        Args:
            filepath: Optional custom filepath
        """
        save_path = Path(filepath) if filepath else HYPERPARAMS_FILE
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Saved config to {save_path}")
    
    @property
    def global_config(self) -> Dict[str, Any]:
        """Get global settings"""
        return self.get_section("global")
    
    @property
    def seed(self) -> int:
        """Get random seed"""
        return self.get("global.seed", 42)
    
    @property
    def device(self) -> str:
        """Get device setting"""
        return self.get("global.device", "auto")


# Singleton instance
config = ConfigManager()


# Convenience functions
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value"""
    return config.get(key, default)


def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get model configuration"""
    return config.get_model_config(model_name)


def get_hyperparams(model_name: str) -> Dict[str, Any]:
    """
    Get hyperparameters for a model as a flat dictionary.
    
    Returns:
        Dict with keys: learning_rate, batch_size, epochs, etc.
    """
    model_config = config.get_model_config(model_name)
    
    # Flatten training and optimizer configs
    hyperparams = {}
    
    if "training" in model_config:
        hyperparams.update(model_config["training"])
    
    if "optimizer" in model_config:
        hyperparams["optimizer_type"] = model_config["optimizer"].get("type", "adam")
        hyperparams["optimizer_config"] = model_config["optimizer"]
    
    if "scheduler" in model_config:
        hyperparams["scheduler_type"] = model_config["scheduler"].get("type", "linear")
        hyperparams["scheduler_config"] = model_config["scheduler"]
    
    if "model" in model_config:
        hyperparams["model_config"] = model_config["model"]
    
    return hyperparams


__all__ = [
    "config",
    "ConfigManager",
    "get_config",
    "get_model_config",
    "get_hyperparams",
]
