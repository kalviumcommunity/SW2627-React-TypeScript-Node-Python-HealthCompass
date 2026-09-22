# 🧭 HealthCompass

### AI-Powered Public Health Guidance & Outbreak Intelligence Platform

> **Navigate changing public health guidance with confidence.**

## Problem Statement

A public health agency publishes outbreak guidelines, vaccination protocols, and advisories that update rapidly, but field workers cannot confirm the current correct guidance during fast-moving situations.

This creates a real operational risk: staff may rely on outdated instructions, uncertain regional guidance, or unofficial sources when time-sensitive decisions are needed. HealthCompass addresses this by centralizing approved guidance, tracking document versions, and retrieving the most relevant, up-to-date information with source-grounded answers.

HealthCompass is a full-stack AI-powered platform designed to help **public health and frontline health workers quickly find, understand, and verify current official health guidance** during rapidly changing outbreak situations.

Public health agencies continuously publish and update outbreak guidelines, vaccination protocols, emergency advisories, standard operating procedures, and regional health instructions. These resources are often distributed across PDFs, websites, circulars, and other repositories.

During a fast-moving situation, the real challenge is not simply finding information. It is determining:

- Which guidance is current?
- Which version is applicable?
- Does it apply to my region?
- What changed from the previous version?
- Where did this recommendation come from?

HealthCompass addresses this problem through:

**Official Documents → Document Intelligence → Version Control → Semantic Search → RAG → Source Verification → Guidance Alerts**

---

# 📌 Table of Contents

- [Overview](#-overview)
- [Problem](#-problem)
- [Solution](#-solution)
- [Key Features](#-key-features)
- [Product Workflow](#-product-workflow)
- [How RAG Works](#-how-rag-works)
- [AI Safety](#-ai-safety)
- [User Roles](#-user-roles)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Core Modules](#-core-modules)
- [Data Model](#-data-model)
- [API Overview](#-api-overview)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Running Locally](#-running-locally)
- [Docker Setup](#-docker-setup)
- [Document Ingestion](#-document-ingestion)
- [AI / RAG Configuration](#-ai--rag-configuration)
- [Example Workflow](#-example-workflow)
- [Testing](#-testing)
- [AI Evaluation](#-ai-evaluation)
- [Security & Privacy](#-security--privacy)
- [Project Roadmap](#-project-roadmap)
- [8-Week Development Plan](#-8-week-development-plan)
- [Contribution Guidelines](#-contribution-guidelines)
- [Pull Request Guidelines](#-pull-request-guidelines)
- [Branching Strategy](#-branching-strategy)
- [Future Scope](#-future-scope)
- [Disclaimer](#-disclaimer)
- [Author](#-author)
- [License](#-license)

---

# 🔎 Overview

HealthCompass is designed as a **trusted information access layer** between official public health guidance and the workers who need that guidance in the field.

Instead of manually searching through multiple documents, a worker can ask:

> **"What is the current isolation guidance for suspected cases in District A?"**

HealthCompass retrieves the most relevant approved guidance, considers version and regional metadata, and presents a concise answer with the underlying source.

### Core Principle

> **The AI explains the guidance; it does not invent the guidance.**

---

# 🚨 Problem

Public health information changes rapidly.

A single disease or outbreak may have:

- Multiple guideline versions
- Different regional policies
- Updated vaccination protocols
- Emergency advisories
- Revised operational procedures

Field workers may have access to all of these documents but still have difficulty determining which one is currently applicable.

### Common Problems

- Information is distributed across multiple sources.
- Old documents remain accessible.
- Document versions are difficult to compare.
- Important instructions may be buried in lengthy PDFs.
- Regional applicability is unclear.
- Manual searching is slow.
- Unofficial information may be mixed with official guidance.

### Result

```text
Fragmented Guidance
        ↓
Manual Searching
        ↓
Confusion / Delay
        ↓
Risk of Using Outdated Guidance
```

---

# 💡 Solution

HealthCompass centralizes approved public health documents and adds an intelligent layer for retrieval and verification.

```text
                OFFICIAL GUIDANCE
                       │
                       ▼
              ┌─────────────────┐
              │ Document Upload │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ Version Control │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ Document Parser │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ Vector Indexing │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ Intelligent RAG │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ Source-Cited AI │
              └────────┬────────┘
                       ▼
               FIELD WORKER
```

---

# ✨ Key Features

## 🔐 Authentication & Role-Based Access

HealthCompass supports authenticated access with role-based permissions.

### Roles

- Field Worker
- Vaccination Worker
- Supervisor
- Public Health Administrator
- Medical / Public Health Reviewer

### Capabilities

- Registration
- Login
- Logout
- Password reset
- JWT authentication
- Role-based authorization
- User management

---

# 📚 Official Guidance Repository

Administrators can upload and manage official health guidance.

### Supported Document Types

- PDF
- DOCX
- HTML
- TXT
- CSV

### Document Metadata

Each document can have:

```text
Document Title
Issuing Authority
Version
Publication Date
Effective Date
Expiry Date
Geographic Scope
Topic
Audience
Status
Source URL
Approval Information
```

### Document Status

```text
Draft
Under Review
Approved
Active
Superseded
Archived
Expired
```

---

# 🔄 Version Management

HealthCompass tracks the history of every guideline.

```text
Version 1.0
    ↓
Version 2.0
    ↓
Version 2.1
    ↓
Version 3.0
```

When a new active version is published, the previous version can automatically become:

> **Superseded**

This prevents old guidance from being accidentally treated as current.

---

# 📝 Change Detection

HealthCompass compares document versions and highlights meaningful changes.

### Example

```text
Previous Version
Vaccination interval: 4 weeks

Current Version
Vaccination interval: 8 weeks

────────────────────────────
CHANGE DETECTED
────────────────────────────

Recommended interval changed
from 4 weeks to 8 weeks.
```

The system can identify changes involving:

- Instructions
- Eligibility
- Time intervals
- Thresholds
- Procedures
- Regional applicability
- Effective dates

---

# 🔎 Intelligent Search

Users can search using natural language.

### Traditional Search

```text
isolation protocol district A
```

### Natural-Language Search

```text
What is the current isolation guidance
for suspected cases in District A?
```

HealthCompass combines semantic retrieval with metadata filtering.

### Search Ranking

The system prioritizes:

1. Active documents
2. Applicable geographic region
3. Latest effective version
4. Authorized source
5. Relevant content
6. Semantic similarity

---

# 🤖 AI Guidance Assistant

The AI assistant allows users to ask questions about approved health guidance.

### Example Questions

```text
What is the current vaccination protocol?

Has the outbreak guidance changed?

Which protocol applies to District A?

What changed between versions 3.0 and 3.1?

What protective measures are currently required?

What does the latest guideline say about isolation?
```

---

# 🔗 Source-Grounded Answers

Every AI response should provide enough information for the user to verify the answer.

Example:

```text
Answer:
The current applicable guidance is Version 4.2.

Source:
Public Health Authority

Document:
Outbreak Response Guideline

Version:
4.2

Effective Date:
12 August 2026

Region:
District A

Section:
Case Management → Isolation
```

The user should be able to open the underlying official document.

---

# 📍 Location-Aware Retrieval

Health guidance may differ by jurisdiction.

HealthCompass supports geographic hierarchy:

```text
Country
   ↓
State / Province
   ↓
District
   ↓
Municipality
   ↓
Facility
```

### Example Retrieval Priority

```text
Facility Guidance
       ↓
District Guidance
       ↓
State Guidance
       ↓
National Guidance
       ↓
General Official Guidance
```

Only guidance that is approved, active, and applicable should receive priority.

---

# 📢 Guidance Change Alerts

HealthCompass can notify users when important guidance changes.

### Alert Types

- New outbreak guidance
- Vaccination protocol update
- Emergency advisory
- Regional policy update
- Critical safety update
- Document superseded
- Guidance expiry

### Notification Channels

MVP:

- In-app notifications
- Email

Future:

- Push notifications
- SMS
- Slack
- Microsoft Teams

---

# 📱 Offline / Low-Connectivity Support

Field workers may work in areas with unreliable connectivity.

Planned capabilities include:

- Save important documents
- Cache commonly used guidance
- Read saved guidance offline
- Synchronize when connectivity returns

The interface should clearly distinguish:

```text
CURRENT
```

from:

```text
CACHED — UPDATE AVAILABLE
```

---

# 🛡️ AI Safety

HealthCompass is not a medical diagnosis system.

The AI should:

- Use approved sources.
- Cite retrieved content.
- Show version information.
- Show effective dates.
- Consider geographic scope.
- Distinguish current from historical guidance.
- Avoid unsupported claims.
- Avoid fabricated sources.
- State uncertainty.
- Refuse unsupported questions.
- Escalate urgent situations appropriately.

### Safe Fallback

```text
No current approved guidance was found
for this question.

Please consult the responsible public
health authority or applicable emergency protocol.
```

---

# 👥 User Roles

| Role               | Primary Responsibilities                   |
| ------------------ | ------------------------------------------ |
| Field Worker       | Search and access current guidance         |
| Vaccination Worker | Access vaccination protocols               |
| Supervisor         | Monitor updates and team information needs |
| Administrator      | Manage documents and users                 |
| Medical Reviewer   | Review and approve authoritative content   |

---

# 🏗️ System Architecture

```text
                           ┌───────────────────────┐
                           │     React Frontend    │
                           │ TypeScript + Tailwind │
                           └───────────┬───────────┘
                                       │
                                       ▼
                           ┌───────────────────────┐
                           │      Express API      │
                           │ Auth + Business Logic │
                           └───────────┬───────────┘
                                       │
               ┌───────────────────────┼───────────────────────┐
               │                       │                       │
               ▼                       ▼                       ▼
        ┌─────────────┐         ┌─────────────┐         ┌──────────────┐
        │   MongoDB   │         │    Redis    │         │ Notification │
        │  Database   │         │    Cache    │         │   Service    │
        └─────────────┘         └─────────────┘         └──────────────┘
                                       │
                                       ▼
                           ┌───────────────────────┐
                           │ Document Processing   │
                           │    Python Workers     │
                           └───────────┬───────────┘
                                       │
                         ┌─────────────┼─────────────┐
                         ▼             ▼             ▼
                  Text Extraction  Metadata      Embeddings
                         │         Extraction          │
                         └─────────────┼─────────────┘
                                       ▼
                           ┌───────────────────────┐
                           │ Vector Search / Index │
                           └───────────┬───────────┘
                                       │
                                       ▼
                           ┌───────────────────────┐
                           │     FastAPI AI        │
                           │       RAG Service     │
                           └───────────┬───────────┘
                                       │
                                       ▼
                           Source-Grounded Answer
```

---

# 🧰 Technology Stack

## Frontend

- React
- TypeScript
- Tailwind CSS
- Redux Toolkit
- React Query
- Recharts

## Backend

- Node.js
- Express.js

## AI Service

- Python
- FastAPI
- RAG pipeline
- Embedding model
- LLM

## Database

- MongoDB
- Redis

## Vector Search

Recommended options:

- Qdrant
- pgvector
- Pinecone
- Weaviate

## Document Processing

- PyMuPDF
- python-docx
- BeautifulSoup
- OCR where required

## Authentication

- JWT
- bcrypt / Argon2

## DevOps

- Docker
- Docker Compose
- GitHub Actions
- AWS / Render / Railway

---

# 📂 Project Structure

The repository follows a monorepo-oriented structure:

```text
healthcompass/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── types/
│   │   └── utils/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── src/
│   │   ├── controllers/
│   │   ├── routes/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── services/
│   │   ├── validators/
│   │   ├── utils/
│   │   └── app.ts
│   └── package.json
│
├── ai-service/
│   ├── app/
│   │   ├── api/
│   │   ├── rag/
│   │   ├── ingestion/
│   │   ├── embeddings/
│   │   ├── retrieval/
│   │   ├── prompts/
│   │   ├── safety/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── database/
│   ├── ai/
│   ├── deployment/
│   └── product/
│
├── scripts/
│   ├── seed/
│   └── ingestion/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

# 🧩 Core Modules

## 1. Authentication

Handles:

- Registration
- Login
- Password reset
- JWT
- Roles
- Permissions

## 2. User Management

Handles:

- Profiles
- Regions
- Organizations
- Account status

## 3. Guidance Management

Handles:

- Uploads
- Metadata
- Approval
- Publication
- Archiving

## 4. Version Control

Handles:

- Version creation
- Current status
- Superseded versions
- Version history

## 5. Document Processing

Handles:

- Text extraction
- Cleaning
- Chunking
- Metadata extraction
- Embedding generation

## 6. Search

Handles:

- Keyword search
- Semantic search
- Filtering
- Ranking

## 7. RAG Assistant

Handles:

- Question understanding
- Retrieval
- Ranking
- LLM generation
- Citations
- Safety checks

## 8. Change Detection

Handles:

- Version comparison
- Change summaries
- Important change detection

## 9. Notifications

Handles:

- New guidance
- Critical updates
- Superseded documents
- User preferences

## 10. Analytics

Handles:

- Search metrics
- User activity
- Frequently requested topics
- Unanswered questions
- Guidance usage

---

# 🗃️ Data Model

Core entities include:

```text
Users
Documents
Document Versions
Document Chunks
Topics
Regions
Queries
Feedback
Alerts
Audit Logs
```

### Simplified Relationships

```text
User
 ├── Queries
 ├── Feedback
 └── Audit Logs

Document
 ├── Versions
 ├── Topic
 ├── Region
 └── Alerts

Document Version
 └── Document Chunks

Query
 ├── Retrieved Sources
 └── Feedback
```

---

# 🔌 API Overview

Example API groups:

```text
/api/auth
/api/users
/api/documents
/api/documents/:id
/api/documents/:id/versions
/api/search
/api/guidance/ask
/api/guidance/sources
/api/alerts
/api/feedback
/api/admin
```

---

# 🔐 Example Authentication

```http
POST /api/auth/login
Content-Type: application/json
```

```json
{
  "email": "worker@example.com",
  "password": "password"
}
```

Response:

```json
{
  "accessToken": "<token>",
  "user": {
    "id": "user_123",
    "role": "FIELD_WORKER"
  }
}
```

---

# 🤖 Example AI Request

```http
POST /api/guidance/ask
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "question": "What is the current isolation guidance?",
  "region": "District A"
}
```

### Example Response

```json
{
  "answer": "The current applicable guidance is Version 4.2...",
  "confidence": 0.94,
  "sources": [
    {
      "title": "Outbreak Response Guideline",
      "version": "4.2",
      "effectiveDate": "2026-08-12",
      "section": "Case Management > Isolation"
    }
  ]
}
```

---

# 🧠 How RAG Works

HealthCompass uses Retrieval-Augmented Generation rather than relying purely on the language model's general knowledge.

```text
                USER QUESTION
                      │
                      ▼
              Query Understanding
                      │
                      ▼
             Region / Topic Detection
                      │
                      ▼
              Semantic Retrieval
                      │
                      ▼
              Candidate Documents
                      │
                      ▼
          Version / Status Filtering
                      │
                      ▼
               Source Ranking
                      │
                      ▼
                 LLM Prompt
                      │
                      ▼
               Generated Answer
                      │
                      ▼
             Citation Validation
                      │
                      ▼
              Safety Validation
                      │
                      ▼
             FINAL RESPONSE
```

---

# 📄 Document Ingestion Pipeline

When an administrator uploads a document:

```text
Upload
  ↓
File Validation
  ↓
Text Extraction
  ↓
Cleaning
  ↓
Section Detection
  ↓
Metadata Extraction
  ↓
Chunking
  ↓
Embedding Generation
  ↓
Vector Indexing
  ↓
Ready for Retrieval
```

Every chunk retains source metadata such as:

```text
document_id
version_id
section
page
region
effective_date
status
```

This enables source traceability.

---

# 🔄 Version Lifecycle

```text
Draft
  ↓
Under Review
  ↓
Approved
  ↓
Active
  ↓
Superseded
  ↓
Archived
```

Only documents meeting the configured publication rules should enter the active retrieval index.

---

# 🌎 Example End-to-End Workflow

### Step 1 — New Guidance

An administrator receives a new official PDF.

```text
Outbreak Guideline v4.2.pdf
```

### Step 2 — Upload

The administrator uploads the document.

### Step 3 — Metadata

```text
Authority: Public Health Authority
Version: 4.2
Effective Date: 2026-08-12
Region: District A
Status: Approved
```

### Step 4 — Processing

HealthCompass extracts and indexes the content.

### Step 5 — Version Comparison

The system compares Version 4.2 with Version 4.1.

### Step 6 — Change Detection

```text
Isolation guidance updated.
Reporting procedure changed.
Effective date updated.
```

### Step 7 — Publish

Version 4.2 becomes active.

Version 4.1 becomes superseded.

### Step 8 — Notification

Relevant workers are notified.

### Step 9 — User Question

```text
What is the current isolation guidance?
```

### Step 10 — RAG

The system retrieves the relevant section from Version 4.2.

### Step 11 — Answer

The AI provides the current guidance and cites the source.

---

# 🚀 Getting Started

## Prerequisites

Install:

- Git
- Node.js 20+
- npm or pnpm
- Python 3.11+
- MongoDB
- Redis
- Docker
- Docker Compose

Depending on the selected vector store and LLM provider, additional credentials or services may be required.

---

# 📥 Clone the Repository

```bash
git clone https://github.com/<your-username>/healthcompass.git

cd healthcompass
```

---

# ⚙️ Environment Variables

Create a local environment file:

```bash
cp .env.example .env
```

Example:

```env
# Application
NODE_ENV=development
PORT=5000

# Database
MONGODB_URI=mongodb://localhost:27017/healthcompass

# Redis
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=replace-with-a-secure-secret

# AI Service
AI_SERVICE_URL=http://localhost:8000

# LLM
LLM_API_KEY=your-api-key

# Vector Database
VECTOR_DB_URL=your-vector-database-url
VECTOR_DB_API_KEY=your-vector-database-key

# Storage
STORAGE_BUCKET=healthcompass-documents
STORAGE_REGION=your-region
```

> Never commit secrets, API keys, passwords, or production credentials.

---

# ▶️ Running Locally

## 1. Start MongoDB and Redis

Using Docker:

```bash
docker compose up -d mongodb redis
```

---

## 2. Start the Backend

```bash
cd backend

npm install

npm run dev
```

The backend should be available at:

```text
http://localhost:5000
```

---

## 3. Start the AI Service

```bash
cd ai-service

python -m venv .venv
```

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run FastAPI:

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 4. Start the Frontend

```bash
cd frontend

npm install

npm run dev
```

The frontend should be available at:

```text
http://localhost:5173
```

---

# 🐳 Docker Setup

For a complete development environment:

```bash
docker compose up --build
```

Stop services:

```bash
docker compose down
```

Remove containers and volumes:

```bash
docker compose down -v
```

---

# 📑 Adding a Guidance Document

The recommended workflow is:

```text
Admin Login
    ↓
Documents
    ↓
Upload Document
    ↓
Enter Metadata
    ↓
Submit for Review
    ↓
Approve
    ↓
Publish
```

Example metadata:

```json
{
  "title": "Outbreak Response Guideline",
  "authority": "Public Health Authority",
  "version": "4.2",
  "publicationDate": "2026-08-10",
  "effectiveDate": "2026-08-12",
  "region": "District A",
  "status": "ACTIVE"
}
```

---

# 🧠 AI / RAG Configuration

The AI service requires:

1. A document parser
2. A chunking strategy
3. An embedding model
4. A vector database
5. An LLM
6. Retrieval logic
7. Citation handling
8. Safety validation

### Recommended retrieval metadata

```text
document_id
version_id
authority
topic
region
audience
publication_date
effective_date
status
section
page
```

This metadata is essential for filtering out outdated and geographically irrelevant sources.

---

# 🔍 Search Strategy

HealthCompass should ideally combine:

### Semantic Search

Find conceptually relevant content.

### Metadata Filtering

Restrict results by:

- Region
- Topic
- Status
- Version
- Date

### Ranking

Prioritize:

```text
Applicable + Active + Current + Official + Relevant
```

This is more reliable than selecting the highest semantic similarity alone.

---

# 🛡️ Safety Strategy

The AI response pipeline should contain multiple safeguards.

```text
Retrieved Sources
      ↓
Source Validation
      ↓
Version Check
      ↓
Applicability Check
      ↓
LLM Generation
      ↓
Citation Check
      ↓
Unsupported Claim Check
      ↓
Final Response
```

Questions without sufficient authoritative evidence should not receive fabricated answers.

---

# 🧪 Testing

## Backend

```bash
cd backend
npm test
```

## Frontend

```bash
cd frontend
npm test
```

## AI Service

```bash
cd ai-service
pytest
```

---

# 🔬 Test Coverage Areas

## Authentication

- Login
- Registration
- Token validation
- Authorization

## Documents

- Upload
- Validation
- Metadata
- Version creation
- Publication
- Archive

## Search

- Keyword search
- Semantic retrieval
- Region filtering
- Current-version filtering

## AI

- Retrieval
- Source grounding
- Citation generation
- Unsupported questions
- Outdated source prevention

## Notifications

- Critical updates
- User targeting
- Delivery status

---

# 📊 AI Evaluation

Because HealthCompass is an AI-enabled information retrieval system, model quality should be evaluated separately from normal application tests.

### Recommended Metrics

| Metric                   | Description                                          |
| ------------------------ | ---------------------------------------------------- |
| Retrieval Relevance      | Whether retrieved chunks are actually useful         |
| Citation Accuracy        | Whether citations support the answer                 |
| Groundedness             | Whether the answer is supported by retrieved content |
| Hallucination Rate       | Unsupported information in generated responses       |
| Current-Version Accuracy | Ability to select current guidance                   |
| Geographic Accuracy      | Ability to select applicable regional guidance       |
| Refusal Accuracy         | Ability to decline unsupported questions             |

### Initial Targets

| Metric                  | Target |
| ----------------------- | -----: |
| Search Success Rate     |   >90% |
| Retrieval Relevance     |   >85% |
| Citation Accuracy       |   >95% |
| Grounded Answer Rate    |   >95% |
| Outdated Retrieval Rate |    <5% |
| User Satisfaction       |   >85% |

These values are evaluation targets for the project and should be validated through testing.

---

# 🔐 Security & Privacy

Security is a core design principle.

### Authentication

- JWT
- Secure password hashing
- Token expiration
- Role-based authorization

### Application Security

- HTTPS
- Input validation
- API rate limiting
- Secure file upload handling
- Access control
- Audit logs
- Secure secrets management

### Data Minimization

The MVP should focus primarily on official public health guidance documents.

Avoid collecting personally identifiable patient information unless a defined use case, governance framework, and appropriate security architecture exist.

---

# 📋 Audit Logging

Important administrative events should be recorded.

Example:

```json
{
  "userId": "user_123",
  "action": "PUBLISH_DOCUMENT",
  "resourceId": "doc_456",
  "timestamp": "2026-09-01T10:30:00Z"
}
```

Potential events:

- Login
- Document upload
- Document approval
- Document publication
- Version creation
- Document archival
- User-role changes
- Alert configuration changes

---

# 📈 Admin Analytics

The administrator dashboard can track:

- Active documents
- Superseded documents
- Pending reviews
- Published updates
- Active users
- Search volume
- AI question volume
- Frequently searched topics
- Unanswered questions
- Reported incorrect responses

Example:

```text
┌─────────────────┬─────────────────┬─────────────────┐
│ Active Guides   │ Pending Review  │ Active Users    │
│      124        │       8         │      487        │
├─────────────────┼─────────────────┼─────────────────┤
│ AI Questions    │ Unanswered      │ Reported Issues │
│     2,481       │       37        │        8        │
└─────────────────┴─────────────────┴─────────────────┘
```

---

# 🧭 Project Roadmap

## Phase 1 — MVP

- [ ] Authentication
- [ ] Role-based access control
- [ ] User management
- [ ] Guidance repository
- [ ] Document upload
- [ ] Document metadata
- [ ] Version management
- [ ] Document processing
- [ ] Semantic search
- [ ] RAG assistant
- [ ] Source citations
- [ ] Current/superseded detection
- [ ] Change comparison
- [ ] Notifications
- [ ] Admin dashboard
- [ ] Audit logs

## Phase 2

- [ ] Advanced offline synchronization
- [ ] Mobile application
- [ ] Multilingual guidance
- [ ] Push notifications
- [ ] Voice search

## Phase 3

- [ ] Automated monitoring of official sources
- [ ] Public health system integration
- [ ] Advanced analytics
- [ ] Cross-agency knowledge federation

## Phase 4

- [ ] Advanced outbreak intelligence
- [ ] Automated change-impact analysis
- [ ] Predictive resource planning
- [ ] AI-assisted policy analysis

---

# 📅 8-Week Development Plan

| Week  | Work                                                |
| ----- | --------------------------------------------------- |
| **1** | Requirements, UX, Architecture, Database            |
| **2** | Authentication, Roles, User Management              |
| **3** | Guidance Repository, Upload, Metadata, Versioning   |
| **4** | Document Processing, Embeddings, Semantic Search    |
| **5** | RAG Pipeline, AI Assistant, Citations               |
| **6** | Change Detection, Notifications, Dashboard          |
| **7** | Testing, Security, Optimization, Docker             |
| **8** | Deployment, Documentation, Evaluation, Presentation |

---

# 🎓 Capstone Scope

HealthCompass is intentionally scoped as an **8-week full-stack AI capstone project**.

The primary technical demonstration should be:

```text
Official Guidance
      ↓
Upload
      ↓
Version
      ↓
Process
      ↓
Index
      ↓
Search
      ↓
Retrieve
      ↓
Generate
      ↓
Cite
      ↓
Compare
      ↓
Alert
```

The project should prioritize **accuracy, traceability, and usability** over building a large number of unrelated healthcare features.

---

# 🧑‍💻 Development Principles

## 1. Source First

Official guidance should be treated as the authority.

## 2. Current First

Current applicable guidance should be prioritized over historical documents.

## 3. Explainability

AI responses should show where information came from.

## 4. Safety

The system should refuse unsupported health guidance rather than guess.

## 5. Human Oversight

Authoritative content should pass through appropriate approval workflows.

## 6. Minimal Data

Avoid unnecessary personal or patient data.

---

# 🤝 Contributing

Contributions are welcome.

### Development Workflow

```bash
git checkout -b feature/document-versioning

git add .

git commit -m "feat: add document version management"

git push origin feature/document-versioning
```

Open a Pull Request against `main`.

---

# 📬 Pull Request Guidelines

A PR should include:

- Clear summary
- Related requirement or issue
- Screenshots for UI changes
- API examples where applicable
- Tests
- Migration notes if required
- Environment/configuration changes

### PR Title Examples

```text
feat: add document version management

feat: implement RAG guidance assistant

feat: add source citation support

fix: prevent superseded documents from retrieval

fix: handle conflicting guidance versions

test: add RAG citation evaluation

- Processes multiple chunks in a single API call to reduce overhead
- Configurable batch size balances API latency and error handling
- Batching reduces total API calls and cost for large corpora
- Failed batches can be retried without reprocessing successful batches

### Cost and performance considerations

- Cost scales with number of chunks and API pricing model
- Latency increases with corpus size and batch size
- Larger vector dimensions increase storage and computation cost
- Batching reduces API overhead but increases per-request complexity
- Consider incremental embedding for large, growing document collections

### Batch embedding management

The enhanced embedding pipeline includes:

- **Batch processing**: Configurable batch size (default: 64) reduces API calls
- **Skip existing embeddings**: Content-based chunk IDs prevent redundant API calls
- **Retry with exponential backoff**: Handles temporary failures automatically
- **Progress saving**: Incremental saves enable resumability for large corpora
- **Run summary**: Comprehensive statistics including cost estimation
- **Resumability**: Can continue from partially completed runs

### How batch size works

- Batch size determines how many chunks are processed in a single API call
- Larger batches reduce API overhead but increase memory usage and per-request complexity
- Default batch size of 64 provides good balance for most use cases
- Adjust based on your corpus size and API rate limits

### How existing embeddings are skipped

- Each chunk generates a unique ID based on its content and metadata
- Before processing, the pipeline checks if a chunk ID already exists in the output file
- Chunks with existing embeddings are skipped, reducing API calls and cost
- This enables efficient re-runs when adding new documents to an existing corpus

### How retries and backoff work

- Temporary failures (rate limits, timeouts, connection errors) trigger automatic retry
- Exponential backoff sequence: 1, 2, 4, 8 seconds between attempts
- Maximum retry attempts configurable via `MAX_RETRY_ATTEMPTS` (default: 3)
- Permanent errors (missing API keys, invalid configuration) fail immediately without retry
- Failed batches are recorded in the run summary for troubleshooting

### How progress is saved and resumed

- Embeddings are saved incrementally after each successful batch
- Uses atomic file operations (write to temp file, then rename) to prevent corruption
- If the process stops, it can continue from where it left off
- Existing embeddings are never deleted during re-runs
- Enables processing of large corpora without risking complete data loss

### How approximate cost is calculated

- Cost estimation based on token count and model pricing
- Rough token estimation: ~4 characters per token
- Example pricing (text-embedding-3-small): $0.02 per 1M tokens
- Result is clearly labeled as estimated (actual cost may vary)
- Helps budget and plan large-scale embedding operations

## Vector Database — Sprint task 3.30

HealthCompass uses ChromaDB as a vector database to store document embeddings alongside their source text and metadata for efficient semantic search and retrieval.

```python
from healthcompass.vector_store import (
    initialize_vector_store,
    get_vector_store_config,
    VectorRecord,
    insert_record,
    get_record,
)

# Get configuration from environment variables
config = get_vector_store_config()

# Initialize database (creates directory and collection if needed)
collection = initialize_vector_store(config)

# Insert a record
record = VectorRecord(
    id="chunk_001",
    embedding=[0.1, 0.2, 0.3, ...],  # Your embedding vector
    text="Vaccination guidance text...",
    metadata={
        "source": "guidance.txt",
        "filename": "guidance.txt",
        "chunk_id": "0",
        "section": "Introduction",
        "page_number": "1",
        "document_type": "guidance"
    }
)
insert_record(collection, record)

# Retrieve a record
retrieved = get_record(collection, "chunk_001")
```

Run the insert and readback test:

```bash
python experiments/vector_db_readback.py
```

### Configuration

Vector database uses environment variables:

- **CHROMA_DB_PATH**: Database storage path (default: `data/chroma_db`)
- **CHROMA_COLLECTION_NAME**: Collection name (default: `healthcompass_documents`)
- **EMBEDDING_MODEL**: Embedding model (determines vector dimension, default: `text-embedding-3-small`)

### Why use a vector database?

- **Semantic Search**: Find documents similar in meaning, not just keyword matches
- **Scalability**: Efficiently handle millions of vectors with fast similarity search
- **Integration**: Seamlessly works with embedding models for RAG applications
- **Metadata Support**: Store rich metadata alongside vectors for filtering and context

### Vector dimension and model compatibility

The vector dimension of the collection must match the embedding model used:

| Model | Dimension |
|-------|-----------|
| text-embedding-3-small | 1536 |
| text-embedding-3-large | 3072 |
| text-embedding-ada-002 | 1536 |

The vector store automatically configures the correct dimension based on the `EMBEDDING_MODEL` environment variable.

### Record schema

Each record contains:
- **id**: Unique identifier for the record
- **embedding**: The high-dimensional vector representing the text
- **text**: The original source text for the chunk
- **metadata**: Rich metadata including source, filename, chunk_id, section, page_number, document_type

### Why store text and metadata with vectors?

- **Citation**: Accurately cite sources when generating answers
- **Context**: Provide full context when retrieving similar documents
- **Verification**: Ensure retrieved content matches user queries
- **Filtering**: Filter results by metadata (e.g., specific documents, sections)
- **Debugging**: Trace retrieval results back to source documents

### Running tests

Unit tests use temporary databases and deterministic test vectors:

```bash
pytest tests/test_vector_database.py -v
```

Integration test for insert and readback:

```bash
python experiments/vector_db_readback.py
```

This generates a report in `experiments/outputs/vector_db_readback.md` with actual test results.

### Health check

Verify database connectivity:

```python
from healthcompass.vector_store import health_check

if health_check():
    print("Vector database is accessible and healthy")
```

### Troubleshooting

**Dimension mismatch error**: The existing collection has a different vector dimension than the configured embedding model. Options:
1. Delete and recreate the collection (WARNING: deletes all data): `rm -rf data/chroma_db`
2. Use the same embedding model that was used to create the collection
3. Create a new collection with a different name

**Collection already exists**: The vector store automatically loads existing collections instead of creating new ones to prevent accidental data loss. To start fresh, delete the database directory or use a different collection name.

See [vector database documentation](docs/vector_database.md) for detailed information.

### Validation

The embedding generation includes comprehensive validation:
- All chunks receive an embedding
- Each embedding is a list of numeric values
- All vectors have the same dimension
- Number of vectors matches number of chunks
- Each vector remains attached to its source text and metadata

### Sample output

The script generates:
- `experiments/outputs/embedded_chunks.json` - Complete embedded chunks with vectors
- `experiments/outputs/embedding_sample.md` - Human-readable sample report

Retrieval and vector search remain future work.

## Testing and team workflow

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m compileall -q src experiments
git diff --check
docs: update local development setup
```

---

# 🌿 Branching Strategy

A simple branching model is recommended:

```text
main
 │
 ├── feature/authentication
 ├── feature/document-management
 ├── feature/version-control
 ├── feature/rag-assistant
 ├── feature/change-detection
 ├── feature/notifications
 └── fix/*
```

For larger team development:

```text
main
  │
  └── develop
       ├── feature/*
       ├── fix/*
       ├── docs/*
       └── test/*
```

---

# 📚 Documentation

Project documentation should live under:

```text
/docs
```

Recommended sections:

```text
docs/
├── architecture/
├── api/
├── database/
├── ai/
├── deployment/
└── product/
```

Recommended documents:

```text
Architecture.md
API.md
Database.md
RAG.md
AI-Safety.md
Deployment.md
```

---

# 🗺️ Future Scope

HealthCompass can eventually evolve into a broader public health intelligence platform.

Potential future capabilities include:

- Automated monitoring of official public health websites
- Automatic detection of new guideline versions
- Multilingual guidance
- Voice-enabled field assistance
- Mobile application
- Offline synchronization
- SMS and messaging integrations
- Public health system integrations
- Cross-agency knowledge search
- Advanced outbreak intelligence
- Guidance impact analysis
- Predictive operational planning

These features are intentionally outside the initial MVP.

---

# ⚠️ Medical & AI Disclaimer

HealthCompass is an **information retrieval and decision-support platform**.

It is not:

- A diagnostic system
- A replacement for healthcare professionals
- A replacement for public health authorities
- An autonomous emergency response system
- A substitute for official clinical or public health protocols

AI-generated responses should be verified against the cited authoritative source, especially in high-risk or rapidly changing situations.

---

# 📌 Project Summary

HealthCompass combines:

```text
Public Health
      +
Document Intelligence
      +
Semantic Search
      +
RAG
      +
Version Control
      +
Change Detection
      +
Source Verification
      +
Notifications
```

### The core problem

> **Frontline workers need the right public health guidance, but rapidly changing and fragmented documents make it difficult to know what is current and applicable.**

### The core solution

> **HealthCompass centralizes official guidance and uses AI-powered retrieval to help users find, understand, and verify current information quickly.**

### The core promise

> **Navigate changing public health guidance with confidence.**

---

# 📄 License

Select and add the appropriate license before making the repository public.

For an academic/open-source project, the MIT License is one possible option.

```text
MIT License
```

---

# ⭐ HealthCompass

> **Find the guidance. Check the version. Understand the change. Verify the source.**
