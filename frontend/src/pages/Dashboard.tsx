import { useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { useBiasAnalysis } from '../hooks/useBiasAnalysis';
import BiasHistoryTable from '../components/BiasHistoryTable';

const BIAS_COLORS: Record<string, string> = {
  confirmation_bias: '#7C3AED',
  anchoring_bias: '#06B6D4',
  availability_heuristic: '#F59E0B',
  sycophancy_bias: '#10B981',
  overconfidence_bias: '#F43F5E',
  framing_effect: '#8B5CF6',
  recency_bias: '#EC4899',
  bandwagon_effect: '#14B8A6',
};

const BIAS_NAMES: Record<string, string> = {
  confirmation_bias: 'Confirmation',
  anchoring_bias: 'Anchoring',
  availability_heuristic: 'Availability',
  sycophancy_bias: 'Sycophancy',
  overconfidence_bias: 'Overconfidence',
  framing_effect: 'Framing',
  recency_bias: 'Recency',
  bandwagon_effect: 'Bandwagon',
};

export default function Dashboard() {
  const { history, metrics, fetchHistory, fetchMetrics } = useBiasAnalysis();

  useEffect(() => {
    fetchHistory();
    fetchMetrics();
  }, [fetchHistory, fetchMetrics]);

  // Build chart data from metrics
  const biasFreqData = metrics
    ? Object.entries(metrics.bias_type_frequency).map(([type, count]) => ({
        name: BIAS_NAMES[type] || type,
        count,
        fill: BIAS_COLORS[type] || '#64748B',
      }))
    : [];

  const pieData = biasFreqData.length > 0 ? biasFreqData : [
    { name: 'No data', count: 1, fill: '#334155' },
  ];

  return (
    <div className="flex-1 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <motion.h1
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl font-bold mb-8"
        >
          <span className="gradient-text">Analytics Dashboard</span>
        </motion.h1>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Queries', value: metrics?.total_queries ?? 0, icon: '📊', color: 'var(--color-accent-cyan)' },
            { label: 'Biased Queries', value: metrics?.biased_queries ?? 0, icon: '⚠️', color: 'var(--color-accent-amber)' },
            { label: 'Bias Rate', value: `${((metrics?.bias_rate ?? 0) * 100).toFixed(1)}%`, icon: '📈', color: 'var(--color-accent-rose)' },
            { label: 'Avg Latency', value: `${((metrics?.avg_processing_time_ms ?? 0) / 1000).toFixed(1)}s`, icon: '⚡', color: 'var(--color-accent-emerald)' },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass-card text-center"
            >
              <span className="text-2xl block mb-2">{stat.icon}</span>
              <p className="text-2xl font-bold" style={{ color: stat.color }}>{stat.value}</p>
              <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>{stat.label}</p>
            </motion.div>
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Bar Chart — Bias Frequency */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="glass-card"
          >
            <h3 className="text-sm font-semibold uppercase tracking-wider mb-4" style={{ color: 'var(--color-text-secondary)' }}>
              Bias Type Frequency
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={biasFreqData} margin={{ top: 5, right: 10, left: 0, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.08)" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#64748B', fontSize: 10 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis tick={{ fill: '#64748B', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: '#111827',
                    border: '1px solid rgba(148, 163, 184, 0.12)',
                    borderRadius: '8px',
                    color: '#F1F5F9',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {biasFreqData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} fillOpacity={0.85} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Pie Chart — Bias Distribution */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="glass-card"
          >
            <h3 className="text-sm font-semibold uppercase tracking-wider mb-4" style={{ color: 'var(--color-text-secondary)' }}>
              Bias Distribution
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={50}
                  paddingAngle={2}
                  strokeWidth={0}
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#111827',
                    border: '1px solid rgba(148, 163, 184, 0.12)',
                    borderRadius: '8px',
                    color: '#F1F5F9',
                    fontSize: '12px',
                  }}
                />
                <Legend
                  wrapperStyle={{ fontSize: '11px', color: '#94A3B8' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* History Table */}
        <BiasHistoryTable history={history} />
      </div>
    </div>
  );
}
