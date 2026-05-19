import { useState, useRef } from 'react';

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

function loadProfile() {
  try {
    const raw = localStorage.getItem('petProfile');
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore
  }
  return {};
}

export default function ReportScreen({ onEdit }) {
  const [result, setResult] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const fileInputRef = useRef(null);
  const profile = loadProfile();

  const uploadImage = async (file) => {
    if (!file.type.startsWith('image/')) {
      alert('이미지 파일만 업로드 가능합니다.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);

    setIsLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('profile', JSON.stringify(profile));

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error(`서버 오류: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      alert(`분석 중 오류가 발생했습니다.\n${err.message}`);
      setPreview(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadImage(file);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) uploadImage(file);
    e.target.value = '';
  };

  const handleReanalyze = () => {
    setResult(null);
    setPreview(null);
  };

  const color = result ? CLASS_COLORS[result.cv_class] : undefined;
  const label = result ? CLASS_LABELS[result.cv_class] : undefined;
  const pct = result ? Math.round(result.confidence * 100) : 0;

  return (
    <div className="screen">
      <div className="report-header">
        <div>
          <p className="report-greeting">안녕하세요 👋</p>
          <h1 className="report-title">
            <span className="name-highlight">{profile.name || '반려동물'}</span>의{'\n'}건강 리포트
          </h1>
        </div>
        <button className="icon-btn" onClick={onEdit} title="정보 수정">
          ⚙️
        </button>
      </div>

      {isLoading ? (
        <div className="loading-state">
          {preview && (
            <img src={preview} className="preview-img" alt="업로드된 이미지" />
          )}
          <div className="spinner" />
          <p className="loading-text">AI가 분석 중입니다...</p>
        </div>
      ) : result ? (
        <>
          {preview && (
            <img src={preview} className="preview-img" alt="분석된 이미지" />
          )}
          <div className="card">
            <p className="card-label">대변 분석 결과</p>
            <div className="class-badge" style={{ color }}>
              {label}
            </div>
            <div className="result-row">
              <span className="result-key">Bristol 등급</span>
              <span className="result-value">{result.bristol_grade}등급</span>
            </div>
            <div className="result-row">
              <span className="result-key">모델 신뢰도</span>
              <span className="result-value">{pct}%</span>
            </div>
            <div className="confidence-bar">
              <div
                className="confidence-fill"
                style={{ width: `${pct}%`, background: color }}
              />
            </div>
          </div>

          <div className="card">
            <p className="card-label">AI 건강 조언</p>
            <p className="advice-text">{result.advice}</p>
          </div>

          <button className="btn-primary" onClick={handleReanalyze}>
            다시 분석하기
          </button>
        </>
      ) : (
        <>
          <div
            className={`drop-zone${isDragging ? ' dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
            <div className="drop-zone-icon">
              {isDragging ? '🎯' : '📷'}
            </div>
            <p className="drop-zone-title">
              {isDragging ? '여기에 놓으세요!' : '사진을 업로드해주세요'}
            </p>
            <p className="drop-zone-desc">
              드래그하거나 클릭하여 이미지를 선택하세요
            </p>
          </div>
          <p className="upload-hint">
            반려동물의 대변 사진으로 건강 상태를 분석해드립니다
          </p>
        </>
      )}
    </div>
  );
}
