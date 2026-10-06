import { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Send,
  Loader2,
  AlertCircle,
  CheckCircle,
  FileText,
  ExternalLink,
  Search,
  BookOpen,
  ChevronRight,
  X,
  Info,
  MessageSquare,
  ArrowRight,
  Bookmark,
} from 'lucide-react';
import { askHealthCompass, ApiError, saveGuidance, removeSavedGuidance, getSavedGuidance } from '../api/client';
import { suggestedQuestions, followUpSuggestions, loadingStages } from '../data/askSuggestions';
import type { RagAnswer, RagSource } from '../types';

// ─── Loading Stage Hook ──────────────────────────────────────────

function useLoadingStage(isLoading: boolean) {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    if (!isLoading) {
      return;
    }

    const timers = [
      setTimeout(() => setStageIndex(1), 1500),
      setTimeout(() => setStageIndex(2), 3500),
    ];

    return () => {
      timers.forEach(clearTimeout);
      setStageIndex(0);
    };
  }, [isLoading]);

  return isLoading ? loadingStages[stageIndex] : '';
}

// ─── Source Panel ────────────────────────────────────────────────

function SourcePanel({
  sources,
  activeSourceIdx,
  onSourceSelect,
  onViewDocument,
}: {
  sources: RagSource[];
  activeSourceIdx: number;
  onSourceSelect: (idx: number) => void;
  onViewDocument: (source: RagSource) => void;
}) {
  const activeSource = sources[activeSourceIdx];
  const [savedSourceIds, setSavedSourceIds] = useState<Map<string, string>>(new Map());
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getSavedGuidance()
      .then((items) => {
        const map = new Map<string, string>();
        items.forEach((it) => {
          if (it.title) map.set(it.title, it.id);
          if (it.source) map.set(it.source, it.id);
        });
        setSavedSourceIds(map);
      })
      .catch(() => {});
  }, []);

  // Clean document title - remove filesystem paths and technical IDs
  const cleanTitle = (title: string, source: string) => {
    // Prefer title if available and clean
    if (title && !title.includes('\\') && !title.includes('/') && !title.includes('C:')) {
      // Remove technical IDs like "d3a0d613" from end
      return title.replace(/\s*[a-f0-9]{8,}(\.pdf)?$/i, '').replace(/\.pdf$/i, '');
    }
    // Fallback to source, clean up path
    if (source) {
      const parts = source.split(/[/\\]/);
      const filename = parts[parts.length - 1] || source;
      return filename.replace(/\s*[a-f0-9]{8,}(\.pdf)?$/i, '').replace(/\.pdf$/i, '');
    }
    return 'Document';
  };

  // Get relevance label based on distance
  const getRelevanceLabel = (distance: number) => {
    const score = 1 - distance;
    if (score >= 0.7) return 'High relevance';
    if (score >= 0.5) return 'Moderate relevance';
    return 'Low relevance';
  };

  // Get relevance color
  const getRelevanceColor = (distance: number) => {
    const score = 1 - distance;
    if (score >= 0.7) return 'bg-primary-500';
    if (score >= 0.5) return 'bg-amber-400';
    return 'bg-gray-400';
  };

  return (
    <div className="h-full flex flex-col bg-white border-l border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-navy-900">Source Grounding</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              {sources.length} source{sources.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </div>

      {/* Source tabs - horizontally scrollable */}
      {sources.length > 1 && (
        <div className="border-b border-gray-200 bg-gray-50/50">
          <div className="flex gap-1 px-3 py-2 overflow-x-auto scrollbar-hide">
            {sources.map((s, idx) => (
              <button
                key={s.chunkId}
                onClick={() => onSourceSelect(idx)}
                className={`flex-shrink-0 text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                  idx === activeSourceIdx
                    ? 'bg-primary-100 text-primary-700 border border-primary-200'
                    : 'text-gray-500 hover:bg-gray-100 border border-transparent'
                }`}
                aria-label={`Source ${idx + 1}`}
              >
                {idx + 1}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Active source detail */}
      {activeSource && (
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {/* Document card */}
          <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
            <div className="flex items-start gap-2.5 mb-3">
              <div className="w-8 h-8 rounded-lg bg-white border border-gray-200 flex items-center justify-center flex-shrink-0">
                <FileText className="h-4 w-4 text-primary-600" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-navy-900 leading-tight mb-1">
                  {cleanTitle(activeSource.title, activeSource.source)}
                </p>
                <p className="text-xs text-gray-500">Official Protocol</p>
              </div>
            </div>
            
            {/* Metadata */}
            <div className="flex items-center gap-3 text-xs text-gray-500 pt-2 border-t border-gray-200">
              <span className="flex items-center gap-1">
                <span className="text-gray-400">Page</span>
                {activeSource.chunkIndex}
              </span>
              <span className="text-gray-300">•</span>
              <span className="flex items-center gap-1">
                <span className="text-gray-400">Chunk</span>
                {activeSource.chunkIndex}
              </span>
              <span className="text-gray-300">•</span>
              <span className="flex items-center gap-1">
                <span className="text-gray-400">Rank</span>
                <span className="font-medium text-gray-700">#{activeSource.rank}</span>
              </span>
            </div>
          </div>

          {/* Relevance */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-xs text-gray-400 font-medium">Relevance</p>
              <span className="text-xs font-medium text-gray-600">
                {getRelevanceLabel(activeSource.distance)}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${getRelevanceColor(activeSource.distance)}`}
                style={{ width: `${Math.max(10, (1 - activeSource.distance) * 100)}%` }}
              />
            </div>
          </div>

          {/* Retrieved Excerpt */}
          {activeSource.excerpt && (
            <div>
              <p className="text-xs text-gray-400 font-medium mb-2">Retrieved Excerpt</p>
              <div className="bg-white border border-gray-200 rounded-lg p-3 max-h-48 overflow-y-auto">
                <p className="text-xs text-gray-600 leading-relaxed whitespace-pre-wrap">
                  {activeSource.excerpt}
                </p>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="space-y-2 pt-1">
            <button
              onClick={() => onViewDocument(activeSource)}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 border border-gray-300 text-sm text-gray-700 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Open Document
            </button>
            <button
              onClick={async () => {
                if (!activeSource || saving) return;
                setSaving(true);
                const title = cleanTitle(activeSource.title, activeSource.source);
                const key = title;
                try {
                  if (savedSourceIds.has(key)) {
                    const id = savedSourceIds.get(key)!;
                    await removeSavedGuidance(id);
                    setSavedSourceIds((prev) => {
                      const next = new Map(prev);
                      next.delete(key);
                      return next;
                    });
                  } else {
                    const saved = await saveGuidance({
                      title,
                      topic: 'Clinical Guidance',
                      source: activeSource.source || 'Ask HealthCompass',
                      excerpt: activeSource.excerpt || '',
                    });
                    setSavedSourceIds((prev) => {
                      const next = new Map(prev);
                      next.set(key, saved.id);
                      return next;
                    });
                  }
                } catch (err) {
                  console.error('Failed to toggle save source:', err);
                } finally {
                  setSaving(false);
                }
              }}
              disabled={saving}
              className={`w-full flex items-center justify-center gap-2 px-3 py-2 border text-sm rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1 ${
                activeSource && savedSourceIds.has(cleanTitle(activeSource.title, activeSource.source))
                  ? 'border-primary-300 bg-primary-50 text-primary-700 hover:bg-primary-100'
                  : 'border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Bookmark
                className={`h-3.5 w-3.5 ${
                  activeSource && savedSourceIds.has(cleanTitle(activeSource.title, activeSource.source))
                    ? 'fill-current text-primary-600'
                    : ''
                }`}
              />
              {activeSource && savedSourceIds.has(cleanTitle(activeSource.title, activeSource.source))
                ? 'Saved in Guidance'
                : 'Save to Guidance'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Document Viewer Modal ───────────────────────────────────────

function DocumentModal({
  source,
  onClose,
}: {
  source: RagSource;
  onClose: () => void;
}) {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  // Clean document title - remove filesystem paths and technical IDs
  const cleanTitle = (title: string, source: string) => {
    // Prefer title if available and clean
    if (title && !title.includes('\\') && !title.includes('/') && !title.includes('C:')) {
      // Remove technical IDs like "d3a0d613" from end
      return title.replace(/\s*[a-f0-9]{8,}(\.pdf)?$/i, '').replace(/\.pdf$/i, '');
    }
    // Fallback to source, clean up path
    if (source) {
      const parts = source.split(/[/\\]/);
      const filename = parts[parts.length - 1] || source;
      return filename.replace(/\s*[a-f0-9]{8,}(\.pdf)?$/i, '').replace(/\.pdf$/i, '');
    }
    return 'Document';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in">
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col animate-slide-up"
        role="dialog"
        aria-label="Document Viewer"
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200">
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-navy-900 truncate">
              {cleanTitle(source.title, source.source)}
            </h3>
            <p className="text-xs text-gray-500">Official Protocol</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
            aria-label="Close document viewer"
          >
            <X className="h-4 w-4 text-gray-400" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5">
          <div className="flex items-center gap-2 mb-3">
            <Info className="h-4 w-4 text-gray-400" />
            <p className="text-xs text-gray-500">
              Showing retrieved excerpt • Full document viewer will be available when document
              serving is implemented.
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-xs text-gray-400">Ref:</span>
              <span className="text-xs font-mono text-gray-500">{source.chunkId}</span>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
              {source.excerpt || 'Document content is not available for preview.'}
            </p>
          </div>
        </div>
        <div className="px-5 py-3 border-t border-gray-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Answer Renderer ─────────────────────────────────────────────

function AnswerDisplay({ answer, chunksUsed }: { answer: string; chunksUsed: number }) {
  // Markdown-lite rendering: headers, bullets, numbered lists, blockquotes, dividers, code, bold
  const renderAnswer = (text: string) => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let listItems: string[] = [];
    let listType: 'ul' | 'ol' | null = null;

    const flushList = () => {
      if (listItems.length === 0) return;
      if (listType === 'ol') {
        elements.push(
          <ol key={`ol-${elements.length}`} className="list-decimal list-inside space-y-1 my-2 text-sm text-gray-700">
            {listItems.map((item, i) => (
              <li key={i}>{renderInline(item)}</li>
            ))}
          </ol>,
        );
      } else {
        elements.push(
          <ul key={`ul-${elements.length}`} className="list-disc list-inside space-y-1 my-2 text-sm text-gray-700">
            {listItems.map((item, i) => (
              <li key={i}>{renderInline(item)}</li>
            ))}
          </ul>,
        );
      }
      listItems = [];
      listType = null;
    };

    for (const line of lines) {
      const trimmed = line.trim();

      // Divider / Horizontal Rule
      if (trimmed === '---' || trimmed === '***' || trimmed === '___') {
        flushList();
        elements.push(<hr key={elements.length} className="my-3.5 border-gray-200" />);
        continue;
      }

      // Blockquotes / System Notes
      if (trimmed.startsWith('> ') || trimmed === '>') {
        flushList();
        const quoteContent = trimmed.startsWith('> ') ? trimmed.slice(2).trim() : '';
        elements.push(
          <div
            key={elements.length}
            className="border-l-4 border-primary-500 bg-primary-50/70 rounded-r-md px-3.5 py-2.5 my-2.5 text-sm text-gray-800"
          >
            {renderInline(quoteContent)}
          </div>,
        );
        continue;
      }

      // Headers
      if (trimmed.startsWith('#### ')) {
        flushList();
        elements.push(
          <h5 key={elements.length} className="text-xs font-bold uppercase tracking-wider text-gray-600 mt-3 mb-1">
            {trimmed.slice(5)}
          </h5>,
        );
        continue;
      }
      if (trimmed.startsWith('### ')) {
        flushList();
        elements.push(
          <h4 key={elements.length} className="text-sm font-semibold text-navy-900 mt-3 mb-1">
            {trimmed.slice(4)}
          </h4>,
        );
        continue;
      }
      if (trimmed.startsWith('## ')) {
        flushList();
        elements.push(
          <h3 key={elements.length} className="text-base font-semibold text-navy-900 mt-3.5 mb-1.5">
            {trimmed.slice(3)}
          </h3>,
        );
        continue;
      }
      if (trimmed.startsWith('# ')) {
        flushList();
        elements.push(
          <h2 key={elements.length} className="text-lg font-bold text-navy-900 mt-4 mb-2">
            {trimmed.slice(2)}
          </h2>,
        );
        continue;
      }

      // Numbered list
      const numberedMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
      if (numberedMatch) {
        if (listType !== 'ol') {
          flushList();
          listType = 'ol';
        }
        listItems.push(numberedMatch[2]);
        continue;
      }

      // Bullet list
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        if (listType !== 'ul') {
          flushList();
          listType = 'ul';
        }
        listItems.push(trimmed.slice(2));
        continue;
      }

      // Empty line
      if (!trimmed) {
        flushList();
        continue;
      }

      // Regular paragraph
      flushList();
      elements.push(
        <p key={elements.length} className="text-sm text-gray-700 leading-relaxed my-1.5">
          {renderInline(trimmed)}
        </p>,
      );
    }

    flushList();
    return elements;
  };

  // Inline formatting: **bold**, `code`, *italic*, [1] source refs
  const renderInline = (text: string): React.ReactNode => {
    const parts: React.ReactNode[] = [];
    let remaining = text;
    let key = 0;

    while (remaining) {
      const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
      const codeMatch = remaining.match(/`([^`]+)`/);
      const italicMatch = remaining.match(/(?<!\*)\*([^*]+)\*(?!\*)/);
      const refMatch = remaining.match(/\[(\d+)\]/);

      type Candidate = { type: 'bold' | 'code' | 'italic' | 'ref'; index: number; full: string; content: string };
      const candidates: Candidate[] = [];

      if (boldMatch && boldMatch.index !== undefined) {
        candidates.push({ type: 'bold', index: boldMatch.index, full: boldMatch[0], content: boldMatch[1] });
      }
      if (codeMatch && codeMatch.index !== undefined) {
        candidates.push({ type: 'code', index: codeMatch.index, full: codeMatch[0], content: codeMatch[1] });
      }
      if (italicMatch && italicMatch.index !== undefined) {
        candidates.push({ type: 'italic', index: italicMatch.index, full: italicMatch[0], content: italicMatch[1] });
      }
      if (refMatch && refMatch.index !== undefined) {
        candidates.push({ type: 'ref', index: refMatch.index, full: refMatch[0], content: refMatch[1] });
      }

      if (candidates.length === 0) {
        parts.push(remaining);
        break;
      }

      candidates.sort((a, b) => a.index - b.index);
      const earliest = candidates[0];

      if (earliest.index > 0) {
        parts.push(remaining.slice(0, earliest.index));
      }

      if (earliest.type === 'bold') {
        parts.push(
          <strong key={key++} className="font-semibold text-navy-900">
            {earliest.content}
          </strong>,
        );
      } else if (earliest.type === 'code') {
        parts.push(
          <code key={key++} className="px-1.5 py-0.5 rounded bg-gray-100 text-primary-700 font-mono text-xs">
            {earliest.content}
          </code>,
        );
      } else if (earliest.type === 'italic') {
        parts.push(
          <em key={key++} className="italic text-gray-700">
            {earliest.content}
          </em>,
        );
      } else if (earliest.type === 'ref') {
        parts.push(
          <span
            key={key++}
            className="inline-flex items-center justify-center w-4 h-4 text-[10px] font-semibold bg-primary-100 text-primary-700 rounded ml-0.5"
          >
            {earliest.content}
          </span>,
        );
      }

      remaining = remaining.slice(earliest.index + earliest.full.length);
    }

    return parts;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-card shadow-card p-5 animate-slide-up">
      <div className="flex items-center gap-2 mb-3">
        <CheckCircle className="h-4.5 w-4.5 text-green-600" />
        <h2 className="text-section-title text-navy-900">HealthCompass Answer</h2>
      </div>
      <div className="border-l-2 border-primary-200 pl-4 mb-4">{renderAnswer(answer)}</div>
      <div className="pt-3 border-t border-gray-100 flex items-center gap-1.5 text-xs text-gray-400">
        <CheckCircle className="h-3.5 w-3.5" />
        Grounded response from {chunksUsed} source{chunksUsed !== 1 ? 's' : ''}
      </div>
    </div>
  );
}

// ─── Ask HealthCompass Page ──────────────────────────────────────

function AskHealthCompass() {
  const location = useLocation();
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<RagAnswer | null>(null);
  const [noResults, setNoResults] = useState(false);
  const [activeSourceIdx, setActiveSourceIdx] = useState(0);
  const [showDocumentModal, setShowDocumentModal] = useState<RagSource | null>(null);
  const [showMobileSources, setShowMobileSources] = useState(false);

  const loadingStage = useLoadingStage(loading);

  // Handle incoming question from Dashboard navigation
  useEffect(() => {
    const incomingQuestion = location.state?.question;
    if (incomingQuestion && typeof incomingQuestion === 'string') {
      setQuestion(incomingQuestion);
      // Auto-submit the question
      setTimeout(() => {
        submitQuestion(incomingQuestion);
      }, 100);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state]);

  const submitQuestion = useCallback(
    async (q?: string) => {
      const queryText = q || question;
      if (!queryText.trim() || loading) return;

      setLoading(true);
      setError(null);
      setResponse(null);
      setNoResults(false);
      setActiveSourceIdx(0);

      try {
        const result = await askHealthCompass(queryText);

        if (!result.sources.length && result.answer.toLowerCase().includes("don't have enough")) {
          setNoResults(true);
        }

        setResponse(result);
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.status === 503) {
            setError(
              'The HealthCompass service is temporarily unavailable. Please ensure the backend is running and API keys are configured.',
            );
          } else {
            setError(err.message);
          }
        } else {
          setError('An unexpected error occurred. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    },
    [question, loading],
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitQuestion();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitQuestion();
    }
  };

  const handleSuggestionClick = (q: string) => {
    setQuestion(q);
    submitQuestion(q);
  };

  const handleFollowUp = (q: string) => {
    setQuestion(q);
    submitQuestion(q);
  };

  const hasSources = response && response.sources.length > 0;

  // Clean document title - remove filesystem paths and technical IDs
  const cleanTitle = (title: string, source: string) => {
    // Prefer title if available and clean
    if (title && !title.includes('\\') && !title.includes('/') && !title.includes('C:')) {
      // Remove technical IDs like "d3a0d613" from end
      return title.replace(/\s*[a-f0-9]{8,}(\.pdf)?$/i, '').replace(/\.pdf$/i, '');
    }
    // Fallback to source, clean up path
    if (source) {
      const parts = source.split(/[/\\]/);
      const filename = parts[parts.length - 1] || source;
      return filename.replace(/\s*[a-f0-9]{8,}(\.pdf)?$/i, '').replace(/\.pdf$/i, '');
    }
    return 'Document';
  };

  return (
    <div className="flex h-full flex-col lg:flex-row animate-fade-in">
      {/* ── Main Content ─────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-6 py-6 lg:px-8 lg:max-w-4xl">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-navy-900 mb-0.5">Ask HealthCompass</h1>
            <p className="text-sm text-gray-500">
              Official public-health protocols and guidance, grounded in your knowledge base.
            </p>
          </div>

          {/* Question Composer */}
          <div className="bg-white border border-gray-200 rounded-card shadow-card p-5 mb-6">
            <form onSubmit={handleSubmit}>
              <div className="relative mb-3">
                <textarea
                  ref={inputRef}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about symptoms, protocols, prevention, vaccination, PPE, or field guidance..."
                  rows={2}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-button text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none resize-none transition-shadow"
                  aria-label="Ask a question"
                  disabled={loading}
                />
              </div>
              <div className="flex items-center justify-between">
                <p className="text-[11px] text-gray-400 hidden sm:block">
                  Press <kbd className="px-1 py-0.5 bg-gray-100 border border-gray-200 rounded text-[10px]">Enter</kbd> to submit
                  • <kbd className="px-1 py-0.5 bg-gray-100 border border-gray-200 rounded text-[10px]">Shift+Enter</kbd> for new line
                </p>
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-button hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {loadingStage}
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      Ask HealthCompass
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Suggested Questions (show before any response) */}
          {!response && !error && !loading && (
            <div className="mb-6 animate-fade-in">
              <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">
                Suggested Questions
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {suggestedQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSuggestionClick(q)}
                    className="flex items-center gap-3 px-4 py-3 bg-white border border-gray-200 rounded-card text-left text-sm text-gray-700 hover:border-primary-200 hover:bg-primary-50/30 transition-all group focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <MessageSquare className="h-4 w-4 text-gray-300 group-hover:text-primary-500 transition-colors flex-shrink-0" />
                    <span className="group-hover:text-primary-700 transition-colors">{q}</span>
                  </button>
                ))}
              </div>

              {/* Empty state intro */}
              <div className="text-center mt-8 py-8">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary-50 mb-3">
                  <Search className="h-5 w-5 text-primary-600" />
                </div>
                <h3 className="text-sm font-medium text-gray-700 mb-1">
                  Find answers from your approved public-health guidance
                </h3>
                <p className="text-xs text-gray-400 max-w-sm mx-auto">
                  HealthCompass searches official documents in your knowledge base and
                  provides grounded, source-verified answers.
                </p>
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="space-y-4 animate-fade-in">
              {/* Question echo */}
              <div className="bg-primary-50/50 border border-primary-100 rounded-card p-4">
                <p className="text-xs text-primary-600 font-medium mb-1">Your Question</p>
                <p className="text-sm text-navy-900">{question}</p>
              </div>
              {/* Skeleton */}
              <div className="bg-white border border-gray-200 rounded-card shadow-card p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Loader2 className="h-4 w-4 text-primary-600 animate-spin" />
                  <span className="text-sm text-primary-700 font-medium animate-pulse-subtle">
                    {loadingStage}
                  </span>
                </div>
                <div className="space-y-3">
                  <div className="h-3 bg-gray-100 rounded w-full animate-pulse" />
                  <div className="h-3 bg-gray-100 rounded w-5/6 animate-pulse" />
                  <div className="h-3 bg-gray-100 rounded w-4/6 animate-pulse" />
                  <div className="h-3 bg-gray-50 rounded w-3/6 animate-pulse" />
                </div>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-orange-50 border border-orange-200 rounded-card p-4 mb-6 animate-slide-up">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-medium text-orange-900 mb-1">
                    Service Unavailable
                  </h3>
                  <p className="text-sm text-orange-700">{error}</p>
                  <p className="text-xs text-orange-500 mt-2">
                    Ensure the backend server is running and the Groq/OpenAI API key is
                    configured.
                  </p>
                  <button
                    onClick={() => {
                      setError(null);
                      submitQuestion();
                    }}
                    className="mt-3 text-xs font-medium text-orange-700 hover:text-orange-900 flex items-center gap-1"
                  >
                    Try again <ArrowRight className="h-3 w-3" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* No Results State */}
          {noResults && response && (
            <div className="bg-gray-50 border border-gray-200 rounded-card p-6 mb-6 text-center animate-slide-up">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-gray-200 mb-3">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <h3 className="text-sm font-medium text-gray-700 mb-1">
                No matching guidance found
              </h3>
              <p className="text-xs text-gray-500 mb-4 max-w-md mx-auto">
                The current knowledge base does not contain enough relevant information for
                this question.
              </p>
              <div className="flex items-center justify-center gap-3">
                <button
                  onClick={() => {
                    setQuestion('');
                    setResponse(null);
                    setNoResults(false);
                    inputRef.current?.focus();
                  }}
                  className="text-xs font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1"
                >
                  Try another question <ArrowRight className="h-3 w-3" />
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={() => window.location.href = '/guidance'}
                  className="text-xs font-medium text-gray-500 hover:text-gray-700 flex items-center gap-1"
                >
                  Browse Guidance Library <BookOpen className="h-3 w-3" />
                </button>
              </div>
            </div>
          )}

          {/* Response */}
          {response && !noResults && !loading && (
            <div className="space-y-4 animate-slide-up">
              {/* Question echo */}
              <div className="bg-primary-50/50 border border-primary-100 rounded-card p-4">
                <p className="text-xs text-primary-600 font-medium mb-1">Your Question</p>
                <p className="text-sm text-navy-900">{response.query}</p>
              </div>

              {/* Answer */}
              <AnswerDisplay
                answer={response.answer}
                chunksUsed={response.metadata.chunksUsed}
              />

              {/* Sources used (inline summary) */}
              {response.sources.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-gray-400">Sources:</span>
                  {response.sources.map((s, idx) => (
                    <span
                      key={s.chunkId}
                      className="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
                    >
                      <span className="inline-flex items-center justify-center w-3.5 h-3.5 text-[9px] font-semibold bg-primary-100 text-primary-700 rounded">
                        {idx + 1}
                      </span>
                      {cleanTitle(s.title, s.source)}
                    </span>
                  ))}
                </div>
              )}

              {/* Mobile source toggle */}
              {hasSources && (
                <button
                  onClick={() => setShowMobileSources(!showMobileSources)}
                  className="lg:hidden w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-white border border-gray-200 rounded-card text-sm text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  <FileText className="h-4 w-4" />
                  {showMobileSources ? 'Hide' : 'View'} Source Details
                  <ChevronRight
                    className={`h-4 w-4 transition-transform ${showMobileSources ? 'rotate-90' : ''}`}
                  />
                </button>
              )}

              {/* Mobile source panel */}
              {showMobileSources && hasSources && (
                <div className="lg:hidden bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden animate-slide-up">
                  <SourcePanel
                    sources={response.sources}
                    activeSourceIdx={activeSourceIdx}
                    onSourceSelect={setActiveSourceIdx}
                    onViewDocument={setShowDocumentModal}
                  />
                </div>
              )}

              {/* Follow-up */}
              <div className="bg-white border border-gray-200 rounded-card shadow-card p-4">
                <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">
                  Suggested Follow-ups
                </p>
                <div className="flex flex-wrap gap-2">
                  {followUpSuggestions.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleFollowUp(q)}
                      className="text-xs px-3 py-1.5 bg-gray-100 text-gray-600 rounded-button hover:bg-primary-50 hover:text-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Source Panel (Desktop) ─────────────────────────── */}
      {hasSources && (
        <div className="hidden lg:block w-[340px] border-l border-gray-200 bg-white overflow-hidden flex-shrink-0">
          <SourcePanel
            sources={response!.sources}
            activeSourceIdx={activeSourceIdx}
            onSourceSelect={setActiveSourceIdx}
            onViewDocument={setShowDocumentModal}
          />
        </div>
      )}

      {/* ── Document Modal ────────────────────────────────── */}
      {showDocumentModal && (
        <DocumentModal
          source={showDocumentModal}
          onClose={() => setShowDocumentModal(null)}
        />
      )}
    </div>
  );
}

export default AskHealthCompass;
