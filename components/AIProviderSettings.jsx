import React, { useState, useEffect } from 'react';
import { Sparkles, Check, X, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';

// AI Provider Settings Component
export default function AIProviderSettings({ showToast }) {
  const [providers, setProviders] = useState({});
  const [currentProvider, setCurrentProvider] = useState('claude');
  const [currentModel, setCurrentModel] = useState('');
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(null);
  const [error, setError] = useState(null);

  // Fetch provider info on mount
  useEffect(() => {
    fetchProviders();
  }, []);

  const fetchProviders = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/ai/providers');
      if (!response.ok) throw new Error('Failed to fetch providers');
      const data = await response.json();
      setProviders(data.providers || {});
      setCurrentProvider(data.current_provider || 'claude');
      setCurrentModel(data.current_model || '');
    } catch (err) {
      setError(err.message);
      showToast?.('Failed to load AI provider settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  const testProvider = async (providerName) => {
    setTesting(providerName);
    try {
      const response = await fetch('/api/ai/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: providerName })
      });
      const data = await response.json();
      if (data.success) {
        showToast?.(`${data.provider} is working correctly!`, 'success');
      } else {
        showToast?.(data.message || 'Test failed', 'error');
      }
    } catch (err) {
      showToast?.(`Failed to test ${providerName}: ${err.message}`, 'error');
    } finally {
      setTesting(null);
    }
  };

  const getStatusColor = (provider) => {
    if (!provider.package_installed) return 'text-slate';
    if (!provider.has_key) return 'text-cream';
    return 'text-patina';
  };

  const getStatusText = (provider) => {
    if (!provider.package_installed) return 'Package not installed';
    if (!provider.has_key) return 'API key missing';
    return 'Ready';
  };

  const getStatusIcon = (provider) => {
    if (!provider.package_installed || !provider.has_key) {
      return <AlertCircle size={16} className="text-cream" />;
    }
    return <CheckCircle size={16} className="text-patina" />;
  };

  if (loading) {
    return (
      <div className="bg-parchment border border-warm-gray overflow-hidden mb-6">
        <div className="bg-warm-gray/50 px-4 py-3 border-b border-warm-gray border-l-[3px] border-l-copper">
          <h3 className="font-body font-bold text-ink flex items-center gap-2">
            <Sparkles size={18} className="text-copper" />
            AI Provider
          </h3>
        </div>
        <div className="p-4 text-center">
          <RefreshCw size={24} className="animate-spin text-copper mx-auto" />
          <p className="text-slate mt-2">Loading provider settings...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-parchment border border-warm-gray overflow-hidden mb-6">
        <div className="bg-warm-gray/50 px-4 py-3 border-b border-warm-gray border-l-[3px] border-l-rust">
          <h3 className="font-body font-bold text-ink flex items-center gap-2">
            <Sparkles size={18} className="text-rust" />
            AI Provider
          </h3>
        </div>
        <div className="p-4">
          <div className="flex items-center gap-2 text-rust">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
          <button
            onClick={fetchProviders}
            className="mt-3 px-4 py-2 bg-copper text-parchment rounded-none uppercase tracking-wide text-sm font-body font-semibold hover:bg-copper/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-parchment border border-warm-gray overflow-hidden mb-6">
      <div className="bg-warm-gray/50 px-4 py-3 border-b border-warm-gray border-l-[3px] border-l-copper">
        <h3 className="font-body font-bold text-ink flex items-center gap-2">
          <Sparkles size={18} className="text-copper" />
          AI Provider
        </h3>
        <p className="text-sm text-slate mt-1">
          Configure which AI service powers Hammy's analysis
        </p>
      </div>

      <div className="p-4">
        {/* Current Provider Display */}
        <div className="mb-4 p-3 bg-warm-gray/30 border border-warm-gray">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm text-slate">Currently using:</span>
              <p className="font-body font-semibold text-ink">
                {providers[currentProvider]?.name || currentProvider}
              </p>
              <p className="text-xs text-slate">{currentModel}</p>
            </div>
            <div className="flex items-center gap-2">
              {getStatusIcon(providers[currentProvider] || {})}
              <span className={`text-sm ${getStatusColor(providers[currentProvider] || {})}`}>
                {getStatusText(providers[currentProvider] || {})}
              </span>
            </div>
          </div>
        </div>

        {/* Provider Cards */}
        <div className="space-y-3">
          {Object.entries(providers).map(([key, provider]) => (
            <div
              key={key}
              className={`p-4 border transition-all ${
                key === currentProvider
                  ? 'border-copper bg-copper/5'
                  : 'border-warm-gray hover:border-slate'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-body font-semibold text-ink">{provider.name}</h4>
                    {key === currentProvider && (
                      <span className="px-2 py-0.5 bg-copper text-parchment text-xs uppercase tracking-wide">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate mt-1">
                    Env var: <code className="bg-warm-gray px-1">{provider.env_var}</code>
                  </p>
                  <div className="flex items-center gap-1 mt-1">
                    {getStatusIcon(provider)}
                    <span className={`text-xs ${getStatusColor(provider)}`}>
                      {getStatusText(provider)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {provider.has_key && provider.package_installed && (
                    <button
                      onClick={() => testProvider(key)}
                      disabled={testing === key}
                      className="px-3 py-1.5 border border-copper text-copper text-xs uppercase tracking-wide font-semibold hover:bg-copper/10 disabled:opacity-50 transition-colors"
                    >
                      {testing === key ? (
                        <RefreshCw size={14} className="animate-spin" />
                      ) : (
                        'Test'
                      )}
                    </button>
                  )}
                </div>
              </div>

              {/* Available Models */}
              {provider.models && (
                <div className="mt-3 pt-3 border-t border-warm-gray/50">
                  <span className="text-xs text-slate">Available models:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {provider.models.map((model) => (
                      <span
                        key={model}
                        className={`px-2 py-0.5 text-xs ${
                          model === currentModel
                            ? 'bg-copper text-parchment'
                            : 'bg-warm-gray text-slate'
                        }`}
                      >
                        {model}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Configuration Note */}
        <div className="mt-4 p-3 bg-cream/10 border border-cream/30">
          <h4 className="font-semibold text-ink text-sm mb-1">Configuration</h4>
          <p className="text-xs text-slate">
            To change providers, set the <code className="bg-warm-gray px-1">ai.provider</code> value
            in your <code className="bg-warm-gray px-1">config.yaml</code> file to one of:
            <code className="bg-warm-gray px-1 ml-1">claude</code>,
            <code className="bg-warm-gray px-1 ml-1">openai</code>, or
            <code className="bg-warm-gray px-1 ml-1">gemini</code>.
          </p>
          <p className="text-xs text-slate mt-2">
            Make sure you have the corresponding API key set in your <code className="bg-warm-gray px-1">.env</code> file.
          </p>
        </div>
      </div>
    </div>
  );
}
