import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. 보안 설정: GitHub에 직접 키를 적지 않고 Secrets에서 불러옵니다 ---
# 나중에 Streamlit Cloud 설정(Secrets)에서 'MY_API_KEY'라는 이름으로 키를 저장해야 합니다.
try:
    SERVICE_KEY = st.secrets["MY_API_KEY"]
except:
    st.error("설정에서 API 키(MY_API_KEY)를 찾을 수 없습니다.")
    st.stop()

BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"

def get_weather_data(nx, ny):
    """기상청 초단기실황 API 호출 함수"""
    now = datetime.now()
    # 기상청 API는 매시 40분에 데이터가 업데이트되므로 안전하게 처리
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00") 

    params = {
        'serviceKey': SERVICE_KEY,
        'pageNo': '1',
        'numOfRows': '10',
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time,
        'nx': nx,
        'ny': ny
    }

    try:
        # API 호출 시 인증키가 이미 인코딩된 경우를 대비해 params를 딕셔너리로 전달
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if data['response']['header']['resultCode'] == '00':
            return data['response']['body']['items']['item']
        else:
            st.warning(f"API 메시지: {data['response']['header']['resultMsg']}")
            return None
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None

# --- 2. Streamlit UI 디자인 ---
st.set_page_config(page_title="우리동네 실시간 날씨", page_icon="🌤️")

st.title("🌤️ 실시간 생활 밀착형 대시보드")
st.markdown("공공데이터 포털 API를 활용한 실시간 날씨 정보입니다.")

# 사이드바 설정
st.sidebar.header("📍 지역 설정")
st.sidebar.write("기상청 격자 좌표를 입력하세요.")
nx = st.sidebar.number_input("격자 X (서울 시청: 60)", value=60)
ny = st.sidebar.number_input("격자 Y (서울 시청: 127)", value=127)

if st.button("실시간 데이터 새로고침"):
    with st.spinner('데이터를 불러오는 중...'):
        items = get_weather_data(nx, ny)
        
        if items:
            # 데이터 변환 (카테고리별 값 매핑)
            weather_data = {item['category']: item['obsrValue'] for item in items}
            
            # 메트릭 카드 레이아웃
            col1, col2, col3 = st.columns(3)
            
            # T1H: 기온, REH: 습도, RN1: 1시간 강수량
            temp = weather_data.get('T1H', '0')
            humi = weather_data.get('REH', '0')
            rain = weather_data.get('RN1', '0')
            
            col1.metric("현재 온도", f"{temp}°C")
            col2.metric("습도", f"{humi}%")
            col3.metric("시간당 강수량", f"{rain}mm")
            
            # 생활 가이드 추가
            st.divider()
            st.subheader("💡 오늘의 생활 가이드")
            temp_val = float(temp)
            if temp_val > 30:
                st.error("폭염주의! 야외 활동을 자제하고 물을 많이 마셔요. 🥤")
            elif temp_val < 5:
                st.info("쌀쌀한 날씨입니다. 따뜻한 외투를 챙기세요! 🧣")
            else:
                st.success("쾌적한 날씨입니다. 가벼운 산책은 어떠신가요? 👟")
                
            # 상세 데이터 보기
            with st.expander("상세 관측 데이터 보기"):
                df = pd.DataFrame(items)
                st.table(df[['category', 'obsrValue']])
        else:
            st.error("데이터를 불러오지 못했습니다. API 키 등록 상태나 격자 좌표를 확인하세요.")

st.caption(f"최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
