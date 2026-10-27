# Client-Project 프로토타입

Windows에서 Python 3을 설치하고 `run.bat`을 실행한 뒤 `http://127.0.0.1:8765`를 여세요. `macro_combo.dll`은 함께 제공되며, C 소스는 `macro_chord.c`입니다.

1. **① 원래 키**를 고르고 가상 키보드에서 키 하나를 클릭합니다. 마우스 버튼을 원래 입력으로 쓰려면 **원래 키를 실제 키·마우스로 선택**을 사용합니다.
2. **② 바꿀 키 조합**을 고르고 결과로 보낼 키를 하나 이상 클릭합니다. 예: `Ctrl`, `Windows`, `←`.
3. 두 선택을 확인하고 **리매핑 저장**을 누릅니다.

각 리매핑은 `bindings.json`의 `bindings` 배열에 저장됩니다. 예: `{"keys":[71],"mouse":null,"output":[17,91,37]}`는 G를 Ctrl + Windows + ←로 바꿉니다. 프로그램을 다시 실행하면 저장된 배열을 자동으로 불러옵니다. 저장 목록에서 항목을 개별 삭제할 수 있습니다.

`bindings.json`은 사용자별 설정이므로 Git에 올리지 않습니다. 저장 형식은 `bindings.example.json`을 참고하세요.

백엔드 API: `POST /draft`는 `{"role":"input","keys":[71],"mouse":null}` 또는 `{"role":"output","keys":[17,91,37]}`를 받습니다. `POST /save`는 두 선택을 하나의 리매핑으로 저장합니다. `GET /state`는 현재 선택과 저장 목록을 반환합니다. API는 같은 PC의 `127.0.0.1:8765`에만 열립니다.

F12는 일시 정지/재개용으로 예약되어 원래 키로 지정할 수 없습니다. 프론트는 테스트용이며, 입력 감지·설정 파일·C 입력 실행이 재사용할 백엔드 부분입니다.

- `app.py`: 입력 감지, 설정 저장·불러오기, API
- `macro_chord.c`, `macro_combo.dll`: 결과 키 조합 전송
- `index.html`: 테스트 화면
- `run.bat`: 실행
- `bindings.json`: 첫 저장 때 생성
- `bindings.example.json`: 저장 형식 예시
- `API_SPEC.md`: 현재 API와 차기 설계안
- `mouse_input_probe.py`, `run_mouse_probe.bat`: 실제 입력 ID 확인용 임시 도구
