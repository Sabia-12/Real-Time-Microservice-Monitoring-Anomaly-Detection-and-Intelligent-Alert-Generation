import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Card, Empty } from '../common/ui';
import { fmtClock, fmtTime } from '../../utils/format';

export default function MetricChart({ title, unit, data, series, domain }) {
  return (
    <Card title={`${title} (${unit})`}>
      {!data?.length ? <Empty text="No data for this range." /> : (
        <div className="h-56" role="img" aria-label={`${title} over time, in ${unit}`}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 8, left: -8, bottom: 0 }}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="t" tickFormatter={fmtClock} stroke="#64748b" fontSize={11} minTickGap={28} />
              <YAxis stroke="#64748b" fontSize={11} domain={domain || ['auto', 'auto']} />
              <Tooltip contentStyle={{ background: '#0b1220', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
                labelFormatter={fmtTime} formatter={(v, n) => [`${v} ${unit}`, n]} />
              {series.length > 1 && <Legend wrapperStyle={{ fontSize: 12 }} />}
              {series.map((s) => <Line key={s.key} type="monotone" dataKey={s.key} name={s.name} stroke={s.color} strokeWidth={2} dot={false} isAnimationActive={false} />)}
            </LineChart>
          </ResponsiveContainer>
        </div>)}
    </Card>
  );
}
