import { useState, useRef, useEffect } from 'react';
import InputField from '../components/InputField';
import TabSelector from '../components/TabSelector';

const CLASS_LABELS = {
  normal: '정상',
  diarrhea: '설사',
  'lack-of-water': '수분 부족',
  'soft-poop': '무른 변',
  unknown: '판단 불가',
};

const CLASS_COLORS = {
  normal: '#5B9E6A',
  diarrhea: '#D9534F',
  'lack-of-water': '#5B8FC9',
  'soft-poop': '#E8A838',
  unknown: '#9E9E9E',
};

const AMOUNT_OPTIONS = [
  { label: '평소', value: '평소' },
  { label: '적게', value: '적게' },
  { label: '많이', value: '많이' },
];
const YN_OPTIONS = [
  { label: '없음', value: '없음' },
  { label: '있음', value: '있음' },
];
const WATER_OPTIONS = [
  { label: '충분', value: '충분' },
  { label: '적음', value: '적음' },
  { label: '거의없음', value: '거의없음' },
];
const EXERCISE_OPTIONS = [
  { label: '평소', value: '평소' },
  { label: '적음', value: '적음' },
  { label: '많음', value: '많음' },
];
const LOCATION_OPTIONS = [
  { label: '실내', value: '실내' },
  { label: '실외', value: '실외' },
];
const ENERGY_OPTIONS = [
  { label: '활발', value: '활발' },
  { label: '보통', value: '보통' },
  { label: '기력저하', value: '기력저하' },
];
const APPETITE_OPTIONS = [
  { label: '정상', value: '정상' },
  { label: '저하', value: '저하' },
  { label: '거부', value: '거부' },
];
const WEATHER_OPTIONS = [
  { label: '맑음', value: '맑음' },
  { label: '흐림', value: '흐림' },
  { label: '비', value: '비' },
  { label: '눈', value: '눈' },
];

const STORAGE_KEY = 'healthCategories';
const EXPIRY_MS = 24 * 60 * 60 * 1000;

const INITIAL_CATEGORIES = {
  meal: { food: '', amount: '', snack: '', water: '' },
  activity: { walkMinutes: '', exercise: '', location: '' },
  condition: { energy: '', appetite: '', vomiting: '', weight: '' },
  environment: { weather: '', temperature: '', stress: '' },
};

function deepCopy(cats) {
  return {
    meal: { ...cats.meal },
    activity: { ...cats.activity },
    condition: { ...cats.condition },
    environment: { ...cats.environment },
  };
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { categories: deepCopy(INITIAL_CATEGORIES), expired: false };
    const { timestamp, data } = JSON.parse(raw);
    if (Date.now() - new Date(timestamp).getTime() > EXPIRY_MS) {
      return { categories: deepCopy(INITIAL_CATEGORIES), expired: true, expiredData: data };
    }
    return { categories: data, expired: false };
  } catch {
    return { categories: deepCopy(INITIAL_CATEGORIES), expired: false };
  }
}

function saveToStorage(categories) {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ timestamp: new Date().toISOString(), data: categories })
  );
}

async function postRecord(categories, result) {
  try {
    await fetch('/api/record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ categories, result }),
    });
  } catch {
    // silent — 기록 실패해도 UX 차단 안 함
  }
}

function loadProfile() {
  try {
    const raw = localStorage.getItem('petProfile');
    if (raw) return JSON.parse(raw);
  } catch {}
  return {};
}

export default function ReportScreen({ onEdit }) {
  const [imageFile, setImageFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [categories, setCategories] = useState(() => deepCopy(INITIAL_CATEGORIES));
  const fileInputRef = useRef(null);
  const resultRef = useRef(null);
  const profile = loadProfile();

  useEffect(() => {
    const { expired, expiredData } = loadFromStorage();
    if (expired && expiredData) {
      postRecord(expiredData, null);
    }
    // 새로고침 시 항상 초기 상태로 시작 — localStorage는 24h 만료 추적용으로만 사용
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  useEffect(() => {
    if (result && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [result]);

  const updateCat = (cat, key) => (value) => {
    setCategories((prev) => {
      const next = { ...prev, [cat]: { ...prev[cat], [key]: value } };
      saveToStorage(next);
      return next;
    });
  };

  const updateCatText = (cat, key) => (e) => updateCat(cat, key)(e.target.value);

  const handleFile = (file) => {
    if (!file.type.startsWith('image/')) {
      alert('이미지 파일만 업로드 가능합니다.');
      return;
    }
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);
    setResult(null);
  };

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setIsDragging(false); };
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
    e.target.value = '';
  };

  const handleAnalyze = async () => {
    if (!imageFile || isLoading) return;
    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', imageFile);
    formData.append('profile', JSON.stringify(profile));
    formData.append('categories', JSON.stringify(categories));
    try {
      const res = await fetch('/api/analyze', { method: 'POST', body: formData });
      if (!res.ok) throw new Error(`서버 오류: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      alert(`분석 중 오류가 발생했습니다.\n${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const color = result ? (CLASS_COLORS[result.cv_class] ?? '#9E9E9E') : undefined;
  const label = result ? (CLASS_LABELS[result.cv_class] ?? result.cv_class) : undefined;
  const pct = result ? Math.round(result.confidence * 100) : 0;

  return (
    <div className="screen">
      {/* 헤더 */}
      <div className="report-header">
        <div>
          <p className="report-greeting">안녕하세요</p>
          <h1 className="report-title">
            <span className="name-highlight">{profile.name || '반려동물'}</span>의{'\n'}건강 리포트
          </h1>
        </div>
        <button className="icon-btn" onClick={onEdit} title="정보 수정">⚙️</button>
      </div>

      {/* 사진 업로드 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
      {preview ? (
        <div className="photo-preview-wrap">
          <img src={preview} className="preview-img" alt="업로드된 사진" />
          <button className="btn-retake" onClick={() => fileInputRef.current.click()}>
            다시 찍기
          </button>
        </div>
      ) : (
        <div
          className={`drop-zone drop-zone--compact${isDragging ? ' dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
        >
          <div className="drop-zone-icon">{isDragging ? '🎯' : '📷'}</div>
          <p className="drop-zone-title">{isDragging ? '여기에 놓으세요!' : '변 사진 업로드'}</p>
          <p className="drop-zone-desc">드래그하거나 클릭하여 선택</p>
        </div>
      )}

      {/* 식사 */}
      <div className="category-block">
        <p className="category-title">🍚 식사</p>
        <div className="category-form">
          <InputField
            label="먹은 음식"
            value={categories.meal.food}
            onChange={updateCatText('meal', 'food')}
            placeholder="예: 건식사료, 닭가슴살"
          />
          <TabSelector
            label="식사량"
            options={AMOUNT_OPTIONS}
            value={categories.meal.amount}
            onChange={updateCat('meal', 'amount')}
          />
          <TabSelector
            label="간식"
            options={YN_OPTIONS}
            value={categories.meal.snack}
            onChange={updateCat('meal', 'snack')}
          />
          <TabSelector
            label="물 섭취량"
            options={WATER_OPTIONS}
            value={categories.meal.water}
            onChange={updateCat('meal', 'water')}
          />
        </div>
      </div>

      {/* 활동 */}
      <div className="category-block">
        <p className="category-title">🦮 활동</p>
        <div className="category-form">
          <InputField
            label="산책 시간 (분)"
            type="number"
            value={categories.activity.walkMinutes}
            onChange={updateCatText('activity', 'walkMinutes')}
            placeholder="예: 30"
          />
          <TabSelector
            label="운동량"
            options={EXERCISE_OPTIONS}
            value={categories.activity.exercise}
            onChange={updateCat('activity', 'exercise')}
          />
          <TabSelector
            label="활동 장소"
            options={LOCATION_OPTIONS}
            value={categories.activity.location}
            onChange={updateCat('activity', 'location')}
          />
        </div>
      </div>

      {/* 컨디션 */}
      <div className="category-block">
        <p className="category-title">💊 컨디션</p>
        <div className="category-form">
          <TabSelector
            label="기력 상태"
            options={ENERGY_OPTIONS}
            value={categories.condition.energy}
            onChange={updateCat('condition', 'energy')}
          />
          <TabSelector
            label="식욕"
            options={APPETITE_OPTIONS}
            value={categories.condition.appetite}
            onChange={updateCat('condition', 'appetite')}
          />
          <TabSelector
            label="구토"
            options={YN_OPTIONS}
            value={categories.condition.vomiting}
            onChange={updateCat('condition', 'vomiting')}
          />
          <InputField
            label="체중 (kg)"
            type="number"
            value={categories.condition.weight}
            onChange={updateCatText('condition', 'weight')}
            placeholder="예: 5.2"
          />
        </div>
      </div>

      {/* 환경 */}
      <div className="category-block">
        <p className="category-title">🌤 환경</p>
        <div className="category-form">
          <TabSelector
            label="날씨"
            options={WEATHER_OPTIONS}
            value={categories.environment.weather}
            onChange={updateCat('environment', 'weather')}
          />
          <InputField
            label="온도 (°C)"
            type="number"
            value={categories.environment.temperature}
            onChange={updateCatText('environment', 'temperature')}
            placeholder="예: 22"
          />
          <InputField
            label="스트레스 요인"
            value={categories.environment.stress}
            onChange={updateCatText('environment', 'stress')}
            placeholder="예: 낯선 손님, 이사"
          />
        </div>
      </div>

      {/* 결과 출력 버튼 */}
      <button
        className="btn-primary btn-analyze"
        onClick={handleAnalyze}
        disabled={!imageFile || isLoading}
      >
        {isLoading ? <span className="btn-spinner" /> : '결과 출력'}
      </button>

      {/* 분석 결과 */}
      {result && (
        <div ref={resultRef}>
          <div className="card" style={{ marginTop: 20 }}>
            <p className="card-label">대변 분석 결과</p>
            <div className="class-badge" style={{ color }}>{label}</div>
            <div className="result-row">
              <span className="result-key">Bristol 등급</span>
              <span className="result-value">{result.bristol_grade}등급</span>
            </div>
            <div className="result-row">
              <span className="result-key">모델 신뢰도</span>
              <span className="result-value">{pct}%</span>
            </div>
            <div className="confidence-bar">
              <div className="confidence-fill" style={{ width: `${pct}%`, background: color }} />
            </div>
          </div>
          <div className="card">
            <p className="card-label">AI 건강 조언</p>
            <p className="advice-text">{result.advice}</p>
          </div>
        </div>
      )}

    </div>
  );
}
