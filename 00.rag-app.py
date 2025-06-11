import os
from dotenv import load_dotenv
from openai import AzureOpenAI

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
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
        print("Please set all required environment variables.")
        return

    # Initialize Azure OpenAI client
    chat_client = AzureOpenAI(
        azure_endpoint=openai_endpoint,
        api_key=openai_api_key,
        api_version="2024-12-01-preview",
    )
    prompt = [
        {
            "role": "system",
            "content": "You are a travel assistant that provides information on travel service available from Margie's Travel."
        },
    ]

    while True:
        input_text = input("Enter your question (or type 'exit' to quit): ")
        if input_text.lower().strip() == 'exit':
            print("Exiting the application.")
            break
        if not input_text.strip():
            print("Please enter a valid question.")
            continue
        prompt.append({"role": "user", "content": input_text})

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
            messages=prompt,
            extra_body=rag_parameters,

        )

        if response and response.choices:
            answer = response.choices[0].message.content
            print(f"Answer: {answer}")
            prompt.append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    main()

