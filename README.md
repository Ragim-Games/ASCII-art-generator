# 글자공방 — Python ASCII Art Generator

**Python + Tkinter로 만든 데스크톱 프로그램**입니다. 브라우저나 웹 서버 없이 독립 창에서 실행됩니다. 참고 화면처럼 모드·스타일·채움 도구 모음, 입력칸, ASCII 결과창으로 구성했으며 한글을 지원합니다.

## 실행

Python 3.10 이상과 Tkinter가 필요합니다. Windows의 python.org 배포판에는 Tkinter가 기본 포함됩니다.

```sh
python -m pip install -r requirements.txt
python main.py
```

Windows에서는 설치 후 `run.bat`을 더블클릭해도 됩니다. Linux에 Tkinter가 없다면 배포판의 `python3-tk` 패키지를 설치하세요. macOS에서는 Tkinter가 포함된 Python을 사용하세요.

## 기능

- 한글 완성형·자모, 영문, 숫자, 기호와 여러 줄 텍스트 (최대 300자)
- 블록 / 크게 / 윤곽선 / 그림자 / 3D / 기울임 스타일
- `█`, `▓`, `#`, `*`, `@`, `.` 채움 선택
- PNG·JPG·WEBP·GIF·BMP 이미지 → ASCII 변환
- 이미지 가로 문자 수·대비·명암 반전 조절
- UTF-8 TXT, PNG 저장 및 텍스트 복사
- Windows 이미지 클립보드 복사
- 미리보기 확대·축소, 가로·세로 스크롤, 밝은/어두운 테마
- 사용자 TTF·OTF·TTC 글꼴 선택
- 모든 처리는 로컬에서 수행, 인터넷·API 키 불필요

## 한글 지원

영문 전용 글자 사전 대신 Pillow로 실제 글꼴을 픽셀에 그린 뒤 문자로 변환합니다. Windows에서는 맑은 고딕, macOS에서는 Apple SD Gothic Neo, Linux에서는 Noto Sans CJK 또는 나눔고딕을 자동 탐색합니다. 자동 탐색되지 않으면 **글꼴 파일…**에서 한글을 포함하는 글꼴을 선택하세요. 글꼴이 없는 문자는 해당 기기의 글꼴 표현에 따라 다릅니다.

기본 블록 모드는 유니코드 블록 문자 `█▀▄`로 한글 획을 보존합니다. 엄격한 ASCII만 필요하면 `#`, `*`, `@`, `.`을 선택하세요. 다른 앱에 붙여넣을 때 고정폭 글꼴을 사용하세요. 프로그램의 미리보기 크기 조절은 TXT 출력에 영향을 주지 않습니다. PNG는 현재 테마 색상으로 저장됩니다.

이미지는 15MB·4,000만 픽셀까지 지원하며 GIF는 첫 프레임을 사용합니다. 출력 제한은 180열·240행입니다. 세로로 너무 긴 이미지는 자르거나 가로 문자 수를 줄이도록 안내합니다. 300자를 넘는 텍스트는 오류를 표시하며 임의로 잘라내지 않습니다. 텍스트의 긴 줄은 출력 폭을 기준으로 자동으로 나눕니다.

이미지 복사는 Windows에서 지원합니다. 다른 OS에서는 PNG 저장을 사용하세요. 시스템에서 클립보드가 사용 중이면 잠시 후 다시 시도하세요.

## 검증

```sh
python -m unittest discover -s tests -p "test_engine.py" -v
python -m unittest discover -s tests -p "test_gui.py" -v
```

GUI 테스트는 데스크톱 세션이 필요합니다. Windows / Python 3.15 / Pillow 13 환경에서 검증했습니다.

| 파일 | 역할 |
| --- | --- |
| `main.py` | Tkinter 데스크톱 화면과 저장·복사 동작 |
| `ascii_engine.py` | 한글 렌더링, 스타일, 이미지 변환, PNG 출력 |
| `requirements.txt` | Pillow 의존성 |
| `run.bat` | Windows 실행 바로가기 |
| `tests/` | 변환 및 GUI 통합 테스트 |
