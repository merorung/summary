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
        background-color: #f8f9fc;  /* 매우 연한 블루그레이 */
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    
    /* 메인 타이틀 */
    .main-title {
        color: #2c3e50;  /* 깊이감 있는 네이비 */
        font-size: 2.25rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 3rem;
        padding-bottom: 1.5rem;
        border-bottom: 3px solid #e2e8f0;  /* 은은한 그레이 */
        letter-spacing: -0.025em;
    }
    
    /* 입력 필드 */
    .stTextInput input {
        width: 100%;
        padding: 1rem;
        border: 2px solid #e2e8f0;  /* 은은한 그레이 */
        border-radius: 1rem;
        font-size: 1rem;
        transition: all 0.2s ease;
        background-color: white;
    }
    
    .stTextInput input:focus {
        border-color: #64748b;  /* 중간 톤의 슬레이트 */
        box-shadow: 0 0 0 4px rgba(100, 116, 139, 0.1);
        outline: none;
    }
    
    .stTextInput input::placeholder {
        color: #94a3b8;  /* 밝은 슬레이트 */
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
        color: #334155;  /* 진한 슬레이트 */
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e2e8f0;
        letter-spacing: -0.025em;
    }
    
    /* 결과 텍스트 */
    .results-container p {
        color: #475569;  /* 중간 톤의 슬레이트 */
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

    /* 버튼 스타일링 */
    .stButton button {
        background-color: #475569;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        transition: all 0.2s ease;
    }

    .stButton button:hover {
        background-color: #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# 제목을 커스텀 HTML로 표시
st.markdown('<h1 class="main-title">웹 페이지 요약 애플리케이션</h1>', unsafe_allow_html=True)

# API 키 입력
API_KEY = st.secrets["GEMINI_API_KEY"]

# URL 입력 받기
url = st.text_input("URL을 입력하세요:", placeholder="https://example.com")

# URL 입력 후 요약 스타일 선택
summary_style = st.selectbox(
    "요약 스타일을 선택하세요:",
    [
        "기본 불렛포인트 요약",
        "TLDR 한 줄 요약",
        "5가지 핵심 키워드",
        "뉴스 기사 형식",
        "Q&A 형식"
    ]
)

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

            # 선택된 스타일에 따라 시스템 지시어 변경
            system_instructions = {
                -모든 요약은 자연스러운 한국어로 진행해야해. 가독성을 위해 줄바꿈도 적극적으로 활용해 줘.
                "기본 불렛포인트 요약": "다음을 한국어로 불렛포인트 형식으로 3줄로 요약해줘. 어미는 ~임, ~함과 같이 간결하게 할 것. 각 문장의 앞에는 이모지를 하나 넣을 것.",
                "TLDR 한 줄 요약": "다음 내용을 한 문장으로 간단히 요약해줘. 'TLDR: ' 로 시작할 것.",
                "5가지 핵심 키워드": "다음 내용에서 가장 중요한 5가지 키워드를 추출하고, 각각에 대해 한 줄로 설명해줘.",
                "뉴스 기사 형식": "다음 내용을 뉴스 기사 형식으로 제목과 함께 3문단으로 요약해줘.",
                "Q&A 형식": "다음 내용을 Q&A 형식으로 가장 중요한 3가지 질문과 답변으로 정리해줘."
            }

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
            
            지시사항: {system_instruction}
            
            내용:
            {cleaned_text}
            """

            # 직접 프롬프트로 응답 생성 (채팅 세션 대신)
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
