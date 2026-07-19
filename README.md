# PDF Connection

PDF Connection은 여러 개의 PDF 파일을 원하는 순서대로 병합하고 중복 페이지를 제거할 뿐만 아니라, 하나의 PDF 파일을 다양한 기준(낱장 분할, 지정 페이지 기준 이분할, 사용자 정의 범위 분할)에 따라 손쉽게 쪼갤 수 있는 통합 데스크톱 GUI 애플리케이션입니다.

기존의 투박한 UI를 전면 탈피하여, **PyQt6**와 **QFluentWidgets**를 적용한 **Windows 11 Fluent Design** 테마로 구현되어 미려하고 모던한 UI/UX를 제공합니다.

---

## 주요 기능

### 1. PDF 병합 (Merge PDFs)
- **순서 지정**: 추가된 PDF 파일 목록의 결합 순서를 `Move Up` / `Move Down` 버튼으로 쉽게 조정합니다.
- **페이지 선택적 제외**: 파일별로 제외하고 싶은 페이지 번호나 범위(1-based)를 지정할 수 있습니다. (예: `1, 3-5`)
- **시각적 중복 제거**: 72 DPI 이미지 픽셀 기반 MD5 해싱을 통해, 완전히 동일한 비주얼의 페이지가 병합 과정에서 중복 삽입되는 것을 자동으로 감지하고 한 장만 남겨 제거합니다.

### 2. PDF 분할 (Split PDF)
- **사이드 네비게이션 메뉴**: 왼쪽 네비게이션 바를 통해 'PDF 병합'과 'PDF 분할' 뷰를 유연하고 미려하게 전환합니다.
- **낱장 분할 (Extract every page)**: 원본 PDF의 모든 페이지를 각각 1페이지짜리 독립된 PDF 파일로 낱낱이 분할합니다.
- **지정 페이지 기준 이분할 (Split into 2 files at page X)**: 지정한 페이지 번호 $X$를 기준으로 앞부분($1 \sim X$ 페이지)과 뒷부분($(X+1) \sim \text{끝}$) 2개의 파일로 쪼갭니다.
- **사용자 지정 범위 분할 (Split by custom ranges)**: 사용자가 입력한 범위 목록(예: `1-3, 4-5`)에 맞춰 조각 파일을 생성합니다.

### 3. 무설치 실행파일 (.exe) 배포 [New]
- PyInstaller를 이용해 단일 실행파일로 빌드되어, Python 및 라이브러리 설치가 되어있지 않은 환경에서도 더블클릭만으로 즉시 사용할 수 있습니다.

---

## 실행 방법

### 방법 A. 단일 실행파일 (.exe) 실행
빌드가 완료되면 `dist/` 디렉토리에 **`PDF_Connection.exe`** 파일이 생성됩니다. 이 파일을 더블클릭하여 바로 실행할 수 있습니다.

### 방법 B. 소스코드로 실행 (Python 3.11+)
```bash
# 1. 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 2. 실행
python main.py
```

---

## 프로젝트 구조

- `pdf_processor.py`: PDF 병합/분할 및 중복/제외 페이지 감지를 수행하는 비즈니스 로직
- `gui.py`: Tkinter 탭(Tab) 레이아웃 기반 그래픽 사용자 인터페이스
- `main.py`: 프로그램 진입점(Entry Point)
- `tests/test_pdf_processor.py`: 핵심 병합 및 분할 로직 검증 자동화 유닛 테스트
- `dist/PDF_Connection.exe`: 최종 윈도우 단일 실행파일 (빌드 완료 후 생성)
