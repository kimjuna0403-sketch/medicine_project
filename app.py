import streamlit as st
from openai import OpenAI
from supabase import create_client, Client
import base64
from PIL import Image, ImageEnhance
import io
import json
from datetime import datetime, timedelta, time
import requests
import xml.etree.ElementTree as ET
import urllib.parse
import calendar
import re

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="💊 스마트 약봉지 분석 시스템",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#667eea">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="스마트 약봉지">
    <link rel="apple-touch-icon" href="https://em-content.zobj.net/thumbs/240/apple/354/pill_1f48a.png">
    <link rel="manifest" href="/manifest.json">
""", unsafe_allow_html=True)
# ==================== 📱 모바일 앱 UI 설정 (CSS) ====================
def apply_mobile_ui():
    st.markdown("""
        <style>
        /* 1. 전체 배경 및 앱 프레임 설정 */
        .stApp {
            background-color: #f0f2f6; /* 전체 배경은 회색 */
            display: flex;
            justify-content: center;
        }
        
        /* 2. 메인 컨텐츠 영역을 폰 사이즈로 고정 */
        .main .block-container {
            max-width: 400px !important; /* 아이폰 Pro Max 너비 정도 */
            padding: 1rem !important;
            padding-bottom: 100px !important; /* 하단 네비게이션 공간 확보 */
            background-color: white;
            margin: 0 auto;
            min-height: 100vh;
            box-shadow: 0 0 20px rgba(0,0,0,0.1); /* 살짝 그림자 주어 입체감 */
            border-radius: 0 0 20px 20px; /* 하단 둥글게 (선택) */
        }
        /* 4. 탭 스타일 변경 (상단 탭이 아닌 버튼형태로 보이게) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            padding: 0;
            margin-bottom: 20px;
        }
        
        .stTabs [data-baseweb="tab"] {
            flex-grow: 1;
            background-color: #f8f9fa;
            border-radius: 12px;
            border: 1px solid #eee;
            padding: 10px;
            font-size: 0.9rem;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #667eea;
            color: white;
            border: none;
        }

        /* 5. 버튼 스타일 (앱 버튼처럼 둥글고 크게) */
        .stButton > button {
            width: 100%;
            border-radius: 15px;
            height: 50px;
            font-weight: bold;
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.1s;
        }
        
        .stButton > button:active {
            transform: scale(0.98);
        }

        /* 6. 하단 네비게이션 바 (가짜) 위치 잡기 */
        .bottom-nav-container {
            position: fixed;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 400px; /* 메인 컨텐츠 너비와 일치 */
            background: white;
            border-top: 1px solid #eee;
            padding: 10px 20px;
            z-index: 99999;
            display: flex;
            justify-content: space-between;
            border-radius: 20px 20px 0 0;
            box-shadow: 0 -4px 10px rgba(0,0,0,0.05);
        }
        
        /* 7. 기타 UI 다듬기 */
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.4rem !important; }
        h3 { font-size: 1.2rem !important; }
        
        /* 이미지 둥글게 */
        img { border-radius: 10px; }
        
        </style>
    """, unsafe_allow_html=True)

# UI 함수 실행
apply_mobile_ui()

# ==================== CSS 스타일링 ====================
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main .block-container {
        background: rgba(255, 255, 255, 0.05);
        padding: 2rem;
        border-radius: 20px;
    }
    
    .main-title {
        color: white;
        text-align: center;
        font-size: 3.5em;
        font-weight: 800;
        margin-bottom: 10px;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
        letter-spacing: -1px;
    }
    
    .sub-title {
        color: rgba(255, 255, 255, 0.95);
        text-align: center;
        font-size: 1.3em;
        margin-bottom: 40px;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 15px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border-radius: 10px;
        padding: 15px 30px;
        font-weight: 600;
        font-size: 1.1em;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: white;
        color: #667eea;
    }
    
    .calendar-container {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    
    .calendar-day {
        padding: 15px;
        margin: 5px;
        border-radius: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        background: #f8f9fa;
        border: 2px solid transparent;
    }
    
    .calendar-day:hover {
        background: #e9ecef;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .calendar-day.has-record {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 700;
        border-color: #667eea;
    }
    
    .calendar-day.today {
        border: 3px solid #28a745;
        font-weight: 700;
    }
    
    .info-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        margin: 15px 0;
        border-left: 5px solid #667eea;
    }
    
    .record-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 10px 0;
        border-left: 4px solid #667eea;
        transition: all 0.3s;
    }
    
    .record-card:hover {
        transform: translateX(5px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    
    .success-box {
        background: #d4edda;
        border-left: 5px solid #28a745;
        padding: 20px;
        border-radius: 10px;
        color: #155724;
        font-weight: 600;
        margin: 15px 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 20px;
        border-radius: 10px;
        color: #856404;
        font-weight: 600;
        margin: 15px 0;
    }
    
    .info-box {
        background: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 20px;
        border-radius: 10px;
        color: #0c5460;
        font-weight: 600;
        margin: 15px 0;
    }
    
    .badge {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 1em;
        margin: 5px;
    }
    
    .badge-success { background: #28a745; color: white; }
    .badge-warning { background: #ffc107; color: #000; }
    .badge-danger { background: #dc3545; color: white; }
    
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
    }
    
    .stButton>button {
        font-weight: 600;
        border-radius: 10px;
        padding: 12px 24px;
        font-size: 1em;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #ddd;
        padding: 12px;
        font-size: 1em;
    }
    
    .stChatMessage {
        background: white;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .streamlit-expanderHeader {
        background: white;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1.1em;
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    h1, h2, h3, h4 {
        color: white !important;
        font-weight: 700 !important;
    }
    
    p, li, span {
        font-size: 1.05em;
        line-height: 1.6;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2em;
        font-weight: 800;
        color: #667eea;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== API 초기화 ====================
@st.cache_resource
def init_clients():
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    supabase_client = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
    return openai_client, supabase_client

client, supabase = init_clients()

# ==================== 헬퍼 함수 ====================
def parse_flexible_date(date_str):
    """AI가 읽은 다양한 날짜 형식을 datetime 객체로 변환"""
    if not date_str or date_str == '알 수 없음':
        return None
        
    clean_str = date_str.replace('년', '-').replace('월', '-').replace('일', '').replace('.', '-').replace('/', '-').strip()
    clean_str = re.sub(r'[-]+', '-', clean_str)
    
    formats = ['%Y-%m-%d', '%y-%m-%d']
    
    for fmt in formats:
        try:
            return datetime.strptime(clean_str, fmt).date()
        except:
            continue
            
    return None

def preprocess_image(image):
    """OCR 성능 향상을 위한 이미지 전처리"""
    try:
        if image.width < 1000:
            ratio = 1000 / image.width
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        return image
    except Exception as e:
        st.warning(f"⚠️ 이미지 전처리 중 오류: {str(e)}")
        return image

# ==================== 식약처 API ====================
def search_mfds_medicine(medicine_name):
    """식약처 e약은요 API로 의약품 검색"""
    try:
        base_url = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
        api_key = st.secrets["MFDS_API_KEY"]
        
        params = {
            'itemName': medicine_name,
            'pageNo': '1',
            'numOfRows': '10',
            'type': 'xml'
        }
        
        encoded_params = urllib.parse.urlencode(params)
        url = f"{base_url}?serviceKey={api_key}&{encoded_params}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            result_code = root.find('.//resultCode')
            
            if result_code is not None and result_code.text == '00':
                items = root.findall('.//item')
                if not items:
                    return None
                
                results = []
                for item in items:
                    medicine_info = {
                        '제품명': item.find('itemName').text if item.find('itemName') is not None else '',
                        '업체명': item.find('entpName').text if item.find('entpName') is not None else '',
                        '품목기준코드': item.find('itemSeq').text if item.find('itemSeq') is not None else '',
                        '효능효과': item.find('efcyQesitm').text if item.find('efcyQesitm') is not None else '정보 없음',
                        '사용법': item.find('useMethodQesitm').text if item.find('useMethodQesitm') is not None else '정보 없음',
                        '주의사항_경고': item.find('atpnWarnQesitm').text if item.find('atpnWarnQesitm') is not None else '',
                        '주의사항': item.find('atpnQesitm').text if item.find('atpnQesitm') is not None else '정보 없음',
                        '상호작용': item.find('intrcQesitm').text if item.find('intrcQesitm') is not None else '정보 없음',
                        '부작용': item.find('seQesitm').text if item.find('seQesitm') is not None else '정보 없음',
                        '보관방법': item.find('depositMethodQesitm').text if item.find('depositMethodQesitm') is not None else '정보 없음',
                        '낱알이미지': item.find('itemImage').text if item.find('itemImage') is not None else '',
                        '공개일자': item.find('openDe').text if item.find('openDe') is not None else '',
                        '수정일자': item.find('updateDe').text if item.find('updateDe') is not None else ''
                    }
                    results.append(medicine_info)
                return results
        return None
    except Exception as e:
        st.error(f"❌ 식약처 API 오류: {str(e)}")
        return None

# ==================== GPT 함수 ====================
def search_medicine_info_gpt(medicine_name):
    """GPT로 약물 정보 검색"""
    try:
        prompt = f"""
다음 약물에 대한 상세 정보를 JSON 형식으로 제공해주세요:
약물명: {medicine_name}

{{
    "약품명": "정확한 약품명",
    "분류": "약물 분류",
    "효능효과": "주요 효능",
    "용법용량": "복용 방법",
    "주의사항": "주의할 점",
    "부작용": "부작용",
    "상호작용": "상호작용",
    "보관방법": "보관법",
    "위험도": "낮음/보통/높음"
}}

반드시 유효한 JSON으로만 답변하세요.
"""
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.endswith("```"):
            result = result[:-3]
        
        return json.loads(result.strip())
    except Exception as e:
        st.error(f"❌ GPT 검색 오류: {str(e)}")
        return None

def analyze_medicine_bag(image):
    """약봉지 이미지 분석"""
    try:
        image = preprocess_image(image)
        
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """약봉지 사진을 분석해서 다음 정보를 추출해주세요.

중요한 규칙:
1. 약 이름은 최대한 정확하게 읽어주세요
2. 흐릿하거나 불명확해도 최선을 다해 추론해주세요
3. 손글씨도 읽어주세요
4. "정", "캡슐", "시럽" 등이 붙은 약 이름을 찾아주세요
5. 약 이름이 전혀 보이지 않으면 빈 배열로 반환하세요

반드시 아래 JSON 형식으로만 답변하세요:
{
  "medicines": ["약이름1", "약이름2", "약이름3"],
  "hospital": "병원명 또는 약국명",
  "date": "조제일 (YYYY-MM-DD 형식)"
}

약 이름을 찾을 수 없으면:
{
  "medicines": [],
  "hospital": "알 수 없음",
  "date": "알 수 없음"
}

다른 텍스트나 설명 없이 오직 JSON만 출력하세요."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                    }
                ]
            }],
            max_tokens=1500,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        
        result = result.strip()
        
        data = json.loads(result)
        
        if not isinstance(data.get('medicines'), list):
            data['medicines'] = []
        
        return data
        
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON 파싱 오류: {str(e)}")
        with st.expander("🔍 GPT 응답 확인 (디버깅용)"):
            st.code(result[:500])
        return None
    except Exception as e:
        st.error(f"❌ 이미지 분석 오류: {str(e)}")
        return None

# ==================== 데이터베이스 함수 ====================
def get_user_info():
    """사이드바에서 사용자 정보 가져오기"""
    if 'patient_name' in st.session_state and st.session_state.patient_name:
        return st.session_state.patient_name, st.session_state.patient_age
    return None, None

def save_to_database(patient_name, patient_age, medicines, hospital, analysis, scan_date=None):
    """Supabase에 저장"""
    try:
        if scan_date is None:
            scan_date = datetime.now().isoformat()
        
        data = {
            "patient_name": patient_name,
            "patient_age": patient_age,
            "medicines": medicines,
            "hospital": hospital,
            "analysis": analysis,
            "scan_date": scan_date,
            "created_at": datetime.now().isoformat()
        }
        supabase.table('medicine_records').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"❌ 저장 오류: {str(e)}")
        return False

def get_records_by_user(patient_name):
    """특정 사용자의 모든 기록 가져오기"""
    try:
        response = supabase.table('medicine_records')\
            .select('*')\
            .eq('patient_name', patient_name)\
            .order('scan_date', desc=True)\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"❌ 기록 조회 오류: {str(e)}")
        return []

def get_records_by_date(patient_name, date):
    """특정 날짜의 기록 가져오기"""
    try:
        date_str = date.strftime('%Y-%m-%d')
        response = supabase.table('medicine_records')\
            .select('*')\
            .eq('patient_name', patient_name)\
            .gte('scan_date', f"{date_str}T00:00:00")\
            .lt('scan_date', f"{date_str}T23:59:59")\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"❌ 날짜별 조회 오류: {str(e)}")
        return []

def delete_record(record_id):
    """특정 기록 삭제"""
    try:
        supabase.table('medicine_records').delete().eq('id', record_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ 삭제 오류: {str(e)}")
        return False

def get_calendar_data(patient_name, year, month):
    """특정 월의 처방 기록이 있는 날짜 리스트 반환"""
    try:
        start_date = f"{year}-{month:02d}-01T00:00:00"
        if month == 12:
            end_date = f"{year+1}-01-01T00:00:00"
        else:
            end_date = f"{year}-{month+1:02d}-01T00:00:00"
        
        response = supabase.table('medicine_records')\
            .select('scan_date')\
            .eq('patient_name', patient_name)\
            .gte('scan_date', start_date)\
            .lt('scan_date', end_date)\
            .execute()
        
        dates_with_records = set()
        for record in response.data:
            date = datetime.fromisoformat(record['scan_date']).date()
            dates_with_records.add(date.day)
        
        return dates_with_records
    except Exception as e:
        st.error(f"❌ 캘린더 데이터 조회 오류: {str(e)}")
        return set()

# ==================== [추가] 자녀 복약 관리 함수 ====================
def create_user(name, age, role):
    try:
        data = {"name": name, "age": age, "role": role}
        response = supabase.table('users').insert(data).execute()
        return response.data[0]['id'] if response.data else None
    except:
        return None

def get_user_by_name(name):
    try:
        response = supabase.table('users').select('*').eq('name', name).execute()
        return response.data[0] if response.data else None
    except:
        return None

def connect_family(parent_id, child_id):
    try:
        data = {"parent_id": parent_id, "child_id": child_id}
        supabase.table('family_connections').insert(data).execute()
        return True
    except:
        return False

def get_my_parents(child_id):
    try:
        response = supabase.table('family_connections')\
            .select('parent_id, users!family_connections_parent_id_fkey(name, age)')\
            .eq('child_id', child_id)\
            .execute()
        return response.data
    except:
        return []

def mark_as_taken(record_id):
    try:
        supabase.table('medicine_records').update({'taken': True}).eq('id', record_id).execute()
        return True
    except:
        return False

def get_today_medicine_status(user_id):
    try:
        today = datetime.now().date()
        response = supabase.table('medicine_records')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('scan_date', f"{today}T00:00:00")\
            .lt('scan_date', f"{today}T23:59:59")\
            .execute()
        return response.data
    except:
        return []

def link_old_records(patient_name, user_id):
    try:
        supabase.table('medicine_records')\
            .update({'user_id': user_id})\
            .eq('patient_name', patient_name)\
            .is_('user_id', 'null')\
            .execute()
    except:
        pass

# ==================== 메인 타이틀 ====================
st.markdown('<h1 class="main-title">💊 스마트 약봉지 분석 시스템</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">AI가 약봉지를 분석하고, 부모님 복약을 관리합니다</p>', unsafe_allow_html=True)

# ==================== 사이드바 ====================
with st.sidebar:
    st.markdown("## 👤 사용자 정보")
    
    # 역할 선택
    user_role = st.radio("사용 모드", ["부모님", "자녀"], horizontal=True)
    
    # 세션 상태 초기화
    if 'patient_name' not in st.session_state:
        st.session_state.patient_name = ""
    if 'patient_age' not in st.session_state:
        st.session_state.patient_age = 30
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    patient_name = st.text_input(
        "이름", 
        value=st.session_state.patient_name,
        placeholder="홍길동", 
        help="복약 기록 관리를 위해 이름을 입력하세요",
        key="name_input"
    )
    
    if user_role == "부모님":
        patient_age = st.number_input(
            "나이", 
            min_value=0, 
            max_value=120, 
            value=st.session_state.patient_age, 
            help="환자 나이를 입력하세요",
            key="age_input"
        )
        st.session_state.patient_age = patient_age
    
    # 세션 상태 업데이트
    st.session_state.patient_name = patient_name
    
    # 로그인/회원가입
    if patient_name:
        user = get_user_by_name(patient_name)
        if user:
            st.session_state.user_id = user['id']
            link_old_records(patient_name, user['id'])
            st.success(f"✅ {patient_name}님, 환영합니다!")
        else:
            if st.button("🆕 회원가입", use_container_width=True):
                role = 'parent' if user_role == "부모님" else 'child'
                age = patient_age if user_role == "부모님" else None
                user_id = create_user(patient_name, age, role)
                if user_id:
                    st.session_state.user_id = user_id
                    link_old_records(patient_name, user_id)
                    st.success("회원가입 완료!")
                    st.rerun()
    else:
        st.warning("⚠️ 이름을 입력하면 복약 기록을 관리할 수 있습니다")
    
    st.divider()
    
    # 사용자별 통계
    if patient_name:
        st.markdown("## 📊 나의 복약 통계")
        try:
            all_records = get_records_by_user(patient_name)
            total_count = len(all_records)
            
            today = datetime.now().date()
            today_records = [r for r in all_records if datetime.fromisoformat(r.get('scan_date', '')).date() == today]
            today_count = len(today_records)
            
            # 최근 7일 통계
            week_ago = today - timedelta(days=7)
            week_records = [r for r in all_records if datetime.fromisoformat(r.get('scan_date', '')).date() >= week_ago]
            week_count = len(week_records)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("총 처방", f"{total_count}건", help="전체 처방 기록")
            with col2:
                st.metric("이번 주", f"{week_count}건", help="최근 7일 기록")
            
            # 가장 많이 처방받은 약
            if all_records:
                all_medicines = []
                for record in all_records:
                    medicines = record.get('medicines', [])
                    if isinstance(medicines, list):
                        all_medicines.extend(medicines)
                
                if all_medicines:
                    from collections import Counter
                    most_common = Counter(all_medicines).most_common(3)
                    
                    st.markdown("### 💊 자주 처방받는 약")
                    for med, count in most_common:
                        st.markdown(f"- **{med}**: {count}회")
        except:
            st.metric("총 처방", "0건")
    else:
        st.markdown("## 📊 이용 통계")
        st.info("이름을 입력하면 개인별 통계를 확인할 수 있습니다")
    
    st.divider()

# ==================== 탭 구성 ====================
if user_role == "부모님":
    tab1, tab2, tab3 = st.tabs(["🏥 처방약 스캔", "💬 약 검색 챗봇", "📅 복약 캘린더"])
    
    # ==================== 탭1: 처방약 스캔 ====================
    with tab1:
        st.markdown("## 📸 약봉지 사진 분석")
        st.markdown("처방받은 약봉지를 업로드하면 AI가 자동으로 약 이름을 추출하고 정보를 제공합니다.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 1️⃣ 사진 업로드")
        with col2:
            st.markdown("### 2️⃣ AI 분석")
        with col3:
            st.markdown("### 3️⃣ 정보 확인 & 저장")
        
        st.divider()
        
        uploaded_file = st.file_uploader(
            "약봉지 사진을 업로드하세요",
            type=['png', 'jpg', 'jpeg'],
            help="약 이름이 선명하게 보이는 사진을 업로드해주세요"
        )
        
        if 'scan_result' not in st.session_state:
            st.session_state.scan_result = None
        if 'scan_img_id' not in st.session_state:
            st.session_state.scan_img_id = None

        if uploaded_file:
            if st.session_state.scan_img_id != uploaded_file.file_id:
                st.session_state.scan_result = None
                st.session_state.scan_img_id = uploaded_file.file_id

            image = Image.open(uploaded_file)
            st.image(image, caption="업로드된 약봉지", width=400)
            
            if st.button("🔍 AI 분석 시작", type="primary", use_container_width=True):
                with st.spinner("🤖 AI가 약봉지를 분석하는 중..."):
                    extracted_data = analyze_medicine_bag(image)
                    
                    if extracted_data:
                        medicines = extracted_data.get('medicines', [])
                        
                        all_medicine_info = []
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for idx, medicine_name in enumerate(medicines):
                            status_text.text(f"🔍 {medicine_name} 정보 검색 중...")
                            progress_bar.progress((idx + 1) / len(medicines))
                            medicine_info = search_medicine_info_gpt(medicine_name)
                            if medicine_info:
                                all_medicine_info.append(medicine_info)
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        st.session_state.scan_result = {
                            'extracted_data': extracted_data,
                            'medicines': medicines,
                            'all_medicine_info': all_medicine_info
                        }
                        st.rerun()
                    else:
                        st.error("❌ 이미지 분석 실패. 다시 시도해주세요.")

        if st.session_state.scan_result:
            result = st.session_state.scan_result
            extracted_data = result['extracted_data']
            medicines = result['medicines']
            all_medicine_info = result['all_medicine_info']

            st.markdown('<div class="success-box">✅ 분석 완료!</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**🏥 병원:** {extracted_data.get('hospital', '정보 없음')}")
            with col2:
                st.info(f"**📅 인식된 날짜:** {extracted_data.get('date', '정보 없음')}")

            for info in all_medicine_info:
                with st.expander(f"💊 {info['약품명']}"):
                    st.write(f"효능: {info.get('효능효과', '-')}")
                    st.write(f"복용법: {info.get('용법용량', '-')}")
                    st.write(f"주의사항: {info.get('주의사항', '-')}")

            st.divider()
            st.markdown("### 💾 저장 날짜 확인")

            ai_date = extracted_data.get('date', '')
            parsed_date = parse_flexible_date(ai_date)
            default_date = parsed_date if parsed_date else datetime.now().date()

            final_date = st.date_input(
                "저장될 날짜", 
                value=default_date,
                help="캘린더에 저장될 날짜입니다."
            )

            if st.button("💾 이 날짜로 저장하기", type="primary", use_container_width=True):
                if patient_name:
                    try:
                        save_datetime = datetime.combine(final_date, time(12, 0, 0)).isoformat()
                        
                        success = save_to_database(
                            patient_name,
                            patient_age,
                            medicines,
                            extracted_data.get('hospital', ''),
                            json.dumps(all_medicine_info, ensure_ascii=False),
                            save_datetime
                        )
                        
                        if success:
                            st.session_state.saved_data = {
                                'name': patient_name,
                                'date': final_date.strftime('%Y-%m-%d'),
                                'count': len(medicines)
                            }
                            st.session_state.save_success = True
                            st.session_state.scan_result = None
                            st.rerun()
                        else:
                            st.error("❌ 데이터베이스 저장 실패")
                    except Exception as e:
                        st.error(f"❌ 저장 중 오류: {str(e)}")
                else:
                    st.warning("⚠️ 사이드바에서 이름을 먼저 입력해주세요!")

        if st.session_state.get('save_success', False):
            st.markdown('<div class="success-box">✅ 저장 완료! 📅 캘린더 탭을 확인하세요.</div>', unsafe_allow_html=True)
            if st.button("확인 (새로 분석하기)"):
                st.session_state.save_success = False
                st.rerun()

    # ==================== 탭2: 챗봇 ====================
    with tab2:
        st.markdown("## 💬 의약품 정보 챗봇")
        st.markdown("궁금한 약 이름을 물어보세요. 식약처 공식 데이터로 답변드립니다!")
        
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        if len(st.session_state.chat_messages) == 0:
            st.markdown("### 💡 빠른 질문")
            cols = st.columns(5)
            quick_q = ["게보린", "타이레놀", "후시딘", "박카스", "소화제"]
            for idx, q in enumerate(quick_q):
                with cols[idx]:
                    if st.button(f"💊 {q}", key=f"q{idx}", use_container_width=True):
                        user_msg = f"{q} 알려줘"
                        st.session_state.chat_messages.append({"role": "user", "content": user_msg})
                        
                        with st.spinner("🔍 검색 중..."):
                            results = search_mfds_medicine(q)
                            
                            if results and len(results) > 0:
                                med = results[0]
                                bot_msg = f"""**💊 {med['제품명']}**

**🏢 제조사:** {med['업체명']}

**✨ 효능효과:**
{med['효능효과'][:400]}{'...' if len(med['효능효과']) > 400 else ''}

**📝 사용법:**
{med['사용법'][:300]}{'...' if len(med['사용법']) > 300 else ''}

**⚠️ 주의사항:**
{med['주의사항'][:300]}{'...' if len(med['주의사항']) > 300 else ''}

더 궁금한 점이 있으면 물어보세요! 💊"""
                            else:
                                bot_msg = f"'{q}'에 대한 정보를 찾지 못했습니다. 다른 약 이름으로 시도해보세요!"
                            
                            st.session_state.chat_messages.append({"role": "assistant", "content": bot_msg})
                        st.rerun()
        
        st.divider()
        
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if prompt := st.chat_input("💬 메시지를 입력하세요 (예: 게보린 알려줘)"):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            medicine_name = prompt.replace('알려줘', '').replace('정보', '').replace('효능', '').replace('부작용', '').strip()
            
            with st.chat_message("assistant"):
                with st.spinner("🔍 식약처 데이터베이스 검색 중..."):
                    results = search_mfds_medicine(medicine_name)
                    
                    if results and len(results) > 0:
                        med = results[0]
                        
                        response = f"""**💊 {med['제품명']}**

**🏢 제조사:** {med['업체명']}

**✨ 효능효과:**
{med['효능효과'][:400]}{'...' if len(med['효능효과']) > 400 else ''}

**📝 사용법:**
{med['사용법'][:300]}{'...' if len(med['사용법']) > 300 else ''}

**⚠️ 주의사항:**
{med['주의사항'][:300]}{'...' if len(med['주의사항']) > 300 else ''}

---
💡 더 자세한 정보가 필요하시면 약사와 상담하세요!"""
                        
                        if med['낱알이미지']:
                            st.image(med['낱알이미지'], caption="💊 약품 이미지", width=250)
                    else:
                        response = f"""'{medicine_name}'에 대한 정보를 찾지 못했습니다. 😢

**💡 검색 팁:**
- 정확한 제품명 입력 (예: '게보린', '타이레놀')
- 띄어쓰기 없이 입력
- 일반명으로 검색 (예: '아세트아미노펜')"""
                    
                    st.markdown(response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
        if len(st.session_state.chat_messages) > 0:
            if st.button("🗑️ 대화 초기화", key="clear_chat", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()

    # ==================== 탭3: 복약 캘린더 ====================
    with tab3:
        st.markdown("## 📅 복약 캘린더 & 처방 기록 관리")
        
        if not patient_name:
            st.markdown('<div class="warning-box">⚠️ 사이드바에서 이름을 입력하면 복약 기록을 관리할 수 있습니다!</div>', unsafe_allow_html=True)
            st.info("""
### 📋 복약 캘린더 기능
- 📅 **캘린더로 처방 기록 한눈에 보기**
- 💊 **날짜별 약물 정보 조회**
- ➕ **수동으로 처방 기록 추가**
- 🗑️ **기록 삭제 및 관리**
- 📊 **복약 통계 및 분석**

👈 사이드바에서 이름을 입력하고 시작하세요!
            """)
        else:
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col1:
                if 'calendar_year' not in st.session_state:
                    st.session_state.calendar_year = datetime.now().year
                if 'calendar_month' not in st.session_state:
                    st.session_state.calendar_month = datetime.now().month
                
                year = st.selectbox(
                    "연도",
                    range(2020, 2030),
                    index=st.session_state.calendar_year - 2020,
                    key="year_select"
                )
                st.session_state.calendar_year = year
            
            with col2:
                month = st.selectbox(
                    "월",
                    range(1, 13),
                    index=st.session_state.calendar_month - 1,
                    format_func=lambda x: f"{x}월",
                    key="month_select"
                )
                st.session_state.calendar_month = month
            
            with col3:
                if st.button("📅 오늘로 이동", use_container_width=True):
                    st.session_state.calendar_year = datetime.now().year
                    st.session_state.calendar_month = datetime.now().month
                    st.rerun()
            
            st.divider()
            
            dates_with_records = get_calendar_data(patient_name, year, month)
            
            st.markdown(f"### 📆 {year}년 {month}월")
            
            weekdays = ["월", "화", "수", "목", "금", "토", "일"]
            cols = st.columns(7)
            for idx, day in enumerate(weekdays):
                with cols[idx]:
                    st.markdown(f"<div style='text-align: center; font-weight: 700; color: white; font-size: 1.1em;'>{day}</div>", unsafe_allow_html=True)
            
            cal = calendar.monthcalendar(year, month)
            today = datetime.now().date()
            
            for week in cal:
                cols = st.columns(7)
                for idx, day in enumerate(week):
                    with cols[idx]:
                        if day == 0:
                            st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                        else:
                            current_date = datetime(year, month, day).date()
                            has_record = day in dates_with_records
                            is_today = current_date == today
                            
                            if has_record and is_today:
                                button_type = "primary"
                                emoji = "📍"
                            elif has_record:
                                button_type = "secondary"
                                emoji = "💊"
                            elif is_today:
                                button_type = "primary"
                                emoji = "📅"
                            else:
                                button_type = "secondary"
                                emoji = ""
                            
                            if st.button(
                                f"{emoji} {day}",
                                key=f"day_{year}_{month}_{day}",
                                use_container_width=True,
                                type=button_type
                            ):
                                st.session_state.selected_date = current_date
                                st.rerun()
            
            st.divider()
            
            if 'selected_date' in st.session_state:
                selected_date = st.session_state.selected_date
                st.markdown(f"## 📋 {selected_date.strftime('%Y년 %m월 %d일')} 처방 기록")
                
                records = get_records_by_date(patient_name, selected_date)
                
                if records:
                    st.success(f"✅ {len(records)}건의 처방 기록이 있습니다")
                    
                    for idx, record in enumerate(records):
                        with st.container():
                            st.markdown('<div class="record-card">', unsafe_allow_html=True)
                            
                            col1, col2, col3 = st.columns([5, 2, 1])
                            
                            with col1:
                                st.markdown(f"### 💊 처방 #{idx+1}")
                                st.markdown(f"**🏥 병원:** {record.get('hospital', '정보 없음')}")
                                st.markdown(f"**📅 조제일:** {record.get('scan_date', '')[:10]}")
                                
                                medicines = record.get('medicines', [])
                                if isinstance(medicines, list):
                                    st.markdown("**💊 처방 약물:**")
                                    for med in medicines:
                                        st.markdown(f"- {med}")
                                
                                with st.expander("📊 상세 정보"):
                                    analysis = record.get('analysis', '{}')
                                    try:
                                        if isinstance(analysis, str):
                                            analysis_data = json.loads(analysis)
                                        else:
                                            analysis_data = analysis
                                        
                                        if isinstance(analysis_data, list) and len(analysis_data) > 0:
                                            for med_info in analysis_data:
                                                st.markdown(f"**{med_info.get('약품명', '알 수 없음')}**")
                                                st.write(f"효능: {med_info.get('효능효과', '정보 없음')[:100]}...")
                                                st.divider()
                                    except:
                                        st.write("상세 정보를 불러올 수 없습니다")
                            
                            with col2:
                                taken = record.get('taken', False)
                                if taken:
                                    st.success("✅ 복용 완료")
                                else:
                                    if st.button("✅ 먹었어요", key=f"take_{record['id']}", use_container_width=True):
                                        mark_as_taken(record['id'])
                                        st.rerun()
                            
                            with col3:
                                if st.button("🗑️", key=f"del_{record['id']}", use_container_width=True):
                                    if delete_record(record['id']):
                                        st.success("삭제 완료!")
                                        st.rerun()
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)
                else:
                    st.info("이 날짜에는 처방 기록이 없습니다")
                    
                    with st.expander("➕ 수동으로 처방 기록 추가하기"):
                        st.markdown("### 📝 처방 정보 입력")
                        
                        manual_hospital = st.text_input("병원/약국명", placeholder="예: 서울대학교병원")
                        manual_medicines = st.text_area(
                            "약 이름 (한 줄에 하나씩)", 
                            placeholder="예:\n타이레놀\n게보린\n소화제",
                            height=100
                        )
                        
                        if st.button("💾 기록 추가", type="primary", use_container_width=True):
                            if manual_hospital and manual_medicines:
                                medicines_list = [m.strip() for m in manual_medicines.split('\n') if m.strip()]
                                
                                scan_date = datetime.combine(selected_date, time(12, 0, 0)).isoformat()
                                
                                if save_to_database(
                                    patient_name,
                                    patient_age,
                                    medicines_list,
                                    manual_hospital,
                                    json.dumps([], ensure_ascii=False),
                                    scan_date
                                ):
                                    st.success("✅ 기록이 추가되었습니다!")
                                    st.rerun()
                            else:
                                st.warning("병원명과 약 이름을 모두 입력해주세요")
            else:
                st.info("👆 캘린더에서 날짜를 선택하면 해당 날짜의 처방 기록을 확인할 수 있습니다")
                
                st.markdown("### 📊 최근 처방 기록")
                recent_records = get_records_by_user(patient_name)[:5]
                
                if recent_records:
                    for record in recent_records:
                        date = datetime.fromisoformat(record['scan_date']).strftime('%Y-%m-%d')
                        medicines = record.get('medicines', [])
                        med_count = len(medicines) if isinstance(medicines, list) else 0
                        
                        st.markdown(f"- **{date}** | {record.get('hospital', '병원 정보 없음')} | {med_count}개 약물")
                else:
                    st.write("아직 기록이 없습니다. 처방약을 스캔하거나 수동으로 추가해보세요!")

else:  # 자녀 모드
    tab1, tab2 = st.tabs(["👨‍👩‍👧 부모님 연결", "📊 복약 현황"])
    
    with tab1:
        st.markdown("## 👨‍👩‍👧 부모님 계정 연결")
        
        parent_name = st.text_input("부모님 이름", placeholder="예: 김영희")
        
        if st.button("🔗 연결하기", type="primary"):
            parent = get_user_by_name(parent_name)
            if parent and st.session_state.user_id:
                if connect_family(parent['id'], st.session_state.user_id):
                    st.success(f"✅ {parent_name}님과 연결되었습니다!")
            else:
                st.error("해당 이름의 부모님을 찾을 수 없습니다")
        
        st.divider()
        
        if st.session_state.user_id:
            parents = get_my_parents(st.session_state.user_id)
            if parents:
                st.markdown("### 연결된 부모님")
                for p in parents:
                    st.info(f"👤 {p['users']['name']} ({p['users']['age']}세)")
    
    with tab2:
        st.markdown("## 📊 부모님 복약 현황")
        
        if st.session_state.user_id:
            parents = get_my_parents(st.session_state.user_id)
            
            if not parents:
                st.warning("연결된 부모님이 없습니다. 먼저 연결해주세요!")
            else:
                for p in parents:
                    parent_id = p['parent_id']
                    parent_name = p['users']['name']
                    
                    st.markdown(f"### 👤 {parent_name}님")
                    
                    today_meds = get_today_medicine_status(parent_id)
                    
                    if today_meds:
                        for med in today_meds:
                            col1, col2 = st.columns([5, 1])
                            
                            with col1:
                                medicines = med.get('medicines', [])
                                med_str = ", ".join(medicines) if isinstance(medicines, list) else "정보 없음"
                                
                                if med.get('taken'):
                                    st.success(f"✅ {med_str} - 복용 완료")
                                else:
                                    st.warning(f"⏰ {med_str} - 아직 복용 전")
                            
                            with col2:
                                if not med.get('taken'):
                                    if st.button("📞", key=f"call_{med['id']}"):
                                        st.info("부모님께 전화하기")
                    else:
                        st.info("오늘 예정된 복약이 없습니다")
                    
                    st.divider()
                    
                    # 최근 7일 통계
                    all_records = get_records_by_user(parent_name)
                    week_ago = datetime.now().date() - timedelta(days=7)
                    week_records = [r for r in all_records if datetime.fromisoformat(r.get('scan_date', '')).date() >= week_ago]
                    
                    taken_count = sum(1 for r in week_records if r.get('taken', False))
                    total_count = len(week_records)
                    compliance_rate = (taken_count / total_count * 100) if total_count > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("이번 주 처방", f"{total_count}건")
                    with col2:
                        st.metric("복용 완료", f"{taken_count}건")
                    with col3:
                        st.metric("복약 순응도", f"{compliance_rate:.0f}%")

# ==================== 푸터 ====================
st.divider()
st.markdown("""
<div style='text-align: center; color: white; padding: 30px; background: rgba(255,255,255,0.1); border-radius: 15px;'>
    <h3 style='margin-bottom: 10px;'>💊 스마트 약봉지 분석 시스템 v4.0 🎉</h3>
    <p style='font-size: 1.1em; margin-bottom: 15px;'>
        <strong>처방약 분석:</strong> OpenAI GPT-4o + 이미지 전처리 | 
        <strong>일반의약품 정보:</strong> 식약처 e약은요 API | 
        <strong>복약 관리:</strong> 캘린더 기반 기록 시스템 + 가족 복약 모니터링 |
        <strong>데이터베이스:</strong> Supabase
    </p>
    <p style='font-size: 0.95em; color: rgba(255,255,255,0.8);'>
        ⚠️ 본 서비스는 참고용이며, 정확한 정보는 의사/약사와 상담하세요.
    </p>
</div>
""", unsafe_allow_html=True)
