"""Storage layer for policy updates and document versions."""

import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .models import PolicyUpdate, DocumentVersion, UpdateCategory, Severity, UpdateStatus


class UpdateStorage:
    """File-based storage for policy updates and document versions."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.updates_file = self.data_dir / "policy_updates.json"
        self.versions_file = self.data_dir / "document_versions.json"
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Create storage files if they don't exist."""
        if not self.updates_file.exists():
            self._write_json(self.updates_file, [])
        if not self.versions_file.exists():
            self._write_json(self.versions_file, [])
    
    def _read_json(self, file_path: Path) -> list:
        """Read JSON file safely."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _write_json(self, file_path: Path, data: list):
        """Write JSON file safely."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Update methods
    
    def create_update(self, update: PolicyUpdate) -> PolicyUpdate:
        """Create a new policy update."""
        updates = self.get_all_updates()
        
        # Check if update with same id exists
        if any(u['id'] == update.id for u in updates):
            raise ValueError(f"Update with id {update.id} already exists")
        
        updates.append(update.model_dump())
        self._write_json(self.updates_file, updates)
        return update
    
    def get_all_updates(self) -> List[dict]:
        """Get all policy updates."""
        return self._read_json(self.updates_file)
    
    def get_update_by_id(self, update_id: str) -> Optional[PolicyUpdate]:
        """Get a specific update by ID."""
        updates = self.get_all_updates()
        for update_data in updates:
            if update_data['id'] == update_id:
                return PolicyUpdate(**update_data)
        return None
    
    def update_update(self, update_id: str, update_data: dict) -> Optional[PolicyUpdate]:
        """Update an existing policy update."""
        updates = self.get_all_updates()
        for i, update in enumerate(updates):
            if update['id'] == update_id:
                update.update(update_data)
                update['updated_at'] = datetime.utcnow().isoformat()
                self._write_json(self.updates_file, updates)
                return PolicyUpdate(**update)
        return None
    
    def delete_update(self, update_id: str) -> bool:
        """Delete a policy update."""
        updates = self.get_all_updates()
        original_length = len(updates)
        updates = [u for u in updates if u['id'] != update_id]
        if len(updates) < original_length:
            self._write_json(self.updates_file, updates)
            return True
        return False
    
    def get_updates_by_category(self, category: UpdateCategory) -> List[PolicyUpdate]:
        """Get updates filtered by category."""
        updates = self.get_all_updates()
        return [PolicyUpdate(**u) for u in updates if u.get('category') == category.value]
    
    def search_updates(self, query: str) -> List[PolicyUpdate]:
        """Search updates by title, summary, or content."""
        updates = self.get_all_updates()
        query_lower = query.lower()
        results = []
        for update_data in updates:
            searchable_text = " ".join([
                update_data.get('title', ''),
                update_data.get('summary', ''),
                update_data.get('previous_instruction', ''),
                update_data.get('new_instruction', ''),
                update_data.get('document_title', ''),
            ]).lower()
            if query_lower in searchable_text:
                results.append(PolicyUpdate(**update_data))
        return results
    
    def get_unread_updates(self) -> List[PolicyUpdate]:
        """Get all unread updates."""
        updates = self.get_all_updates()
        return [PolicyUpdate(**u) for u in updates if not u.get('is_read', False)]
    
    def mark_update_as_read(self, update_id: str) -> bool:
        """Mark an update as read."""
        return self.update_update(update_id, {'is_read': True}) is not None
    
    def get_archived_updates(self) -> List[PolicyUpdate]:
        """Get archived updates."""
        updates = self.get_all_updates()
        return [PolicyUpdate(**u) for u in updates if u.get('status') == UpdateStatus.ARCHIVED.value]
    
    # Version methods
    
    def create_version(self, version: DocumentVersion) -> DocumentVersion:
        """Create a new document version."""
        versions = self.get_all_versions()
        
        # Check if version with same id exists
        if any(v['id'] == version.id for v in versions):
            raise ValueError(f"Version with id {version.id} already exists")
        
        versions.append(version.model_dump())
        self._write_json(self.versions_file, versions)
        return version
    
    def get_all_versions(self) -> List[dict]:
        """Get all document versions."""
        return self._read_json(self.versions_file)
    
    def get_version_by_id(self, version_id: str) -> Optional[DocumentVersion]:
        """Get a specific version by ID."""
        versions = self.get_all_versions()
        for version_data in versions:
            if version_data['id'] == version_id:
                return DocumentVersion(**version_data)
        return None
    
    def get_versions_by_document(self, document_id: str) -> List[DocumentVersion]:
        """Get all versions of a specific document."""
        versions = self.get_all_versions()
        return [DocumentVersion(**v) for v in versions if v.get('document_id') == document_id]
    
    def get_latest_version(self, document_id: str) -> Optional[DocumentVersion]:
        """Get the latest version of a document."""
        versions = self.get_versions_by_document(document_id)
        if not versions:
            return None
        # Sort by version string (simple version comparison)
        # For production, use proper semantic versioning
        return sorted(versions, key=lambda v: v.version, reverse=True)[0]


# Global storage instance
_storage_instance: Optional[UpdateStorage] = None


def get_storage() -> UpdateStorage:
    """Get the global storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = UpdateStorage()
    return _storage_instance
