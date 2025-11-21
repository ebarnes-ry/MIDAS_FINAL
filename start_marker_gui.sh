#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading .env file..."
    export $(grep -v '^#' .env | xargs)
    echo "Environment variables loaded"
else
    echo "No .env file found"
fi

# Ensure GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ] && [ -n "$GOOGLE_API_KEY" ]; then
    export GEMINI_API_KEY="$GOOGLE_API_KEY"
    echo "Set GEMINI_API_KEY from GOOGLE_API_KEY"
fi

# Check if API key is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "GEMINI_API_KEY not set. Please check your .env file."
    exit 1
fi

echo "Starting marker GUI with API key configured..."
marker_gui
