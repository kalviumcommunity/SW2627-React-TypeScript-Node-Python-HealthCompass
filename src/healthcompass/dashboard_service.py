"""Dashboard service providing real HealthCompass metrics and guidance intelligence.

Aggregates data from guidance documents, policy updates, and knowledge base status.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

from healthcompass.guidance_service import GuidanceService
from healthcompass.updates.storage import UpdateStorage, get_storage


@dataclass
class DashboardMetrics:
    """Real dashboard metrics from actual HealthCompass data."""
    totalGuidance: int
    indexedGuidance: int
    processingGuidance: int
    failedGuidance: int
    archivedGuidance: int
    recentUpdates: int
    criticalUpdates: int
    activeAlerts: int


@dataclass
class GuidanceSummary:
    """Summary of a guidance document for dashboard display."""
    id: str
    title: str
    category: str
    version: str
    authority: str
    region: str
    effectiveDate: str
    status: str
    indexedAt: Optional[str] = None


@dataclass
class UpdateSummary:
    """Summary of a policy update for dashboard display."""
    id: str
    title: str
    category: str
    severity: str
    previousVersion: str
    newVersion: str
    effectiveDate: str
    publishedAt: str
    isRead: bool


@dataclass
class CategoryCount:
    """Count of guidance documents by category."""
    category: str
    count: int


@dataclass
class KnowledgeBaseHealth:
    """Knowledge base health status."""
    indexed: int
    processing: int
    failed: int
    archived: int


@dataclass
class DashboardResponse:
    """Real data-driven dashboard response."""
    metrics: DashboardMetrics
    recentGuidance: List[GuidanceSummary]
    recentUpdates: List[UpdateSummary]
    categoryCounts: List[CategoryCount]
    knowledgeBaseHealth: KnowledgeBaseHealth

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DashboardService:
    """Service providing aggregated real dashboard metrics."""

    def __init__(self, guidance_service: Optional[GuidanceService] = None):
        self.guidance_service = guidance_service or GuidanceService()
        self.update_storage = get_storage()

    def get_dashboard(self) -> DashboardResponse:
        """Generate dashboard from real HealthCompass data."""
        # Get all guidance documents
        docs = self.guidance_service.list_documents()
        
        # Calculate real metrics
        total_guidance = len(docs)
        indexed_guidance = len([d for d in docs if d.status == "indexed"])
        processing_guidance = len([d for d in docs if d.status == "processing"])
        failed_guidance = len([d for d in docs if d.status == "failed"])
        archived_guidance = len([d for d in docs if d.status == "archived"])
        
        # Get recent updates
        updates_data = self.update_storage.get_all_updates()
        recent_updates = len(updates_data)
        critical_updates = len([u for u in updates_data if u.get('severity', '').lower() in ['critical', 'high']])
        
        # Critical alerts = critical updates (no fake alerts)
        active_alerts = critical_updates
        
        metrics = DashboardMetrics(
            totalGuidance=total_guidance,
            indexedGuidance=indexed_guidance,
            processingGuidance=processing_guidance,
            failedGuidance=failed_guidance,
            archivedGuidance=archived_guidance,
            recentUpdates=recent_updates,
            criticalUpdates=critical_updates,
            activeAlerts=active_alerts,
        )
        
        # Recent guidance (last 5 updated/indexed)
        recent_guidance = []
        for doc in docs[:5]:
            recent_guidance.append(
                GuidanceSummary(
                    id=doc.id,
                    title=doc.title,
                    category=doc.category,
                    version=doc.version,
                    authority=doc.authority,
                    region=doc.region,
                    effectiveDate=doc.effective_date,
                    status=doc.status,
                    indexedAt=doc.indexed_at,
                )
            )
        
        # Recent updates (last 5 published)
        recent_updates_list = []
        for update_data in sorted(updates_data, key=lambda u: u.get('published_at', ''), reverse=True)[:5]:
            recent_updates_list.append(
                UpdateSummary(
                    id=update_data['id'],
                    title=update_data['title'],
                    category=update_data['category'],
                    severity=update_data['severity'],
                    previousVersion=update_data['previous_version'],
                    newVersion=update_data['new_version'],
                    effectiveDate=update_data['effective_date'],
                    publishedAt=update_data['published_at'],
                    isRead=update_data.get('is_read', False),
                )
            )
        
        # Category counts (dynamically calculated)
        category_counts_map = {}
        for doc in docs:
            cat = doc.category or "General"
            category_counts_map[cat] = category_counts_map.get(cat, 0) + 1
        
        category_counts = [
            CategoryCount(category=cat, count=count)
            for cat, count in sorted(category_counts_map.items())
        ]
        
        # Knowledge base health
        knowledge_base_health = KnowledgeBaseHealth(
            indexed=indexed_guidance,
            processing=processing_guidance,
            failed=failed_guidance,
            archived=archived_guidance,
        )
        
        return DashboardResponse(
            metrics=metrics,
            recentGuidance=recent_guidance,
            recentUpdates=recent_updates_list,
            categoryCounts=category_counts,
            knowledgeBaseHealth=knowledge_base_health,
        )
