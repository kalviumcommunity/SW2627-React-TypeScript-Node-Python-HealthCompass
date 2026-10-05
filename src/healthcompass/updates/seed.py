"""Seed data for policy updates and document versions."""

from datetime import datetime, timedelta
from .models import (
    PolicyUpdate,
    DocumentVersion,
    ChangedSection,
    Severity,
    UpdateCategory,
    UpdateStatus,
)
from .storage import get_storage


def seed_demo_data():
    """Populate storage with demo policy updates and document versions."""
    storage = get_storage()
    
    # Clear existing data
    storage._write_json(storage.updates_file, [])
    storage._write_json(storage.versions_file, [])
    
    # Document: Outbreak Response Guideline
    outbreak_doc_id = "doc-outbreak-001"
    
    # Version 4.1
    outbreak_v41 = DocumentVersion(
        id="version-outbreak-4.1",
        document_id=outbreak_doc_id,
        version="4.1",
        title="Outbreak Response Guideline",
        content="""
# Outbreak Response Guideline v4.1

## Section 3: Isolation Duration

Standard isolation period for confirmed cases is 10 days from symptom onset.

## Section 5: Testing Protocol

Rapid antigen testing required on day 5 and day 10.
""",
        source_file="outbreak_v4.1.pdf",
        effective_date="2026-08-01",
        published_date="2026-07-28",
        status="superseded",
    )
    storage.create_version(outbreak_v41)
    
    # Version 4.2
    outbreak_v42 = DocumentVersion(
        id="version-outbreak-4.2",
        document_id=outbreak_doc_id,
        version="4.2",
        title="Outbreak Response Guideline",
        content="""
# Outbreak Response Guideline v4.2

## Section 3: Isolation Duration

Standard isolation period for confirmed cases is 7 days upon consecutive negative rapid tests taken 24 hours apart, provided fever has resolved for >48 hours.

## Section 5: Testing Protocol

Rapid antigen testing required on day 3, day 5, and day 7.
""",
        source_file="outbreak_v4.2.pdf",
        effective_date="2026-09-15",
        published_date="2026-09-12",
        status="active",
    )
    storage.create_version(outbreak_v42)
    
    # Update: Outbreak Response Guideline v4.1 → v4.2
    outbreak_update = PolicyUpdate(
        id="update-001",
        document_id=outbreak_doc_id,
        document_title="Outbreak Response Guideline",
        previous_version_id="version-outbreak-4.1",
        new_version_id="version-outbreak-4.2",
        previous_version="4.1",
        new_version="4.2",
        category=UpdateCategory.OUTBREAK,
        severity=Severity.HIGH,
        status=UpdateStatus.PUBLISHED,
        title="Isolation Duration Updated for Acute Respiratory Syndrome",
        summary="Standard isolation period updated from 10 days to 7 days upon consecutive negative rapid tests taken 24 hours apart, provided fever has resolved for >48 hours.",
        previous_instruction="Standard isolation period for confirmed cases is 10 days from symptom onset.",
        new_instruction="Standard isolation period for confirmed cases is 7 days upon consecutive negative rapid tests taken 24 hours apart, provided fever has resolved for >48 hours.",
        changed_sections=[
            ChangedSection(
                section_name="Section 3 — Isolation Duration",
                previous_content="Standard isolation period for confirmed cases is 10 days from symptom onset.",
                new_content="Standard isolation period for confirmed cases is 7 days upon consecutive negative rapid tests taken 24 hours apart, provided fever has resolved for >48 hours.",
                change_summary="Reduced isolation period based on new evidence of viral shedding patterns.",
            ),
        ],
        effective_date="2026-09-15",
        published_at="2026-09-12T08:00:00Z",
        published_by="Regional Epidemiologist",
        authority="National Public Health Authority",
        change_reason="Updated based on WHO recommendations and regional surveillance data",
        impact="Reduces isolation burden while maintaining public safety; expected to improve compliance.",
        region="District A",
        is_read=False,
    )
    storage.create_update(outbreak_update)
    
    # Document: Pediatric & Booster Vaccination Protocol
    vaccine_doc_id = "doc-vaccine-001"
    
    # Version 5.0
    vaccine_v50 = DocumentVersion(
        id="version-vaccine-5.0",
        document_id=vaccine_doc_id,
        version="5.0",
        title="Pediatric & Booster Vaccination Protocol",
        content="""
# Pediatric & Booster Vaccination Protocol v5.0

## Section 2: Booster Intervals

Primary series: 2 doses, 4 weeks apart.
Booster dose: 6 months after primary series completion.
""",
        source_file="vaccine_v5.0.pdf",
        effective_date="2026-07-01",
        published_date="2026-06-28",
        status="superseded",
    )
    storage.create_version(vaccine_v50)
    
    # Version 5.1
    vaccine_v51 = DocumentVersion(
        id="version-vaccine-5.1",
        document_id=vaccine_doc_id,
        version="5.1",
        title="Pediatric & Booster Vaccination Protocol",
        content="""
# Pediatric & Booster Vaccination Protocol v5.1

## Section 2: Booster Intervals

Primary series: 2 doses, 4 weeks apart.
Booster dose: 3 months after primary series completion for immunocompromised patients.
Booster dose: 6 months after primary series completion for general population.
""",
        source_file="vaccine_v5.1.pdf",
        effective_date="2026-09-01",
        published_date="2026-08-28",
        status="active",
    )
    storage.create_version(vaccine_v51)
    
    # Update: Vaccination Protocol v5.0 → v5.1
    vaccine_update = PolicyUpdate(
        id="update-002",
        document_id=vaccine_doc_id,
        document_title="Pediatric & Booster Vaccination Protocol",
        previous_version_id="version-vaccine-5.0",
        new_version_id="version-vaccine-5.1",
        previous_version="5.0",
        new_version="5.1",
        category=UpdateCategory.VACCINATION,
        severity=Severity.MEDIUM,
        status=UpdateStatus.PUBLISHED,
        title="Booster Interval Adjusted for Immunocompromised Patients",
        summary="Booster dose interval reduced from 6 months to 3 months for immunocompromised patients after primary series completion.",
        previous_instruction="Booster dose: 6 months after primary series completion.",
        new_instruction="Booster dose: 3 months after primary series completion for immunocompromised patients. Booster dose: 6 months after primary series completion for general population.",
        changed_sections=[
            ChangedSection(
                section_name="Section 2 — Booster Intervals",
                previous_content="Booster dose: 6 months after primary series completion.",
                new_content="Booster dose: 3 months after primary series completion for immunocompromised patients. Booster dose: 6 months after primary series completion for general population.",
                change_summary="Reduced interval for high-risk group based on immunogenicity studies.",
            ),
        ],
        effective_date="2026-09-01",
        published_at="2026-08-28T10:30:00Z",
        published_by="National Immunization Advisory",
        authority="Ministry of Health",
        change_reason="Updated based on CDC/WHO guidance for immunocompromised populations",
        impact="Provides earlier protection for vulnerable populations.",
        region="District A",
        is_read=False,
    )
    storage.create_update(vaccine_update)
    
    # Document: PPE Standards for District High-Density Facilities
    ppe_doc_id = "doc-ppe-001"
    
    # Version 1.9
    ppe_v19 = DocumentVersion(
        id="version-ppe-1.9",
        document_id=ppe_doc_id,
        version="1.9",
        title="PPE Standards for District High-Density Facilities",
        content="""
# PPE Standards for District High-Density Facilities v1.9

## Section 4: N95 Respirator Usage

N95 respirators required for all aerosol-generating procedures.
Fit testing required annually.
""",
        source_file="ppe_v1.9.pdf",
        effective_date="2026-06-15",
        published_date="2026-06-10",
        status="superseded",
    )
    storage.create_version(ppe_v19)
    
    # Version 2.0
    ppe_v20 = DocumentVersion(
        id="version-ppe-2.0",
        document_id=ppe_doc_id,
        version="2.0",
        title="PPE Standards for District High-Density Facilities",
        content="""
# PPE Standards for District High-Density Facilities v2.0

## Section 4: N95 Respirator Usage

N95 respirators required for all aerosol-generating procedures.
Fit testing required annually and after significant weight change.
Alternative KN95 respirators acceptable when N95 supply constrained.
""",
        source_file="ppe_v2.0.pdf",
        effective_date="2026-09-20",
        published_date="2026-09-15",
        status="active",
    )
    storage.create_version(ppe_v20)
    
    # Update: PPE Standards v1.9 → v2.0
    ppe_update = PolicyUpdate(
        id="update-003",
        document_id=ppe_doc_id,
        document_title="PPE Standards for District High-Density Facilities",
        previous_version_id="version-ppe-1.9",
        new_version_id="version-ppe-2.0",
        previous_version="1.9",
        new_version="2.0",
        category=UpdateCategory.PPE,
        severity=Severity.MEDIUM,
        status=UpdateStatus.PUBLISHED,
        title="Fit Testing Requirements Expanded and KN95 Alternatives Added",
        summary="N95 fit testing now required after significant weight change. KN95 respirators acceptable as alternative when N95 supply constrained.",
        previous_instruction="Fit testing required annually.",
        new_instruction="Fit testing required annually and after significant weight change. Alternative KN95 respirators acceptable when N95 supply constrained.",
        changed_sections=[
            ChangedSection(
                section_name="Section 4 — N95 Respirator Usage",
                previous_content="Fit testing required annually.",
                new_content="Fit testing required annually and after significant weight change. Alternative KN95 respirators acceptable when N95 supply constrained.",
                change_summary="Enhanced fit testing schedule and added respirator alternatives for supply resilience.",
            ),
        ],
        effective_date="2026-09-20",
        published_at="2026-09-15T14:00:00Z",
        published_by="District Infection Control Officer",
        authority="District Health Department",
        change_reason="Addressed fit testing gaps and supply chain concerns",
        impact="Ensures proper respirator fit and provides contingency for supply shortages.",
        region="District A",
        is_read=False,
    )
    storage.create_update(ppe_update)
    
    # Archive some older updates
    archived_update = PolicyUpdate(
        id="update-archived-001",
        document_id="doc-archived-001",
        document_title="Historical Infection Control Guidelines",
        previous_version_id="version-archived-1.0",
        new_version_id="version-archived-1.1",
        previous_version="1.0",
        new_version="1.1",
        category=UpdateCategory.INFECTION_CONTROL,
        severity=Severity.LOW,
        status=UpdateStatus.ARCHIVED,
        title="Contact Tracing Protocol Update (Archived)",
        summary="Updated contact tracing procedures for non-respiratory infections.",
        previous_instruction="Contact tracing within 48 hours of exposure notification.",
        new_instruction="Contact tracing within 72 hours of exposure notification for non-respiratory infections.",
        changed_sections=[],
        effective_date="2026-05-01",
        published_at="2026-04-28T09:00:00Z",
        published_by="District Epidemiologist",
        authority="District Health Department",
        is_read=True,
    )
    storage.create_update(archived_update)
    
    print(f"[OK] Seeded {len(storage.get_all_updates())} policy updates")
    print(f"[OK] Seeded {len(storage.get_all_versions())} document versions")


if __name__ == "__main__":
    seed_demo_data()
