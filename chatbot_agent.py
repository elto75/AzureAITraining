import ast
import json
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import streamlit as st
# from azureopenai import HumanMessage, SystemMessage, AIMessage

load_dotenv()
    
# set environment variables
openai_endpoint = os.getenv('OPENAI_ENDPOINT')
openai_api_key = os.getenv('OPENAI_API_KEY')
chat_model = os.getenv('CHAT_MODEL')
chat_model_deployment_name = os.getenv('CHAT_MODEL_DEPLOYMENT_NAME')
embedding_model = os.getenv('EMBEDDING_MODEL')
embedding_deployment_name = os.getenv('EMBEDDING_DEPLOYMENT_NAME')
search_endpoint = os.getenv('SEARCH_ENDPOINT')
search_api_key = os.getenv('SEARCH_API_KEY')
index_name = os.getenv('INDEX_NAME')

if not all([openai_endpoint, openai_api_key, chat_model, chat_model_deployment_name, embedding_model, search_endpoint, search_api_key, index_name]):
    st.write("Please set all required environment variables.")
    st.stop()

# print(f"Using OpenAI Endpoint: {openai_endpoint}")
# print(f"Using OpenAI API Key: {openai_api_key}")
# print(f"Using Chat Model: {chat_model}")
# print(f"Using Chat Model Deployment Name: {chat_model_deployment_name}")
# print(f"Using Embedding Model: {embedding_model}")
# print(f"Using Embedding Deployment Name: {embedding_deployment_name}")
# print(f"Using Search Endpoint: {search_endpoint}")
# print(f"Using Search API Key: {search_api_key}")
# print(f"Using Index Name: {index_name}")

# Initialize Azure OpenAI client
chat_client = AzureOpenAI(
    azure_endpoint=openai_endpoint,
    api_key=openai_api_key,
    api_version="2024-12-01-preview",
)

st.title("KT 멤버십 고객 지원 챗봇")

st.write("이벤트와 자주 묻는 질문(FAQ)에 대한 답변을 제공하는 챗봇입니다.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "",
        },
    ]


for message in st.session_state.messages:
    if message["role"] != 'system':
        st.chat_message(message["role"]).write(message["content"])

def topic_decision(message):
    user_query = f"""
                    # User Query Topic Classifier: FAQ vs Event Search

                    ## Purpose
                    You are an expert in analyzing user queries to classify whether they are related to FAQ (Frequently Asked Questions) or Event Search.

                    ## Input
                    User query text

                    ## Output
                    Output the classification result in the following format:
                    {{'Classification': '[FAQ/Event Search]',
                    'Confidence': '[High/Medium/Low]',
                    'Judgment Basis': '[Brief explanation of the classification reason]'}}

                    ## Classification Criteria

                    ### FAQ Query Characteristics:
                    - Seeking answers to frequently asked questions
                    - General information requests
                    - Basic information questions about products/services
                    - Problem-solving method questions
                    - Questions about policies or procedures
                    - Questions without time constraints

                    ### Event Search Query Characteristics:
                    - Searching for information about specific events
                    - Including specific information such as time, date, location, etc.
                    - Questions about event participation methods or conditions
                    - Searching for events taking place within a specific period
                    - Questions about promotions or special events

                    ### Classification Method:
                    - Keyword-based analysis (FAQ-related keywords vs Event-related keywords)
                    - Analysis of question structure and format
                    - Checking for time-related expressions
                    - Understanding query intent (information acquisition vs specific event participation)
                    - 5W1H-based query analysis

                    ## Examples

                    ### FAQ Query Examples:
                    - "I'm curious about how to use Product A"
                    - "What is the refund policy?"
                    - "How do I delete my account?"
                    - "How long does shipping take?"

                    ### Event Search Query Examples:
                    - "Are there any discount events happening this weekend?"
                    - "Until when is the Family Month event in May?"
                    - "Where is the pop-up store that's opening tomorrow?"
                    - "I'm curious about how to participate in the summer season special promotion"
                    - "Where will next month's new product launch event be held?"
                    - "What are the membership benefit?"


                    ## Classification Process
                    1. Analyze the user query to check keywords, structure, time expressions, etc.
                    2. Compare with the characteristics of FAQ and Event Search
                    3. Determine the most appropriate classification and evaluate confidence
                    4. Output the classification result and judgment basis

                    ## Notes
                    - If characteristics of both categories appear, classify based on the more strongly appearing characteristics but prioritize Event Search if it includes '혜택' or specific event-related keywords'
                    - If the query is ambiguous or does not fit either category, classify as 'Uncertain'
                    - If the classification is uncertain, mark the confidence as 'Low' and indicate that additional information is needed

                    ---

                    User Query: {message}
                                             """
    print(f"User Query for Topic Decision: {user_query}")
    response = chat_client.chat.completions.create(
        model=chat_model_deployment_name,
        messages=[{'role': 'user', 'content': user_query}],
    )

    if response and response.choices:
        answer = response.choices[0].message.content
        return answer


def get_openai_response(topic, messages):

    faq_prompt = """Carefully read the user’s query and identify the key keywords and intent .

                    Match the user’s query to the FAQ documents based on the schema fields (Type, Question, Answer) .

                    # Input format:

                    형태: [type of question]
                    질문: [question]
                    답변: [answer]

                    If no matching FAQ is found, reply:
                    “죄송합니다. 문의하신 내용에 대한 정보가 없습니다. 다른 정보를 요청해 주세요.”

                    Ensure response output order matches the query order of the FAQ documents.
                    """
    event_prompt = """You are an expert Event Search Assistant.  
                      Your task is to find and present relevant events from the provided documents based on a user’s query. The documents are given in the following schema:  
                     
                      # Input format:
                      이벤트 정보  
                      • 타이틀: [event title]  
                      • 정보: [summary of the event]  
                      • 내용: [detailed information about the event]  
                      • URL: [url]  

                      When a user asks about events, follow these steps:

                      1. Read the user’s query carefully and identify key criteria such as date, location, topic, or participation method.
                      2. Search the provided documents for any events whose title, summary, or details match the user’s criteria and title has more priority.  
                      3. Rank matching events by relevance, considering both exact keyword matches and semantic similarity.  
                      4. For each relevant event, output in Markdown:

                      # Output format:
                      - [event title] 
                      - 기간: [응모기간 in the summary of the event]
                      - 정보: [summary of the event]  
                      - 내용: [detailed information about the event]  
                      - URL: [url]  

                      If no events match, reply with:
                      > “죄송합니다. 문의하신 내용에 대한 정보가 없습니다. 다른 정보를 요청해 주세요.”

                      Ensure clarity, brevity, and correctness in your responses.
                      Do not change event title.
                      Ensure that output url is a input url to prevent hallucination.
                      one output per one event.
                      you can summarize only detailed information about the event in a single document.
                      you can output multiple events if they match the user query.
                      finally, Check the output data from input data and ensure that the output is correct.
                      """
    if topic["Classification"] == 'FAQ':
        index_name = "kt-membership-faq"
        messages[0]["content"] = faq_prompt
    elif topic["Classification"] == 'Event Search':
        index_name = "kt-membership-event"
        messages[0]["content"] = event_prompt
    # Additional parameters to apply RAG pattern using the Azure AI Search service
    rag_parameters = {
        "data_sources": [
            {
                "type": "azure_search",
                "parameters": {
                    "endpoint": search_endpoint,
                    "index_name": index_name,
                    "authentication": {
                        "type": "api_key",
                        "key": search_api_key
                    },
                    "query_type": "vector",
                    "embedding_dependency": {
                        "type": "deployment_name",
                        "deployment_name": embedding_deployment_name,
                    }
                }
            }
        ]
    }

    

    response = chat_client.chat.completions.create(
        model=chat_model_deployment_name,
        messages=messages,
        extra_body=rag_parameters,
    )

    if response and response.choices:
        answer = response.choices[0].message.content
        return answer


input_question = st.chat_input("질문을 입력하세요:")

if input_question:
    st.session_state.messages.append({"role": "user", "content": input_question})
    st.chat_message("user").write(input_question)
    with st.spinner("Thinking..."):
        topic_string = topic_decision(input_question)
        print(f"Topic decision response: {topic_string}")
        topic = ast.literal_eval(topic_string)
        print(f"Detected topic: {topic}")
        if topic["Classification"] == 'FAQ' or topic["Classification"] == 'Event Search':
            answer = get_openai_response(topic, st.session_state.messages)
        else:
            answer = "죄송합니다. 요청하신 내용에 대한 정보를 가지고 있지 않습니다. 다른 질문을 해주세요.[토픽 결정 실패]"
    if answer:
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.chat_message("assistant").write(answer)
    else:
        st.write("No response from the model. Please try again.")
    