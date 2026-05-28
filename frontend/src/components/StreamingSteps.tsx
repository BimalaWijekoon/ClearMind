import { motion, AnimatePresence } from 'framer-motion';
import type { StepUpdate } from '../api/client';

interface StreamingStepsProps {
  steps: StepUpdate[];
  isProcessing: boolean;
}

const STEP_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  base_agent: { label: 'Base Agent — Generating answer with Chain-of-Thought', icon: '🤖', color: 'var(--color-accent-cyan)' },
  monitor_agent: { label: 'Monitor Agent — Analyzing reasoning for biases', icon: '🔍', color: 'var(--color-accent-amber)' },
  debias_agent: { label: 'Debias Agent — Applying bias-specific corrections', icon: '🛠️', color: 'var(--color-accent-emerald)' },
  post_check_monitor: { label: 'Post-Check — Verifying correction quality', icon: '✅', color: 'var(--color-accent-violet)' },
  complete: { label: 'Pipeline Complete', icon: '🎯', color: 'var(--color-accent-emerald)' },
};

export default function StreamingSteps({ steps, isProcessing }: StreamingStepsProps) {
  if (steps.length === 0 && !isProcessing) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-4xl mx-auto mt-6"
    >
      <div className="glass-card">
        <h3 className="text-sm font-semibold mb-4 uppercase tracking-wider" style={{ color: 'var(--color-text-secondary)' }}>
          Pipeline Progress
        </h3>
        <div className="space-y-3">
          <AnimatePresence mode="popLayout">
            {steps.map((step, i) => {
              const config = STEP_CONFIG[step.step] || { label: step.step, icon: '⚙️', color: 'var(--color-text-secondary)' };
              const isComplete = step.status === 'complete';
              const isStarted = step.status === 'started';

              return (
                <motion.div
                  key={`${step.step}-${step.status}-${i}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                  className="flex items-center gap-3 p-3 rounded-xl transition-all"
                  style={{
                    background: isComplete
                      ? 'rgba(16, 185, 129, 0.06)'
                      : isStarted
                      ? 'rgba(124, 58, 237, 0.06)'
                      : 'transparent',
                    border: `1px solid ${isComplete ? 'rgba(16, 185, 129, 0.15)' : isStarted ? 'rgba(124, 58, 237, 0.15)' : 'transparent'}`,
                  }}
                >
                  {/* Status icon */}
                  <div className="flex-shrink-0 text-lg">
                    {isStarted && !isComplete ? (
                      <span className="inline-block w-5 h-5 border-2 rounded-full animate-spin-slow" style={{ borderColor: `${config.color}40`, borderTopColor: config.color }} />
                    ) : (
                      <span>{config.icon}</span>
                    )}
                  </div>

                  {/* Label */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium" style={{ color: isComplete ? config.color : 'var(--color-text-primary)' }}>
                      {config.label}
                    </p>
                    {isComplete && step.data && (
                      <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--color-text-muted)' }}>
                        {step.step === 'monitor_agent' && step.data.is_biased
                          ? `${step.data.bias_count} bias(es) detected — score: ${(step.data.overall_score as number)?.toFixed(2)}`
                          : step.step === 'monitor_agent'
                          ? 'No biases detected ✓'
                          : step.step === 'debias_agent' && step.data.action === 'skipped'
                          ? 'Skipped — no correction needed'
                          : step.step === 'debias_agent' && step.data.similarity != null
                          ? `Similarity: ${(step.data.similarity as number)?.toFixed(3)}`
                          : step.step === 'complete'
                          ? `Total time: ${(step.data.processing_time_ms as number)?.toFixed(0)}ms`
                          : ''
                        }
                      </p>
                    )}
                  </div>

                  {/* Status badge */}
                  <span className={`badge ${isComplete ? 'badge-low' : 'badge-medium'}`}>
                    {isComplete ? 'Done' : 'Running'}
                  </span>
                </motion.div>
              );
            })}
          </AnimatePresence>

          {isProcessing && steps.length > 0 && steps[steps.length - 1]?.step !== 'complete' && (
            <div className="flex items-center gap-2 py-2 px-3">
              <span className="inline-block w-3 h-3 rounded-full animate-pulse-glow" style={{ background: 'var(--color-accent-violet)' }} />
              <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Processing...</span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
