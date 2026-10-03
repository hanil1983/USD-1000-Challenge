# Chart Quiz MVP

과거 100개 캔들을 보고 LONG / SHORT / WAIT를 선택한 뒤,
미래 20개 캔들을 공개해서 결과를 확인하는 차트 학습 프로그램입니다.

## 1. 설치

터미널에서 프로젝트 폴더로 이동한 뒤:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell에서는 가상환경 활성화 명령이 다음과 같습니다.

```powershell
.venv\Scripts\Activate.ps1
```

## 2. 실행

```bash
streamlit run app.py
```

브라우저가 자동으로 열리지 않으면 터미널에 표시되는 Local URL을 브라우저에서 여세요.

## 3. 현재 기능

- BTC / ETH / AAPL / TSLA / NVDA / SPY
- 1일봉 / 1시간봉
- 미래 날짜 숨김
- 캔들 + 거래량 + RSI(14)
- LONG / SHORT / WAIT 선택
- 미래 20봉 공개
- 최종 수익률
- MFE / MAE
- 누적 문제 수 / 정답률

## 4. 다음 확장 추천

1. EMA20 / EMA60 토글
2. 한 봉씩 공개하는 Bar Replay
3. Stop Loss / Take Profit 입력
4. CSV 또는 SQLite에 답안 기록
5. 조건별 정답률 분석
6. Binance/Bybit API로 Funding Rate, Open Interest 추가
