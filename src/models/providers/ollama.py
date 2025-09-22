from __future__ import annotations
from typing import Any, Dict, List, Optional
import time
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception
from pydantic import ValidationError
from ollama import Client, ResponseError
from .base import ModelProvider, ChatRequest, ModelResponse, ModelError, ModelRetryable, ModelTimeout
from ...utils.image_converter import to_base64

RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504}

def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError, httpx.RemoteProtocolError)):
        return True
    if isinstance(exc, ResponseError):
        try:
            return int(getattr(exc, "status_code", 0)) in RETRYABLE_STATUS
        except Exception:
            return False
    return isinstance(exc, ModelRetryable)

class OllamaProvider(ModelProvider):
    def __init__(self, host: str = "http://localhost:11434", request_timeout_s: float = 300, keep_alive: str = "5m"):
        self.client = Client(host=host, timeout=request_timeout_s)
        self.keep_alive = keep_alive
        self.host = host
        self.request_timeout_s = request_timeout_s

    def _process_messages(self, messages: List[Dict[str, Any]], images: Optional[List[Any]]) -> List[Dict[str, Any]]:
        if not images: return messages
        base64_images = [to_base64(img) for img in images]
        processed_messages = []
        images_added = False
        for msg in messages:
            if msg.get("role") == "user" and not images_added:
                processed_msg = msg.copy()
                processed_msg["images"] = base64_images
                processed_messages.append(processed_msg)
                images_added = True
            else:
                processed_messages.append(msg)
        return processed_messages

    @retry(reraise=True, wait=wait_exponential_jitter(initial=0.5, max=4), stop=stop_after_attempt(3), retry=retry_if_exception(_is_retryable))
    def chat(self, req: ChatRequest) -> ModelResponse:
        options = dict(req.params or {})
        keep_alive = options.pop('keep_alive', self.keep_alive)
        
        custom_timeout = options.pop('timeout', self.request_timeout_s)
        client = Client(host=self.host, timeout=custom_timeout) if custom_timeout != self.request_timeout_s else self.client

        messages = self._process_messages(req.messages, req.images)
        json_format = "json" if req.schema else None
        
        t0 = time.perf_counter()
        
        try:
            response = client.chat(
                model=req.model,
                messages=messages,
                options=options,
                format=json_format,
                keep_alive=keep_alive
            )
        except httpx.ReadTimeout as e:
            raise ModelTimeout(f"Ollama timeout after {custom_timeout}s: {e}") from e
        except ResponseError as e:
            msg = str(e)
            if _is_retryable(e): raise ModelRetryable(msg) from e
            raise ModelError(msg) from e
        except Exception as e:
            raise ModelError(f"Ollama request failed: {e}") from e

        dt = time.time() - t0

        # === ROBUST CONTENT EXTRACTION LOGIC ===
        # The ollama client is inconsistent. Sometimes it returns a dict,
        # sometimes an object. We handle both.
        content = ""
        model_name = req.model
        raw_response_dict = {}

        if isinstance(response, dict):
            # Handle dictionary response
            raw_response_dict = response
            if 'message' in response and isinstance(response.get('message'), dict):
                content = response['message'].get('content', '')
            model_name = response.get('model', req.model)
        elif hasattr(response, 'message') and hasattr(response.message, 'content'):
            # Handle object response (like Pydantic model or dataclass)
            content = response.message.content
            model_name = getattr(response, 'model', req.model)
            # Attempt to convert object to dict for metadata
            try:
                raw_response_dict = response.__dict__
            except AttributeError:
                raw_response_dict = {} # Can't convert, so we'll have less metadata
        else:
            # If the structure is completely unknown, raise an error.
            raise ModelError(f"Received unexpected response structure from Ollama: {response}")

        meta = {"provider": "ollama", "model": model_name, "latency": dt}
        for key in ['total_duration', 'load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration']:
            if key in raw_response_dict:
                meta[key] = raw_response_dict[key]

        parsed = None
        if req.schema and content:
            try:
                parsed = req.schema.model_validate_json(content)
            except ValidationError as ve:
                meta["validation_error"] = f"Failed to validate JSON: {ve}. Raw content: {content[:500]}"
                print(f"SCHEMA VALIDATION FAILED for model {model_name}: {ve}")

        return ModelResponse(content=content, raw=response, meta=meta, parsed=parsed)
    
    def health_check(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception:
            return False