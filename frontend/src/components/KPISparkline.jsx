import React, { useMemo } from 'react';
import { AreaChart, Area, ResponsiveContainer, Tooltip } from 'recharts';

// Generates mock 7-point trend data seeded from a base value
function generateTrend(baseValue) {
  const points = [];
  let val = Math.max(0, baseValue * 0.6);
  for (let i = 0; i < 7; i++) {
    val = Math.max(0, val + (Math.random() - 0.38) * baseValue * 0.25);
    points.push({ v: Math.round(val) });
  }
  // Ensure last point trends toward baseValue
  points.push({ v: typeof baseValue === 'number' ? baseValue : 0 });
  return points;
}

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/90 backdrop-blur-sm border border-slate-200 rounded-xl px-2 py-1 text-[11px] font-semibold text-slate-700 shadow-md">
        {payload[0].value}
      </div>
    );
  }
  return null;
};

export default function KPISparkline({ value, color = '#5b7fa6' }) {
  const numericValue = parseInt(String(value)?.replace(/\D/g, '') || '0', 10);
  const data = useMemo(() => generateTrend(numericValue || 20), [numericValue]);

  return (
    <ResponsiveContainer width="100%" height={52}>
      <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={`sg-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.22} />
            <stop offset="95%" stopColor={color} stopOpacity={0.0} />
          </linearGradient>
        </defs>
        <Tooltip content={<CustomTooltip />} cursor={false} />
        <Area
          type="monotoneX"
          dataKey="v"
          stroke={color}
          strokeWidth={2}
          fill={`url(#sg-${color.replace('#', '')})`}
          dot={false}
          activeDot={{ r: 3, fill: color, strokeWidth: 0 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

