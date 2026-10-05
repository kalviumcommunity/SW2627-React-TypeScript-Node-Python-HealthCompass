"""Guidance document registry and management service.

Handles document metadata persistence, duplicate detection,
safe file storage, ingestion into ChromaDB, and document filtering.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, List, Optional

from healthcompass.indexing_service import index_guidance_document, IndexingError
from healthcompass.vector_store import initialize_vector_store

DOCUMENTS_DIR = Path("data/documents")
REGISTRY_FILE = Path("data/documents_registry.json")
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm"}


@dataclass
class GuidanceDocument:
    """Document record in the HealthCompass Guidance Library."""

    id: str
    title: str
    description: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    category: str
    region: str
    authority: str
    version: str
    effective_date: str
    status: str  # 'processing', 'indexed', 'failed', 'archived'
    chunk_count: int = 0
    page_count: int = 1
    tags: List[str] = field(default_factory=list)
    file_hash: str = ""
    embedding_provider: str = "local"
    embedding_model: str = ""
    vector_dimension: int = 0
    indexed_at: str = ""
    processing_time_ms: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GuidanceDocument:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class GuidanceService:
    """Service managing document storage, registry, and ingestion."""

    def __init__(self, documents_dir: Path = DOCUMENTS_DIR, registry_file: Path = REGISTRY_FILE):
        self.documents_dir = documents_dir
        self.registry_file = registry_file
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_registry()
        self._seed_default_guidance_if_empty()

    def _ensure_registry(self) -> None:
        if not self.registry_file.exists():
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_registry([])

    def _load_registry(self) -> List[GuidanceDocument]:
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [GuidanceDocument.from_dict(d) for d in data]
        except Exception:
            return []

    def _save_registry(self, docs: List[GuidanceDocument]) -> None:
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump([d.to_dict() for d in docs], f, indent=2)

    def _seed_default_guidance_if_empty(self) -> None:
        """Seed initial official public health guidance documents so the library starts populated."""
        docs = self._load_registry()
        if docs:
            return

        # Create seeded guidelines in data/documents
        seed_items = [
            {
                "title": "National Vaccination Priority Framework",
                "filename": "vaccination_priority_v4.2.txt",
                "description": "Standard operating guidelines for priority tier allocation, cold-chain temperature control, and adverse reaction surveillance.",
                "category": "Vaccination",
                "region": "National",
                "authority": "National Public Health Directorate",
                "version": "4.2",
                "effective_date": "2026-08-15",
                "tags": ["Vaccination", "Cold Chain", "Priority Tiers", "Surveillance"],
                "content": (
                    "National Vaccination Priority Framework (Version 4.2)\n"
                    "Issuing Authority: National Public Health Directorate\n"
                    "Effective Date: August 15, 2026\n\n"
                    "Section 1: Priority Groups\n"
                    "Tier 1 includes frontline healthcare workers, emergency responders, and critical clinical staff. "
                    "Tier 2 includes adults aged 65 and older, individuals with severe comorbidities, and immunocompromised patients. "
                    "Tier 3 encompasses essential public transit, sanitation, and municipal personnel.\n\n"
                    "Section 2: Storage and Cold-Chain Protocols\n"
                    "Ultra-cold formulations must be maintained at -80C to -60C. Standard refrigerated vaccines require steady 2C to 8C monitoring. "
                    "Any temperature excursion exceeding 30 minutes must trigger an immediate quarantine of the affected lot and report to regional depot.\n\n"
                    "Section 3: Dosing and Adverse Reactions\n"
                    "Recipients must be observed for 15 minutes post-injection (30 minutes for history of anaphylaxis). "
                    "Emergency epinephrine autoinjectors (1:1000) must be available at all vaccination points."
                ),
            },
            {
                "title": "Nipah Virus Outbreak Response Protocol",
                "filename": "nipah_outbreak_protocol_2026.txt",
                "description": "Critical response protocol for suspected Henipavirus outbreaks, isolation procedures, contact tracing, and barrier nursing standards.",
                "category": "Outbreak",
                "region": "District A",
                "authority": "Emergency Public Health Taskforce",
                "version": "3.1",
                "effective_date": "2026-09-01",
                "tags": ["Outbreak", "Nipah", "Isolation", "PPE", "Surveillance"],
                "content": (
                    "Nipah Virus Outbreak Response Protocol 2026-03\n"
                    "Issuing Authority: Emergency Public Health Taskforce\n"
                    "Effective Date: September 1, 2026\n\n"
                    "Section 1: Case Definition and Clinical Presentation\n"
                    "Suspected case: Acute fever, altered mental status, acute respiratory distress, or severe headache following exposure to endemic fauna or suspected case contacts. "
                    "Confirmed case: Laboratory confirmation via RT-PCR or viral isolation in approved BSL-4 facility.\n\n"
                    "Section 2: Infection Prevention & Control (IPC)\n"
                    "Standard, droplet, and airborne precautions are mandatory. Healthcare staff must wear N95/FFP3 respirators, double nitrile gloves, fluid-resistant gowns, and full face shields. "
                    "Suspect cases must be placed immediately in negative pressure isolation rooms or well-ventilated single rooms separated by at least 2 meters.\n\n"
                    "Section 3: Contact Tracing and Quarantine\n"
                    "High-risk contacts must undergo strict home or institutional quarantine for 21 days with twice-daily temperature surveillance. "
                    "Immediate hospital transfer is required if body temperature exceeds 38.0C."
                ),
            },
            {
                "title": "Field Infection Control & PPE SOP",
                "filename": "field_ppe_sop_tier2.txt",
                "description": "Standard operating procedures for Personal Protective Equipment (PPE) don/doff procedures in primary care and mobile health clinics.",
                "category": "PPE & Infection Control",
                "region": "National",
                "authority": "Infection Control Directorate",
                "version": "2.0",
                "effective_date": "2026-07-20",
                "tags": ["PPE", "Donning", "Doffing", "Mobile Clinic", "Primary Care"],
                "content": (
                    "Field Infection Control & PPE Standard Operating Procedure\n"
                    "Issuing Authority: Infection Control Directorate\n"
                    "Effective Date: July 20, 2026\n\n"
                    "Section 1: Donning Sequence\n"
                    "1. Perform hand hygiene (alcohol rub for 20 seconds).\n"
                    "2. Don gown, securing ties at neck and waist.\n"
                    "3. Don N95/FFP2 respirator; perform positive/negative seal check.\n"
                    "4. Don eye protection / face shield.\n"
                    "5. Don gloves, pulling cuff over gown sleeves.\n\n"
                    "Section 2: Doffing Sequence (Critical Risk of Contamination)\n"
                    "1. Remove gloves using glove-in-glove technique; perform hand hygiene.\n"
                    "2. Remove gown by peeling forward from shoulders, rolling inside out.\n"
                    "3. Perform hand hygiene.\n"
                    "4. Remove face shield touching only straps from behind.\n"
                    "5. Remove respirator touching only elastic bands.\n"
                    "6. Perform comprehensive hand hygiene and exit isolation anteroom."
                ),
            },
        ]

        seeded_docs = []
        for item in seed_items:
            file_path = self.documents_dir / item["filename"]
            content = item["content"].encode("utf-8")
            file_path.write_bytes(content)
            doc_id = f"doc_{sha256(item['filename'].encode()).hexdigest()[:12]}"
            doc = GuidanceDocument(
                id=doc_id,
                title=item["title"],
                description=item["description"],
                filename=item["filename"],
                file_path=str(file_path.relative_to(Path("."))) if file_path.is_relative_to(Path(".")) else str(file_path),
                file_size=len(content),
                mime_type="text/plain",
                category=item["category"],
                region=item["region"],
                authority=item["authority"],
                version=item["version"],
                effective_date=item["effective_date"],
                status="processing",
                chunk_count=0,
                page_count=1,
                tags=item["tags"],
                file_hash=sha256(content).hexdigest(),
                embedding_provider="local",
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
            seeded_docs.append(doc)

        self._save_registry(seeded_docs)

        # Index seeded docs into ChromaDB vector store using canonical pipeline
        try:
            collection = initialize_vector_store()
            for doc in seeded_docs:
                try:
                    index_guidance_document(doc, Path(doc.file_path), collection=collection)
                except Exception as e:
                    print(f"Warning: Failed to index seeded doc '{doc.title}': {e}")
                    doc.status = "failed"
                    doc.error_message = str(e)
            self._save_registry(seeded_docs)
        except Exception as e:
            print(f"Warning: Failed to initialize vector store for seeded docs: {e}")
            for doc in seeded_docs:
                doc.status = "failed"
                doc.error_message = f"Vector store initialization failed: {e}"
            self._save_registry(seeded_docs)

    def list_documents(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        region: Optional[str] = None,
    ) -> List[GuidanceDocument]:
        """List documents matching filters."""
        docs = self._load_registry()

        if status and status.lower() != "all":
            docs = [d for d in docs if d.status.lower() == status.lower()]

        if category and category.lower() != "all":
            docs = [d for d in docs if d.category.lower() == category.lower()]

        if region and region.lower() != "all":
            docs = [d for d in docs if d.region.lower() == region.lower()]

        if search and search.strip():
            q = search.lower().strip()
            docs = [
                d
                for d in docs
                if q in d.title.lower()
                or q in d.description.lower()
                or q in d.authority.lower()
                or q in d.category.lower()
                or q in d.region.lower()
                or q in d.filename.lower()
                or any(q in t.lower() for t in d.tags)
            ]

        # Sort with active/indexed first, newest updated first
        docs.sort(key=lambda d: d.updated_at or d.created_at, reverse=True)
        return docs

    def get_document(self, document_id: str) -> Optional[GuidanceDocument]:
        """Get a document by ID."""
        for doc in self._load_registry():
            if doc.id == document_id:
                return doc
        return None

    def check_duplicate(self, file_bytes: bytes, filename: str) -> Optional[GuidanceDocument]:
        """Check if a file with identical SHA256 or filename already exists."""
        file_hash = sha256(file_bytes).hexdigest()
        for doc in self._load_registry():
            if doc.file_hash == file_hash or doc.filename == filename:
                return doc
        return None

    def _update_document_in_registry(self, doc: GuidanceDocument) -> None:
        """Update or insert a document record in the registry file."""
        docs = [d for d in self._load_registry() if d.id != doc.id]
        docs.append(doc)
        self._save_registry(docs)

    def add_document(
        self,
        file_bytes: bytes,
        filename: str,
        title: str,
        category: str,
        description: str = "",
        region: str = "National",
        authority: str = "Ministry of Health",
        version: str = "1.0",
        effective_date: str = "",
        tags: Optional[List[str]] = None,
    ) -> GuidanceDocument:
        """Save document file, create registry entry, and index into ChromaDB."""
        # 1. Validate inputs
        if not title or not title.strip():
            raise ValueError("Document title is required.")
        if not category or not category.strip():
            raise ValueError("Category is required.")

        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format '{suffix}'. Supported formats are: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB.")

        # 2. Check duplicates
        existing = self.check_duplicate(file_bytes, filename)
        if existing and existing.status in {"indexed", "active"}:
            return existing

        # 3. Determine safe filename and storage path
        file_hash = sha256(file_bytes).hexdigest()
        clean_name = f"{Path(filename).stem}_{file_hash[:8]}{suffix}"
        target_path = self.documents_dir / clean_name
        target_path.write_bytes(file_bytes)

        # 4. Generate unique document ID
        doc_id = f"doc_{file_hash[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        doc = GuidanceDocument(
            id=doc_id,
            title=title.strip() or Path(filename).stem.replace("_", " ").title(),
            description=description.strip(),
            filename=filename,
            file_path=str(target_path.relative_to(Path("."))),
            file_size=len(file_bytes),
            mime_type="application/pdf" if suffix == ".pdf" else "text/plain",
            category=category or "General",
            region=region or "National",
            authority=authority or "National Public Health Authority",
            version=version or "1.0",
            effective_date=effective_date or now_str[:10],
            status="processing",
            chunk_count=0,
            page_count=1,
            tags=tags or [],
            file_hash=file_hash,
            created_at=now_str,
            updated_at=now_str,
        )

        # Save record with 'processing' state before indexing starts
        self._update_document_in_registry(doc)

        # 5. Ingest and Index via canonical indexing service
        try:
            index_guidance_document(doc, target_path)
        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            doc.updated_at = datetime.now(timezone.utc).isoformat()

        # Update registry with final state (indexed or failed)
        self._update_document_in_registry(doc)
        return doc

    def archive_document(self, document_id: str) -> Optional[GuidanceDocument]:
        """Mark document as archived."""
        docs = self._load_registry()
        target = None
        for doc in docs:
            if doc.id == document_id:
                doc.status = "archived"
                doc.updated_at = datetime.now(timezone.utc).isoformat()
                target = doc
                break
        if target:
            self._save_registry(docs)
        return target

    def reindex_document(self, document_id: str) -> Optional[GuidanceDocument]:
        """Re-run ingestion on document file."""
        doc = self.get_document(document_id)
        if not doc:
            return None

        file_path = Path(doc.file_path)
        if not file_path.exists():
            doc.status = "failed"
            doc.error_message = f"Document file not found on disk: {doc.file_path}"
            doc.updated_at = datetime.now(timezone.utc).isoformat()
            self._update_document_in_registry(doc)
            return doc

        # Mark as processing
        doc.status = "processing"
        doc.error_message = None
        doc.updated_at = datetime.now(timezone.utc).isoformat()
        self._update_document_in_registry(doc)

        # Ingest and Index via canonical indexing service
        try:
            index_guidance_document(doc, file_path)
        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            doc.updated_at = datetime.now(timezone.utc).isoformat()

        # Save final state in registry
        self._update_document_in_registry(doc)
        return doc
