import { motion } from 'framer-motion';
import type { BiasReport as BiasReportType } from '../api/client';

interface BiasReportProps {
  report: BiasReportType;
  title?: string;
}

const BIAS_LABELS: Record<string, { name: string; icon: string }> = {
  confirmation_bias: { name: 'Confirmation Bias', icon: '🔄' },
  anchoring_bias: { name: 'Anchoring Bias', icon: '⚓' },
  availability_heuristic: { name: 'Availability Heuristic', icon: '📰' },
  sycophancy_bias: { name: 'Sycophancy', icon: '🤝' },
  overconfidence_bias: { name: 'Overconfidence', icon: '💪' },
  framing_effect: { name: 'Framing Effect', icon: '🖼️' },
  recency_bias: { name: 'Recency Bias', icon: '🕐' },
  bandwagon_effect: { name: 'Bandwagon Effect', icon: '🚂' },
};

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.75) return 'var(--color-accent-rose)';
  if (confidence >= 0.45) return 'var(--color-accent-amber)';
  return 'var(--color-accent-emerald)';
}

export default function BiasReport({ report, title = 'Bias Report' }: BiasReportProps) {
  if (!report.is_biased) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass-card w-full max-w-4xl mx-auto mt-6"
        id="bias-report-clean"
      >
        <div className="text-center py-4">
          <span className="text-3xl">🛡️</span>
          <p className="text-sm mt-2 font-medium" style={{ color: 'var(--color-accent-emerald)' }}>
            No cognitive biases detected
          </p>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
            {report.classifier_available ? 'Checked with RoBERTa classifier + 8 rule-based detectors' : 'Checked with 8 rule-based detectors'}
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="glass-card w-full max-w-4xl mx-auto mt-6"
      id="bias-report"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: 'var(--color-text-secondary)' }}>
          {title}
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Overall:
          </span>
          <span
            className="text-sm font-bold"
            style={{ color: getConfidenceColor(report.overall_bias_score) }}
          >
            {(report.overall_bias_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {report.biases_detected.map((bias, i) => {
          const label = BIAS_LABELS[bias.bias_type] || { name: bias.bias_type, icon: '⚠️' };
          const color = getConfidenceColor(bias.confidence);

          return (
            <motion.div
              key={bias.bias_type}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 * i }}
              className="p-4 rounded-xl"
              style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--color-border)' }}
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xl">{label.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">{label.name}</span>
                    <span className={`badge badge-${bias.severity}`}>{bias.severity}</span>
                    <span className="text-xs ml-auto px-2 py-0.5 rounded" style={{ background: 'var(--color-bg-secondary)', color: 'var(--color-text-muted)' }}>
                      {bias.detection_method}
                    </span>
                  </div>
                </div>
              </div>

              {/* Confidence bar */}
              <div className="mb-2">
                <div className="flex justify-between text-xs mb-1">
                  <span style={{ color: 'var(--color-text-muted)' }}>Confidence</span>
                  <span style={{ color }}>{(bias.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="confidence-bar">
                  <div
                    className="confidence-bar-fill"
                    style={{ width: `${bias.confidence * 100}%`, background: color }}
                  />
                </div>
              </div>

              {/* Evidence */}
              <p className="text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                {bias.evidence}
              </p>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
