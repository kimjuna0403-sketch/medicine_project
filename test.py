import streamlit as st
from openai import OpenAI
from supabase import create_client, Client
import base64
from PIL import Image
import io
import json
from datetime import datetime
import requests
import xml.etree.ElementTree as ET

# ==================== 페이지 설정 ====================
st.set_page_config(
    page_title="💊 약봉지 스캔 & 의약품 검색 시스템",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS 스타일링 ====================
st.markdown("""
    <style>
    /* 메인 배경 */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 카드 스타일 */
    .medicine-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* 타이틀 */
    .main-title {
        color: white;
        text-align: center;
        font-size: 3em;
        font-weight: bold;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    /* 서브타이틀 */
    .sub-title {
        color: #f0f0f0;
        text-align: center;
        font-size: 1.2em;
        margin-bottom: 30px;
    }
    
    /* 위험도 배지 */
    .risk-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        margin: 5px;
    }
    
    .risk-low { background: #10b981; color: white; }
    .risk-medium { background: #f59e0b; color: white; }
    .risk-high { background: #ef4444; color: white; }
    
    /* 검색 결과 카드 */
    .search-result-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #667eea;
    }
    
    /* 약 이미지 컨테이너 */
    .medicine-image-container {
        text-align: center;
        padding: 10px;
        background: #f8f9fa;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    /* 정보 섹션 */
    .info-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .info-section h4 {
        color: #667eea;
        margin-bottom: 10px;
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

# ==================== 식약처 API 함수 ====================
def search_mfds_medicine(medicine_name):
    """식약처 e약은요 API로 의약품 검색"""
    try:
        # API 엔드포인트
        url = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
        
        # 요청 파라미터
        params = {
            'serviceKey': st.secrets["MFDS_API_KEY"],  # 인증키
            'itemName': medicine_name,  # 제품명으로 검색
            'pageNo': '1',  # 페이지 번호
            'numOfRows': '10',  # 한 페이지 결과 수
            'type': 'xml'  # 응답 형식
        }
        
        # API 호출
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            # XML 파싱
            root = ET.fromstring(response.content)
            
            # 결과 코드 확인
            result_code = root.find('.//resultCode')
            result_msg = root.find('.//resultMsg')
            
            if result_code is not None and result_code.text == '00':
                # 검색 결과가 있을 때
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
                        '주의사항_경고': item.find('atpnWarnQesitm').text if item.find('atpnWarnQesitm') is not None else '정보 없음',
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
            else:
                # 에러 발생
                error_msg = result_msg.text if result_msg is not None else "알 수 없는 오류"
                st.warning(f"API 응답: {error_msg}")
                return None
        else:
            st.error(f"HTTP 오류: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"식약처 API 오류: {str(e)}")
        return None

# ==================== GPT 약물 정보 검색 ====================
def search_medicine_info_gpt(medicine_name):
    """GPT로 약물 정보 검색 (처방약용)"""
    try:
        prompt = f"""
다음 약물에 대한 상세 정보를 JSON 형식으로 제공해주세요:
약물명: {medicine_name}

다음 형식으로 답변해주세요:
{{
    "약품명": "정확한 약품명",
    "분류": "약물 분류 (예: 진통제, 소화제, 항생제 등)",
    "효능효과": "이 약의 주요 효능",
    "용법용량": "복용 방법과 용량",
    "주의사항": "복용 시 주의할 점",
    "부작용": "발생 가능한 부작용",
    "상호작용": "함께 복용하면 안 되는 약이나 음식",
    "보관방법": "보관 방법",
    "위험도": "낮음/보통/높음 중 하나"
}}

반드시 유효한 JSON 형식으로만 답변해주세요.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip()
        
        # JSON 파싱
        if result.startswith("```json"):
            result = result[7:]
        if result.endswith("```"):
            result = result[:-3]
        
        medicine_info = json.loads(result.strip())
        return medicine_info
        
    except Exception as e:
        st.error(f"GPT 검색 오류: {str(e)}")
        return None

# ==================== 이미지 인코딩 ====================
def encode_image(image):
    """이미지를 base64로 인코딩"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# ==================== 약봉지 분석 ====================
def analyze_medicine_bag(image):
    """약봉지 이미지 분석 (GPT Vision)"""
    try:
        base64_image = encode_image(image)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """이 약봉지 이미지를 분석해서 다음 정보를 JSON 형식으로 추출해주세요:

1. 약 이름들 (리스트로)
2. 병원명
3. 환자명 (있다면)
4. 조제일자 (있다면)

JSON 형식:
{
    "medicines": ["약1", "약2", ...],
    "hospital": "병원명",
    "patient_name": "환자명",
    "date": "날짜"
}

약 이름은 정확하게 추출해주세요. 반드시 유효한 JSON으로만 답변하세요."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        result = response.choices[0].message.content.strip()
        
        # JSON 파싱
        if result.startswith("```json"):
            result = result[7:]
        if result.endswith("```"):
            result = result[:-3]
        
        extracted_data = json.loads(result.strip())
        return extracted_data
        
    except Exception as e:
        st.error(f"이미지 분석 오류: {str(e)}")
        return None

# ==================== 결과 저장 ====================
def save_to_database(patient_name, patient_age, medicines, hospital, analysis):
    """Supabase에 분석 결과 저장"""
    try:
        data = {
            "patient_name": patient_name,
            "patient_age": patient_age,
            "medicines": medicines,
            "hospital": hospital,
            "analysis": analysis,
            "scan_date": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        response = supabase.table('medicine_records').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"저장 오류: {str(e)}")
        return False

# ==================== 메인 타이틀 ====================
st.markdown('<h1 class="main-title">💊 약봉지 스캔 & 의약품 검색 시스템</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">처방약은 AI로 빠르게, 일반의약품은 식약처 공식 정보로 정확하게</p>', unsafe_allow_html=True)

# ==================== 사이드바 ====================
with st.sidebar:
    st.header("📊 시스템 정보")
    
    # 환자 정보 입력
    st.subheader("👤 환자 정보")
    patient_name = st.text_input("이름", placeholder="홍길동")
    patient_age = st.number_input("나이", min_value=0, max_value=120, value=30)
    
    st.divider()
    
    # 통계 정보
    st.subheader("📈 이용 통계")
    try:
        response = supabase.table('medicine_records').select('*').execute()
        total_count = len(response.data)
        
        today = datetime.now().date()
        today_count = len([r for r in response.data if r.get('created_at', '').startswith(str(today))])
        
        st.metric("총 분석 건수", f"{total_count}건")
        st.metric("오늘 분석", f"{today_count}건")
    except:
        st.metric("총 분석 건수", "0건")
        st.metric("오늘 분석", "0건")
    
    st.divider()
    
    # 사용 방법
    with st.expander("📖 사용 방법"):
        st.markdown("""
        **🏥 처방약 분석 (탭1)**
        1. 약봉지 사진 업로드
        2. AI 분석 시작 클릭
        3. 약물 정보 확인 (GPT 생성)
        
        **💊 일반의약품 검색 (탭2)**
        1. 약 이름 입력 (예: 게보린, 타이레놀)
        2. 검색 버튼 클릭
        3. 식약처 공식 정보 확인
        """)
    
    # 주의사항
    with st.expander("⚠️ 주의사항"):
        st.warning("""
        - 본 서비스는 참고용입니다
        - 처방약 정보는 AI가 생성한 것으로 참고용입니다
        - 일반의약품 정보는 식약처 공식 정보입니다
        - 정확한 정보는 의사/약사 상담이 필요합니다
        """)
    
    # API 상태
    with st.expander("🔧 API 상태"):
        st.markdown("""
        - ✅ OpenAI GPT-4o-mini
        - ✅ 식약처 e약은요 API
        - ✅ Supabase Database
        """)

# ==================== 메인 탭 구성 ====================
tab1, tab2, tab3 = st.tabs(["🏥 처방약 분석 (AI)", "💊 일반의약품 검색 (식약처)", "📋 과거 기록"])

# ==================== 탭1: 약봉지 스캔 (GPT) ====================
with tab1:
    st.header("📸 약봉지 사진 분석")
    st.markdown("처방받은 약봉지를 업로드하면 AI가 자동으로 약 이름을 추출하고 정보를 제공합니다.")
    
    # 3단계 프로세스 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 1️⃣ 사진 업로드")
        st.markdown("약봉지 사진을 업로드하세요")
    with col2:
        st.markdown("### 2️⃣ AI 분석")
        st.markdown("GPT가 약 이름을 추출합니다")
    with col3:
        st.markdown("### 3️⃣ 정보 확인")
        st.markdown("각 약물의 상세 정보를 확인합니다")
    
    st.divider()
    
    # 파일 업로더
    uploaded_file = st.file_uploader(
        "약봉지 사진을 업로드하세요",
        type=['png', 'jpg', 'jpeg'],
        help="약 이름이 선명하게 보이는 사진을 업로드해주세요"
    )
    
    if uploaded_file:
        # 이미지 표시
        image = Image.open(uploaded_file)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(image, caption="업로드된 약봉지", width='stretch')
        
        # 분석 버튼
        if st.button("🔍 AI 분석 시작", type="primary", key="analyze_btn"):
            with st.spinner("약봉지 이미지를 분석하는 중..."):
                # 1단계: 이미지에서 약 이름 추출
                extracted_data = analyze_medicine_bag(image)
                
                if extracted_data:
                    st.success("✅ 약 이름 추출 완료!")
                    
                    # 추출된 정보 표시
                    st.subheader("📋 추출된 정보")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**병원명:** {extracted_data.get('hospital', '정보 없음')}")
                    with col2:
                        st.info(f"**조제일자:** {extracted_data.get('date', '정보 없음')}")
                    
                    medicines = extracted_data.get('medicines', [])
                    
                    if medicines:
                        st.subheader(f"💊 추출된 약물 ({len(medicines)}개)")
                        
                        # 진행 바
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        all_medicine_info = []
                        
                        # 2단계: 각 약물 정보 검색
                        for idx, medicine_name in enumerate(medicines):
                            status_text.text(f"약물 정보 검색 중... ({idx+1}/{len(medicines)}) - {medicine_name}")
                            progress_bar.progress((idx + 1) / len(medicines))
                            
                            # GPT로 약물 정보 검색
                            medicine_info = search_medicine_info_gpt(medicine_name)
                            
                            if medicine_info:
                                all_medicine_info.append(medicine_info)
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        # 3단계: 결과 표시
                        st.success("✅ 모든 약물 정보 검색 완료!")
                        
                        for idx, info in enumerate(all_medicine_info):
                            with st.expander(f"💊 {info['약품명']}", expanded=(idx==0)):
                                # 위험도 배지
                                risk_level = info.get('위험도', '보통')
                                if risk_level == '낮음':
                                    badge_class = 'risk-low'
                                    emoji = '🟢'
                                elif risk_level == '높음':
                                    badge_class = 'risk-high'
                                    emoji = '🔴'
                                else:
                                    badge_class = 'risk-medium'
                                    emoji = '🟡'
                                
                                st.markdown(f'<span class="risk-badge {badge_class}">{emoji} 위험도: {risk_level}</span>', unsafe_allow_html=True)
                                st.markdown(f"**분류:** {info.get('분류', '정보 없음')}")
                                
                                # 탭으로 정보 구분
                                info_tab1, info_tab2, info_tab3, info_tab4, info_tab5 = st.tabs([
                                    "효능", "복용법", "주의사항", "부작용", "기타"
                                ])
                                
                                with info_tab1:
                                    st.markdown("#### 💊 효능효과")
                                    st.write(info.get('효능효과', '정보 없음'))
                                
                                with info_tab2:
                                    st.markdown("#### 📝 용법용량")
                                    st.write(info.get('용법용량', '정보 없음'))
                                
                                with info_tab3:
                                    st.markdown("#### ⚠️ 주의사항")
                                    st.write(info.get('주의사항', '정보 없음'))
                                
                                with info_tab4:
                                    st.markdown("#### 🚨 부작용")
                                    st.write(info.get('부작용', '정보 없음'))
                                
                                with info_tab5:
                                    st.markdown("#### 🍽️ 상호작용")
                                    st.write(info.get('상호작용', '정보 없음'))
                                    st.markdown("#### 📦 보관방법")
                                    st.write(info.get('보관방법', '정보 없음'))
                        
                        # 저장 버튼
                        st.divider()
                        if st.button("💾 분석 결과 저장하기", type="primary"):
                            if patient_name:
                                success = save_to_database(
                                    patient_name,
                                    patient_age,
                                    medicines,
                                    extracted_data.get('hospital', ''),
                                    json.dumps(all_medicine_info, ensure_ascii=False)
                                )
                                if success:
                                    st.success("✅ 분석 결과가 저장되었습니다!")
                            else:
                                st.warning("⚠️ 사이드바에서 환자 이름을 입력해주세요.")
                    else:
                        st.warning("약 이름을 찾을 수 없습니다. 더 선명한 사진으로 다시 시도해주세요.")
                else:
                    st.error("이미지 분석에 실패했습니다. 다시 시도해주세요.")

# ==================== 탭2: 일반의약품 검색 챗봇 (식약처) ====================
with tab2:
    st.header("💬 의약품 정보 챗봇")
    st.markdown("궁금한 약 이름을 물어보세요. 식약처 공식 데이터로 답변드립니다!")
    
    # 세션 상태 초기화
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    # 채팅 컨테이너
    chat_container = st.container()
    
    with chat_container:
        # 기존 메시지 표시
        for message in st.session_state.chat_messages:
            if message['role'] == 'user':
                st.markdown(f'''
                <div class="chat-message user-message">
                    <strong>👤 나:</strong> {message['content']}
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="chat-message bot-message">
                    <strong>🤖 약사봇:</strong><br>{message['content']}
                </div>
                ''', unsafe_allow_html=True)
    
    st.divider()
    
    # 인기 질문 (처음에만 표시)
    if len(st.session_state.chat_messages) == 0:
        st.markdown("**💡 이렇게 물어보세요:**")
        popular_questions = [
            "게보린 알려줘",
            "타이레놀 정보",
            "후시딘 효능",
            "박카스 부작용",
            "소화제 추천"
        ]
        cols = st.columns(len(popular_questions))
        for idx, question in enumerate(popular_questions):
            with cols[idx]:
                if st.button(question, key=f"quick_{idx}"):
                    st.session_state.chat_input = question
                    st.rerun()
    
    # 채팅 입력창
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "메시지를 입력하세요",
            placeholder="예: 게보린 알려줘",
            key="chat_input_field",
            label_visibility="collapsed"
        )
    with col2:
        send_button = st.button("📨 전송", type="primary", key="send_btn")
    
    # 메시지 처리
    if send_button and user_input:
        # 사용자 메시지 추가
        st.session_state.chat_messages.append({
            'role': 'user',
            'content': user_input
        })
        
        # 약 이름 추출 (간단한 키워드 추출)
        medicine_name = user_input.replace('알려줘', '').replace('정보', '').replace('효능', '').replace('부작용', '').strip()
        
        with st.spinner("식약처 데이터베이스 검색 중..."):
            results = search_mfds_medicine(medicine_name)
            
            if results and len(results) > 0:
                # 첫 번째 결과 사용
                medicine = results[0]
                
                # 봇 응답 생성
                bot_response = f"""
**💊 {medicine['제품명']}**

**🏢 제조사:** {medicine['업체명']}

**✨ 효능효과:**
{medicine['효능효과'][:300]}{'...' if len(medicine['효능효과']) > 300 else ''}

**📝 사용법:**
{medicine['사용법'][:200]}{'...' if len(medicine['사용법']) > 200 else ''}

**⚠️ 주의사항:**
{medicine['주의사항'][:200]}{'...' if len(medicine['주의사항']) > 200 else ''}

---
더 자세한 정보가 필요하시면 약사와 상담하세요! 💊
                """
                
                # 낱알 이미지 있으면 추가
                if medicine['낱알이미지']:
                    bot_response = f"![약품이미지]({medicine['낱알이미지']})\n\n" + bot_response
                
            else:
                bot_response = f"""
죄송합니다. '{medicine_name}'에 대한 정보를 찾지 못했습니다. 😢

**검색 팁:**
- 정확한 제품명을 입력해주세요 (예: '게보린', '타이레놀')
- 일반명으로 검색해보세요 (예: '아세트아미노펜')
- 다른 이름으로 시도해보세요

다시 물어봐주세요!
                """
        
        # 봇 응답 추가
        st.session_state.chat_messages.append({
            'role': 'bot',
            'content': bot_response
        })
        
        # 페이지 새로고침하여 메시지 표시
        st.rerun()
    
    # 채팅 초기화 버튼
    if len(st.session_state.chat_messages) > 0:
        if st.button("🗑️ 대화 초기화", key="clear_chat"):
            st.session_state.chat_messages = []
            st.rerun()

# ==================== 탭3: 과거 기록 ====================
with tab3:
    st.header("📋 과거 복약 기록")
    st.markdown("지금까지 스캔한 약봉지 기록을 확인할 수 있습니다.")
    
    try:
        # 최근 10개 기록 불러오기
        response = supabase.table('medicine_records')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()
        
        if response.data:
            for record in response.data:
                with st.expander(f"📅 {record['scan_date'][:10]} - {record['patient_name']}님"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**환자명:** {record['patient_name']}")
                    with col2:
                        st.write(f"**나이:** {record['patient_age']}세")
                    with col3:
                        st.write(f"**병원:** {record.get('hospital', '정보 없음')}")
                    
                    st.markdown("**처방 약물:**")
                    medicines = record.get('medicines', [])
                    if isinstance(medicines, list):
                        for med in medicines:
                            st.write(f"- {med}")
                    else:
                        st.write(medicines)
        else:
            st.info("아직 기록이 없습니다. 약봉지를 스캔해보세요!")
    
    except Exception as e:
        st.error(f"기록을 불러오는 중 오류가 발생했습니다: {str(e)}")

# ==================== 푸터 ====================
st.divider()
st.markdown("""
<div style='text-align: center; color: white; padding: 20px;'>
    <p>💊 약봉지 스캔 & 의약품 검색 시스템 v2.0</p>
    <p style='font-size: 0.8em;'>
        처방약 분석: OpenAI GPT-4o-mini | 일반의약품 정보: 식약처 e약은요 API<br>
        본 서비스는 참고용이며, 정확한 정보는 의사/약사와 상담하세요.
    </p>
</div>
""", unsafe_allow_html=True)