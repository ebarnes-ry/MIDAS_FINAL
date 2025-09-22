# Complete Pipeline Integration

This document describes the newly integrated complete pipeline functionality that chains Vision → Reasoning → Code Generation.

## Overview

The complete pipeline now processes mathematical documents through three main stages:

1. **Vision Analysis**: Processes document with Marker and VLM analysis
2. **Reasoning**: AI reasoning to solve the mathematical problem
3. **Code Generation**: Generates SymPy code from the reasoning output

## New API Endpoints

### Complete Pipeline
- `POST /api/v1/vision/complete` - Runs the entire pipeline in one request

### Individual Stages
- `POST /api/v1/reasoning/reason` - Reasoning processing only
- `POST /api/v1/codegen/generate` - Code generation only

## Frontend Changes

### New Components
- `PipelineResults.tsx` - Results page with collapsible sections
- `PipelineLoading.tsx` - Loading component showing current stage

### Updated Components
- `FullVisionPipeline.tsx` - Now uses complete pipeline instead of just vision analysis
- `SimpleAPIService.ts` - Added `runCompletePipeline()` method

### New Processing Stages
- `thinking` - AI is analyzing the problem
- `solving` - AI is working through the solution
- `writing_code` - AI is generating SymPy code

## Data Flow

```
Document Upload → Vision Analysis → Reasoning → Code Generation → Results Display
```

### Vision Output
- Problem statement (edited LaTeX)
- Visual context (if applicable)
- Source metadata

### Reasoning Output
- Original problem
- Worked solution (step-by-step)
- Final answer
- Think reasoning (internal AI process)

### Code Generation Output
- Generated SymPy code
- Processing metadata

## Results Page Layout

The results page displays:

**Left Column:**
- Problem statement
- Collapsible thinking process
- Collapsible worked solution
- Final answer (highlighted)

**Right Column:**
- Collapsible generated SymPy code
- Processing details and timing
- Visual context (if available)

## Usage

1. Upload a document (PDF/image)
2. Select relevant blocks
3. Edit the LaTeX content if needed
4. Click "Analyze" to run the complete pipeline
5. View results with collapsible sections

## Configuration

All processing settings are configured in `config.yaml`:
- Model selection for each stage
- Prompt templates
- Processing parameters

The pipeline automatically uses the configured models for each stage without requiring frontend configuration.
