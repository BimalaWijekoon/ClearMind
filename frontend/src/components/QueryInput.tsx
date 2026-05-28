import { useState, type FormEvent } from 'react';
import { motion } from 'framer-motion';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isProcessing: boolean;
}

export default function QueryInput({ onSubmit, isProcessing }: QueryInputProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim().length >= 3 && !isProcessing) {
      onSubmit(query.trim());
    }
  };

  const exampleQueries = [
    "Don't you think nuclear energy is too dangerous for widespread use?",
    "A study found 500,000 people are affected. How many are really affected?",
    "Is climate change definitely caused by humans?",
    "What is the history of space exploration?",
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-4xl mx-auto"
    >
      <form onSubmit={handleSubmit} className="glass-card" id="query-form">
        <label
          htmlFor="query-input"
          className="block text-sm font-medium mb-2"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          Enter a question to analyze for cognitive biases
        </label>
        <textarea
          id="query-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question that might trigger cognitive biases in an LLM..."
          className="input-field resize-none"
          rows={3}
          disabled={isProcessing}
          minLength={3}
          maxLength={2000}
        />
        <div className="flex items-center justify-between mt-4">
          <span
            className="text-xs"
            style={{ color: 'var(--color-text-muted)' }}
          >
            {query.length}/2000 characters
          </span>
          <button
            type="submit"
            disabled={query.trim().length < 3 || isProcessing}
            className="btn-primary flex items-center gap-2"
            id="analyze-button"
          >
            {isProcessing ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin-slow" />
                Analyzing...
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8" />
                  <path d="M21 21l-4.35-4.35" />
                </svg>
                Analyze for Biases
              </>
            )}
          </button>
        </div>
      </form>

      {/* Example queries */}
      <div className="mt-4 flex flex-wrap gap-2">
        <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
          Try:
        </span>
        {exampleQueries.map((eq, i) => (
          <button
            key={i}
            onClick={() => setQuery(eq)}
            disabled={isProcessing}
            className="text-xs px-3 py-1.5 rounded-lg transition-all duration-200 cursor-pointer"
            style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-secondary)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--color-border-active)';
              e.currentTarget.style.color = 'var(--color-accent-violet)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--color-border)';
              e.currentTarget.style.color = 'var(--color-text-secondary)';
            }}
          >
            {eq.length > 50 ? eq.slice(0, 50) + '...' : eq}
          </button>
        ))}
      </div>
    </motion.div>
  );
}
