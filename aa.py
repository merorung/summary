import streamlit as st
import bs4
from langchain_community.document_loaders import WebBaseLoader
from fake_useragent import UserAgent
import re
import google.generativeai as genai

# 제목 설정
st.title('웹 페이지 요약 애플리케이션')

# API 키 입력 (Streamlit Secrets에서 관리하는 것을 추천)
API_KEY = st.secrets["GEMINI_API_KEY"]  # Streamlit 대시보드에서 설정 필요

# URL 입력 받기
url = st.text_input("URL을 입력하세요:", placeholder="https://example.com")

if url:  # URL이 입력되었을 때만 실행
    try:
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
        
        # 결과 표시
        st.subheader("요약 결과:")
        st.write(messages_with_metadata.text)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
