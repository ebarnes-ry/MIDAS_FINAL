from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Type, Dict, Any, Tuple
from enum import Enum
import yaml
import json
import jinja2
import hashlib
import importlib.util
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PromptConfig:
    #immutable prompt config
    name: str
    version: str
    system_template: str
    user_template: str
    stop_sequences: Optional[list[str]] = None

    @property
    def ref(self) -> str:
        return f"{self.name}@{self.version}"


class PromptManager:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = Path(prompts_dir)
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts dir not found: {self.prompts_dir}")
        
        self.jinja_env = jinja2.Environment(
            undefined=jinja2.StrictUndefined, #strict checking, but 'is defined' test still works
            trim_blocks=True,
            lstrip_blocks=True,
            cache_size=100, #cache compiled templates
        )
        self._cache: Dict[str, PromptConfig] = {}

    def load_prompt(self, prompt_ref: str) -> PromptConfig:
        if prompt_ref in self._cache:
            return self._cache[prompt_ref]
        
        #parse ref
        if '@' not in prompt_ref:
            raise ValueError(f"Invalid prompt reference: {prompt_ref}")
        
        path_parts, version = prompt_ref.rsplit('@', 1)
        prompt_path = self.prompts_dir / path_parts / version
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        
        config = self._load_config(prompt_path)
        system_template = self._load_template(prompt_path, "system.j2")
        user_template = self._load_template(prompt_path, "user.j2")

        prompt_config = PromptConfig(
            name=path_parts,
            version=version,
            system_template=system_template,
            user_template=user_template,
            stop_sequences=config.get('stop_sequences'),
        )

        self._cache[prompt_ref] = prompt_config
        logger.info(f"Loaded prompt: {prompt_ref}")
        return prompt_config

    def render(self, prompt_ref: str, variables: Dict[str, Any]) -> List[Dict[str, str]]:
        print(f"PromptManager.render called with prompt_ref='{prompt_ref}'")
        print(f"Variables: {list(variables.keys())}")
        
        config = self.load_prompt(prompt_ref)
        print(f"Loaded prompt config: {config.name}@{config.version}")
        
        try:
            print(f"Rendering system template...")
            system_content = self.jinja_env.from_string(config.system_template).render(**variables)
            print(f"System content rendered, length: {len(system_content)}")
            print(f"System content: {system_content[:200]}...")
            
            print(f"Rendering user template...")
            user_content = self.jinja_env.from_string(config.user_template).render(**variables)
            print(f"User content rendered, length: {len(user_content)}")
            print(f"User content: {user_content[:200]}...")
            
        except jinja2.UndefinedError as e:
            print(f"Jinja undefined error: {e}")
            raise ValueError(f"Missing required variable in prompt {prompt_ref}: {e}")
        except Exception as e:
            print(f"Template rendering error: {e}")
            raise

        messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ]
        print(f"Returning {len(messages)} messages")
        return messages

    def _load_config(self, prompt_path: Path) -> dict:
        config_path = prompt_path / "config.yaml"
        if not config_path.exists():
            return {}
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
        
    def _load_template(self, prompt_path: Path, template_name: str) -> str:
        template_path = prompt_path / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        return template_path.read_text()

    def clear_cache(self):
        self._cache.clear()
        self.jinja_env.cache.clear()
        logger.info("Cleared prompt manager caches")