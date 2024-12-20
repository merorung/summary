import streamlit as st
import bs4
from langchain_community.document_loaders import WebBaseLoader
from fake_useragent import UserAgent
import re
import google.generativeai as genai

# 커스텀 CSS 추가
st.markdown("""
<style>
    /* 전체 앱 컨테이너 */
    .stApp {
        max-width: 800px;  /* 더 좁은 컨테이너로 가독성 향상 */
        margin: 0 auto;
        padding: 3rem 2rem;
        background-color: #fafafa;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    
    /* 메인 타이틀 */
    .main-title {
        color: #0f172a;
        font-size: 2.25rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 3rem;
        padding-bottom: 1.5rem;
        border-bottom: 3px solid #e2e8f0;
        letter-spacing: -0.025em;
    }
    
    /* 입력 필드 */
    .stTextInput input {
        width: 100%;
        padding: 1rem;
        border: 2px solid #e2e8f0;
        border-radius: 1rem;
        font-size: 1rem;
        transition: all 0.2s ease;
        background-color: white;
    }
    
    .stTextInput input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
        outline: none;
    }
    
    .stTextInput input::placeholder {
        color: #94a3b8;
    }
    
    /* 결과 컨테이너 */
    .results-container {
        background-color: white;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 
                    0 10px 15px -3px rgba(0, 0, 0, 0.05);
        margin-top: 2rem;
        border: 1px solid #e2e8f0;
    }
    
    /* 결과 제목 */
    .results-container h3 {
        color: #0f172a;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #f1f5f9;
        letter-spacing: -0.025em;
    }
    
    /* 결과 텍스트 */
    .results-container p {
        color: #334155;
        font-size: 1.1rem;
        line-height: 1.8;
        margin: 0;
        white-space: pre-line;  /* 줄바꿈 유지 */
    }
    
    /* 로딩 스피너 */
    .stSpinner {
        text-align: center;
        color: #3b82f6;
    }
    
    /* 에러 메시지 */
    .stError {
        background-color: #fef2f2;
        color: #dc2626;
        padding: 1rem;
        border-radius: 0.75rem;
        border: 1px solid #fee2e2;
        margin-top: 1rem;
        font-weight: 500;
    }
    
    /* 전체 텍스트 색상 조정 */
    .stMarkdown {
        color: #334155;
    }
</style>
""", unsafe_allow_html=True)

# 제목을 커스텀 HTML로 표시
st.markdown('<h1 class="main-title">웹 페이지 요약 애플리케이션</h1>', unsafe_allow_html=True)

# API 키 입력
API_KEY = st.secrets["GEMINI_API_KEY"]

# URL 입력 받기
url = st.text_input("URL을 입력하세요:", placeholder="https://example.com")

if url:
    try:
        # 로딩 상태 표시
        with st.spinner('웹 페이지를 분석 중입니다...'):
            # 웹 페이지 로딩
            loader = WebBaseLoader(url, header_template={'User-Agent': UserAgent().chrome})
            docs = loader.load()
            
            # 텍스트 정제
            raw_page_content = docs[0].page_content
            cleaned_text = re.sub(r'\n+', '\n', raw_page_content)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
            cleaned_text = cleaned_text.strip()

            # 모델 설정
            model_name = "gemini-1.5-pro"
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 0
            }
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]

            system_instruction = "다음을 한국어로 불렛포인트 형식으로 3줄로 요약해줘. 어미는 ~임, ~함과 같이 간결하게 할 것. 각 문장의 앞에는 이모지를 하나 넣을 것."

            # Gemini 모델 설정
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            # 채팅 세션 시작 및 응답 생성
            chat_session = model.start_chat(history=[])
            messages_with_metadata = chat_session.send_message(cleaned_text)
            
            # 결과를 커스텀 컨테이너에 표시
            st.markdown(f"""
            <div class="results-container">
                <h3>요약 결과</h3>
                <p>{messages_with_metadata.text}</p>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}") 
