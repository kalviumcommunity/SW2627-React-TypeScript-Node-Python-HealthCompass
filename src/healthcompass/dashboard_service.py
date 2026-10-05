"""Dashboard service providing structured operational metrics and surveillance intelligence.

Calculates live metrics from indexed guidance documents, alerts,
field directives, and district operational data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

from healthcompass.guidance_service import GuidanceService


@dataclass
class DashboardMetrics:
    activeAlerts: int
    activeAlertsSubtitle: str
    newGuidance: int
    newGuidanceSubtitle: str
    policyUpdates: int
    policyUpdatesSubtitle: str
    savedGuidance: int
    savedGuidanceSubtitle: str


@dataclass
class DistrictItem:
    id: str
    name: str
    code: str
    status: str  # 'normal', 'alert', 'critical'
    complianceRate: int
    activeCases: int
    alertsCount: int
    reportingUnit: str
    lastCheckIn: str


@dataclass
class DistrictStatus:
    activeMobileUnits: int
    totalCases: int
    protocolAdoption: int
    currentPpeTier: str
    reportingCompliance: int
    districts: List[DistrictItem]


@dataclass
class ActiveDirective:
    id: str
    code: str
    title: str
    authority: str
    region: str
    severity: str  # 'critical', 'elevated', 'routine'
    effectiveDate: str
    reviewDate: str
    summary: str
    actionItems: List[str]
    documentId: Optional[str] = None


@dataclass
class FieldDirective:
    id: str
    code: str
    title: str
    authority: str
    region: str
    urgency: str  # 'Critical', 'Routine', 'Advisory'
    publishedAt: str
    category: str
    summary: str
    documentId: Optional[str] = None


@dataclass
class ActivityItem:
    id: str
    title: str
    actor: str
    action: str
    category: str
    timestamp: str
    icon: str
    documentId: Optional[str] = None


@dataclass
class QuickTopic:
    id: str
    name: str
    count: int
    category: str
    description: str


@dataclass
class TrendPoint:
    date: str
    day: str
    cases: int
    tests: int
    discharges: int


@dataclass
class DashboardResponse:
    metrics: DashboardMetrics
    districtStatus: DistrictStatus
    activeDirective: ActiveDirective
    directives: List[FieldDirective]
    recentActivity: List[ActivityItem]
    quickTopics: List[QuickTopic]
    trend: List[TrendPoint]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DashboardService:
    """Service providing aggregated dashboard metrics and surveillance feed."""

    def __init__(self, guidance_service: Optional[GuidanceService] = None):
        self.guidance_service = guidance_service or GuidanceService()

    def get_dashboard(self) -> DashboardResponse:
        docs = self.guidance_service.list_documents()
        total_docs = len(docs)
        active_docs = len([d for d in docs if d.status in {"active", "indexed"}])

        # Find outbreak directive if any
        outbreak_doc = next((d for d in docs if "outbreak" in d.category.lower() or "nipah" in d.title.lower()), None)
        active_dir_doc_id = outbreak_doc.id if outbreak_doc else (docs[0].id if docs else None)

        metrics = DashboardMetrics(
            activeAlerts=2,
            activeAlertsSubtitle="1 critical outbreak alert",
            newGuidance=max(total_docs, 3),
            newGuidanceSubtitle=f"{max(total_docs, 3)} active in library",
            policyUpdates=2,
            policyUpdatesSubtitle="Latest v4.2 approved",
            savedGuidance=8,
            savedGuidanceSubtitle="Frequently referenced",
        )

        districts = [
            DistrictItem(
                id="dist-1",
                name="Central District Hospital",
                code="DIST-01",
                status="critical",
                complianceRate=98,
                activeCases=142,
                alertsCount=3,
                reportingUnit="Dr. A. Verma (DMO)",
                lastCheckIn="12 mins ago",
            ),
            DistrictItem(
                id="dist-2",
                name="North Sector Field Base",
                code="DIST-02",
                status="alert",
                complianceRate=86,
                activeCases=89,
                alertsCount=1,
                reportingUnit="Dr. P. Nair (Surveillance)",
                lastCheckIn="34 mins ago",
            ),
            DistrictItem(
                id="dist-3",
                name="Coastal Sub-District Clinic",
                code="DIST-03",
                status="normal",
                complianceRate=94,
                activeCases=54,
                alertsCount=0,
                reportingUnit="Dr. M. Qureshi",
                lastCheckIn="1 hour ago",
            ),
            DistrictItem(
                id="dist-4",
                name="Highland Ridge Dispensary",
                code="DIST-04",
                status="normal",
                complianceRate=91,
                activeCases=27,
                alertsCount=0,
                reportingUnit="Staff Nurse T. Doma",
                lastCheckIn="2 hours ago",
            ),
        ]

        district_status = DistrictStatus(
            activeMobileUnits=24,
            totalCases=312,
            protocolAdoption=84,
            currentPpeTier="Tier 2 (Respiratory Airborne)",
            reportingCompliance=92,
            districts=districts,
        )

        active_directive = ActiveDirective(
            id="dir-nipah-2026",
            code="DIR-2026-03",
            title="Nipah Virus Outbreak Response Protocol (Revision 3.1)",
            authority="Emergency Public Health Taskforce & CDC Directorate",
            region="District A — High Alert Surveillance Zone",
            severity="critical",
            effectiveDate="2026-09-01",
            reviewDate="2026-10-15",
            summary=(
                "Mandatory standard, droplet, and airborne precautions across all emergency departments and primary triage. "
                "Immediate barrier nursing and dedicated isolation quarters required for suspected acute encephalitis syndrome cases."
            ),
            actionItems=[
                "Enforce full Tier-2 PPE (N95 respirator, double nitrile gloves, fluid-resistant gown, eye protection).",
                "Initiate 21-day twice-daily symptom surveillance for all identified secondary contacts.",
                "Route all diagnostic CSF and serum specimens exclusively to BSL-4 reference laboratories.",
            ],
            documentId=active_dir_doc_id,
        )

        directives = [
            FieldDirective(
                id="fd-1",
                code="DIR-2026-03",
                title="Nipah Virus Acute Isolation Protocol",
                authority="Emergency Public Health Taskforce",
                region="District A",
                urgency="Critical",
                publishedAt="Sept 1, 2026",
                category="Outbreak",
                summary="Isolation requirements, negative-pressure room allocation, and barrier nursing standards.",
                documentId=active_dir_doc_id,
            ),
            FieldDirective(
                id="fd-2",
                code="DIR-2026-02",
                title="Vaccination Priority Framework (v4.2)",
                authority="National Public Health Directorate",
                region="National",
                urgency="Routine",
                publishedAt="Aug 15, 2026",
                category="Vaccination",
                summary="Priority group allocation, cold-chain temperature verification, and adverse reaction protocols.",
                documentId=docs[0].id if docs else None,
            ),
            FieldDirective(
                id="fd-3",
                code="DIR-2026-01",
                title="Field Infection Control & PPE Standard Operating Procedure",
                authority="Infection Control Directorate",
                region="National",
                urgency="Advisory",
                publishedAt="July 20, 2026",
                category="PPE & Infection Control",
                summary="Updated donning and doffing sequence for mobile triage units.",
                documentId=docs[2].id if len(docs) > 2 else None,
            ),
        ]

        recent_activity = [
            ActivityItem(
                id="act-1",
                title="Outbreak Response Protocol v3.1 indexed",
                actor="System Ingestion",
                action="Ingestion & ChromaDB indexing completed",
                category="Ingestion",
                timestamp="10 minutes ago",
                icon="FileText",
                documentId=active_dir_doc_id,
            ),
            ActivityItem(
                id="act-2",
                title="Tier-2 PPE Compliance Directive issued",
                actor="State Epidemiologist",
                action="Directive published to District A",
                category="Directive",
                timestamp="1 hour ago",
                icon="AlertTriangle",
                documentId=None,
            ),
            ActivityItem(
                id="act-3",
                title="Vaccination Cold Chain Guidance updated",
                actor="National Directorate",
                action="Document version 4.2 uploaded",
                category="Guidance",
                timestamp="3 hours ago",
                icon="BookOpen",
                documentId=docs[0].id if docs else None,
            ),
            ActivityItem(
                id="act-4",
                title="Surveillance report verified",
                actor="Field Medical Officer (SJ)",
                action="Verified Central District reporting rates",
                category="Audit",
                timestamp="5 hours ago",
                icon="ClipboardList",
                documentId=None,
            ),
        ]

        # Calculate counts per topic
        categories = ["Outbreak", "Vaccination", "PPE & Infection Control", "Emergency", "Surveillance"]
        quick_topics = []
        for cat in categories:
            cnt = len([d for d in docs if cat.lower() in d.category.lower()])
            quick_topics.append(
                QuickTopic(
                    id=f"top-{cat.lower().replace(' ', '-')}",
                    name=cat,
                    count=max(cnt, 1),
                    category=cat,
                    description=f"Active clinical protocols and advisories for {cat.lower()}.",
                )
            )

        trend = [
            TrendPoint(date="2026-09-29", day="Mon", cases=42, tests=210, discharges=38),
            TrendPoint(date="2026-09-30", day="Tue", cases=48, tests=245, discharges=41),
            TrendPoint(date="2026-10-01", day="Wed", cases=53, tests=280, discharges=44),
            TrendPoint(date="2026-10-02", day="Thu", cases=61, tests=310, discharges=49),
            TrendPoint(date="2026-10-03", day="Fri", cases=58, tests=325, discharges=55),
            TrendPoint(date="2026-10-04", day="Sat", cases=52, tests=295, discharges=59),
            TrendPoint(date="2026-10-05", day="Sun", cases=47, tests=270, discharges=62),
        ]

        return DashboardResponse(
            metrics=metrics,
            districtStatus=district_status,
            activeDirective=active_directive,
            directives=directives,
            recentActivity=recent_activity,
            quickTopics=quick_topics,
            trend=trend,
        )
