import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 깨우고 싶은 Streamlit 앱 URL들을 리스트에 모두 등록하세요
APP_URLS = [
    "https://inhazmed-investment.streamlit.app",
    "https://inha-med-equipment.streamlit.app",
    "https://hira-medical-device.streamlit.app",
    "https://labelapp-akn2dgydwrwaxlnpjoesha.streamlit.app",
    "https://inhazmed-search.streamlit.app",
    "https://inhazmed-hdd-backup.streamlit.app",
]

def wake_up_apps():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        for url in APP_URLS:
            try:
                print(f"접속 시도 중: {url}")
                driver.get(url)
                # 각 앱이 완전히 로드되고 소켓이 맺어지도록 5초 대기
                time.sleep(5)
                print(f"성공적으로 활성화됨: {url}")
            except Exception as e:
                print(f"앱 접속 실패 ({url}): {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    wake_up_apps()