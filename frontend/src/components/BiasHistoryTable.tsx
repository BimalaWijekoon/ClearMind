import { motion } from 'framer-motion';
import type { HistoryRecord } from '../api/client';

interface BiasHistoryTableProps {
  history: HistoryRecord[];
}

const BIAS_EMOJI: Record<string, string> = {
  confirmation_bias: '🔄',
  anchoring_bias: '⚓',
  availability_heuristic: '📰',
  sycophancy_bias: '🤝',
  overconfidence_bias: '💪',
  framing_effect: '🖼️',
  recency_bias: '🕐',
  bandwagon_effect: '🚂',
};

export default function BiasHistoryTable({ history }: BiasHistoryTableProps) {
  if (history.length === 0) {
    return (
      <div className="glass-card text-center py-12" id="history-empty">
        <span className="text-4xl block mb-3">📭</span>
        <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
          No queries yet. Start analyzing questions to build your history.
        </p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="glass-card overflow-hidden"
      id="bias-history"
    >
      <h3 className="text-sm font-semibold uppercase tracking-wider mb-4" style={{ color: 'var(--color-text-secondary)' }}>
        Query History
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              <th className="text-left py-3 px-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>Query</th>
              <th className="text-left py-3 px-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>Biases</th>
              <th className="text-center py-3 px-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>Score</th>
              <th className="text-center py-3 px-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>Similarity</th>
              <th className="text-right py-3 px-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>Time</th>
            </tr>
          </thead>
          <tbody>
            {history.map((record, i) => (
              <motion.tr
                key={record.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.03 }}
                className="transition-colors"
                style={{ borderBottom: '1px solid var(--color-border)' }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'var(--color-bg-hover)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <td className="py-3 px-2 max-w-xs truncate" style={{ color: 'var(--color-text-primary)' }}>
                  {record.query}
                </td>
                <td className="py-3 px-2">
                  <div className="flex gap-1 flex-wrap">
                    {record.biases_detected.length === 0 ? (
                      <span className="text-xs" style={{ color: 'var(--color-accent-emerald)' }}>✓ Clean</span>
                    ) : (
                      record.biases_detected.map((b) => (
                        <span key={b} title={b} className="text-sm cursor-help">
                          {BIAS_EMOJI[b] || '⚠️'}
                        </span>
                      ))
                    )}
                  </div>
                </td>
                <td className="py-3 px-2 text-center">
                  <span
                    className="font-mono text-xs font-bold"
                    style={{
                      color: record.overall_bias_score >= 0.75
                        ? 'var(--color-accent-rose)'
                        : record.overall_bias_score >= 0.45
                        ? 'var(--color-accent-amber)'
                        : 'var(--color-accent-emerald)',
                    }}
                  >
                    {(record.overall_bias_score * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="py-3 px-2 text-center font-mono text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                  {record.semantic_similarity != null ? `${(record.semantic_similarity * 100).toFixed(1)}%` : '—'}
                </td>
                <td className="py-3 px-2 text-right font-mono text-xs" style={{ color: 'var(--color-text-muted)' }}>
                  {(record.processing_time_ms / 1000).toFixed(1)}s
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}
