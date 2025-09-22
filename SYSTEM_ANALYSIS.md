# MIDAS V3 System Analysis

## Executive Summary

MIDAS V3 is a three-stage mathematical document analysis pipeline that processes PDFs/images through Vision → Reasoning → Verification stages. The system uses a combination of local Ollama models and external services (Gemini) to extract mathematical problems, solve them with step-by-step reasoning, and generate/verify SymPy code.

## Architecture Overview

### High-Level Flow
```
Document Upload → Marker OCR → Vision Analysis → Reasoning → Code Generation/Verification → Results
```

### Core Components
- **FastAPI Backend**: RESTful API with FastAPI, CORS-enabled for frontend integration
- **Model Management**: Centralized ModelManager with provider abstraction (Ollama, OpenAI-compatible)
- **Pipeline Components**: Vision, Reasoning, Verification pipelines with distinct responsibilities
- **Prompt System**: Versioned Jinja2 templates with strict variable validation

## Detailed Component Analysis

### 1. Vision Pipeline (`src/pipeline/vision/`)

#### **Inputs:**
- **VisionInput**: `file_path` (str), `file_type` (str)
- **UserSelection**: `selected_block_ids` (List[str]), `edited_latex` (str), `original_image_path` (str)

#### **Processing Steps:**

1. **Document Processing** (Marker Service):
   - **Input Format**: PDF/image files
   - **Processing**: Marker library with Gemini-1.5-flash LLM enhancement
   - **Marker Configuration**:
     - `use_llm: true` with custom math block correction prompts
     - `force_ocr: true`, `strip_existing_ocr: true`
     - `disable_image_extraction: true` (LLM describes instead)
   - **Output Format**: JSONOutput with hierarchical blocks, spatial coordinates, HTML content

2. **UI Transformation**:
   - **Input**: Marker JSONOutput
   - **Process**: Flatten hierarchical structure to `UIDocument`
   - **Block Classification**: Automatically identifies editable blocks (Text, Equation, SectionHeader, etc.)
   - **Spatial Mapping**: Creates lookup maps by block ID
   - **Output**: `UIDocument` with `blocks`, `spatial_map`, `editable_blocks`, `images`, `metadata`

3. **Visual Contextualization** (VLM Analysis):
   - **Trigger Condition**: Visual blocks detected (Figure, Picture, Table, Diagram)
   - **Model**: qwen2.5vl:7b via Ollama
   - **Prompt**: vision/analyze@v1
   - **Input Variables**: `problem_text` (user's edited LaTeX)
   - **Schema Validation**: Pydantic `VisualContext` model
   - **Error Recovery**: JSON repair via qwen3:8b with vision/repair_json@v1 prompt
   - **Output Schema**:
     ```json
     {
       "elements": [{"description": str, "visual_type": enum, "data": optional}],
       "summary": str,
       "contains_essential_info": bool
     }
     ```

#### **Outputs:**
- **VisionFinalOutput**:
  - `problem_statement`: User's final edited LaTeX
  - `visual_context`: Optional VisualContext object with visual elements
  - `source_metadata`: Processing details, block counts, VLM analysis flag

#### **Failure Points:**
- Marker processing failures if document is corrupted or unsupported format
- VLM JSON parsing failures despite repair mechanism
- Block classification errors for complex mathematical content
- Image region extraction failures due to coordinate misalignment

### 2. Reasoning Pipeline (`src/pipeline/reasoning/`)

#### **Inputs:**
- **ReasoningInput**: `problem_statement` (str), `visual_context` (Optional[str]), `source_metadata` (Optional[Dict])

#### **Processing:**
- **Model**: phi4-mini-reasoning:latest via Ollama
- **Prompt**: reasoning/solve@v1
- **Template Variables**: `problem_text`, conditionally `visual_context`
- **Model Parameters**: `temperature: 0.1`, `top_p: 0.95`, `repeat_penalty: 1.1`, `timeout: 300s`

#### **Response Parsing:**
1. **Think Tag Extraction**: Regex pattern `<think>(.*?)</think>` for internal reasoning
2. **Worked Solution**: Full response with think tags removed
3. **Final Answer Extraction**: Multiple patterns including `\boxed{}`, "Answer:", "Therefore:", etc.

#### **Outputs:**
- **ReasoningOutput**:
  - `original_problem`: Copy of input problem
  - `worked_solution`: Step-by-step solution (think tags removed)
  - `final_answer`: Extracted final answer using pattern matching
  - `think_reasoning`: Internal AI reasoning from think tags
  - `processing_metadata`: Model info, prompt version, response length

#### **Failure Points:**
- Model timeout on complex problems (300s limit)
- Failed final answer extraction when solution doesn't follow expected patterns
- Think tag parsing failures if model doesn't follow format
- Visual context integration issues when VLM data is malformed

### 3. Verification Pipeline (`src/pipeline/verification/`)

#### **Inputs:**
- **ReasoningOutput**: Complete reasoning output from previous stage

#### **Processing Architecture:**

1. **SymPy Code Generation**:
   - **Model**: qwen2.5-coder:7b via Ollama
   - **Prompt**: codegen/baseline_codegen@v2
   - **Template Variables**: `reasoning` (full ReasoningOutput object)
   - **Parameters**: `temperature: 0.1`, `max_tokens: 2000`
   - **Code Extraction**: Regex patterns for `\`\`\`python`, `\`\`\``, `<code>` blocks

2. **Safe Code Execution**:
   - **Sandbox Environment**: Whitelisted builtins and SymPy imports only
   - **Resource Limits**: 300s timeout, 512MB memory limit
   - **Security**: No file system access, restricted import capabilities
   - **Output Capture**: Separate stdout/stderr streams, execution timing

3. **Error Analysis & Classification**:
   - **Error Types**: SYNTAX_ERROR, RUNTIME_ERROR, TIMEOUT, SYMBOLIC_FAILURE, etc.
   - **Completeness Checks**: Verifies final answer comparison and verification output
   - **Pattern Recognition**: Classifies errors by exception type and message content

4. **Repair System** (Up to 3 attempts):
   - **Progressive Disclosure**: More context provided with each repair attempt
   - **Error-Specific Prompts**: Tailored repair strategies per error type
   - **LLM Repair**: Uses qwen2.5-coder:7b with modified temperature (0.2)
   - **Convergence Detection**: Stops when status="verified" is achieved

#### **Confidence Scoring Algorithm:**
```
base_score = 0.3 if execution_successful else 0.0
error_penalty = min(error_count * 0.1, 0.3)
step_bonus = (verified_steps / total_steps) * 0.3
answer_bonus = 0.4 if answer_matches else -0.2 if answer_mismatch
final_confidence = max(0.0, min(1.0, base_score - error_penalty + step_bonus + answer_bonus))
```

#### **Outputs:**
- **VerificationResult**:
  - `status`: "verified"|"failed"|"partial"|"timeout"|"needs_reasoning_repair"
  - `confidence_score`: 0.0-1.0 calculated confidence
  - `reasoning_output`: Original ReasoningOutput
  - `generated_code`: Final SymPy verification code
  - `execution_result`: Detailed execution info (success, stdout, stderr, timing, namespace)
  - `step_verifications`: List of verified solution steps
  - `answer_match`: Boolean indicating if computed answer matches claimed answer
  - `errors`: Classified error list with suggested fixes
  - `repair_history`: Record of all repair attempts
  - `metadata`: Attempt count, confidence thresholds, etc.

#### **Failure Points:**
- Code generation failures when model produces non-executable code
- Timeout issues with complex symbolic computations
- Verification incompleteness when code doesn't check all solution steps
- False positives/negatives in answer matching due to format differences
- Repair system convergence failures after 3 attempts

### 4. Model Management System (`src/models/`)

#### **ModelManager Architecture:**
- **Configuration**: Single YAML file with providers, services, tasks
- **Provider Abstraction**: Unified interface for Ollama and OpenAI-compatible APIs
- **Lazy Loading**: Providers instantiated on first use
- **Performance Tracking**: Per-task latency and success rate monitoring

#### **Provider Configurations:**

1. **OllamaProvider** (Primary):
   - **Host**: http://localhost:11434
   - **Timeout**: 300s per request
   - **Keep-Alive**: 5m
   - **Retry Logic**: Exponential backoff, 3 attempts max
   - **Image Support**: Base64 encoding for vision models
   - **Response Handling**: Robust parsing for dict/object response formats

2. **OpenAI Provider** (Secondary):
   - **Base URL**: https://openrouter.ai/api/v1
   - **JSON Schema**: Structured output with Pydantic validation
   - **Image Support**: Data URL format for vision models
   - **Error Handling**: Classified retryable vs. permanent failures

3. **MarkerService** (Document Processing):
   - **LLM Integration**: Gemini-1.5-flash for enhanced OCR
   - **API Key**: Configured in YAML (security risk - hardcoded)
   - **Custom Prompts**: Math-focused block correction prompts
   - **Output Format**: JSON with spatial coordinates and HTML content

#### **Active Model Assignments:**
```yaml
vision: qwen2.5vl:7b (Ollama) - Image analysis
reasoning: phi4-mini-reasoning:latest (Ollama) - Problem solving
verification: qwen2.5-coder:7b (Ollama) - Code generation
validation: qwen2.5vl:7b (Ollama) - Content validation
json_repair: qwen3:8b (Ollama) - JSON fixing
explain_step: qwen3:8b (Ollama) - Step explanations
marker: gemini-1.5-flash (Google) - Document processing
```

#### **Failure Points:**
- Ollama service unavailability causing complete system failure
- Model loading failures if models not pulled locally
- API key exposure in configuration files
- No fallback providers for critical tasks
- Memory issues with large documents in Marker processing

### 5. Prompt System (`prompts/`)

#### **Template Structure:**
- **Versioned Directories**: `category/name/version/` (e.g., `vision/analyze/v1/`)
- **Template Files**: `system.j2` (system prompt), `user.j2` (user prompt)
- **Configuration**: Optional `config.yaml` for stop sequences, etc.
- **Variable Validation**: Jinja2 StrictUndefined prevents missing variables

#### **Active Prompt Templates:**

1. **vision/analyze@v1**:
   - **Purpose**: Extract visual elements from images
   - **Variables**: `problem_text`
   - **Output**: JSON VisualContext schema
   - **Instructions**: Identify graphs, tables, diagrams; determine essential info flag

2. **vision/validate@v1**:
   - **Purpose**: Validate mathematical content in images
   - **Variables**: None (image only)
   - **Output**: JSON with contains_math boolean and reason

3. **reasoning/solve@v1**:
   - **Purpose**: Solve mathematical problems
   - **Variables**: `problem_text`, optional `visual_context`
   - **Format**: `<think>` tags for reasoning, then worked solution
   - **Instructions**: Concise reasoning, clear final answer

4. **codegen/baseline_codegen@v2**:
   - **Purpose**: Generate SymPy verification code
   - **Variables**: `reasoning` (ReasoningOutput object)
   - **Output**: Python code with specific verification format
   - **Requirements**: Explicit imports, step verification, answer comparison

#### **Failure Points:**
- Template rendering failures with undefined variables
- Inconsistent model adherence to prompt instructions
- Version management complexity as prompts evolve
- Lack of automated prompt effectiveness testing

## Data Flow Analysis

### Complete Pipeline Data Flow

#### **1. Document Upload & Processing**
```
User File → FastAPI Upload → Image Validation (qwen2.5vl) →
Marker Processing (Gemini) → UI Transformation → UIDocument
```

**Data Transformations:**
- **File** → **PIL Image** → **Base64** → **VLM Input**
- **File** → **Temporary File** → **Marker JSONOutput** → **UIDocument**
- **JSONOutput Blocks** → **Flattened UIBlocks** → **Spatial/Editable Maps**

#### **2. Vision Analysis**
```
UserSelection + UIDocument + Source Image →
VLM Analysis (qwen2.5vl) → JSON Parsing → VisualContext → VisionFinalOutput
```

**Data Transformations:**
- **UserSelection.edited_latex** → **Prompt Variable** → **VLM Input**
- **Source Image** → **Base64** → **VLM Context**
- **VLM Response** → **JSON Parsing** → **VisualContext Object**
- **Failed JSON** → **Repair Service** → **Fixed JSON** → **VisualContext**

#### **3. Reasoning Processing**
```
VisionFinalOutput → ReasoningInput →
Reasoning Model (phi4-mini) → Response Parsing → ReasoningOutput
```

**Data Transformations:**
- **VisionFinalOutput.problem_statement** → **ReasoningInput.problem_statement**
- **VisualContext.summary** → **ReasoningInput.visual_context**
- **Model Response** → **Regex Extraction** → **Think/Solution/Answer Components**

#### **4. Verification & Code Generation**
```
ReasoningOutput → Code Generation (qwen2.5-coder) →
Safe Execution → Error Analysis → Repair Loop → VerificationResult
```

**Data Transformations:**
- **ReasoningOutput** → **Template Variables** → **Code Generation Prompt**
- **Model Response** → **Code Extraction** → **Python Code String**
- **Code String** → **AST Parsing** → **Safe Execution** → **ExecutionResult**
- **ExecutionResult** → **Error Classification** → **Repair Prompts** → **Fixed Code**

### Critical Data Dependencies

1. **Vision → Reasoning**: `problem_statement` and optional `visual_context.summary`
2. **Reasoning → Verification**: Complete `ReasoningOutput` object with all fields
3. **User Input**: `edited_latex` becomes the canonical problem statement
4. **Image Data**: Original image required for VLM analysis and cropping
5. **Block Selection**: `selected_block_ids` determines scope of analysis

### Data Format Specifications

#### **Image Data Formats:**
- **Input**: PDF, PNG, JPG files
- **Processing**: PIL Image objects
- **VLM Transmission**: Base64 encoded strings
- **Storage**: Base64 strings in session management

#### **Mathematical Content Formats:**
- **Input**: Raw HTML from Marker with potential LaTeX
- **Processing**: HTML to text extraction with math tag preservation
- **User Editing**: Plain text/LaTeX editing interface
- **Final**: Clean LaTeX problem statement

#### **Code Formats:**
- **Generation**: Python code strings with SymPy imports
- **Execution**: AST-parsed and exec() in sandboxed namespace
- **Output**: Stdout/stderr text streams with execution metadata

## System Configuration Analysis

### Configuration Files

#### **Main Configuration** (`src/config/config.yaml`):
```yaml
providers:
  ollama_local: {host: localhost:11434, timeout: 300s}
  openrouter: {base_url: openrouter.ai/api/v1}

services:
  marker: {use_llm: true, llm_service: gemini, api_key: [EXPOSED]}

tasks:
  vision: {model: qwen2.5vl:7b, prompt: vision/analyze@v1}
  reasoning: {model: phi4-mini-reasoning, prompt: reasoning/solve@v1}
  verification: {model: qwen2.5-coder:7b, prompt: codegen/baseline_codegen@v2}
```

#### **Security Issues:**
- **API Keys**: Gemini API key hardcoded in configuration file
- **No Encryption**: Configuration stored in plain text
- **File Permissions**: No restricted access to config files

#### **Performance Configuration:**
- **Timeouts**: 300s for most tasks, adequate for complex problems
- **Memory Limits**: 512MB for code execution, may be insufficient for large symbolic computations
- **Model Parameters**: Conservative temperatures (0.1) for consistency

### Deployment Configuration

#### **Development Setup:**
- **Server**: Uvicorn ASGI server with auto-reload
- **CORS**: Enabled for localhost:3000 and localhost:5173
- **Port**: 8000 for API, assumes frontend on 3000/5173

#### **Dependencies:**
- **Python**: Modern Python with FastAPI, Pydantic, PIL
- **External Services**: Ollama server, Gemini API access
- **System Dependencies**: Marker library and its requirements

## Critical Failure Points & Weaknesses

### **1. Single Points of Failure**
- **Ollama Dependency**: All local models depend on single Ollama instance
- **Gemini Dependency**: Marker processing requires external API
- **No Fallback Providers**: Task failures cascade without alternatives

### **2. Security Vulnerabilities**
- **Code Execution**: Despite sandboxing, arbitrary code execution in verification
- **API Key Exposure**: Gemini key stored in plain text configuration
- **Input Validation**: Limited validation of user-uploaded files

### **3. Performance Bottlenecks**
- **Sequential Processing**: Vision→Reasoning→Verification blocks user interaction
- **Model Loading**: No model pre-warming or connection pooling
- **Memory Usage**: No limits on document size or complexity

### **4. Error Handling Gaps**
- **Partial Failures**: System may succeed partially but return incomplete results
- **Error Propagation**: Upstream failures may cause confusing downstream errors
- **Recovery Mechanisms**: Limited automatic recovery from transient failures

### **5. Data Quality Issues**
- **Format Inconsistencies**: Multiple data transformation points introduce format drift
- **Information Loss**: OCR and VLM processing may lose mathematical nuance
- **Validation Gaps**: Insufficient validation of intermediate results

### **6. Scalability Limitations**
- **Single-Threaded**: No concurrent processing of multiple requests
- **Memory Growth**: Session management may accumulate data without cleanup
- **Model Contention**: Single Ollama instance shared across all tasks

### **7. Configuration Fragility**
- **Model Dependencies**: Assumes specific models are available locally
- **Version Coupling**: Tight coupling between prompts, models, and code
- **Environment Sensitivity**: Many hardcoded paths and assumptions

## Recommendations for Improvement

### **Immediate Actions (High Priority)**
1. **Security**: Remove hardcoded API keys, implement proper secret management
2. **Error Handling**: Add comprehensive error boundaries and user-friendly messages
3. **Validation**: Implement stricter input validation for all file uploads
4. **Monitoring**: Add detailed logging and performance monitoring

### **Short-term Improvements (Medium Priority)**
1. **Fallback Providers**: Implement backup models/providers for critical tasks
2. **Performance**: Add async processing and progress indicators
3. **Data Validation**: Strengthen intermediate result validation
4. **Configuration**: Externalize configuration with environment variables

### **Long-term Architecture (Low Priority)**
1. **Microservices**: Separate vision, reasoning, verification into independent services
2. **Queue System**: Implement async job processing with status tracking
3. **Model Management**: Add automatic model management and health checking
4. **Horizontal Scaling**: Design for multi-instance deployment

This analysis provides a comprehensive technical foundation for understanding the current system state, identifying improvement opportunities, and planning future development priorities.