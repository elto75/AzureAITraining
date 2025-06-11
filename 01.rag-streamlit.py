import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import streamlit as st

load_dotenv()
    
# set environment variables
openai_endpoint = os.getenv('OPENAI_ENDPOINT')
openai_api_key = os.getenv('OPENAI_API_KEY')
chat_model = os.getenv('CHAT_MODEL')
embedding_model = os.getenv('EMBEDDING_MODEL')
embedding_deployment_name = os.getenv('EMBEDDING_DEPLOYMENT_NAME')
search_endpoint = os.getenv('SEARCH_ENDPOINT')
search_api_key = os.getenv('SEARCH_API_KEY')
index_name = os.getenv('INDEX_NAME')

if not all([openai_endpoint, openai_api_key, chat_model, embedding_model, search_endpoint, search_api_key, index_name]):
    st.write("Please set all required environment variables.")
    st.stop()

# Initialize Azure OpenAI client
chat_client = AzureOpenAI(
    azure_endpoint=openai_endpoint,
    api_key=openai_api_key,
    api_version="2024-12-01-preview",
)

st.title("Margie's Travel Assistant")

st.write("Ask your travel-related questions below:")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "You are a travel assistant that provides information on travel service available from Margie's Travel."
        },
    ]

for message in st.session_state.messages:
    if message["role"] != 'system':
        st.chat_message(message["role"]).write(message["content"])

def get_openai_response(messages):

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
        model=chat_model,
        messages=messages,
        extra_body=rag_parameters,
    )

    if response and response.choices:
        answer = response.choices[0].message.content
        return answer


input_question = st.chat_input("Enter your question:")

if input_question:
    st.session_state.messages.append({"role": "user", "content": input_question})
    st.chat_message("user").write(input_question)
    with st.spinner("Thinking..."):
        answer = get_openai_response(st.session_state.messages)
    if answer:
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.chat_message("assistant").write(answer)
    else:
        st.write("No response from the model. Please try again.")
    
