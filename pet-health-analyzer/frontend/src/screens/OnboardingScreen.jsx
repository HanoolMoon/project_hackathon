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

const INITIAL_FORM = {
  name: '',
  species: '개',
  age: '',
  weight: '',
  neutered: false,
  food_type: '건식',
};

export default function OnboardingScreen({ onComplete }) {
  const [form, setForm] = useState(INITIAL_FORM);

  const update = (key) => (value) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = () => {
    if (!form.name.trim()) return alert('이름을 입력해주세요.');
    if (!form.age) return alert('나이를 입력해주세요.');
    if (!form.weight) return alert('체중을 입력해주세요.');

    const profile = {
      ...form,
      age: Number(form.age),
      weight: Number(form.weight),
    };

    localStorage.setItem('petProfile', JSON.stringify(profile));
    onComplete();
  };

  return (
    <div className="screen">
      <div className="onboarding-header">
        <div className="logo">🐾</div>
        <h1 className="title">처음 만나요!</h1>
        <p className="subtitle">반려동물을 소개해주세요</p>
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

      <button className="btn-primary" onClick={handleSubmit}>
        시작하기
      </button>
    </div>
  );
}
