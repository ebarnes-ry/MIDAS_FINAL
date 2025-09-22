from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Literal, Union, Type
from pydantic import BaseModel
from PIL import Image

#unified model errors
class ModelError(RuntimeError): ...
class ModelTimeout(ModelError): ...
class ModelRetryable(ModelError): ...

@dataclass(frozen=True)
class ChatRequest:
    model: str
    messages: List[Dict[str, Any]]
    params: Dict[str, Any] | None = None
    schema: Optional[Type[BaseModel]] = None #pydantic model -> json schema
    #json_mode: bool = False #force format='json' if true
    extra_body: Optional[Dict[str, Any]] = None #extra body for openai/openrouter specifically for openrouter only args
    images: Optional[List[Union[str, bytes, Image.Image]]] = None #images to include in the chat

@dataclass(frozen=True)
class ModelResponse:
    content: str
    raw: Any #provider-native response obj/dict
    meta: Dict[str, Any] #timings, token  counts, model, created_at, etc.
    parsed: Optional[BaseModel] = None #populated if schema was provided

class ModelProvider(ABC):
    @abstractmethod
    def chat(self, req: ChatRequest) -> ModelResponse:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        raise NotImplementedError

