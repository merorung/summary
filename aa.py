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

            # 기본 시스템 프롬프트 정의
            base_instruction = """
            기본 규칙:
            1. 모든 답변은 자연스러운 한국어로 제공할 것
            2. 전문용어가 있다면 쉽게 풀어서 설명할 것
            3. 문장은 간결하고 명확하게 작성할 것
            4. 존댓말을 사용할 것
            """

            # 선택된 스타일에 따라 시스템 지시어 변경
            system_instructions = {
                "기본 불렛포인트 요약": """
                다음 내용을 3개의 핵심 포인트로 요약해주세요.
                규칙:
                1. 각 포인트는 새로운 줄에 작성할 것
                2. 각 줄 앞에는 관련된 이모지를 넣을 것
                3. 문장은 '~입니다', '~했습니다'로 끝낼 것
                4. 가장 중요한 내용만 간단명료하게 작성할 것
                """,
                
                "TLDR 한 줄 요약": """
                다음 내용의 핵심을 단 한 문장으로 요약해주세요.
                규칙:
                1. 반드시 'TLDR: '로 시작할 것
                2. 30단어 이내로 작성할 것
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
                
                "뉴스 기사 형식": """
                다음 내용을 뉴스 기사처럼 작성해주세요.
                구성:
                1. 제목: 핵심을 담은 눈에 띄는 헤드라인
                2. 부제목: 주요 내용을 한 줄로
                3. 본문: 3개의 단락으로 구성
                   - 첫 단락: 가장 중요한 내용
                   - 둘째 단락: 세부 설명
                   - 셋째 단락: 결론 또는 향후 전망
                """,
                
                "Q&A 형식": """
                다음 내용을 Q&A 형식으로 정리해주세요.
                규칙:
                1. 가장 중요한 3가지 질문을 선정할 것
                2. 각 질문은 'Q: '로 시작
                3. 각 답변은 'A: '로 시작
                4. 답변은 명확하고 구체적으로 작성
                5. 질문과 답변 사이는 한 줄 띄울 것
                """
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
