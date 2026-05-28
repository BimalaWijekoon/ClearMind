import { motion } from 'framer-motion';
import CalibrationChart from '../components/CalibrationChart';

export default function EvaluationPage() {
  // Placeholder data — populated after running evaluation notebooks
  const benchmarkResults = [
    { metric: 'TruthfulQA Accuracy', base: '—', clearmind: '—', delta: '—' },
    { metric: 'Bias Detection F1 (macro)', base: '—', clearmind: '—', delta: '—' },
    { metric: 'ECE (before calibration)', base: '—', clearmind: '—', delta: '—' },
    { metric: 'ECE (after temp. scaling)', base: '—', clearmind: '—', delta: '—' },
    { metric: 'CrowS-Pairs Stereotype Reduction', base: '—', clearmind: '—', delta: '—' },
    { metric: 'Avg Semantic Similarity', base: '—', clearmind: '—', delta: '—' },
    { metric: 'Avg Pipeline Latency', base: '—', clearmind: '—', delta: '—' },
  ];

  const perClassF1 = [
    { bias: 'Confirmation', f1: '—', support: '—' },
    { bias: 'Anchoring', f1: '—', support: '—' },
    { bias: 'Availability', f1: '—', support: '—' },
    { bias: 'Sycophancy', f1: '—', support: '—' },
    { bias: 'Overconfidence', f1: '—', support: '—' },
    { bias: 'Framing', f1: '—', support: '—' },
    { bias: 'Recency', f1: '—', support: '—' },
    { bias: 'Bandwagon', f1: '—', support: '—' },
    { bias: 'No Bias', f1: '—', support: '—' },
  ];

  return (
    <div className="flex-1 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <motion.h1
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl font-bold mb-2"
        >
          <span className="gradient-text">Evaluation &amp; Benchmarks</span>
        </motion.h1>
        <p className="text-sm mb-8" style={{ color: 'var(--color-text-muted)' }}>
          Results populated after running notebook 06_full_evaluation_benchmark.ipynb
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Main Results Table */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card"
          >
            <h3 className="text-sm font-semibold uppercase tracking-wider mb-4" style={{ color: 'var(--color-text-secondary)' }}>
              Benchmark Results
            </h3>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <th className="text-left py-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>Metric</th>
                  <th className="text-center py-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>Base LLM</th>
                  <th className="text-center py-2 font-medium" style={{ color: 'var(--color-accent-violet)' }}>ClearMind</th>
                  <th className="text-center py-2 font-medium" style={{ color: 'var(--color-accent-emerald)' }}>Δ</th>
                </tr>
              </thead>
              <tbody>
                {benchmarkResults.map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td className="py-3 text-sm" style={{ color: 'var(--color-text-primary)' }}>{row.metric}</td>
                    <td className="py-3 text-center font-mono text-xs" style={{ color: 'var(--color-text-secondary)' }}>{row.base}</td>
                    <td className="py-3 text-center font-mono text-xs font-bold" style={{ color: 'var(--color-accent-violet)' }}>{row.clearmind}</td>
                    <td className="py-3 text-center font-mono text-xs" style={{ color: 'var(--color-accent-emerald)' }}>{row.delta}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </motion.div>

          {/* Per-Class F1 Table */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card"
          >
            <h3 className="text-sm font-semibold uppercase tracking-wider mb-4" style={{ color: 'var(--color-text-secondary)' }}>
              Per-Class Bias Detection F1
            </h3>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <th className="text-left py-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>Bias Type</th>
                  <th className="text-center py-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>F1 Score</th>
                  <th className="text-center py-2 font-medium" style={{ color: 'var(--color-text-muted)' }}>Support</th>
                </tr>
              </thead>
              <tbody>
                {perClassF1.map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td className="py-2.5" style={{ color: 'var(--color-text-primary)' }}>{row.bias}</td>
                    <td className="py-2.5 text-center font-mono text-xs" style={{ color: 'var(--color-accent-cyan)' }}>{row.f1}</td>
                    <td className="py-2.5 text-center font-mono text-xs" style={{ color: 'var(--color-text-muted)' }}>{row.support}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        </div>

        {/* Calibration Chart */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-6"
        >
          <CalibrationChart />
        </motion.div>

        {/* Note */}
        <div
          className="mt-6 p-4 rounded-xl text-sm"
          style={{
            background: 'rgba(6, 182, 212, 0.06)',
            border: '1px solid rgba(6, 182, 212, 0.15)',
            color: 'var(--color-accent-cyan)',
          }}
        >
          💡 <strong>Note:</strong> Run the evaluation notebooks to populate these tables with real data.
          The calibration chart above shows sample data — replace with actual ECE results from notebook 04.
        </div>
      </div>
    </div>
  );
}
