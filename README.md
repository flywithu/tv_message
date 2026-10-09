# TV Message

TV 화면에 사용자 메시지(한글 OK)를 띄우는 Home Assistant 커스텀 통합 + 로컬 CLI.
메시지를 이미지로 만들어 TV가 가져가게 하는 방식이라 TV 쪽 설정이 필요 없습니다.

| 방식 | 대상 | 포트 |
|---|---|---|
| DLNA (UPnP AVTransport) | 삼성 Tizen TV 등 | 9197 |
| Google Cast | Android TV 스틱, Chromecast 호환 기기 | 8009 |

`auto`(기본)는 DLNA를 먼저, 실패하면 Cast를 시도합니다. 확인된 기기: 삼성 UN65MU8000(DLNA), TiVo Stream 4K / BIP-UW200(Cast).

## 구성

```
custom_components/tv_message/   HA 통합 (이 폴더를 HA의 custom_components에 복사)
  renderer.py dlna.py cast.py   HA에 의존하지 않는 핵심 코드
  fonts/                        나눔고딕 Bold (OFL) - HA 컨테이너엔 한글 폰트가 없어서 번들
blueprints/automation/tv_message/tv_on_message.yaml   "TV 켜지면 + 시간대면 메시지" 블루프린트
tools/send.py                   로컬 테스트용 CLI (HA와 같은 코드 사용)
tests/test_core.py              단위 테스트
legacy/                         예전 삼성 TV 제어 API/CLI (메시지와 무관, 필요 없으면 삭제)
```

## 로컬 테스트

```
venv\Scripts\python.exe tools\send.py 192.168.10.38 "지금은 취침시간입니다." --duration 10
venv\Scripts\python.exe tools\send.py 192.168.10.19 "안녕" --protocol cast
venv\Scripts\python.exe tools\send.py 192.168.10.38 --clear
venv\Scripts\python.exe -m unittest discover tests
```

PC 방화벽에서 TV가 접속할 포트(기본 8765/TCP)를 허용해야 합니다.

## Home Assistant 설치

1. `custom_components/tv_message` 폴더를 HA 설정 폴더의 `custom_components/`에 복사하고 HA를 재시작합니다.
2. 설정 → 기기 및 서비스 → 통합 추가 → **TV Message** → TV IP 입력 (TV가 꺼져 있어도 됩니다).
3. 이미지는 HA 자신의 웹서버(`/api/tv_message/<토큰>.jpg`)로 제공하므로 별도 포트나 방화벽 설정이 필요 없습니다.
   HA 주소를 자동 감지하지 못하면 등록 시 "HA 주소"에 `http://<HA IP>:8123`을 넣으세요.

### 서비스

- `tv_message.show` : `message`, `duration`(초), `host`(생략 시 등록된 모든 TV), `background_color`, `text_color`, `wait_for_tv`
  - TV가 막 켜진 직후에는 응답까지 몇 초 걸려서 `wait_for_tv`(기본 30초) 동안 재시도합니다.
- `tv_message.clear` : 표시 중인 메시지 즉시 내리기

### 시나리오: TV가 켜지면 지정 시간대에 메시지 (반복 가능)

블루프린트 `blueprints/automation/tv_message/tv_on_message.yaml`을 HA 설정 폴더의
`blueprints/automation/tv_message/`에 복사한 뒤 설정 → 자동화 → 블루프린트에서 만듭니다.

- TV가 **켜지는 순간** 시간대 안이면 메시지를 한 번 표시합니다.
- **반복 간격(분)** 이 1 이상이면, TV가 켜져 있고 시간대 안인 동안 그 간격마다 다시 표시합니다. 0이면 한 번만.
- 메시지는 `duration`초 뒤에 자동으로 내려갑니다.

직접 작성하는 예시 (TV가 켜져 있는 동안 10분마다 10초씩):

```yaml
automation:
  - alias: 취침시간 TV 안내
    mode: restart
    trigger:
      - platform: state
        entity_id: media_player.samsung_tv   # TV 켜짐 상태를 알려주는 엔티티
        to: "on"
        id: tv_on
      - platform: time_pattern
        minutes: "/10"
        id: tick
    condition:
      - condition: time
        after: "22:00:00"
        before: "06:00:00"    # 자정을 넘기는 시간대도 가능
      - condition: state
        entity_id: media_player.samsung_tv
        state: "on"
    action:
      - service: tv_message.show
        data:
          message: "지금은 취침시간입니다."
          duration: 10
```

켜짐 여부는 HA 내장 SamsungTV 통합 등의 엔티티를, 시간 조건은 HA의 `time` 조건을 그대로 사용합니다.
