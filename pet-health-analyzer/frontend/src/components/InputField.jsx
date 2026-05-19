export default function InputField({ label, type = 'text', value, onChange, placeholder }) {
  return (
    <div className="input-group">
      <label className="input-label">{label}</label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="input-field"
      />
    </div>
  );
}
