import { useState } from 'react';
import InputField from '../components/InputField';
import TabSelector from '../components/TabSelector';
import ToggleSwitch from '../components/ToggleSwitch';

const SPECIES_OPTIONS = [
  { label: '개', value: '개' },
  { label: '고양이', value: '고양이' },
  { label: '기타', value: '기타' },
];

const FOOD_OPTIONS = [
  { label: '건식', value: '건식' },
  { label: '습식', value: '습식' },
  { label: '생식', value: '생식' },
];

function loadSavedProfile() {
  try {
    const raw = localStorage.getItem('petProfile');
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore
  }
  return {
    name: '',
    species: '개',
    age: '',
    weight: '',
    neutered: false,
    food_type: '건식',
  };
}

export default function EditProfileScreen({ onBack, onReset }) {
  const saved = loadSavedProfile();
  const [form, setForm] = useState({
    ...saved,
    age: String(saved.age ?? ''),
    weight: String(saved.weight ?? ''),
  });

  const update = (key) => (value) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSave = () => {
    if (!form.name.trim()) return alert('이름을 입력해주세요.');
    if (!form.age) return alert('나이를 입력해주세요.');
    if (!form.weight) return alert('체중을 입력해주세요.');

    const profile = {
      ...form,
      age: Number(form.age),
      weight: Number(form.weight),
    };

    localStorage.setItem('petProfile', JSON.stringify(profile));
    onBack();
  };

  return (
    <div className="screen">
      <button className="btn-back" onClick={onBack}>
        ← 뒤로가기
      </button>

      <div className="onboarding-header" style={{ paddingTop: 0 }}>
        <h1 className="title">정보 수정</h1>
        <p className="subtitle">반려동물 정보를 변경할 수 있어요</p>
      </div>

      <div className="form-card">
        <InputField
          label="이름"
          value={form.name}
          onChange={(e) => update('name')(e.target.value)}
          placeholder="예: 초코"
        />
        <TabSelector
          label="종"
          options={SPECIES_OPTIONS}
          value={form.species}
          onChange={update('species')}
        />
        <InputField
          label="나이 (세)"
          type="number"
          value={form.age}
          onChange={(e) => update('age')(e.target.value)}
          placeholder="예: 3"
        />
        <InputField
          label="체중 (kg)"
          type="number"
          value={form.weight}
          onChange={(e) => update('weight')(e.target.value)}
          placeholder="예: 5.5"
        />
        <ToggleSwitch
          label="중성화 여부"
          checked={form.neutered}
          onChange={update('neutered')}
        />
        <TabSelector
          label="사료 종류"
          options={FOOD_OPTIONS}
          value={form.food_type}
          onChange={update('food_type')}
        />
      </div>

      <button className="btn-primary" onClick={handleSave}>
        저장하기
      </button>
      <button
        className="btn-reset"
        onClick={() => {
          if (window.confirm('반려동물 정보를 초기화할까요?')) {
            localStorage.clear();
            onReset();
          }
        }}
      >
        정보 초기화
      </button>
    </div>
  );
}
