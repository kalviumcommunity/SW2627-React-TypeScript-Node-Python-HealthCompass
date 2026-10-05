# HealthCompass Frontend

## Overview

This is the React + TypeScript frontend for the HealthCompass public health RAG application.

## Tech Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Lucide React (icons)

## Development

### Prerequisites

- Node.js 18+
- npm

### Installation

```bash
cd frontend
npm install
```

### Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure the API URL in `.env`:

```
VITE_API_URL=http://localhost:8000
```

### Running the Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the next available port).

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Previewing Production Build

```bash
npm run preview
```

## Pages

- **Dashboard** (`/`) - Overview with quick stats and recent guidance
- **Ask HealthCompass** (`/ask`) - RAG question-answering interface
- **Guidance Library** (`/guidance`) - Searchable guidance documents
- **Updates & Policies** (`/updates`) - Recent policy changes
- **Alert Center** (`/alerts`) - Active health alerts
- **Saved Guidance** (`/saved`) - Saved guidance items

## API Integration

The frontend communicates with the FastAPI backend through the API client in `src/api/client.ts`.

### API Endpoints

- `POST /ask` - Ask HealthCompass a question
- `GET /guidance` - Get all guidance items
- `GET /guidance/search?query=...` - Search guidance
- `GET /alerts` - Get active alerts
- `GET /updates` - Get policy updates
- `GET /stats` - Get dashboard statistics

## Architecture

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API client and type definitions
│   ├── components/
│   │   └── layout/
│   │       └── Layout.tsx      # Main layout with sidebar
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── AskHealthCompass.tsx
│   │   ├── GuidanceLibrary.tsx
│   │   ├── Updates.tsx
│   │   ├── Alerts.tsx
│   │   └── SavedGuidance.tsx
│   ├── App.tsx                # Main app with routing
│   ├── main.tsx               # Entry point
│   └── index.css              # Tailwind CSS imports
├── .env.example               # Environment configuration template
├── package.json
├── tailwind.config.js
└── vite.config.ts
```

## Important Notes

- The frontend is designed to work with the existing Python backend
- LLM generation requires an OpenAI API key configured in the backend
- Without an API key, the Ask endpoint returns a demonstration mode response
- Saved guidance is stored in localStorage for demo purposes
