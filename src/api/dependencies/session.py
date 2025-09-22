"""
Session management for document processing.

This handles storing processed documents in memory during a user session,
allowing the frontend to reference documents by ID for selections and edits.
"""

import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass

from src.pipeline.vision.types import UIDocument
from src.models.manager import ModelManager


@dataclass
class DocumentSession:
    """Represents a document processing session."""
    document_id: str
    ui_document: UIDocument  # Your existing UIDocument from pipeline
    original_image_base64: str
    created_at: datetime
    last_accessed: datetime
    processing_metadata: Dict[str, any]

class SessionManager:
    """
    Thread-safe in-memory session storage.
    
    In production, you might want to use Redis or a database,
    but in-memory is fine for development and small-scale deployment.
    """
    
    def __init__(self, session_timeout_minutes: int = 60):
        self._sessions: Dict[str, DocumentSession] = {}
        self._lock = threading.Lock()
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
    
    def create_session(
        self, 
        ui_document: UIDocument, 
        original_image_base64: str,
        processing_metadata: Dict[str, any] = None
    ) -> str:
        """Create a new document session and return its ID."""
        document_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        session = DocumentSession(
            document_id=document_id,
            ui_document=ui_document,
            original_image_base64=original_image_base64,
            created_at=now,
            last_accessed=now,
            processing_metadata=processing_metadata or {}
        )
        
        with self._lock:
            # Clean up expired sessions before adding new one
            self._cleanup_expired_sessions()
            self._sessions[document_id] = session
        
        return document_id
    
    def get_session(self, document_id: str) -> Optional[DocumentSession]:
        """Retrieve a document session by ID."""
        with self._lock:
            session = self._sessions.get(document_id)
            if session:
                # Update last accessed time
                session.last_accessed = datetime.utcnow()
                
                # Check if session has expired
                if datetime.utcnow() - session.created_at > self.session_timeout:
                    del self._sessions[document_id]
                    return None
                    
            return session
    
    def delete_session(self, document_id: str) -> bool:
        """Delete a document session."""
        with self._lock:
            return self._sessions.pop(document_id, None) is not None
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions (called with lock held)."""
        now = datetime.utcnow()
        expired_ids = [
            doc_id for doc_id, session in self._sessions.items()
            if now - session.created_at > self.session_timeout
        ]
        
        for doc_id in expired_ids:
            del self._sessions[doc_id]
        
        if expired_ids:
            print(f"🧹 Cleaned up {len(expired_ids)} expired document sessions")
    
    def get_stats(self) -> Dict[str, any]:
        """Get session manager statistics."""
        with self._lock:
            return {
                "active_sessions": len(self._sessions),
                "timeout_minutes": self.session_timeout.total_seconds() / 60,
                "oldest_session_age": (
                    min(
                        (datetime.utcnow() - session.created_at).total_seconds() 
                        for session in self._sessions.values()
                    ) if self._sessions else 0
                )
            }

# Global session manager instance
session_manager = SessionManager()

# FastAPI dependency functions
def get_session_manager() -> SessionManager:
    """FastAPI dependency to get the session manager."""
    return session_manager

def get_model_manager() -> ModelManager:
    """FastAPI dependency to get the model manager from app state."""
    from ..main import app_state
    return app_state["model_manager"]