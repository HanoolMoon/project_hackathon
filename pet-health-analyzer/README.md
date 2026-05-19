# Pet Health Analyzer

반려동물의 대변 사진을 CV 모델로 분류하고, GPT API로 맞춤 건강 조언을 제공하는 CLI 도구.

## 설치

```bash
cd pet-health-analyzer
pip install -r requirements.txt
```

## 환경 변수 설정

`config/.env` 파일 생성 후 API 키 입력:

```
OPENAI_API_KEY=여기에_키_입력
```

## 실행

```bash
# 기본 실행 (첫 번째 프로필 자동 선택)
python main.py --image ./data/input_images/photo.jpg

# 특정 프로필 지정
python main.py --image ./data/input_images/photo.jpg --pet 1
```

## 테스트

```bash
python -m pytest tests/ -v
```

---

## Colab에서 poop_classifier.pkl 추출 방법

학습 완료 후 `models/poop_classifier.pkl`을 생성하려면 Colab에서 아래 코드를 실행하세요.

### 방법 1: torch.save (권장)

```python
import torch

# model은 학습된 nn.Module 인스턴스
torch.save(model, "poop_classifier.pkl")

# Colab → 로컬 다운로드
from google.colab import files
files.download("poop_classifier.pkl")
```

### 방법 2: Google Drive에 저장 후 다운로드

```python
from google.colab import drive
drive.mount("/content/drive")

torch.save(model, "/content/drive/MyDrive/poop_classifier.pkl")
```

### 모델 학습 예시 (ResNet18 기반)

```python
import torch
import torch.nn as nn
from torchvision import models, transforms
from torch.utils.data import DataLoader, ImageFolder

# 데이터 전처리
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

# 데이터셋 로드 (폴더 구조: data/train/{normal,diarrhea,lack-of-water,soft-poop}/)
train_dataset = ImageFolder("data/train", transform=transform)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# 모델 정의 (4-class ResNet18)
model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, 4)
model = model.to("cuda" if torch.cuda.is_available() else "cpu")

# 학습
device = "cuda" if torch.cuda.is_available() else "cpu"
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

for epoch in range(10):
    model.train()
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
    print(f"Epoch {epoch+1} 완료")

# 저장
model.eval()
torch.save(model, "poop_classifier.pkl")
print("모델 저장 완료!")
```

> **주의**: `train_dataset.classes` 순서가 `config/settings.py`의 `CLASSES` 리스트 순서와
> 일치해야 올바른 분류 결과가 나옵니다.
> `ImageFolder`는 알파벳 순으로 클래스를 정렬하므로 아래 순서가 됩니다:
> `["diarrhea", "lack-of-water", "normal", "soft-poop"]`
> 이 경우 `settings.py`의 `CLASSES`도 동일하게 수정하세요.

---

## 클래스별 Bristol 등급

| 클래스 | Bristol 등급 | 설명 |
|--------|-------------|------|
| normal | 3~4등급 | 정상적인 변 |
| soft-poop | 5~6등급 | 무른 변 |
| diarrhea | 7등급 | 묽은 변/설사 |
| lack-of-water | 1~2등급 | 딱딱하고 건조한 변 |

## 분석 로그

`data/analysis_logs/` 폴더에 `YYYY-MM-DD_HH-MM.json` 형식으로 저장됩니다.
