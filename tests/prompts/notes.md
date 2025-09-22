Core Functionality
1. Load a prompt by reference - vision/analyze@v1 → PromptConfig
2. Render templates with variables - Variables in, messages out
3. Auto-inject schema hints - For HINT and JSON and STRICT modes only
4. Handle missing variables - Fail clearly when template needs a var you didn't provide
5. Cache prompts - Load once, reuse many times

Schema Modes (actual use cases)
NONE - No schema anywhere (reasoning tasks)
HINT - Schema in prompt, no enforcement (experimentation)
JSON - Schema in prompt + JSON validation with format = 'json' (structured output)
STRICT - Provider-enforced schema with .model_json_schema() on pydantic schema (guaranteed structure)

Error Cases That Matter
Missing prompt files - Clear error when prompt doesn't exist
Invalid schema.py - Clear error when Schema class is wrong
Template errors - Clear error for malformed Jinja2