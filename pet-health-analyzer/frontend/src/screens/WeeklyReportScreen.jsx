import { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';

// cv_class → 상태 매핑
const STATUS_MAP = {
  normal:         { value: 3, label: '정상', color: '#5B9E6A' },
  caution:        { value: 2, label: '주의', color: '#E8A838' },
  'soft-poop':    { value: 2, label: '주의', color: '#E8A838' },
  diarrhea:       { value: 1, label: '위험', color: '#D9534F' },
  'lack-of-water':{ value: 1, label: '위험', color: '#D9534F' },
};

const CONDITION_COLORS = {
  energy:   { positive: ['활발'],    negative: ['기력저하'] },
  appetite: { positive: ['정상'],    negative: ['거부'] },
  vomiting: { positive: ['없음'],    negative: ['있음'] },
};

function conditionColor(key, value) {
  if (CONDITION_COLORS[key]?.positive.includes(value)) return '#5B9E6A';
  if (CONDITION_COLORS[key]?.negative.includes(value)) return '#D9534F';
  return '#E8A838';
}

function getMode(values) {
  const counts = {};
  values.filter(Boolean).forEach(v => { counts[v] = (counts[v] || 0) + 1; });
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return entries[0] ? { value: entries[0][0], count: entries[0][1] } : { value: '-', count: 0 };
}

function formatShortDate(iso) {
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function formatDateRange(records) {
  if (!records.length) return '';
  const first = new Date(records[0].saved_at);
  const last  = new Date(records[records.length - 1].saved_at);
  const fmt = d => `${d.getMonth() + 1}/${d.getDate()}`;
  return `${fmt(first)} ~ ${fmt(last)}`;
}

function processRecords(records) {
  return records.map(r => {
    const status = STATUS_MAP[r.result?.cv_class] ?? { value: 2, label: '주의', color: '#E8A838' };
    return {
      date:        formatShortDate(r.saved_at),
      status:      status.value,
      statusLabel: status.label,
      statusColor: status.color,
      walk:        parseInt(r.categories?.activity?.walkMinutes) || 0,
      energy:      r.categories?.condition?.energy   || '',
      appetite:    r.categories?.condition?.appetite || '',
      vomiting:    r.categories?.condition?.vomiting || '',
    };
  });
}

// 변 상태 차트 커스텀 점
function StatusDot({ cx, cy, payload }) {
  if (cx == null || cy == null) return null;
  return (
    <circle
      cx={cx} cy={cy} r={7}
      fill={payload.statusColor}
      stroke="#fff" strokeWidth={2}
    />
  );
}

// 변 상태 차트 툴팁
function StatusTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-date">{label}</p>
      <p className="chart-tooltip-value" style={{ color: payload[0].payload.statusColor }}>
        {payload[0].payload.statusLabel}
      </p>
    </div>
  );
}

// 산책 차트 툴팁
function WalkTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-date">{label}</p>
      <p className="chart-tooltip-value" style={{ color: '#C8A97E' }}>
        {payload[0].value}분
      </p>
    </div>
  );
}

function loadProfile() {
  try {
    const raw = localStorage.getItem('petProfile');
    if (raw) return JSON.parse(raw);
  } catch {}
  return {};
}

export default function WeeklyReportScreen({ onBack }) {
  const [chartData,    setChartData]    = useState([]);
  const [dateRange,    setDateRange]    = useState('');
  const [condSummary,  setCondSummary]  = useState(null);
  const [summary,      setSummary]      = useState('');
  const [loadingData,  setLoadingData]  = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const profile = loadProfile();

  useEffect(() => {
    fetch('/api/records')
      .then(r => r.json())
      .then(records => {
        const recent = records.slice(-7);
        const processed = processRecords(recent);
        setChartData(processed);
        setDateRange(formatDateRange(recent));
        setCondSummary({
          energy:   getMode(processed.map(d => d.energy)),
          appetite: getMode(processed.map(d => d.appetite)),
          vomiting: getMode(processed.map(d => d.vomiting)),
        });
      })
      .catch(() => {})
      .finally(() => setLoadingData(false));
  }, []);

  useEffect(() => {
    fetch('/api/weekly-summary')
      .then(r => r.json())
      .then(data => setSummary(data.summary ?? ''))
      .catch(() => setSummary('AI 코멘트를 불러올 수 없습니다.'))
      .finally(() => setLoadingSummary(false));
  }, []);

  return (
    <div className="screen">
      {/* 헤더 */}
      <button className="btn-back" onClick={onBack}>← 뒤로가기</button>
      <div className="weekly-header">
        <h1 className="weekly-title">
          <span className="name-highlight">{profile.name || '반려동물'}</span>의 주간 리포트
        </h1>
        {dateRange && <p className="weekly-date-range">{dateRange}</p>}
      </div>

      {loadingData ? (
        <div className="loading-state" style={{ flex: 'none', paddingTop: 40 }}>
          <div className="spinner" />
          <p className="loading-text">데이터를 불러오는 중...</p>
        </div>
      ) : chartData.length === 0 ? (
        <div className="weekly-empty">
          <p>분석 기록이 없습니다.</p>
          <p>변 사진을 업로드하고 결과를 출력해보세요.</p>
        </div>
      ) : (
        <>
          {/* 그래프 1 — 변 상태 추이 */}
          <div className="chart-card">
            <p className="chart-title-text">변 상태 추이</p>
            <ResponsiveContainer width="100%" height={175}>
              <LineChart data={chartData} margin={{ top: 12, right: 12, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#EEEBE4" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis
                  domain={[0.5, 3.5]}
                  ticks={[1, 2, 3]}
                  tickFormatter={v => ({ 1: '위험', 2: '주의', 3: '정상' }[v] ?? '')}
                  tick={{ fontSize: 11 }}
                  width={46}
                />
                <Tooltip content={<StatusTooltip />} />
                <Line
                  type="monotone"
                  dataKey="status"
                  stroke="#C8A97E"
                  strokeWidth={2}
                  dot={<StatusDot />}
                  activeDot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* 그래프 2 — 산책 시간 추이 */}
          <div className="chart-card">
            <p className="chart-title-text">산책 시간 (분)</p>
            <ResponsiveContainer width="100%" height={175}>
              <BarChart data={chartData} margin={{ top: 12, right: 12, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#EEEBE4" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${v}분`}
                  width={50}
                  allowDecimals={false}
                />
                <Tooltip content={<WalkTooltip />} />
                <Bar dataKey="walk" fill="#C8A97E" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* 그래프 3 — 컨디션 요약 */}
          {condSummary && (
            <div className="chart-card">
              <p className="chart-title-text">이번 주 컨디션 요약</p>
              <div className="condition-grid">
                {[
                  { label: '기력', key: 'energy',   mode: condSummary.energy },
                  { label: '식욕', key: 'appetite',  mode: condSummary.appetite },
                  { label: '구토', key: 'vomiting',  mode: condSummary.vomiting },
                ].map(({ label, key, mode }) => (
                  <div key={key} className="condition-item">
                    <p className="condition-label">{label}</p>
                    <p
                      className="condition-value"
                      style={{ color: conditionColor(key, mode.value) }}
                    >
                      {mode.value}
                    </p>
                    {mode.count > 0 && (
                      <p className="condition-count">{mode.count}회</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* AI 종합 코멘트 */}
      <div className="chart-card weekly-summary-card">
        <p className="chart-title-text">AI 종합 코멘트</p>
        {loadingSummary ? (
          <div className="summary-loading">
            <div className="spinner" />
          </div>
        ) : (
          <p className="advice-text">{summary}</p>
        )}
      </div>
    </div>
  );
}
