#!/usr/bin/env python
# coding: utf-8

# ---
# # 필요한 라이브러리 설치

# In[1]:


get_ipython().run_cell_magic('capture', '', '!pip install -q beautifulsoup4\n!pip install -q langchain-community\n')


# In[2]:


get_ipython().run_cell_magic('capture', '', '!pip install -q fake-useragent\n')


# 

# 

# In[3]:


get_ipython().run_cell_magic('capture', '', '!pip install -q google-generativeai\n')


# # 튜토리얼

# In[4]:


import bs4
from langchain_community.document_loaders import WebBaseLoader
from fake_useragent import UserAgent

# 여러 개의 url 지정 가능
url = input("URL을 입력하세요: ") # "https://blog.langchain.dev/customers-replit/"

loader = WebBaseLoader(url, header_template={'User-Agent': UserAgent().chrome})

docs = loader.load()


# In[5]:


docs[0]


# In[6]:


docs[0].metadata["title"]


# In[7]:


docs[0].metadata["source"]


# In[8]:


docs[0].metadata["description"]


# In[9]:


docs[0].metadata["language"]


# In[10]:


raw_page_content = docs[0].page_content


# In[11]:


raw_page_content


# In[12]:


import re

# 불필요한 줄바꿈 및 공백 제거
cleaned_text = re.sub(r'\n+', '\n', raw_page_content)  # 여러 개의 줄바꿈을 하나로 줄임
cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # 여러 개의 공백을 하나로 줄임
cleaned_text = cleaned_text.strip()  # 양쪽의 불필요한 공백 제거


# In[13]:


cleaned_text


# # API Key 설정

# In[ ]:


import getpass

API_KEY = getpass.getpass()


# # 모델 설정

# In[ ]:


model_name = "gemini-1.5-pro"
temperature = 0.7
top_p = 0.95
top_k = 0

threshold = "BLOCK_NONE"


# In[ ]:


import google.generativeai as genai

generation_config = {
    "temperature": temperature,
    "top_p": top_p,
    "top_k": top_k,
}
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": threshold
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": threshold
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": threshold
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": threshold
    },
]

system_instruction = "다음을 한국어로 불렛포인트 형식으로 3줄로 요약해줘. 어미는 ~임, ~함과 같이 간결하게 할 것. 각 문장의 앞에는 이모지를 하나 넣을 것."

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(model_name=model_name,
                              generation_config=generation_config,
                              safety_settings=safety_settings,
                              system_instruction=system_instruction)


# # 메타 데이터 포함 응답 얻기

# In[ ]:


chat_session = model.start_chat(history=[])

messages_with_metadata = chat_session.send_message(cleaned_text)

print(messages_with_metadata)


# # 텍스트 응답만 얻기

# In[ ]:


messages_only_text = messages_with_metadata.text

print(messages_only_text)


# In[ ]:




