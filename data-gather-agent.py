from pathlib import Path
import chromedriver_autoinstaller
import dotenv
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager  # ChromeDriver 매니저 추가
import time


from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FilePurpose, CodeInterpreterTool, ListSortOrder, MessageRole
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import base64

import urllib.request
import time
import re
import sys


def sanitize_filename(filename):
    # 허용할 문자 집합: 한글, 영문자, 숫자, 밑줄(_), 점(.)
    pattern = r'[^가-힣a-zA-Z0-9._]+'
    # 특수문자는 언더바(_)로 대체
    return re.sub(pattern, '_', filename)

def wait_for_page_load(driver, timeout=60):
    def page_is_loaded(driver):
        return driver.execute_script("return document.readyState") == "complete"
    
    WebDriverWait(driver, timeout).until(page_is_loaded)
    time.sleep(1)  # 추가적인 시간 대기 (필요시 조정 가능)
    main_page_url = driver.current_url
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    iframe_index = 0
    while iframe_index < len(iframes):
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        EC.frame_to_be_available_and_switch_to_it((By.ID, iframes[iframe_index].get_attribute("id")))
        driver.switch_to.frame(iframes[iframe_index])
        WebDriverWait(driver, timeout).until(page_is_loaded)
        driver.switch_to.default_content()  # Switch back to the main content after handling the iframe
        iframe_index += 1
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
    time.sleep(1)  # 추가적인 시간 대기 (필요시 조정 가능)

    # print("페이지 로딩 완료!")

def upload_blob_file(self, blob_service_client: BlobServiceClient, container_name: str):
    container_client = blob_service_client.get_container_client(container=container_name)
    with open(file=os.path.join('filepath', 'filename'), mode="rb") as data:
        blob_client = container_client.upload_blob(name="sample-blob.txt", data=data, overwrite=True)

def main(): 
    page_no = 1
    # Load environment variables from .env file
    dotenv_path = Path(".env")
    if len(sys.argv) >= 2:
        dotenv_path = sys.argv[1]
    dotenv.load_dotenv(dotenv_path = dotenv_path, override=True)

    project_endpoint= os.getenv("PROJECT_ENDPOINT")
    model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")
    event_list_url = os.getenv("EVENT_LIST_URL")

    azure_vision_endpoint = os.getenv("AZURE_VISION_ENDPOINT")
    azure_vision_api_key = os.getenv("AZURE_VISION_API_KEY")

    # azure_search_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
    # azure_search_index_name = os.getenv("AZURE_SEARCH_SERVICE_INDEX_NAME")
    # azure_search_api_key = os.getenv("AZURE_SEARCH_SERVICE_API_KEY")

    max_page_no = int(os.getenv("MAX_PAGE_NO"))  # 최대 페이지 번호 설정
    data_file_dir = os.getenv("FILE_DIR")
    page_type = os.getenv("PAGE_TYPE", "event")  # 페이지 타입 설정, 기본값은 "event"

    # azure_storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    # azure_storage_account_api_key = os.getenv("AZURE_STORAGE_ACCOUNT_API_KEY")
    # azure_storage_account_endpoint = os.getenv("AZURE_STORAGE_ACCOUNT_ENDPOINT")
    # azure_storage_container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
    
    list_container_name = os.getenv("LIST_CONTAINER_NAME", "event-list")  

    # Create an Image Analysis client
    vision_client = ImageAnalysisClient(
        endpoint=azure_vision_endpoint,
        credential=AzureKeyCredential(azure_vision_api_key)
    )
    # blob_service_client = BlobServiceClient(account_url=f"https://{azure_storage_account_name}.blob.core.windows.net/", credential=DefaultAzureCredential())

    # container_client = blob_service_client.get_container_client(container=azure_storage_container_name)
    # search_client = SearchClient(azure_search_endpoint, azure_search_index_name, AzureKeyCredential(azure_search_api_key))

    error_string = ""

    if not model_deployment or not event_list_url:
        if not model_deployment:
            if error_string:
                error_string += ", MODEL_DEPLOYMENT_NAME"
            else:
                error_string = "MODEL_DEPLOYMENT_NAME"
        if not event_list_url:
            if error_string:
                error_string += ", EVENT_LIST_URL"
            else:
                error_string = "EVENT_LIST_URL" 

        raise ValueError(f"Please set the {error_string} environment variables.")
    # event_base_url = event_list_url[:0 + event_list_url.rindex("/event") + len("/event")]  # Extract base URL from the event list URL


    # headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    # 브라우저 꺼짐 방지 옵션
    chrome_options = Options()
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-setuid-sandbox")
    # chrome_options.add_argument("--disable-features=NetworkService")
    chrome_options.add_experimental_option("detach", True)
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--disable-software-rasterizer")
    # chrome_options.add_argument("--use-gl=swiftshader")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--enable-features=VaapiVideoDecoder,UseFcmRegistrationTokens")
    # chrome_options.binary_location = os.getenv("CHROME_BINARY_LOCATION", "D:/chrome-win64/chrome.exe")
    # chrome_options.binary_location = os.getenv("CHROME_BINARY_LOCATION", "C:/Program Files/Google/Chrome/Application/chrome.exe")
    # chromedriver 경로 설정 (필요시)
    # chrome_service = Service(executable_path="D:/chrome-win64/chromedriver-win64/chromedriver.exe")
    
    # chromedriver_autoinstaller.install()
    chromeDriverPath = chromedriver_autoinstaller.install()
    print(f"ChromeDriver installed at: {chromeDriverPath}")
    chrome_service = Service(executable_path=chromeDriverPath)

#    driver = webdriver.Chrome(executable_path="D:/chrome-win64/chromedriver-win64", options=chrome_options)  # chromedriver 경로를 지정할 수도 있습니다.
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    driver.get(event_list_url)
    
    wait_for_page_load(driver)  # 페이지 로딩 대기

    while True:
        
        event_lists = driver.find_element(By.CLASS_NAME, list_container_name).find_elements(By.TAG_NAME, "li")
        # print(f"Event List: {event_lists}")


        event_length = len(event_lists)
        contents = []
        
        for index in range(event_length):
            event_lists = driver.find_element(By.CLASS_NAME, list_container_name).find_elements(By.TAG_NAME, "li")
            item = event_lists[index]

            # item.find_element(By.TAG_NAME, "a").execute_script(script_text)



            if page_type == "event":
                local_file_path = data_file_dir + "/event" + f"{page_no:02d}" + f"{index + 1:02d}" + ".txt"
                if os.path.exists(local_file_path):
                    print(f"file {local_file_path} already exists.")
                    continue
                item = event_lists[index]
                
                script_text = item.find_element(By.TAG_NAME, "a").get_attribute('onclick')
                driver.execute_script("arguments[0].click();", item.find_element(By.TAG_NAME, "a"))  # Click the link to navigate
                wait_for_page_load(driver)  # 페이지 로딩 대기

                contents_html = driver.find_element(By.CLASS_NAME, "contents")

                contents_txt_iframe = contents_html.find_element(By.TAG_NAME, "iframe")
                iframe_url = contents_txt_iframe.get_attribute("src")
                iframe_pagebase_url = iframe_url[:0 + iframe_url.rindex("/")]
                iframe_base_url = iframe_url[:0 + iframe_url.index("/", 9)]
                driver.switch_to.frame(contents_txt_iframe)
                # contents_txt_element = driver.find_element(By.CLASS_NAME, "txt")
                if contents_txt_iframe is None:
                    print("No content iframe found for this event.")
                    driver.back()
                    wait_for_page_load(driver)
                    continue
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                images = []
                for img in soup.find_all('img'):
                    src = ""
                    try:
                        src = img.get('src')
                    except Exception as e:
                        print(f"이미지 src 추출 실패: {e}")
                        continue
                    if src[0:4] == "http":
                        image_url = src
                    elif src[0:2] == "./":
                        image_url = iframe_pagebase_url + img.get('src').replace("./", "/")
                    elif src:
                        image_url = iframe_base_url + src
                    img.decompose()  # Remove the image tag from the soup
                    if not src:
                        continue
                    if image_url:
                        images.append(image_url)

                        # 시간 측정
                        start = time.time()

                        # # 이미지 요청 및 다운로드
                        # try:
                        #     urllib.request.urlretrieve(image_url, "images/" + sanitize_filename(image_url.split("/")[-1]))
                        #     # print(f"다운로드 시간: {time.time() - start:.2f}초")
                        # except Exception as e:
                        #     print(f"이미지 다운로드 실패:[url:{image_url}, error:{e}]")

                for tag in soup.find_all('a'):
                    # src = img.get('src')
                    tag.decompose() # Remove the a tag from the soup
                    if tag:
                        print(tag.get_text(strip=True))

                image_texts = []
                for event_image in images:
                    #Get a caption for the image. This will be a synchronously (blocking) call.
                    try:
                        result = vision_client.analyze_from_url(
                            image_url=event_image,
                            visual_features=[VisualFeatures.READ],
                            gender_neutral_caption=True,  # Optional (default is False)
                        )
                        event_image_texts = []
                        for block in result.read.blocks:
                            for line in block.lines:
                                event_image_texts.append(line.text)
                    except Exception as e:
                        print(f"이미지 분석 실패: [url:{event_image}, error:{e}]")
                        event_image_texts = []

                    image_text = "\n".join(event_image_texts)
                    image_texts.append(image_text)
                
                contents_text = []
                contents_text.append(soup.get_text(strip=True))
                contents_text.append("\n".join(image_texts))
            
                driver.switch_to.default_content()  # Switch back to the default content
                content = {
                        "타이틀": contents_html.find_element(By.CLASS_NAME, "contents-title").text,
                        "정보": contents_html.find_element(By.CLASS_NAME, "info").text,
                        "내용": "\n".join(contents_text),
                        "url": driver.current_url,
                    }
                print(f"uploading content: {content}")
                with open(local_file_path, "w", encoding="utf-8") as f:
                    f.write("이벤트 정보\n")
                    f.write(f"타이틀: {content['타이틀']}\n")
                    f.write(f"정보: {content['정보']}\n")
                    f.write(f"내용: {content['내용']}\n")
                    f.write(f"url: {content['url']}\n")
                    f.close()
                # print(f"Search index upload results: {results}")
                contents.append(content)

                print(f"Content: {content}")

                
                # image OCM 프로세싱 및 RAG 등록 소스 작성

                driver.back()
                wait_for_page_load(driver)  # 페이지 로딩 대기
            elif page_type == "faq":
                # FAQ 페이지 처리
                faq_page_no = 1

                while True:
                    local_file_path = data_file_dir + "/faq" + f"{index + 1:02d}" + f"{faq_page_no:02d}" + ".txt" 
                    if os.path.exists(local_file_path):
                        print(f"file {local_file_path} already exists.")
                        break
                    item = event_lists[index]
                    
                    script_text = item.find_element(By.TAG_NAME, "a").get_attribute('onclick')
                    driver.execute_script("arguments[0].click();", item.find_element(By.TAG_NAME, "a"))  # Click the link to navigate
                    wait_for_page_load(driver)  # 페이지 로딩 대기

                    faq_list = driver.find_element(By.CLASS_NAME, "accordions").find_elements(By.TAG_NAME, "li")

                    for faq_index in range(len(faq_list)):
                        faq = faq_list[faq_index]
                        faq_type = faq.find_element(By.CLASS_NAME, "linked").text
                        faq_question = faq.find_element(By.CLASS_NAME, "qna").text

                        driver.execute_script("arguments[0].click();", faq.find_element(By.TAG_NAME, "a"))
                        # time.sleep(1)  # Wait for the FAQ to expand
                        time.sleep(2)  # Wait for the FAQ to expand
                        wait_for_page_load(driver)
                        faq = faq_list[faq_index]
                        faq_answer_soup = BeautifulSoup(faq.find_element(By.CLASS_NAME, "faqClass").get_attribute('innerHTML'), 'html.parser')
                        faq_answer = []
                        for answer_text in faq_answer_soup.find_all('p'):
                            faq_answer.append(answer_text.get_text(strip=True))
                        
                        content = {
                            "형태": faq_type,
                            "질문": faq_question,
                            "답변": "\n".join(faq_answer),
                        }
                        contents.append(content)
                    if page_type == "faq":
                        faq_file_data = {
                            "id": base64.urlsafe_b64encode(local_file_path.replace("\n ", "_").replace("/", "_").encode('utf-8')).decode('ascii'),
                            "content": contents,
                            "metadata": {
                                "file_path": local_file_path,
                            }
                        }
                        with open(local_file_path, "w", encoding="utf-8") as f:
                            # f.write(str(faq_file_data))
                            for content in contents:
                                f.write(f"형태: {content['형태']}\n")
                                f.write(f"질문: {content['질문']}\n")
                                f.write(f"답변: {content['답변']}\n\n")

                            f.close()
                    # file_list = [f for f in os.listdir(data_file_dir) if os.path.isfile(os.path.join(data_file_dir, f))]
                    # for file_name in file_list:
                    #     with open(os.path.join(data_file_dir, file_name), "r", encoding="utf-8") as f:
                    #         file_data = f.read()
                    #         blob_client = container_client.upload_blob(name=os.path.join(data_file_dir, file_name), data=file_data, overwrite=True)

                    try:
                        scope_element = driver.find_element(By.CLASS_NAME, "pagination").find_element(By.CLASS_NAME, "scope")
                        if faq_page_no % 10 == 0:
                            try:
                                disabled = scope_element.find_element(By.CLASS_NAME, "next.disabled")
                                print(f"FAQ 페이지 {faq_page_no} 처리 완료.")
                                break
                            except Exception as e:
                                driver.execute_script("arguments[0].click();", scope_element.find_element(By.CLASS_NAME, "next"))
                                wait_for_page_load(driver)
                                faq_page_no += 1
                                continue
                        prev_faq_page_no = faq_page_no
                        for child in scope_element.find_elements(By.TAG_NAME, "a"):
                            if child.text == str(faq_page_no + 1):
                                driver.execute_script("arguments[0].click();", child)
                                wait_for_page_load(driver)
                                faq_page_no += 1
                                break
                        if prev_faq_page_no == faq_page_no:
                            print(f"FAQ 페이지 {faq_page_no} 처리 완료.")
                            break
                        
                    except Exception as e:
                        print(f"FAQ 페이지 {faq_page_no} 처리 완료.")
                        break


        try:
            next_button = driver.find_element(By.CLASS_NAME, "next.disabled")
            print("모든 페이지를 처리했습니다.")
            break
        except Exception as e:
            try:
                next_button = driver.find_element(By.CLASS_NAME, "next")
                next_button.click()
                page_no += 1
                wait_for_page_load(driver)
            except Exception as e:
                print(f"다음 페이지로 이동할 수 없습니다: {e}")
                break

    driver.quit()


if __name__ == '__main__': 
    main()

