import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. 보안 설정: Secrets에서 API 키 불러오기 ---
try:
    SERVICE_KEY = st.secrets["MY_API_KEY"]
except:
    st.error("설정에서 API 키(MY_API_KEY)를 찾을 수 없습니다. Streamlit Cloud의 Secrets 설정을 확인하세요.")
    st.stop()

# 에어코리아 대기오염 정보 조회 엔드포인트
BASE_URL = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"

def get_air_quality(sido_name):
    """특정 시도별 실시간 미세먼지 측정 데이터를 가져오는 함수"""
    params = {
        'serviceKey': SERVICE_KEY,
        'returnType': 'json',
        'numOfRows': '100',
        'pageNo': '1',
        'sidoName': sido_name,  # 서울, 부산, 대구, 인천, 광주, 대전, 울산, 경기 등
        'ver': '1.0'
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if data['response']['header']['resultCode'] == '00':
            return data['response']['body']['items']
        else:
            st.warning(f"API 호출 결과: {data['response']['header']['resultMsg']}")
            return None
    except Exception as e:
        st.error(f"연결 오류: {e}")
        return None

# --- 2. Streamlit UI ---
st.set_page_config(page_title="실시간 미세먼지 알림이", page_icon="😷")

st.title("😷 실시간 우리 동네 미세먼지")
st.markdown("한국환경공단(에어코리아) API 기반 실시간 대기질 정보입니다.")

# 지역 선택 (사이드바)
sido_list = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
selected_sido = st.sidebar.selectbox("🗺️ 시/도를 선택하세요", sido_list)

if st.button(f"{selected_sido} 지역 데이터 불러오기"):
    with st.spinner('최신 정보를 수집 중입니다...'):
        items = get_air_quality(selected_sido)
        
        if items:
            # 첫 번째 측정소(가장 최근 데이터) 정보 출력
            latest_station = items[0]
            
            st.subheader(f"📍 {latest_station['stationName']} 측정소 현황")
            
            # 메트릭 카드 배치
            m1, m2, m3 = st.columns(3)
            
            pm10_val = latest_station.get('pm10Value', '-')
            pm25_val = latest_station.get('pm25Value', '-')
            khai_val = latest_station.get('khaiValue', '-') # 통합대기환경지수
            
            m1.metric("미세먼지(PM10)", f"{pm10_val} ㎍/㎥")
            m2.metric("초미세먼지(PM2.5)", f"{pm25_val} ㎍/㎥")
            m3.metric("통합대기지수", khai_val)

            # 상태에 따른 색상 가이드
            st.divider()
            try:
                pm10_int = int(pm10_val)
                if pm10_int <= 30:
                    st.success("✨ 공기가 매우 깨끗합니다! 환기하기 딱 좋은 날이에요.")
                elif pm10_int <= 80:
                    st.info("☁️ 보통 수준입니다. 야외 활동에 큰 지장은 없어요.")
                elif pm10_int <= 150:
                    st.warning("⚠️ 미세먼지가 나쁨입니다. 가급적 마스크를 착용하세요.")
                else:
                    st.error("🚨 매우 나쁨! 실외 활동을 자제하고 창문을 닫으세요.")
            except:
                st.write("실시간 수치 확인 불가 (점검 중인 측정소일 수 있습니다.)")

            # 선택한 시도의 전체 측정소 리스트 보기
            with st.expander(f"🔍 {selected_sido} 전체 측정소 데이터 보기"):
                df = pd.DataFrame(items)
                # 주요 열만 필터링하여 출력
                display_df = df[['stationName', 'dataTime', 'pm10Value', 'pm25Value', 'khaiGrade']]
                display_df.columns = ['측정소', '측정시간', '미세먼지', '초미세먼지', '종합등급']
                st.dataframe(display_df)
        else:
            st.error("데이터를 가져오지 못했습니다. API 키나 서버 상태를 확인하세요.")

st.caption(f"제공: 한국환경공단(에어코리아) | 기준 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
