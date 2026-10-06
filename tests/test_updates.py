"""Tests for policy updates and document versioning."""

import pytest
from pathlib import Path
import tempfile
import shutil

from healthcompass.updates import (
    PolicyUpdate,
    DocumentVersion,
    ChangedSection,
    Severity,
    UpdateCategory,
    UpdateStatus,
    UpdateStorage,
    get_storage,
)
from healthcompass.updates.diff import generate_text_diff, get_diff_summary


@pytest.fixture
def temp_storage():
    """Create a temporary storage instance for testing."""
    temp_dir = tempfile.mkdtemp()
    storage = UpdateStorage(data_dir=temp_dir)
    yield storage
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestDocumentVersion:
    """Tests for DocumentVersion model."""

    def test_document_version_creation(self):
        """Test creating a document version."""
        version = DocumentVersion(
            id="version-001",
            document_id="doc-001",
            version="1.0",
            title="Test Document",
            content="Test content",
            source_file="test.pdf",
            effective_date="2026-01-01",
            published_date="2026-01-01",
            status="active",
        )
        assert version.id == "version-001"
        assert version.document_id == "doc-001"
        assert version.version == "1.0"
        assert version.title == "Test Document"
        assert version.status == "active"

    def test_document_version_defaults(self):
        """Test document version with default values."""
        version = DocumentVersion(
            id="version-002",
            document_id="doc-002",
            version="2.0",
            title="Test Document 2",
            content="Test content 2",
        )
        assert version.source_file is None
        assert version.effective_date is None
        assert version.published_date is None
        assert version.status == "active"


class TestPolicyUpdate:
    """Tests for PolicyUpdate model."""

    def test_policy_update_creation(self):
        """Test creating a policy update."""
        update = PolicyUpdate(
            id="update-001",
            document_id="doc-001",
            document_title="Test Document",
            previous_version_id="version-001",
            new_version_id="version-002",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.OUTBREAK,
            severity=Severity.HIGH,
            status=UpdateStatus.PUBLISHED,
            title="Test Update",
            summary="Test summary",
            previous_instruction="Previous instruction",
            new_instruction="New instruction",
            published_by="Test Author",
            authority="Test Authority",
        )
        assert update.id == "update-001"
        assert update.category == UpdateCategory.OUTBREAK
        assert update.severity == Severity.HIGH
        assert update.status == UpdateStatus.PUBLISHED
        assert update.is_read is False

    def test_policy_update_with_changed_sections(self):
        """Test policy update with changed sections."""
        section = ChangedSection(
            section_name="Section 1",
            previous_content="Old content",
            new_content="New content",
            change_summary="Summary of change",
        )
        update = PolicyUpdate(
            id="update-002",
            document_id="doc-002",
            document_title="Test Document 2",
            previous_version_id="version-003",
            new_version_id="version-004",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.VACCINATION,
            severity=Severity.MEDIUM,
            status=UpdateStatus.PUBLISHED,
            title="Test Update 2",
            summary="Test summary 2",
            previous_instruction="Previous instruction 2",
            new_instruction="New instruction 2",
            changed_sections=[section],
        )
        assert len(update.changed_sections) == 1
        assert update.changed_sections[0].section_name == "Section 1"


class TestUpdateStorage:
    """Tests for UpdateStorage."""

    def test_create_and_retrieve_version(self, temp_storage):
        """Test creating and retrieving a document version."""
        version = DocumentVersion(
            id="version-001",
            document_id="doc-001",
            version="1.0",
            title="Test Document",
            content="Test content",
        )
        created = temp_storage.create_version(version)
        assert created.id == version.id

        retrieved = temp_storage.get_version_by_id("version-001")
        assert retrieved is not None
        assert retrieved.id == "version-001"
        assert retrieved.title == "Test Document"

    def test_create_duplicate_version_raises_error(self, temp_storage):
        """Test that creating duplicate version raises error."""
        version = DocumentVersion(
            id="version-001",
            document_id="doc-001",
            version="1.0",
            title="Test Document",
            content="Test content",
        )
        temp_storage.create_version(version)
        with pytest.raises(ValueError, match="already exists"):
            temp_storage.create_version(version)

    def test_get_versions_by_document(self, temp_storage):
        """Test retrieving all versions of a document."""
        version1 = DocumentVersion(
            id="version-001",
            document_id="doc-001",
            version="1.0",
            title="Test Document",
            content="Test content 1",
        )
        version2 = DocumentVersion(
            id="version-002",
            document_id="doc-001",
            version="2.0",
            title="Test Document",
            content="Test content 2",
        )
        version3 = DocumentVersion(
            id="version-003",
            document_id="doc-002",
            version="1.0",
            title="Different Document",
            content="Different content",
        )

        temp_storage.create_version(version1)
        temp_storage.create_version(version2)
        temp_storage.create_version(version3)

        versions = temp_storage.get_versions_by_document("doc-001")
        assert len(versions) == 2
        assert all(v.document_id == "doc-001" for v in versions)

    def test_create_and_retrieve_update(self, temp_storage):
        """Test creating and retrieving a policy update."""
        update = PolicyUpdate(
            id="update-001",
            document_id="doc-001",
            document_title="Test Document",
            previous_version_id="version-001",
            new_version_id="version-002",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.OUTBREAK,
            severity=Severity.HIGH,
            status=UpdateStatus.PUBLISHED,
            title="Test Update",
            summary="Test summary",
            previous_instruction="Previous instruction",
            new_instruction="New instruction",
        )
        created = temp_storage.create_update(update)
        assert created.id == update.id

        retrieved = temp_storage.get_update_by_id("update-001")
        assert retrieved is not None
        assert retrieved.id == "update-001"
        assert retrieved.title == "Test Update"

    def test_create_duplicate_update_raises_error(self, temp_storage):
        """Test that creating duplicate update raises error."""
        update = PolicyUpdate(
            id="update-001",
            document_id="doc-001",
            document_title="Test Document",
            previous_version_id="version-001",
            new_version_id="version-002",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.OUTBREAK,
            severity=Severity.HIGH,
            status=UpdateStatus.PUBLISHED,
            title="Test Update",
            summary="Test summary",
            previous_instruction="Previous instruction",
            new_instruction="New instruction",
        )
        temp_storage.create_update(update)
        with pytest.raises(ValueError, match="already exists"):
            temp_storage.create_update(update)

    def test_update_update(self, temp_storage):
        """Test updating an existing policy update."""
        update = PolicyUpdate(
            id="update-001",
            document_id="doc-001",
            document_title="Test Document",
            previous_version_id="version-001",
            new_version_id="version-002",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.OUTBREAK,
            severity=Severity.HIGH,
            status=UpdateStatus.PUBLISHED,
            title="Test Update",
            summary="Test summary",
            previous_instruction="Previous instruction",
            new_instruction="New instruction",
        )
        temp_storage.create_update(update)

        updated = temp_storage.update_update("update-001", {"is_read": True})
        assert updated is not None
        assert updated.is_read is True

    def test_delete_update(self, temp_storage):
        """Test deleting a policy update."""
        update = PolicyUpdate(
            id="update-001",
            document_id="doc-001",
            document_title="Test Document",
            previous_version_id="version-001",
            new_version_id="version-002",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.OUTBREAK,
            severity=Severity.HIGH,
            status=UpdateStatus.PUBLISHED,
            title="Test Update",
            summary="Test summary",
            previous_instruction="Previous instruction",
            new_instruction="New instruction",
        )
        temp_storage.create_update(update)

        deleted = temp_storage.delete_update("update-001")
        assert deleted is True

        retrieved = temp_storage.get_update_by_id("update-001")
        assert retrieved is None

    def test_get_updates_by_category(self, temp_storage):
        """Test filtering updates by category."""
        update1 = PolicyUpdate(
            id="update-001",
            document_id="doc-001",
            document_title="Test Document",
            previous_version_id="version-001",
            new_version_id="version-002",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.OUTBREAK,
            severity=Severity.HIGH,
            status=UpdateStatus.PUBLISHED,
            title="Test Update",
            summary="Test summary",
            previous_instruction="Previous instruction",
            new_instruction="New instruction",
        )
        update2 = PolicyUpdate(
            id="update-002",
            document_id="doc-002",
            document_title="Test Document 2",
            previous_version_id="version-003",
            new_version_id="version-004",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.VACCINATION,
            severity=Severity.MEDIUM,
            status=UpdateStatus.PUBLISHED,
            title="Test Update 2",
            summary="Test summary 2",
            previous_instruction="Previous instruction 2",
            new_instruction="New instruction 2",
        )

        temp_storage.create_update(update1)
        temp_storage.create_update(update2)

        outbreak_updates = temp_storage.get_updates_by_category(UpdateCategory.OUTBREAK)
        assert len(outbreak_updates) == 1
        assert outbreak_updates[0].category == UpdateCategory.OUTBREAK

    def test_search_updates(self, temp_storage):
        """Test searching updates."""
        update1 = PolicyUpdate(
            id="update-001",
            document_id="doc-001",
            document_title="Isolation Guidelines",
            previous_version_id="version-001",
            new_version_id="version-002",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.OUTBREAK,
            severity=Severity.HIGH,
            status=UpdateStatus.PUBLISHED,
            title="Isolation Duration Updated",
            summary="Updated isolation period from 10 days to 7 days",
            previous_instruction="Isolation period: 10 days",
            new_instruction="Isolation period: 7 days",
        )
        update2 = PolicyUpdate(
            id="update-002",
            document_id="doc-002",
            document_title="Vaccination Protocol",
            previous_version_id="version-003",
            new_version_id="version-004",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.VACCINATION,
            severity=Severity.MEDIUM,
            status=UpdateStatus.PUBLISHED,
            title="Booster Interval Changed",
            summary="Booster interval reduced",
            previous_instruction="Booster: 6 months",
            new_instruction="Booster: 3 months",
        )

        temp_storage.create_update(update1)
        temp_storage.create_update(update2)

        results = temp_storage.search_updates("isolation")
        assert len(results) == 1
        assert "isolation" in results[0].title.lower()

    def test_get_unread_updates(self, temp_storage):
        """Test retrieving unread updates."""
        update1 = PolicyUpdate(
            id="update-001",
            document_id="doc-001",
            document_title="Test Document",
            previous_version_id="version-001",
            new_version_id="version-002",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.OUTBREAK,
            severity=Severity.HIGH,
            status=UpdateStatus.PUBLISHED,
            title="Test Update",
            summary="Test summary",
            previous_instruction="Previous instruction",
            new_instruction="New instruction",
            is_read=False,
        )
        update2 = PolicyUpdate(
            id="update-002",
            document_id="doc-002",
            document_title="Test Document 2",
            previous_version_id="version-003",
            new_version_id="version-004",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.VACCINATION,
            severity=Severity.MEDIUM,
            status=UpdateStatus.PUBLISHED,
            title="Test Update 2",
            summary="Test summary 2",
            previous_instruction="Previous instruction 2",
            new_instruction="New instruction 2",
            is_read=True,
        )

        temp_storage.create_update(update1)
        temp_storage.create_update(update2)

        unread = temp_storage.get_unread_updates()
        assert len(unread) == 1
        assert unread[0].id == "update-001"

    def test_mark_update_as_read(self, temp_storage):
        """Test marking an update as read."""
        update = PolicyUpdate(
            id="update-001",
            document_id="doc-001",
            document_title="Test Document",
            previous_version_id="version-001",
            new_version_id="version-002",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.OUTBREAK,
            severity=Severity.HIGH,
            status=UpdateStatus.PUBLISHED,
            title="Test Update",
            summary="Test summary",
            previous_instruction="Previous instruction",
            new_instruction="New instruction",
            is_read=False,
        )
        temp_storage.create_update(update)

        success = temp_storage.mark_update_as_read("update-001")
        assert success is True

        retrieved = temp_storage.get_update_by_id("update-001")
        assert retrieved is not None
        assert retrieved.is_read is True

    def test_get_archived_updates(self, temp_storage):
        """Test retrieving archived updates."""
        update1 = PolicyUpdate(
            id="update-001",
            document_id="doc-001",
            document_title="Test Document",
            previous_version_id="version-001",
            new_version_id="version-002",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.OUTBREAK,
            severity=Severity.HIGH,
            status=UpdateStatus.PUBLISHED,
            title="Test Update",
            summary="Test summary",
            previous_instruction="Previous instruction",
            new_instruction="New instruction",
        )
        update2 = PolicyUpdate(
            id="update-002",
            document_id="doc-002",
            document_title="Test Document 2",
            previous_version_id="version-003",
            new_version_id="version-004",
            previous_version="1.0",
            new_version="2.0",
            category=UpdateCategory.VACCINATION,
            severity=Severity.MEDIUM,
            status=UpdateStatus.ARCHIVED,
            title="Test Update 2",
            summary="Test summary 2",
            previous_instruction="Previous instruction 2",
            new_instruction="New instruction 2",
        )

        temp_storage.create_update(update1)
        temp_storage.create_update(update2)

        archived = temp_storage.get_archived_updates()
        assert len(archived) == 1
        assert archived[0].status == UpdateStatus.ARCHIVED


class TestDiffGeneration:
    """Tests for diff generation utilities."""

    def test_generate_text_diff_simple(self):
        """Test simple text diff."""
        previous = "Old text here"
        new = "New text here"
        diff = generate_text_diff(previous, new)

        assert len(diff) > 0
        assert any(c.type == "removed" for c in diff)
        assert any(c.type == "added" for c in diff)

    def test_generate_text_diff_no_change(self):
        """Test diff with no changes."""
        text = "Same text here"
        diff = generate_text_diff(text, text)

        # Should only have unchanged changes
        assert all(c.type == "unchanged" for c in diff)

    def test_generate_text_diff_complete_replacement(self):
        """Test diff with complete replacement."""
        previous = "Completely different old text"
        new = "Completely different new text"
        diff = generate_text_diff(previous, new)

        removed = [c for c in diff if c.type == "removed"]
        added = [c for c in diff if c.type == "added"]
        assert len(removed) > 0
        assert len(added) > 0

    def test_get_diff_summary(self):
        """Test diff summary calculation."""
        previous = "Old text here"
        new = "New text here"
        summary = get_diff_summary(previous, new)

        assert "total_changes" in summary
        assert "added_count" in summary
        assert "removed_count" in summary
        assert "unchanged_count" in summary
        assert "change_percentage" in summary
        assert summary["total_changes"] > 0

    def test_get_diff_summary_no_change(self):
        """Test diff summary with no changes."""
        text = "Same text here"
        summary = get_diff_summary(text, text)

        assert summary["total_changes"] == 0
        assert summary["change_percentage"] == 0


class TestGlobalStorage:
    """Tests for global storage instance."""

    def test_get_storage_returns_instance(self):
        """Test that get_storage returns an instance."""
        storage = get_storage()
        assert isinstance(storage, UpdateStorage)

    def test_get_storage_returns_same_instance(self):
        """Test that get_storage returns the same instance."""
        storage1 = get_storage()
        storage2 = get_storage()
        assert storage1 is storage2
