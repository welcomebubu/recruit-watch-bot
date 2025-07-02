import os
import requests
from bs4 import BeautifulSoup
import time

# ------------ 조건 필터 설정 ------------
# 제목에 꼭 들어가야 하는 모든 필수 키워드를 리스트로 작성합니다.
INCLUDE_KEYWORDS = ['사회복지', '서울', '정규직', '경력']  # 예: 사회복지+서울+정규직 다 들어간 공고만 알려줌

# 회사명에도 조건을 넣고 싶다면 아래를 사용 (예: 복지관)
INCLUDE_COMPANY_KEYWORDS = ['']  # 회사명에 '복지관'이 들어간 경우만

# ------------ 필터 함수 ------------
def job_matches(title, company=''):
    # 제목과 회사명에 각각 조건이 모두 들어간 공고만 True 반환
    return (
        all(k in title for k in INCLUDE_KEYWORDS) and
        all(c in company for c in INCLUDE_COMPANY_KEYWORDS)
    )

# ------------ 텔레그램 함수 ------------
def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': text})

# ------------ 채용사이트별 크롤링 함수 ------------
def get_jobs_jobkorea():
    url = "https://www.jobkorea.co.kr/Search/?stext=사회복지"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    soup = BeautifulSoup(res.text, 'html.parser')
    jobs = []
    for post in soup.select('.list-default .list-post'):
        a_tag = post.select_one('.title a')
        company_tag = post.select_one('.name.dev_view')
        if a_tag and company_tag:
            title = a_tag.text.strip()
            company = company_tag.text.strip()
            link = "https://www.jobkorea.co.kr" + a_tag.get('href', '')
            jobs.append(("[잡코리아] " + title, link, company))
    return jobs

def get_jobs_saramin():
    url = "https://www.saramin.co.kr/zf_user/search?search_done=y&searchType=search&searchword=사회복지"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    soup = BeautifulSoup(res.text, 'html.parser')
    jobs = []
    for job in soup.select('div.item_recruit'):
        a_tag = job.select_one('h2.job_tit > a')
        company_tag = job.select_one('div.area_corp > strong.corp_name > a')
        if a_tag and company_tag:
            title = a_tag.get('title', '').strip()
            company = company_tag.text.strip()
            link = "https://www.saramin.co.kr" + a_tag.get('href', '')
            jobs.append(("[사람인] " + title, link, company))
    return jobs

def get_jobs_incruit():
    url = "https://search.incruit.com/list/search.asp?col=job&kw=사회복지"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    soup = BeautifulSoup(res.text, 'html.parser')
    jobs = []
    for job in soup.select('div.cntList > div.list_info > div.infoCommon'):
        a_tag = job.select_one('span.companyNm > a')
        j_tag = job.select_one('span.accent')
        if a_tag and j_tag:
            title = j_tag.text.strip()
            company = a_tag.text.strip()
            link = a_tag.get('href', '')
            if not link.startswith('http'):
                link = "https://www.incruit.com" + link
            jobs.append(("[인크루트] " + title, link, company))
    return jobs

# ------------ 기타 함수 ------------
def load_history(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    return set()

def save_history(filename, links):
    with open(filename, 'w', encoding='utf-8') as f:
        for link in links:
            f.write(f"{link}\n")

# ------------ 메인 실행 ------------
def main():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    HISTORY_FILE = "history.txt"

    old_links = load_history(HISTORY_FILE)
    jobs = []
    # 사이트별로 공고 가져오기
    try:
        jobs += get_jobs_jobkorea()
    except Exception as e:
        print("Jobkorea error:", e)
    time.sleep(1)
    try:
        jobs += get_jobs_saramin()
    except Exception as e:
        print("Saramin error:", e)
    time.sleep(1)
    try:
        jobs += get_jobs_incruit()
    except Exception as e:
        print("Incruit error:", e)

    # 중복방지
    new_jobs = [(title, link, company) for (title, link, company) in jobs if link not in old_links]
    # 조건에 맞는 공고만 알림 발송
    for title, link, company in new_jobs:
        # job_matches의 두번째 인자에 회사명 전달
        if job_matches(title, company):
            send_telegram(TOKEN, CHAT_ID, f"{title} / {company}\n{link}")

    all_links = old_links.union(link for _, link, _ in jobs)
    save_history(HISTORY_FILE, all_links)

if __name__ == '__main__':
    main()
