from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# 파일 경로
REALTIME_JSON = BASE_DIR / "realtime_data.json"
HISTORY_CSV = BASE_DIR / "history_data.csv"
DIAGRAM_HTML = BASE_DIR / "diagram.html"
BACKGROUND_IMAGE = BASE_DIR / "background.png"
LOG_FILE = BASE_DIR / "mecom_hmi.log"
CONTROL_COMMAND_JSON = BASE_DIR / "control_command.json"
CONTROL_ENABLED = True  # Set to True to enable PLC write commands
COIL_ADDRESS = 1       # 단일 코일 주소: True=시작, False=정지
CONTROL_WRITE_UNIT = 1

# Modbus 설정
MODBUS_PORT = "COM6"
MODBUS_BAUDRATE = 9600
MODBUS_SLAVE_ID = 1
POLL_INTERVAL = 0.5
BIT_READ_START = 0     # Discrete Input 시작 주소 (모드버스맵: 10001 = offset 0)
BIT_WRITE_START = 500  # P00500 시작 주소
WORD_READ_START = 0    # D00000 시작 주소

# 이력 저장 설정
HISTORY_COLUMNS = [
    "날짜",
    "지중공급온도(1동)",
    "지중환수온도(1동)",
    "지중공급온도(2동)",
    "지중환수온도(2동)",
    "2차공급온도(1동)",
    "2차환수온도(1동)",
    "2차공급온도(2동)",
    "2차환수온도(2동)",
    "1동유량",
    "2동유량",
    "생산열량",
    "누적열량"
]
HISTORY_RECORD_INTERVAL_SEC = 60

# config.py 하단에 추가
DB_PATH = BASE_DIR / "mecom_data.db"
ADMIN_PASSWORD = "1234"  # 접근 비밀번호 설정
TEST_MODE = False  # 테스트 모드: PLC 연결 없이 샘플 데이터 사용