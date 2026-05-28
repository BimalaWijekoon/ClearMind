import { useWebSocket } from '../hooks/useWebSocket';
import QueryInput from '../components/QueryInput';
import StreamingSteps from '../components/StreamingSteps';
import AnswerComparison from '../components/AnswerComparison';
import BiasReport from '../components/BiasReport';
import ReasoningTrace from '../components/ReasoningTrace';

export default function Home() {
  const { steps, result, error, isProcessing, sendQuery } = useWebSocket();

  return (
    <div className="flex-1 py-8 px-4">
      {/* Hero */}
      <div className="text-center mb-10 max-w-3xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          <span className="gradient-text">ClearMind</span>
        </h1>
        <p className="text-lg" style={{ color: 'var(--color-text-secondary)' }}>
          AI Metacognition Engine — Detects and corrects cognitive biases in LLM outputs in real time
        </p>
        <div className="flex justify-center gap-6 mt-4">
          {[
            { label: '8 Bias Types', icon: '🧠' },
            { label: 'Real-Time CoT', icon: '⚡' },
            { label: 'Recursive Check', icon: '🔄' },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--color-text-muted)' }}>
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Query Input */}
      <QueryInput onSubmit={sendQuery} isProcessing={isProcessing} />

      {/* Error */}
      {error && (
        <div
          className="max-w-4xl mx-auto mt-4 p-4 rounded-xl text-sm"
          style={{
            background: 'rgba(244, 63, 94, 0.08)',
            border: '1px solid rgba(244, 63, 94, 0.2)',
            color: 'var(--color-accent-rose)',
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* Pipeline Steps */}
      <StreamingSteps steps={steps} isProcessing={isProcessing} />

      {/* Results */}
      {result && (
        <>
          <AnswerComparison
            baseAnswer={result.base_answer}
            correctedAnswer={result.corrected_answer}
            semanticSimilarity={result.semantic_similarity}
          />

          <BiasReport report={result.bias_report} />

          {result.residual_bias_report && result.residual_bias_report.is_biased && (
            <BiasReport
              report={result.residual_bias_report}
              title="Residual Biases (Post-Correction Check)"
            />
          )}

          <ReasoningTrace
            cotTrace={result.cot_trace}
            biasTypes={result.bias_report.biases_detected.map((b) => b.bias_type)}
          />

          {/* Processing time */}
          <div className="max-w-4xl mx-auto mt-4 text-center">
            <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              Pipeline completed in {(result.processing_time_ms / 1000).toFixed(2)}s
              {result.bias_report.classifier_available && ' • RoBERTa classifier active'}
            </span>
          </div>
        </>
      )}
    </div>
  );
}
