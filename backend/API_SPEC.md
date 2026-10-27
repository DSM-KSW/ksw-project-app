# 통합 리매핑 시스템 API 명세서

이 문서는 **현재 프로토타입 API**와 **차기 API 설계안(v1)**을 구분한다. v1은 프론트엔드와 백엔드가 앞으로 맞출 계약이며, 현재 `app.py`에 구현되었다는 뜻은 아니다.

## 1. 현재 프로토타입 API — 구현됨

- 실행: Windows에서 `run.bat`
- 기본 주소: `http://127.0.0.1:8765`
- 데이터: UTF-8 JSON. 성공한 POST는 본문 없이 `204 No Content`를 반환한다.
- 서버는 로컬 PC의 `127.0.0.1`에만 바인딩된다.

| 메서드 | 경로 | 기능 |
|---|---|---|
| `GET` | `/` | 테스트용 HTML 화면 |
| `GET` | `/state` | 현재 상태, 선택된 입력·출력, 저장된 리매핑 조회 |
| `POST` | `/capture` | 다음 실제 입력을 원래 입력으로 선택하기 시작 |
| `POST` | `/capture-event` | 테스트 화면이 감지한 입력을 캡처에 전달 |
| `POST` | `/draft` | 저장 전 원래 입력 또는 출력 키 조합 선택 |
| `POST` | `/save` | 선택된 원래 입력과 출력 조합 저장 |
| `POST` | `/delete` | 저장 목록에서 인덱스로 삭제 |

### 현재 요청 예시

```http
POST /draft
Content-Type: application/json

{"role":"input","keys":[71],"mouse":null}
```

```http
POST /draft
Content-Type: application/json

{"role":"output","keys":[17,91,37],"mouse":null}
```

이후 `POST /save`를 호출한다. `POST /delete` 본문은 `{"index":0}`이다. `POST /capture-event` 본문은 `{"source":"keyboard","code":71,"pressed":true}` 또는 `{"source":"mouse","code":"마우스 X1","pressed":true}` 형태다. 키를 놓을 때 `pressed:false`를 보낸다.

현재 `bindings.json` 예시:

```json
{
  "bindings": [
    {"keys": [71], "mouse": null, "output": [17, 91, 37]}
  ]
}
```

현재 제약: 원래 입력은 키보드 키 하나 또는 지원되는 마우스 입력 하나다. 출력은 **키보드 키 1~8개만** 지원한다. 마우스 출력, HID 추가 버튼의 캡처·출력, 아래 v1 경로는 아직 구현되지 않았다. `F12`는 일시 정지/재개에 예약되어 원래 입력으로 지정할 수 없다.

## 2. 차기 API 설계안 v1 — 미구현

### 기본 규칙

- 기본 주소: `http://127.0.0.1:8765/api/v1`
- 요청·응답: `application/json; charset=utf-8`
- 저장 대상은 **원래 입력 하나 → 출력 동작 1~8개**다. 출력의 순서가 중요하다.
- `keyboard`는 Windows 가상 키 코드(VK)를 숫자로 저장한다. 예: `A=65`, `Ctrl=17`, `F20=131`.
- 표준 마우스 입력은 화면 표시명 대신 훅에서 받은 `message`와 `detail`을 저장한다. `detail`은 X 버튼이면 `mouseData` 상위 16비트의 버튼 번호, 휠이면 회전 방향 `1` 또는 `-1`, 일반 버튼이면 `0`이다.
- HID 입력은 장치가 실제로 보고한 `usage_page`와 `usage_id`를 기록한다. HID 장치별 보고 형식 확인과 장치 식별 방식은 구현할 때 확정한다. 임의로 6번 이상의 Windows X 버튼 번호를 만들지 않는다.
- 출력의 `mouse`는 Windows `SendInput`으로 전송 가능한 표준 버튼·휠 동작만 정의한다. 임의 HID 버튼 출력은 별도 장치 드라이버 지원 없이는 약속하지 않는다.

### 입력 객체

```json
{"type":"keyboard","vk":71}
```

```json
{"type":"mouse","message":523,"detail":1}
```

```json
{"type":"hid","device_id":"장치에서_확인한_ID","usage_page":9,"usage_id":6}
```

두 번째 예시는 `WM_XBUTTONDOWN(523)`과 `XBUTTON1(1)`을 뜻한다. 다른 표준 누름 입력은 왼쪽 `513/0`, 오른쪽 `516/0`, 가운데 `519/0`, X2 `523/2`다. 세로 휠은 `522/1`(위) 또는 `522/-1`(아래)로 정규화한다. 뗌 메시지는 버튼 상태 관리에 사용하고 기본 리매핑 트리거로 저장하지 않는다.

### 출력 동작 객체

```json
{"type":"keyboard","vk":17}
```

```json
{"type":"mouse","button":"x1","action":"click"}
```

마우스 출력 `button` 값은 `left`, `right`, `middle`, `x1`, `x2`, `wheel_vertical`, `wheel_horizontal`이다. 버튼에는 `action:"click"`, 휠에는 `action:"scroll"`과 `amount`(휠 델타, 예: `120` 또는 `-120`)를 사용한다. 키보드 출력들이 먼저 눌리고, 마우스 출력이 실행된 뒤, 키보드 출력들이 역순으로 떼어지는 동작을 기본으로 한다. 출력에 마우스 버튼이 여러 개 포함되면 배열 순서대로 클릭한다.

### 리매핑 객체 예시

`G`를 `Ctrl + 왼쪽 화살표`로 변경:

```json
{
  "id": "bind-001",
  "input": {"type": "keyboard", "vk": 71},
  "output": [
    {"type": "keyboard", "vk": 17},
    {"type": "keyboard", "vk": 37}
  ],
  "enabled": true
}
```

추가 버튼 X2를 `Ctrl + 마우스 왼쪽 클릭`으로 변경:

```json
{
  "id": "bind-002",
  "input": {"type": "mouse", "message": 523, "detail": 2},
  "output": [
    {"type": "keyboard", "vk": 17},
    {"type": "mouse", "button": "left", "action": "click"}
  ],
  "enabled": true
}
```

여기서 `523/2`는 실제로 받은 원래 입력 ID이고, `left`는 Windows에 생성하도록 요청할 출력 동작이다. 입력 ID와 출력 동작을 구분한다.

### 엔드포인트

| 메서드 | 경로 | 요청 | 성공 응답 |
|---|---|---|---|
| `GET` | `/status` | 없음 | `200`, 동작 상태·훅 상태·최근 실행 결과 |
| `GET` | `/bindings` | 없음 | `200`, `{"bindings":[...]}` |
| `POST` | `/bindings` | `input`, `output`, `enabled` | `201`, 생성된 리매핑 객체 |
| `PUT` | `/bindings/{id}` | `input`, `output`, `enabled` | `200`, 변경된 리매핑 객체 |
| `DELETE` | `/bindings/{id}` | 없음 | `204` |
| `POST` | `/capture/start` | 없음 | `202`, 캡처 시작 |
| `GET` | `/capture` | 없음 | `200`, 캡처 진행 상태와 감지된 입력 |
| `POST` | `/capture/cancel` | 없음 | `204` |
| `POST` | `/engine/pause` | 없음 | `204` |
| `POST` | `/engine/resume` | 없음 | `204` |

`POST /bindings` 요청 예시:

```json
{
  "input": {"type": "mouse", "message": 523, "detail": 2},
  "output": [
    {"type": "keyboard", "vk": 17},
    {"type": "mouse", "button": "left", "action": "click"}
  ],
  "enabled": true
}
```

`GET /capture` 응답 예시:

```json
{
  "status": "captured",
  "input": {"type": "mouse", "message": 523, "detail": 2},
  "display_name": "마우스 X2"
}
```

`display_name`은 화면용이며 저장·비교에는 `input`의 숫자 ID를 사용한다. 캡처 상태는 `idle`, `waiting`, `captured` 중 하나다.

오류 응답은 `{"error":{"code":"INVALID_INPUT","message":"설명"}}` 형식이다. 예상 상태 코드는 `400`(형식 오류), `404`(없는 리매핑), `409`(중복 입력 또는 캡처 충돌), `500`(저장·입력 실행 실패)이다. 같은 원래 입력을 다시 저장하면 `POST`는 `409`를 반환하고, 변경은 해당 `id`에 `PUT`으로 수행한다.

### 저장·마이그레이션

v1의 `bindings.json`은 `{"schema_version":1,"bindings":[...]}` 형태로 저장한다. 프로그램 시작 시 기존 `{"bindings":[{"keys":[...],"mouse":...,"output":[...]}]}` 파일을 읽어 v1 객체로 변환해야 한다. 변환 전 원본을 백업하고, 지원하지 못하는 항목이 있으면 원본을 덮어쓰지 않고 오류를 알려야 한다. 파일 저장은 임시 파일 작성 후 교체하여 중간에 종료되어도 설정 파일이 깨지지 않게 한다.

## 3. 구현 순서

1. 기존 설정 파일을 보존하면서 v1 리매핑 객체와 REST API를 추가한다.
2. C 전송 함수에 표준 마우스 출력을 추가한다.
3. 실제 마우스로 진단 프로그램을 실행해 추가 버튼이 마우스 메시지, 키보드 VK, HID 중 어느 경로로 들어오는지 확인한다.
4. 필요한 경우 해당 HID 장치 보고서를 파싱하는 입력 어댑터를 추가한다.

