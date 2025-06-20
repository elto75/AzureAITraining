# Data Gather agent

1. 보안 문제로 업로드 되지 않는 파일


.env
````
OPENAI_ENDPOINT=https://dalhyun-openai-mvp-200.openai.azure.com/
OPENAI_API_KEY=...
CHAT_MODEL=gpt-4o-mini
CHAT_MODEL_DEPLOYMENT_NAME=mvp-gpt-4o-mini
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_DEPLOYMENT_NAME=mvp-text-embedding-ada-002
SEARCH_ENDPOINT=https://dalhyun-ai-search-mvp-200.search.windows.net
SEARCH_API_KEY=...
INDEX_NAME=ktmembership
````
env_event_index
````
; PROJECT_ENDPOINT="https://dalhyun-fine-project-resource.services.ai.azure.com/api/projects/dalhyun-fine-project"
MODEL_DEPLOYMENT_NAME="mvp-gpt-4o-mini"
EVENT_LIST_URL="https://event.kt.com/html/event/ongoing_event_list.html"

AZURE_VISION_ENDPOINT=https://westus.api.cognitive.microsoft.com/
AZURE_VISION_API_KEY=...
# Vision API endpoint and key for image processing

; AZURE_SEARCH_SERVICE_ENDPOINT=https://dalhyun-ai-search-mvp.search.windows.net
; AZURE_SEARCH_SERVICE_INDEX_NAME=event_index
; AZURE_SEARCH_SERVICE_API_KEY=...

; AZURE_STORAGE_ACCOUNT_ENDPOINT=...
; AZURE_STORAGE_ACCOUNT_API_KEY=...
; AZURE_STORAGE_ACCOUNT_NAME=dalhyunstorageaccount001

PAGE_TYPE="event"

MAX_PAGE_NO=2

FILE_DIR=data/event_files

LIST_CONTAINER_NAME=event-list
````
env_faq_index
````
; PROJECT_ENDPOINT="https://dalhyun-fine-project-resource.services.ai.azure.com/api/projects/dalhyun-fine-project"
MODEL_DEPLOYMENT_NAME="mvp-gpt-4o-mini"
EVENT_LIST_URL="https://ermsweb.kt.com/pc/faq/faqList.do"

AZURE_VISION_ENDPOINT=https://dalhyun-ai-service-mvp.cognitiveservices.azure.com/
AZURE_VISION_API_KEY=
# Vision API endpoint and key for image processing

; AZURE_SEARCH_SERVICE_ENDPOINT=https://dalhyun-ai-search-mvp.search.windows.net
; AZURE_SEARCH_SERVICE_INDEX_NAME=event_index
; AZURE_SEARCH_SAZURE_VISION_ENDPOINT=https://westus.api.cognitive.microsoft.com/
; AZURE_STORAGE_ACCOUNT_ENDPOINT=
; AZURE_STORAGE_ACCOUNT_API_KEY=...
; AZURE_STORAGE_ACCOUNT_NAME=dalhyunstorageaccount001


PAGE_TYPE="faq"

MAX_PAGE_NO=1

FILE_DIR=data/faq_files
LIST_CONTAINER_NAME=tab-items
````

1. 설치 필요한 패키지 - uv 또는 pip를 이용하여 설치 uv add dotenv or pip install dotenv 형태
   - azure-ai-agents
   - azure-identity
   - azure-search-documents
   - beautifulsoup4
   - chromedriver-autoinstaller
   - dotenv
   - selenium
   - webdriver-manager
   - azure-ai-vision-imageanalysis
   - azure-storage-blob
   - langgraph

1. Azure Resource 삭제
az group delete --name dalhyun-rg
az search service delete --name dalhyun-search-mvp-001 --resource-group dalhyun-rg
az cognitiveservices account deployment delete --name dalhyun-openai-mvp-001 --resource-group dalhyun-rg --deployment-name mvp-gpt4o-mini
az cognitiveservices account deployment delete --name dalhyun-openai-mvp-001 --resource-group dalhyun-rg --deployment-name mvp-text-embedding-3-small 
az storage account delete --name dalhyunstorageaccount001 --resource-group dalhyun-rg --location westus --sku Standard_LRS --kind StorageV2
az cognitiveservices account delete --name dalhyun-openai-mvp-001 --resource-group dalhyun-rg
az cognitiveservices account purge --name dalhyun-openai-mvp-001 --resource-group dalhyun-rg --location westus
az cognitiveservices account create --name dalhyun-openai-mvp-001 --resource-group dalhyun-rg --location westus --kind OpenAI --sku s0
az cognitiveservices account deployment create --name dalhyun-openai-mvp-004 --resource-group dalhyun-rg --deployment-name mvp-gpt4o-mini --model-name gpt-4o-mini --model-version 2024-07-18 --model-format OpenAI --sku-capacity 1 --sku-name GlobalStandard
az cognitiveservices account deployment create --name dalhyun-openai-mvp-004 --resource-group dalhyun-rg --deployment-name mvp-text-embedding-3-small --model-name text-embedding-3-small --model-version 1 --model-format OpenAI --sku-capacity 1 --sku-name GlobalStandard

az storage account create --name dalhyunstorageaccount001 --resource-group dalhyun-rg --location westus --sku Standard_LRS --kind StorageV2
az cognitiveservices account purge --name dalhyun-ai-service-mvp-001 --resource-group dalhyun-mvp --location westus

1. Azure Resource 생성
````
az group create --name dalhyun-rg --location westus
az search service create --name dalhyun-search-mvp-001 --location westus --resource-group dalhyun-rg --sku Basic --partition-count 1 --replica-count 1
az cognitiveservices account create --name dalhyun-openai-mvp-001 --resource-group dalhyun-rg --location westus --kind OpenAI --sku s0
az cognitiveservices account deployment create --name dalhyun-openai-mvp-001 --resource-group dalhyun-rg --deployment-name mvp-gpt4o-mini --model-name gpt-4o-mini --model-version 2024-07-18 --model-format OpenAI --sku-capacity 1 --sku-name GlobalStandard
az cognitiveservices account deployment create --name dalhyun-openai-mvp-001 --resource-group dalhyun-rg --deployment-name mvp-text-embedding-3-small --model-name text-embedding-3-small --model-version 1 --model-format OpenAI --sku-capacity 1 --sku-name GlobalStandard
az storage account create --name dalhyunstorageaccount001 --resource-group dalhyun-rg --location westus --sku Standard_LRS --kind StorageV2
az cognitiveservices account create --name dalhyun-ai-service-mvp-001 --resource-group dalhyun-mvp --sku s0 --location westus --kind CognitiveServices


````
1. data-gather-agent.py 실행하여 rag 자료 생성
````
# 실행전 env_event_index파일과 env_faq_index파일의 환경 변수 설정필요
# 크롬 브라우저 설치되어 있어야 함
# uv 사용시
uv run python data-gather-agent.py env_event_index
uv run python data-gather-agent.py env_faq_index
# python 직접 사용시
python data-gather-agent.py env_event_index
python data-gather-agent.py env_faq_index
````
data 폴더에 event_files, faq_files에 파일 생성 확인
단 기존의 파일이 있으면 생성하지 않고 건너 뜀
삭제하고 실행시 다운받아서 폴드에 저장됨(실행전 폴더는 생성해 두어야 함, 실행전 크롬 설치되어 있어야 함)


1. Data file Upload
   SDK를 이용하여 업로드 하려고 하였으나 SDK에서 제공하는 인증 방식이 권한이 없는 방식이라 진행하지 못함
   uploadDocs.bat에 스토리지 키를 설정하고 cmd 창에서 실행
   ## 원인 파악중이지만 두번째 명령이 직접 실행되지 않아 기존 uploadDocs.bat파일 실행된 창에서 마지막 명령어 수동 실행 필요
1. Azure AI Search 생성
   스크립트가 자동 생성되지 않아 portal에서 생성
   ragdatas 컨테이너의 서브 폴더 event_files를 kt-membership-event 인덱스로, faq_files를 kt-membership-faq 인덱스로 생성(벡터 DB  적용)

1. https://dalhyun-chatbot-effgbubhhgabetgk.westus-01.azurewebsites.net/ 웹앱에서 동작 확인

1. Sample
   자동차 관련 이벤트를 알려줘
   인터넷 장애는 어떻게 신고해야 해?
   인터넷 품질을 개선 시키는 방법을 알려줘