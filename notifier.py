import os
import requests
from bs4 import BeautifulSoup
import time

# 텔레그램 알림 함수
def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': text})

# 잡코리아 크롤링 함수
def get_jobs_jobkorea():
    url = "https://www.jobkorea.co.kr/Search/?stext=사회복지"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, 'html.parser')
    jobs = []
    for post in soup.select('.list-default .list-post'):
        a_tag = post.select_one('.title a')
        if a_tag:
            title = a_tag.text.strip()
            link = "https://www.jobkorea.co.kr" + a_tag.get('href', '')
            jobs.append(("[잡코리아] " + title, link))
    return jobs

# 사람인 크롤링 함수
def get_jobs_saramin():
    url = "https://www.saramin.co.kr/zf_user/search?search_done=y&searchType=search&searchword=사회복지"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, 'html.parser')
    jobs = []
    for job in soup.select('div.item_recruit'):
        a_tag = job.select_one('h2.job_tit > a')
        if a_tag:
            title = a_tag.get('title', '').strip()
            link = "https://www.saramin.co.kr" + a_tag.get('href', '')
            jobs.append(("[사람인] " + title, link))
    return jobs

# 인크루트 크롤링 함수
def get_jobs_incruit():
    url = "https://search.incruit.com/list/search.asp?col=job&kw=사회복지"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, 'html.parser')
    jobs = []
    for job in soup.select('div.cntList > div.list_info > div.infoCommon'):
        a_tag = job.select_one('span.companyNm > a')
        j_tag = job.select_one('span.accent')
        if a_tag and j_tag:
            title = j_tag.text.strip()
            link = a_tag.get('href', '')
            # 인크루트는 링크가 절대주소 아니면 보정
            if not link.startswith('http'):
                link = "https://www.incruit.com" + link
            jobs.append(("[인크루트] " + title, link))
    return jobs

# 기타 공통 함수
def load_history(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    return set()

def save_history(filename, links):
    with open(filename, 'w', encoding='utf-8') as f:
        for link in links:
            f.write(f"{link}\n")

def main():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    HISTORY_FILE = "history.txt"

    old_links = load_history(HISTORY_FILE)
    # 모든 사이트 공고 합치기
    jobs = []
    try:
        jobs += get_jobs_jobkorea()
    except Exception as e:
        print("Jobkorea error:", e)
    time.sleep(1)  # 사이트 간 딜레이를 주어 예절 지키기
    try:
        jobs += get_jobs_saramin()
    except Exception as e:
        print("Saramin error:", e)
    time.sleep(1)
    try:
        jobs += get_jobs_incruit()
    except Exception as e:
        print("Incruit error:", e)

    # 중복 방지
    new_jobs = [(title, link) for (title, link) in jobs if link not in old_links]
    for title, link in new_jobs:
        send_telegram(TOKEN, CHAT_ID, f"{title}\n{link}")

    all_links = old_links.union(link for _, link in jobs)
    save_history(HISTORY_FILE, all_links)

if __name__ == '__main__':
    main()
