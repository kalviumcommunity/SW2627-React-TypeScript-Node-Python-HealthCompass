import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Bookmark,
  Upload,
  FileText,
  X,
  Loader2,
  CheckCircle,
  AlertCircle,
  Clock,
  MapPin,
  ChevronDown,
  RefreshCw,
  Eye,
  MessageSquare,
  BookOpen,
  Plus,
  Archive,
} from 'lucide-react';

// ─── Types ───────────────────────────────────────────────────────

interface GuidanceDocument {
  id: string;
  title: string;
  description: string;
  filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  category: string;
  region: string;
  authority: string;
  version: string;
  effective_date: string;
  status: string;
  chunk_count: number;
  page_count: number;
  tags: string[];
  file_hash: string;
  embedding_provider: string;
  created_at: string;
  updated_at: string;
  error_message: string | null;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CATEGORY_OPTIONS = [
  'Outbreak',
  'Vaccination',
  'PPE & Infection Control',
  'Emergency',
  'Surveillance',
  'General',
];

const REGION_OPTIONS = [
  'National',
  'District A',
  'District B',
  'North Sector',
  'South Sector',
];

// ─── Upload Modal ────────────────────────────────────────────────

function UploadModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('General');
  const [description, setDescription] = useState('');
  const [region, setRegion] = useState('National');
  const [authority, setAuthority] = useState('National Public Health Authority');
  const [version, setVersion] = useState('1.0');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [tags, setTags] = useState('');
  const [uploading, setUploading] = useState(false);
  const [, setUploadPhase] = useState<'idle' | 'uploading' | 'processing' | 'indexed' | 'failed'>('idle');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      if (!title) {
        setTitle(selected.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' '));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title.trim()) return;

    setUploading(true);
    setUploadPhase('processing');
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title.trim());
    formData.append('category', category);
    formData.append('description', description.trim());
    formData.append('region', region);
    formData.append('authority', authority.trim());
    formData.append('version', version.trim());
    formData.append('effective_date', effectiveDate);
    formData.append('tags', tags.trim());

    try {
      const res = await fetch(`${API_URL}/api/guidance/upload`, {
        method: 'POST',
        body: formData,
      });

      const body = await res.json().catch(() => ({}));

      if (!res.ok) {
        setUploadPhase('failed');
        throw new Error(body.detail || body.message || `Upload failed (${res.status})`);
      }

      if (body.status === 'indexed' || body.success) {
        setUploadPhase('indexed');
        setUploadSuccess(body.message || `Guidance document '${title}' uploaded and indexed successfully.`);
      } else {
        setUploadPhase('processing');
        setUploadSuccess('Document uploaded. Processing in background...');
      }

      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err) {
      setUploadPhase('failed');
      setUploadError(err instanceof Error ? err.message : 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in">
      <div
        className="bg-white rounded-lg shadow-xl max-w-xl w-full max-h-[85vh] flex flex-col animate-slide-up"
        role="dialog"
        aria-label="Upload Guidance Document"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Upload className="h-4.5 w-4.5 text-primary-600" />
            <h3 className="text-sm font-semibold text-navy-900">Add Guidance Document</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
            aria-label="Close"
          >
            <X className="h-4 w-4 text-gray-400" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* File Drop */}
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
              file
                ? 'border-primary-300 bg-primary-50/30'
                : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.md,.html,.htm"
              onChange={handleFileSelect}
              className="hidden"
            />
            {file ? (
              <div className="flex items-center justify-center gap-2">
                <FileText className="h-5 w-5 text-primary-600" />
                <span className="text-sm font-medium text-navy-900">{file.name}</span>
                <span className="text-xs text-gray-400">
                  ({(file.size / 1024).toFixed(1)} KB)
                </span>
              </div>
            ) : (
              <>
                <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600 mb-1">
                  Click to upload or drag and drop
                </p>
                <p className="text-xs text-gray-400">
                  PDF, TXT, MD, HTML (max 25 MB)
                </p>
              </>
            )}
          </div>

          {/* Title */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Document Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Nipah Virus Outbreak Response Protocol"
              className="w-full px-3 py-2 border border-gray-300 rounded-button text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              required
            />
          </div>

          {/* Category + Region */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Category *</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-button text-sm text-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white"
              >
                {CATEGORY_OPTIONS.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Region</label>
              <select
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-button text-sm text-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white"
              >
                {REGION_OPTIONS.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of this guidance document..."
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-button text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none resize-none"
            />
          </div>

          {/* Authority + Version + Date */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Authority</label>
              <input
                type="text"
                value={authority}
                onChange={(e) => setAuthority(e.target.value)}
                placeholder="Issuing authority"
                className="w-full px-3 py-2 border border-gray-300 rounded-button text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Version</label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="1.0"
                className="w-full px-3 py-2 border border-gray-300 rounded-button text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Effective Date</label>
              <input
                type="date"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-button text-sm text-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              />
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Tags (comma-separated)</label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g. Outbreak, PPE, Isolation"
              className="w-full px-3 py-2 border border-gray-300 rounded-button text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
            />
          </div>

          {/* Error */}
          {uploadError && (
            <div className="flex items-start gap-2 p-3 bg-orange-50 border border-orange-200 rounded-lg">
              <AlertCircle className="h-4 w-4 text-orange-600 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-orange-700">{uploadError}</p>
            </div>
          )}

          {/* Success */}
          {uploadSuccess && (
            <div className="flex items-start gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-green-700">{uploadSuccess}</p>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
          <p className="text-[11px] text-gray-400">
            Documents are automatically chunked, embedded, and indexed into the knowledge base.
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-button hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit as any}
              disabled={uploading || !file || !title.trim()}
              className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-button hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Indexing...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  Upload & Index
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Document Detail Modal ───────────────────────────────────────

function DocumentDetailModal({
  doc,
  onClose,
  onAsk,
  onViewFile,
  onReindex,
  onArchive,
  actionLoading,
}: {
  doc: GuidanceDocument;
  onClose: () => void;
  onAsk: (title: string) => void;
  onViewFile: (id: string) => void;
  onReindex: (id: string) => void;
  onArchive: (id: string) => void;
  actionLoading?: string | null;
}) {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  const statusColors: Record<string, string> = {
    active: 'bg-green-100 text-green-700',
    indexed: 'bg-green-100 text-green-700',
    processing: 'bg-amber-100 text-amber-700',
    failed: 'bg-red-100 text-red-700',
    archived: 'bg-gray-100 text-gray-600',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in">
      <div
        className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[80vh] flex flex-col animate-slide-up"
        role="dialog"
        aria-label="Document Details"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200">
          <div className="flex items-center gap-2 min-w-0">
            <BookOpen className="h-4.5 w-4.5 text-primary-600 flex-shrink-0" />
            <h3 className="text-sm font-semibold text-navy-900 truncate">{doc.title}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
            aria-label="Close"
          >
            <X className="h-4 w-4 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Status Badge */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wide ${statusColors[doc.status] || statusColors.active}`}>
              {doc.status}
            </span>
            <span className="text-xs text-gray-400">v{doc.version}</span>
            <span className="text-xs text-gray-400">•</span>
            <span className="text-xs text-gray-400">{doc.category}</span>
          </div>

          {/* Description */}
          {doc.description && (
            <p className="text-sm text-gray-600 leading-relaxed">{doc.description}</p>
          )}

          {/* Error */}
          {(doc.status === 'failed' || doc.error_message) && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-xs font-semibold text-red-800">Indexing Failed</p>
                  <p className="text-xs text-red-700 mt-0.5">{doc.error_message || 'Document processing or indexing failed.'}</p>
                  <button
                    onClick={() => onReindex(doc.id)}
                    disabled={actionLoading === doc.id}
                    className="mt-2.5 px-3 py-1 text-xs font-medium bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 transition-colors flex items-center gap-1.5"
                  >
                    {actionLoading === doc.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <RefreshCw className="h-3 w-3" />
                    )}
                    {actionLoading === doc.id ? 'Re-indexing...' : 'Retry Indexing'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Metadata Grid */}
          <div className="bg-gray-50 rounded-card p-4 grid grid-cols-2 gap-3">
            <div>
              <p className="text-[11px] text-gray-400 mb-0.5">Authority</p>
              <p className="text-xs text-gray-700 font-medium">{doc.authority}</p>
            </div>
            <div>
              <p className="text-[11px] text-gray-400 mb-0.5">Region</p>
              <p className="text-xs text-gray-700 font-medium">{doc.region}</p>
            </div>
            <div>
              <p className="text-[11px] text-gray-400 mb-0.5">Effective Date</p>
              <p className="text-xs text-gray-700 font-medium">{doc.effective_date || 'N/A'}</p>
            </div>
            <div>
              <p className="text-[11px] text-gray-400 mb-0.5">File</p>
              <p className="text-xs text-gray-700 font-medium truncate">{doc.filename}</p>
            </div>
            <div>
              <p className="text-[11px] text-gray-400 mb-0.5">Indexed Chunks</p>
              <p className="text-xs text-gray-700 font-medium">{doc.chunk_count}</p>
            </div>
            <div>
              <p className="text-[11px] text-gray-400 mb-0.5">Pages</p>
              <p className="text-xs text-gray-700 font-medium">{doc.page_count}</p>
            </div>
            <div>
              <p className="text-[11px] text-gray-400 mb-0.5">Embedding</p>
              <p className="text-xs text-gray-700 font-medium capitalize">{doc.embedding_provider}</p>
            </div>
            <div>
              <p className="text-[11px] text-gray-400 mb-0.5">File Size</p>
              <p className="text-xs text-gray-700 font-medium">{(doc.file_size / 1024).toFixed(1)} KB</p>
            </div>
          </div>

          {/* Tags */}
          {doc.tags.length > 0 && (
            <div>
              <p className="text-[11px] text-gray-400 mb-1.5">Tags</p>
              <div className="flex flex-wrap gap-1.5">
                {doc.tags.map((tag) => (
                  <span key={tag} className="text-[11px] px-2 py-0.5 bg-primary-50 text-primary-700 rounded">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => onAsk(doc.title)}
              className="px-3 py-1.5 text-xs font-medium text-primary-700 bg-primary-50 rounded-button hover:bg-primary-100 transition-colors flex items-center gap-1.5"
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Ask About This
            </button>
            <button
              onClick={() => onViewFile(doc.id)}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-button hover:bg-gray-200 transition-colors flex items-center gap-1.5"
            >
              <Eye className="h-3.5 w-3.5" />
              View File
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onReindex(doc.id)}
              disabled={actionLoading === doc.id}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-button hover:bg-gray-200 disabled:opacity-50 transition-colors flex items-center gap-1.5"
              title="Re-index this document"
            >
              {actionLoading === doc.id ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <RefreshCw className="h-3.5 w-3.5" />
              )}
              {actionLoading === doc.id ? 'Re-indexing...' : doc.status === 'failed' ? 'Retry Indexing' : 'Re-index'}
            </button>
            {doc.status !== 'archived' && (
              <button
                onClick={() => onArchive(doc.id)}
                className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-button hover:bg-gray-200 transition-colors flex items-center gap-1.5"
                title="Archive this document"
              >
                <Archive className="h-3.5 w-3.5" />
                Archive
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── GuidanceLibrary Page ────────────────────────────────────────

function GuidanceLibrary() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<GuidanceDocument[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<GuidanceDocument | null>(null);
  const [savedItems, setSavedItems] = useState<Set<string>>(new Set());

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (searchQuery.trim()) params.set('search', searchQuery.trim());
      if (categoryFilter !== 'all') params.set('category', categoryFilter);
      if (statusFilter !== 'all') params.set('status', statusFilter);

      const queryString = params.toString();
      const res = await fetch(`${API_URL}/api/guidance${queryString ? `?${queryString}` : ''}`);
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data: GuidanceDocument[] = await res.json();
      setDocuments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load guidance');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, categoryFilter, statusFilter]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleSearch = () => {
    loadDocuments();
  };

  const handleReset = () => {
    setSearchQuery('');
    setCategoryFilter('all');
    setStatusFilter('all');
  };

  const toggleSave = (id: string) => {
    const newSaved = new Set(savedItems);
    if (newSaved.has(id)) {
      newSaved.delete(id);
    } else {
      newSaved.add(id);
    }
    setSavedItems(newSaved);
  };

  const handleAsk = (title: string) => {
    navigate('/ask', { state: { question: title } });
  };

  const handleViewFile = (docId: string) => {
    window.open(`${API_URL}/api/guidance/${docId}/file`, '_blank');
  };

  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleReindex = async (docId: string) => {
    setActionLoading(docId);
    setActionError(null);
    try {
      const res = await fetch(`${API_URL}/api/guidance/${docId}/reindex`, { method: 'POST' });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          body.detail ||
          body.message ||
          `Re-index failed (${res.status})`
        );
      }
      await loadDocuments();
      if (selectedDoc?.id === docId && body.document) {
        setSelectedDoc(body.document);
      }
    } catch (err) {
      console.error('Re-index error:', err);
      setActionError(err instanceof Error ? err.message : 'Re-index failed');
      loadDocuments();
    } finally {
      setActionLoading(null);
    }
  };

  const handleArchive = async (docId: string) => {
    setActionLoading(docId);
    setActionError(null);
    try {
      const res = await fetch(`${API_URL}/api/guidance/${docId}/archive`, { method: 'POST' });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || body.message || `Archive failed (${res.status})`);
      }
      await loadDocuments();
      setSelectedDoc(null);
    } catch (err) {
      console.error('Archive error:', err);
      setActionError(err instanceof Error ? err.message : 'Archive failed');
    } finally {
      setActionLoading(null);
    }
  };

  const statusColors: Record<string, string> = {
    active: 'bg-green-100 text-green-700',
    indexed: 'bg-green-100 text-green-700',
    processing: 'bg-amber-100 text-amber-700',
    failed: 'bg-red-100 text-red-700',
    archived: 'bg-gray-100 text-gray-600',
  };

  const categoryColors: Record<string, string> = {
    outbreak: 'bg-red-50 text-red-600',
    vaccination: 'bg-blue-50 text-blue-600',
    'ppe & infection control': 'bg-amber-50 text-amber-600',
    emergency: 'bg-orange-50 text-orange-600',
    surveillance: 'bg-indigo-50 text-indigo-600',
    general: 'bg-gray-50 text-gray-600',
  };

  return (
    <div className="max-w-dashboard mx-auto px-6 py-6 lg:px-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-navy-900 mb-0.5">Guidance Library</h1>
          <p className="text-sm text-gray-500">
            Official health guidelines, vaccination protocols, and clinical advisories.
          </p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-button hover:bg-primary-700 transition-colors flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          <Plus className="h-4 w-4" />
          Add Guidance
        </button>
      </div>

      {/* Action Error Alert Banner */}
      {actionError && (
        <div className="mb-4 p-3.5 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between animate-fade-in shadow-sm">
          <div className="flex items-center gap-2.5 min-w-0">
            <AlertCircle className="h-4.5 w-4.5 text-red-600 flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-xs font-semibold text-red-800">Action Failed</p>
              <p className="text-xs text-red-700 truncate">{actionError}</p>
            </div>
          </div>
          <button
            onClick={() => setActionError(null)}
            className="p-1 text-red-400 hover:text-red-600 rounded transition-colors ml-2 flex-shrink-0"
            aria-label="Dismiss error"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Toolbar */}
      <div className="bg-white border border-gray-200 rounded-card shadow-card p-4 mb-6">
        <div className="flex items-center gap-3 flex-wrap">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Search guidelines, topics, or circular keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-button text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-shadow"
            />
          </div>

          {/* Category Filter */}
          <div className="relative">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="appearance-none pl-3 pr-8 py-2 border border-gray-300 rounded-button text-sm text-gray-700 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white"
            >
              <option value="all">All Categories</option>
              {CATEGORY_OPTIONS.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
          </div>

          {/* Status Filter */}
          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="appearance-none pl-3 pr-8 py-2 border border-gray-300 rounded-button text-sm text-gray-700 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="indexed">Indexed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
              <option value="archived">Archived</option>
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
          </div>

          {/* Reset */}
          <button
            onClick={handleReset}
            className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-button transition-colors"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-orange-50 border border-orange-200 rounded-card p-4 mb-6 border-l-4 border-l-orange-400">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-orange-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-orange-700">{error}</p>
              <button
                onClick={loadDocuments}
                className="text-xs text-orange-600 hover:text-orange-800 font-medium mt-1 flex items-center gap-1"
              >
                <RefreshCw className="h-3 w-3" /> Retry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white border border-gray-200 rounded-card p-4 shadow-card animate-pulse">
              <div className="h-4 w-16 bg-gray-200 rounded mb-3" />
              <div className="h-3 w-24 bg-gray-100 rounded mb-2" />
              <div className="h-5 w-48 bg-gray-200 rounded mb-2" />
              <div className="h-3 w-36 bg-gray-100 rounded mb-3" />
              <div className="h-3 w-full bg-gray-50 rounded mb-2" />
              <div className="h-3 w-4/5 bg-gray-50 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && documents.length === 0 && (
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary-50 mb-4">
            <BookOpen className="h-6 w-6 text-primary-600" />
          </div>
          <h3 className="text-sm font-medium text-gray-700 mb-1">
            No guidance documents found
          </h3>
          <p className="text-xs text-gray-400 mb-4 max-w-sm mx-auto">
            {searchQuery || categoryFilter !== 'all' || statusFilter !== 'all'
              ? 'Try adjusting your search or filters.'
              : 'Upload your first official health guidance document to get started.'}
          </p>
          {!searchQuery && categoryFilter === 'all' && statusFilter === 'all' && (
            <button
              onClick={() => setShowUploadModal(true)}
              className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-button hover:bg-primary-700 transition-colors flex items-center gap-2 mx-auto"
            >
              <Upload className="h-4 w-4" />
              Upload Document
            </button>
          )}
        </div>
      )}

      {/* Document Grid */}
      {!loading && documents.length > 0 && (
        <>
          <p className="text-xs text-gray-500 mb-4">
            Showing {documents.length} protocol{documents.length !== 1 ? 's' : ''}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="bg-white border border-gray-200 rounded-card shadow-card hover:shadow-card-hover transition-all duration-200 p-4 group cursor-pointer"
                onClick={() => setSelectedDoc(doc)}
              >
                {/* Top Row */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide ${statusColors[doc.status] || statusColors.active}`}>
                      {doc.status}
                    </span>
                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${categoryColors[doc.category.toLowerCase()] || categoryColors.general}`}>
                      {doc.category}
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleSave(doc.id);
                    }}
                    className={`p-1.5 rounded-md transition-colors ${
                      savedItems.has(doc.id)
                        ? 'bg-primary-100 text-primary-600'
                        : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'
                    }`}
                    aria-label={savedItems.has(doc.id) ? 'Unsave' : 'Save'}
                  >
                    <Bookmark className={`h-3.5 w-3.5 ${savedItems.has(doc.id) ? 'fill-current' : ''}`} />
                  </button>
                </div>

                {/* Date & Version */}
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[11px] text-gray-400 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {doc.effective_date || 'N/A'}
                  </span>
                  <span className="text-[11px] text-gray-400">v{doc.version}</span>
                </div>

                {/* Title */}
                <h3 className="text-sm font-semibold text-navy-900 mb-1 group-hover:text-primary-700 transition-colors leading-snug">
                  {doc.title}
                </h3>

                {/* Authority & Region */}
                <p className="text-xs text-gray-500 mb-0.5">{doc.authority}</p>
                <p className="text-[11px] text-gray-400 mb-2 flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {doc.region}
                </p>

                {/* Processing State Banner */}
                {doc.status === 'processing' && (
                  <div className="mb-2 p-2 bg-amber-50 border border-amber-200 rounded-md flex items-center gap-1.5 animate-pulse">
                    <Loader2 className="h-3.5 w-3.5 text-amber-600 animate-spin flex-shrink-0" />
                    <p className="text-[10px] text-amber-700 font-medium">Processing & Indexing Document...</p>
                  </div>
                )}

                {/* Failed State Banner with Retry */}
                {doc.status === 'failed' && (
                  <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded-md">
                    <div className="flex items-start gap-1.5">
                      <AlertCircle className="h-3.5 w-3.5 text-red-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] font-semibold text-red-700">Indexing Failed</p>
                        <p className="text-[10px] text-red-600 line-clamp-2" title={doc.error_message || 'Indexing failed'}>
                          {doc.error_message || 'Document processing or indexing failed.'}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleReindex(doc.id);
                        }}
                        disabled={actionLoading === doc.id}
                        className="px-2 py-0.5 text-[10px] font-medium bg-red-100 hover:bg-red-200 text-red-700 rounded transition-colors flex items-center gap-1 flex-shrink-0"
                        title="Retry indexing"
                      >
                        {actionLoading === doc.id ? (
                          <Loader2 className="h-2.5 w-2.5 animate-spin" />
                        ) : (
                          <RefreshCw className="h-2.5 w-2.5" />
                        )}
                        Retry
                      </button>
                    </div>
                  </div>
                )}

                {/* Description */}
                <p className="text-xs text-gray-600 mb-3 line-clamp-2 leading-relaxed">{doc.description}</p>

                {/* Tags */}
                {doc.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {doc.tags.slice(0, 3).map((tag) => (
                      <span key={tag} className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">
                        {tag}
                      </span>
                    ))}
                    {doc.tags.length > 3 && (
                      <span className="text-[10px] text-gray-400">+{doc.tags.length - 3}</span>
                    )}
                  </div>
                )}

                {/* Footer */}
                <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                  <div className="flex items-center gap-1.5 text-[11px] text-gray-400">
                    <FileText className="h-3 w-3" />
                    {doc.chunk_count} chunks • {doc.page_count} page{doc.page_count !== 1 ? 's' : ''}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAsk(doc.title);
                    }}
                    className="text-[11px] font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1 transition-colors"
                  >
                    <MessageSquare className="h-3 w-3" />
                    Ask
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={loadDocuments}
        />
      )}

      {/* Document Detail Modal */}
      {selectedDoc && (
        <DocumentDetailModal
          doc={selectedDoc}
          onClose={() => setSelectedDoc(null)}
          onAsk={handleAsk}
          onViewFile={handleViewFile}
          onReindex={handleReindex}
          onArchive={handleArchive}
          actionLoading={actionLoading}
        />
      )}
    </div>
  );
}

export default GuidanceLibrary;
