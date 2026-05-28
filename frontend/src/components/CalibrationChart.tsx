import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface CalibrationChartProps {
  binData?: Array<{
    bin_lower: number;
    bin_upper: number;
    avg_confidence: number;
    avg_accuracy: number;
    count: number;
  }>;
  ece?: number;
}

export default function CalibrationChart({ binData, ece }: CalibrationChartProps) {
  // Use sample data if no real data provided
  const data = binData || [
    { bin_lower: 0.0, bin_upper: 0.1, avg_confidence: 0.05, avg_accuracy: 0.04, count: 12 },
    { bin_lower: 0.1, bin_upper: 0.2, avg_confidence: 0.15, avg_accuracy: 0.18, count: 28 },
    { bin_lower: 0.2, bin_upper: 0.3, avg_confidence: 0.25, avg_accuracy: 0.22, count: 45 },
    { bin_lower: 0.3, bin_upper: 0.4, avg_confidence: 0.35, avg_accuracy: 0.38, count: 52 },
    { bin_lower: 0.4, bin_upper: 0.5, avg_confidence: 0.45, avg_accuracy: 0.42, count: 67 },
    { bin_lower: 0.5, bin_upper: 0.6, avg_confidence: 0.55, avg_accuracy: 0.58, count: 73 },
    { bin_lower: 0.6, bin_upper: 0.7, avg_confidence: 0.65, avg_accuracy: 0.61, count: 89 },
    { bin_lower: 0.7, bin_upper: 0.8, avg_confidence: 0.75, avg_accuracy: 0.72, count: 95 },
    { bin_lower: 0.8, bin_upper: 0.9, avg_confidence: 0.85, avg_accuracy: 0.78, count: 64 },
    { bin_lower: 0.9, bin_upper: 1.0, avg_confidence: 0.95, avg_accuracy: 0.82, count: 38 },
  ];

  const chartData = data.filter(d => d.count > 0).map(d => ({
    name: `${(d.bin_lower * 100).toFixed(0)}-${(d.bin_upper * 100).toFixed(0)}%`,
    accuracy: parseFloat((d.avg_accuracy * 100).toFixed(1)),
    confidence: parseFloat((d.avg_confidence * 100).toFixed(1)),
    gap: parseFloat((Math.abs(d.avg_accuracy - d.avg_confidence) * 100).toFixed(1)),
  }));

  return (
    <div className="glass-card" id="calibration-chart">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: 'var(--color-text-secondary)' }}>
          Reliability Diagram
        </h3>
        {ece != null && (
          <span className="text-sm font-bold" style={{ color: ece < 0.05 ? 'var(--color-accent-emerald)' : ece < 0.1 ? 'var(--color-accent-amber)' : 'var(--color-accent-rose)' }}>
            ECE: {ece.toFixed(4)}
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.08)" />
          <XAxis dataKey="name" tick={{ fill: '#64748B', fontSize: 11 }} />
          <YAxis tick={{ fill: '#64748B', fontSize: 11 }} domain={[0, 100]} />
          <Tooltip
            contentStyle={{
              background: '#111827',
              border: '1px solid rgba(148, 163, 184, 0.12)',
              borderRadius: '8px',
              color: '#F1F5F9',
              fontSize: '12px',
            }}
          />
          <Bar dataKey="accuracy" name="Accuracy %" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.gap > 10 ? '#F43F5E' : entry.gap > 5 ? '#F59E0B' : '#10B981'} fillOpacity={0.8} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <p className="text-xs mt-2 text-center" style={{ color: 'var(--color-text-muted)' }}>
        Bars show actual accuracy per confidence bin. Color: 🟢 well-calibrated | 🟡 slight gap | 🔴 miscalibrated
      </p>
    </div>
  );
}
