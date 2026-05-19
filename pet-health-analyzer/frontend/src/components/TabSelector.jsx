export default function TabSelector({ label, options, value, onChange }) {
  return (
    <div className="input-group">
      <label className="input-label">{label}</label>
      <div className="tab-group">
        {options.map((opt) => (
          <button
            key={opt.value}
            className={`tab-btn${value === opt.value ? ' active' : ''}`}
            onClick={() => onChange(opt.value)}
            type="button"
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
