export default function ToggleSwitch({ label, checked, onChange }) {
  return (
    <div className="input-group toggle-group">
      <span className="input-label">{label}</span>
      <button
        type="button"
        className={`toggle${checked ? ' on' : ''}`}
        onClick={() => onChange(!checked)}
        aria-checked={checked}
        role="switch"
      >
        <span className="toggle-knob" />
      </button>
    </div>
  );
}
