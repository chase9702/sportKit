from fastapi import FastAPI, HTTPException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI()

SEOUL_API_URL = ("http://openAPI.seoul.go.kr:8088/674d4f586c73656433396f77544170/json/ListPublicReservationSport/1/100"
                 "/테니스장")
MAIN_URL = "https://yeyak.seoul.go.kr/web/main.do"

CHROME_DRIVER_PATH = "/Users/imsehwan/Downloads/chromedriver-mac-arm64/chromedriver"


@app.get("/scrape-tennis-info")
async def scrape_tennis_info():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = ChromeService(executable_path=CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(MAIN_URL)

        select_T100 = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "select_T100"))
        )
        for option in select_T100.find_elements(By.TAG_NAME, 'option'):
            if option.text == "테니스장":
                option.click()
                break

        select_svc_T100 = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "svc_T100"))
        )

        WebDriverWait(driver, 10).until_not(
            EC.text_to_be_present_in_element_value((By.NAME, "svc_T100"), "조회중")
        )

        WebDriverWait(driver, 30).until(
            lambda driver: "조회중" not in select_svc_T100.get_attribute('innerHTML')
        )

        # 모든 옵션 요소를 가져와서 HTML 형식으로 반환
        options_html = select_svc_T100.get_attribute('outerHTML')

        # WebDriver 종료
        driver.quit()

        return {"html": options_html}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fetch-sports-data")
async def fetch_sports_data():
    response = requests.get(SEOUL_API_URL)

    if response.status_code == 200:
        data = response.json()
        rows = data.get('ListPublicReservationSport', {}).get('row', [])

        filtered_data = [
            {
                "GUBUN": item.get("GUBUN", "N/A"),
                "SVCID": item.get("SVCID", "N/A"),
                "MAXCLASSNM": item.get("MAXCLASSNM", "N/A"),
                "MINCLASSNM": item.get("MINCLASSNM", "N/A"),
                "SVCSTATNM": item.get("SVCSTATNM", "N/A"),
                "SVCNM": item.get("SVCNM", "N/A"),
                "SVCURL": item.get("SVCURL", "N/A"),
            }
            for item in rows
        ]

        return filtered_data
    else:
        raise HTTPException(status_code=400, detail="Failed to fetch data from the API")
