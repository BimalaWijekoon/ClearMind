import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ReasoningTraceProps {
  cotTrace: string;
  biasTypes?: string[];
}

export default function ReasoningTrace({ cotTrace, biasTypes = [] }: ReasoningTraceProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!cotTrace) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="glass-card w-full max-w-4xl mx-auto mt-6"
      id="reasoning-trace"
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between cursor-pointer"
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">🧠</span>
          <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: 'var(--color-text-secondary)' }}>
            Chain-of-Thought Reasoning
          </h3>
          {biasTypes.length > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(244, 63, 94, 0.1)', color: 'var(--color-accent-rose)' }}>
              {biasTypes.length} bias annotations
            </span>
          )}
        </div>
        <motion.span
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-lg"
          style={{ color: 'var(--color-text-muted)' }}
        >
          ▼
        </motion.span>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div
              className="mt-4 p-4 rounded-xl text-sm leading-relaxed whitespace-pre-wrap"
              style={{
                background: 'var(--color-bg-primary)',
                border: '1px solid var(--color-border)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.82rem',
                color: 'var(--color-text-secondary)',
              }}
            >
              {cotTrace}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
