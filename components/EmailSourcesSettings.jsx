import React, { useState, useEffect } from 'react';
import { Mail, Plus, Check, X, RefreshCw, AlertCircle, Trash2, Edit2, ToggleLeft, ToggleRight, Shield } from 'lucide-react';

// Category labels for display
const CATEGORY_LABELS = {
  job_board: 'Job Boards',
  ats: 'Applicant Tracking Systems',
  custom: 'Custom Sources',
  recruiter: 'Recruiters',
  company: 'Company Careers',
};

export default function EmailSourcesSettings({ showToast }) {
  const [sources, setSources] = useState([]);
  const [categories, setCategories] = useState({});
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    sender_email: '',
    sender_pattern: '',
    subject_keywords: '',
    category: 'custom',
  });

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/email-sources');
      if (!response.ok) throw new Error('Failed to fetch sources');
      const data = await response.json();
      setSources(data.sources || []);
      setCategories(data.categories || {});
    } catch (err) {
      showToast?.('Failed to load email sources', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingId
        ? `/api/email-sources/${editingId}`
        : '/api/email-sources';
      const method = editingId ? 'PATCH' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to save source');
      }

      showToast?.(editingId ? 'Source updated' : 'Source added', 'success');
      resetForm();
      fetchSources();
    } catch (err) {
      showToast?.(err.message, 'error');
    }
  };

  const handleToggleEnabled = async (source) => {
    try {
      const response = await fetch(`/api/email-sources/${source.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: source.enabled ? 0 : 1 }),
      });

      if (!response.ok) throw new Error('Failed to toggle source');
      showToast?.(source.enabled ? 'Source disabled' : 'Source enabled', 'success');
      fetchSources();
    } catch (err) {
      showToast?.(err.message, 'error');
    }
  };

  const handleDelete = async (source) => {
    if (!confirm(`Delete "${source.name}"? This cannot be undone.`)) return;

    try {
      const response = await fetch(`/api/email-sources/${source.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to delete source');
      }

      showToast?.('Source deleted', 'success');
      fetchSources();
    } catch (err) {
      showToast?.(err.message, 'error');
    }
  };

  const startEdit = (source) => {
    setEditingId(source.id);
    setFormData({
      name: source.name || '',
      sender_email: source.sender_email || '',
      sender_pattern: source.sender_pattern || '',
      subject_keywords: source.subject_keywords || '',
      category: source.category || 'custom',
    });
    setShowAddForm(true);
  };

  const resetForm = () => {
    setShowAddForm(false);
    setEditingId(null);
    setFormData({
      name: '',
      sender_email: '',
      sender_pattern: '',
      subject_keywords: '',
      category: 'custom',
    });
  };

  if (loading) {
    return (
      <div className="bg-parchment border border-warm-gray overflow-hidden mb-6">
        <div className="bg-warm-gray/50 px-4 py-3 border-b border-warm-gray border-l-[3px] border-l-copper">
          <h3 className="font-body font-bold text-ink flex items-center gap-2">
            <Mail size={18} className="text-copper" />
            Email Sources
          </h3>
        </div>
        <div className="p-4 text-center">
          <RefreshCw size={24} className="animate-spin text-copper mx-auto" />
          <p className="text-slate mt-2">Loading email sources...</p>
        </div>
      </div>
    );
  }

  const builtinSources = sources.filter(s => s.is_builtin);
  const customSources = sources.filter(s => !s.is_builtin);

  return (
    <div className="bg-parchment border border-warm-gray overflow-hidden mb-6">
      <div className="bg-warm-gray/50 px-4 py-3 border-b border-warm-gray border-l-[3px] border-l-copper">
        <h3 className="font-body font-bold text-ink flex items-center gap-2">
          <Mail size={18} className="text-copper" />
          Email Sources
        </h3>
        <p className="text-sm text-slate mt-1">
          Configure which email senders Hammy scans for job alerts
        </p>
      </div>

      <div className="p-4">
        {/* Summary Stats */}
        <div className="flex gap-4 mb-4 text-sm">
          <span className="text-slate">
            <strong className="text-ink">{builtinSources.length}</strong> built-in
          </span>
          <span className="text-slate">
            <strong className="text-ink">{customSources.length}</strong> custom
          </span>
          <span className="text-slate">
            <strong className="text-ink">{sources.filter(s => s.enabled).length}</strong> enabled
          </span>
        </div>

        {/* Built-in Sources Section */}
        <div className="mb-6">
          <h4 className="font-body font-semibold text-ink mb-3 flex items-center gap-2">
            <Shield size={16} className="text-patina" />
            Built-in Sources
          </h4>
          <div className="space-y-2">
            {builtinSources.map(source => (
              <SourceRow
                key={source.id}
                source={source}
                onToggle={() => handleToggleEnabled(source)}
                isBuiltin
              />
            ))}
          </div>
        </div>

        {/* Custom Sources Section */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-body font-semibold text-ink">Custom Sources</h4>
            <button
              onClick={() => {
                resetForm();
                setShowAddForm(!showAddForm);
              }}
              className="flex items-center gap-2 px-3 py-1.5 bg-copper text-parchment text-sm uppercase tracking-wide font-semibold hover:bg-copper/90 transition-colors"
            >
              <Plus size={16} />
              {showAddForm ? 'Cancel' : 'Add Source'}
            </button>
          </div>

          {/* Add/Edit Form */}
          {showAddForm && (
            <form onSubmit={handleSubmit} className="bg-warm-gray/30 border border-warm-gray p-4 mb-4">
              <h4 className="font-body font-semibold text-ink mb-3">
                {editingId ? 'Edit Source' : 'Add New Email Source'}
              </h4>
              <div className="grid gap-3">
                <div>
                  <label className="block text-sm font-body font-medium text-ink mb-1">
                    Source Name <span className="text-rust">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper transition-colors outline-none"
                    placeholder="e.g., Stripe Careers, Remote.com"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-body font-medium text-ink mb-1">
                      Sender Email
                    </label>
                    <input
                      type="text"
                      value={formData.sender_email}
                      onChange={(e) => setFormData({ ...formData, sender_email: e.target.value })}
                      className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper transition-colors outline-none"
                      placeholder="jobs@company.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-body font-medium text-ink mb-1">
                      Sender Pattern
                    </label>
                    <input
                      type="text"
                      value={formData.sender_pattern}
                      onChange={(e) => setFormData({ ...formData, sender_pattern: e.target.value })}
                      className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper transition-colors outline-none"
                      placeholder="@company.com"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-body font-medium text-ink mb-1">
                    Subject Keywords (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={formData.subject_keywords}
                    onChange={(e) => setFormData({ ...formData, subject_keywords: e.target.value })}
                    className="w-full px-3 py-2 border-b border-warm-gray bg-transparent text-ink font-body placeholder-slate focus:border-b-copper transition-colors outline-none"
                    placeholder="job, opportunity, hiring"
                  />
                </div>

                <div className="flex justify-end gap-2 mt-2">
                  <button
                    type="button"
                    onClick={resetForm}
                    className="px-4 py-2 border border-warm-gray text-slate text-sm uppercase tracking-wide font-semibold hover:bg-warm-gray/50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-copper text-parchment text-sm uppercase tracking-wide font-semibold hover:bg-copper/90 transition-colors"
                  >
                    {editingId ? 'Save Changes' : 'Add Source'}
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* Custom Sources List */}
          {customSources.length > 0 ? (
            <div className="space-y-2">
              {customSources.map(source => (
                <SourceRow
                  key={source.id}
                  source={source}
                  onToggle={() => handleToggleEnabled(source)}
                  onEdit={() => startEdit(source)}
                  onDelete={() => handleDelete(source)}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-6 text-slate">
              <Mail size={32} className="mx-auto mb-2 opacity-50" />
              <p>No custom sources yet. Add one above to start tracking emails from custom job boards.</p>
            </div>
          )}
        </div>

        {/* Help Text */}
        <div className="p-3 bg-cream/10 border border-cream/30 text-sm">
          <h4 className="font-semibold text-ink mb-1">How Email Sources Work</h4>
          <ul className="text-slate space-y-1 text-xs">
            <li>1. When you scan emails, Hammy checks sender addresses against these patterns</li>
            <li>2. Built-in sources use specialized parsers optimized for each job board</li>
            <li>3. Custom sources use AI to extract job details from email content</li>
            <li>4. Disable sources you don't use to speed up scanning</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

// Source row component
function SourceRow({ source, onToggle, onEdit, onDelete, isBuiltin }) {
  const enabled = source.enabled;

  return (
    <div className={`flex items-center gap-3 p-3 border transition-colors ${
      enabled ? 'border-warm-gray bg-parchment' : 'border-warm-gray/50 bg-warm-gray/20'
    }`}>
      {/* Toggle */}
      <button
        onClick={onToggle}
        className={`flex-shrink-0 ${enabled ? 'text-patina' : 'text-slate'}`}
        title={enabled ? 'Disable source' : 'Enable source'}
      >
        {enabled ? <ToggleRight size={24} /> : <ToggleLeft size={24} />}
      </button>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`font-body font-semibold ${enabled ? 'text-ink' : 'text-slate'}`}>
            {source.name}
          </span>
          {isBuiltin && (
            <span className="px-1.5 py-0.5 bg-patina/20 text-patina text-xs uppercase tracking-wide">
              Built-in
            </span>
          )}
          {source.parser_class && (
            <span className="px-1.5 py-0.5 bg-copper/20 text-copper text-xs uppercase tracking-wide">
              Specialized
            </span>
          )}
        </div>
        <div className="text-xs text-slate mt-0.5 truncate">
          {source.sender_pattern || source.sender_email || 'No pattern'}
          {source.subject_keywords && ` · Keywords: ${source.subject_keywords}`}
        </div>
      </div>

      {/* Actions */}
      {!isBuiltin && (
        <div className="flex items-center gap-1">
          {onEdit && (
            <button
              onClick={onEdit}
              className="p-1.5 text-slate hover:text-copper transition-colors"
              title="Edit source"
            >
              <Edit2 size={16} />
            </button>
          )}
          {onDelete && (
            <button
              onClick={onDelete}
              className="p-1.5 text-slate hover:text-rust transition-colors"
              title="Delete source"
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>
      )}
    </div>
  );
}
