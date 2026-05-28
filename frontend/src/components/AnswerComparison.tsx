import { motion } from 'framer-motion';

interface AnswerComparisonProps {
  baseAnswer: string;
  correctedAnswer: string | null;
  semanticSimilarity: number | null;
}

export default function AnswerComparison({ baseAnswer, correctedAnswer, semanticSimilarity }: AnswerComparisonProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="w-full max-w-4xl mx-auto mt-6"
    >
      {/* Similarity badge */}
      {correctedAnswer && semanticSimilarity != null && (
        <div className="flex justify-center mb-4">
          <div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
            style={{
              background: 'rgba(124, 58, 237, 0.1)',
              border: '1px solid rgba(124, 58, 237, 0.2)',
              color: 'var(--color-accent-violet)',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
            Semantic Similarity: {(semanticSimilarity * 100).toFixed(1)}%
            {semanticSimilarity < 0.7 && <span className="text-xs opacity-70">(significant correction)</span>}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Base Answer */}
        <div className="glass-card" id="base-answer">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">🤖</span>
            <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: 'var(--color-text-secondary)' }}>
              Original Answer
            </h3>
            {correctedAnswer && (
              <span className="badge badge-high ml-auto">Biased</span>
            )}
          </div>
          <div
            className="text-sm leading-relaxed whitespace-pre-wrap"
            style={{
              color: correctedAnswer ? 'var(--color-text-muted)' : 'var(--color-text-primary)',
            }}
          >
            {baseAnswer}
          </div>
        </div>

        {/* Corrected Answer */}
        {correctedAnswer ? (
          <div className="glass-card gradient-border" id="corrected-answer">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">✨</span>
              <h3 className="text-sm font-semibold uppercase tracking-wider gradient-text">
                Corrected Answer
              </h3>
              <span className="badge badge-low ml-auto">Debiased</span>
            </div>
            <div className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--color-text-primary)' }}>
              {correctedAnswer}
            </div>
          </div>
        ) : (
          <div className="glass-card flex items-center justify-center" id="no-correction">
            <div className="text-center py-8">
              <span className="text-4xl mb-3 block">✅</span>
              <p className="text-sm font-medium" style={{ color: 'var(--color-accent-emerald)' }}>
                No Correction Needed
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
                No cognitive biases were detected
              </p>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
