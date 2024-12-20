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
        max-width: 800px;
        margin: 0 auto;
        padding: 3rem 2rem;
        background-color: #f8f9fc;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    
    /* 메인 타이틀 */
    .main-title {
        color: #2c3e50;
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
        border-color: #64748b;
        box-shadow: 0 0 0 4px rgba(100, 116, 139, 0.1);
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
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.1);
        margin-top: 2rem;
        border: 1px solid #e2e8f0;
    }
    
    /* 결과 제목 */
    .results-container h3 {
        color: #334155;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e2e8f0;
        letter-spacing: -0.025em;
    }
    
    /* 결과 텍스트 */
    .results-container p {
        color: #475569;
        font-size: 1.1rem;
        line-height: 1.8;
        margin: 0;
        white-space: pre-line;
    }
    
    /* 로딩 스피너 */
    .stSpinner {
        text-align: center;
        color: #64748b;
    }
    
    /* 에러 메시지 */
    .stError {
        background-color: #fef2f2;
        color: #991b1b;
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

    /* 프라이머리 버튼 스타일링 */
    .stButton button[kind="primary"] {
        background-color: #22c55e;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        transition: all 0.2s ease;
        width: 100%;
        margin-top: 1.5rem;
    }

    .stButton button[kind="primary"]:hover {
        background-color: #16a34a;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* URL 입력 컨테이너 스타일 */
    .url-input-container {
        position: relative;
        width: 100%;
    }
    
    /* 입력창 스타일 */
    .stTextInput input {
        width: 100%;
        padding-right: 50px !important;  /* 버튼을 위한 공간 확보 */
    }
    
    /* 내부 화살표 버튼 스타일 */
    .inner-arrow-button {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        background-color: #475569;
        color: white;
        border: none;
        border-radius: 6px;
        width: 35px;
        height: 35px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }
    
    .inner-arrow-button:hover {
        background-color: #334155;
    }

    /* 숨길 요소 스타일 */
    .hide-input {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# 제목을 커스텀 HTML로 표시
st.markdown('<h1 class="main-title">웹 페이지 요약 애플리케이션</h1>', unsafe_allow_html=True)

# API 키 입력
API_KEY = st.secrets["GEMINI_API_KEY"]

# HTML 컴포넌트 부분을 columns로 변경
col1, col2 = st.columns([6,1])  # 6:1 비율로 분할

with col1:
    url = st.text_input("", placeholder="https://example.com", label_visibility="collapsed")
with col2:
    submit_button = st.button("➜", key="submit", help="URL 분석 시작")

# URL과 버튼이 눌렸을 때만 실행되도록 조건 수정
if url and submit_button:
    try:
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

            # 기본 시스템 프롬프트 정의
            base_instruction = """
            기본 규칙:
            1. 모든 답변에는 마크다운 형식 적용
            2. 모든 답변은 자연스러운 한국어로 제공할 것
            3. 전문용어가 있다면 쉽게 풀어서 설명할 것
            4. 문장은 간결하고 명확하게 작성할 것
            5. 존댓말을 사용할 것
            """

            # 선택된 스타일에 따라 시스템 지시어 변경
            system_instructions = {
                "일반 요약": """
                다음 내용을 먼저 일반적인 텍스트로 간단히 용갸해주고, 불렛 포인트를 활용하여 가독성을 높여주세요.
                """,

                "세줄 요약": """
                다음 내용을 3개의 핵심 포인트로 요약해주세요.
                규칙:
                1. 각 포인트 사이에는 한 줄의 공백을 줄 것
                2. 각 줄 앞에는 관련된 이모지를 넣을 것
                3. 문장은 '~입니다', '~했습니다'로 끝낼 것
                4. 가장 중요한 내용만 간단명료하게 작성할 것
                """,

                "TLDR 한 줄 요약": """
                다음 내용의 핵심을 단 한 문장으로 요약해주세요.
                규칙:
                1. 30단어 이내로 작성할 것
                3. 가장 중요한 핵심 메시지만 포함할 것
                """,
                
                "5가지 핵심 키워드": """
                다음 내용에서 가장 중요한 5개의 키워드를 추출하고 설명해주세요.
                형식:
                1. [키워드1]: 설명
                2. [키워드2]: 설명
                3. [키워드3]: 설명
                4. [키워드4]: 설명
                5. [키워드5]: 설명
                """,
                
                "Q&A 형식": """
                다음 내용을 Q&A 형식으로 정리해주세요.
                규칙:
                1. 가장 중요한 3가지 질문을 선정할 것
                2. 각 질문은 'Q: '로 시작
                3. 각 답변은 'A: '로 시작
                4. 답변은 명확하고 구체적으로 작성
                5. 질문과 답변 사이는 한 줄 띄울 것
                6. 답변과 그 다음 질문 사이도 한 줄 띄울 것
                """
            }

            summary_style = "일반 요약"
            system_instruction = system_instructions[summary_style]

            # Gemini 모델 설정
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            # 프롬프트 구성
            prompt = f"""
            역할: 당신은 전문적인 콘텐츠 요약 도우미입니다.
            
            {base_instruction}
            
            구체적 지시사항: {system_instruction}
            
            내용:
            {cleaned_text}
            """

            # 직접 프롬프트로 응답 생성
            response = model.generate_content(prompt)
            
            # 결과를 커스텀 컨테이너에 표시
            st.markdown(f"""
            <div class="results-container">
                <h3>요약 결과</h3>
                <p>{response.text}</p>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
