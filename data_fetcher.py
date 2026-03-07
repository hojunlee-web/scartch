import datetime
import pytz
from duckduckgo_search import DDGS
from config import PRIORITY_COMPANIES, REPORT_PATH

def search_news(company_name, max_results=5):
    """
    Search recent news for a given company focusing on FDA events.
    """
    query = f"{company_name} FDA OR PDUFA OR AdCom OR CRL OR Approval"
    try:
        results = DDGS().news(keywords=query, max_results=max_results)
        if not results:
            return []
        
        # Convert generator to list
        return list(results)
    except Exception as e:
        print(f"Error fetching news for {company_name}: {e}")
        return []

def classify_events(news_list):
    """
    Basic heuristic to classify news into time buckets.
    In a production app, an LLM would parse these dates accurately.
    For this bot, we will bucket them based on keywords or recency.
    """
    this_week = []
    next_30_days = []
    next_90_days = []
    
    # We will just dump recent news into 'This Week' for now as a placeholder 
    # since extracting exact future PDUFA dates from plain text requires NLP.
    for n in news_list:
        title = n.get('title', '')
        date = n.get('date', 'Unknown Date')[:10]
        
        # Determine event type
        event_type = "Update"
        title_lower = title.lower()
        if "approval" in title_lower:
            event_type = "Approval"
        elif "pdufa" in title_lower:
            event_type = "PDUFA"
        elif "complete response letter" in title_lower or "crl" in title_lower:
            event_type = "CRL"
        elif "advisory committee" in title_lower or "adcom" in title_lower:
            event_type = "AdCom"
        elif "ind" in title_lower:
            event_type = "IND Filing"

        # Simplified to "This Week" since it's recent news.
        this_week.append({
            "date": date,
            "title": title,
            "event_type": event_type,
            "source": n.get("source", "Web")
        })
        
    return this_week, next_30_days, next_90_days

def generate_report():
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.datetime.now(kst)
    date_str = now.strftime("%Y-%m-%d")
    
    report_lines = []
    report_lines.append(f"## FDA 이벤트 캘린더 — {date_str}\n")
    
    all_this_week = []
    all_30 = []
    all_90 = []
    
    company_updates = {}
    
    for company in PRIORITY_COMPANIES:
        news = search_news(company)
        company_updates[company] = news
        
        tw, n30, n90 = classify_events(news)
        
        for item in tw:
            all_this_week.append((company, item))
        for item in n30:
            all_30.append((company, item))
        for item in n90:
            all_90.append((company, item))

    # Compile This Week
    report_lines.append("### 🔴 이번 주 (향후 7일 이내)")
    report_lines.append("| 날짜 | 기업 | 약물명 | 적응증 | 이벤트 유형 | 비고 |")
    report_lines.append("|------|---------|-----------|------------|------------|-------|")
    if not all_this_week:
         report_lines.append("| - | - | - | - | 확인된 단기 이벤트 없음 | - |")
    else:
        for comp, item in all_this_week[:10]: # Limit to avoid massive tables
            title_trunc = item['title'][:50] + "..." if len(item['title']) > 50 else item['title']
            report_lines.append(f"| {item['date']} | {comp} | Unknown | Unknown | {item['event_type']} | {title_trunc} |")
    report_lines.append("\n")

    # Compile 30 Days
    report_lines.append("### 🟡 향후 30일")
    report_lines.append("| 날짜 | 기업 | 약물명 | 적응증 | 이벤트 유형 | 비고 |")
    report_lines.append("|------|---------|-----------|------------|------------|-------|")
    report_lines.append("| - | - | - | - | *향후 30일 이벤트를 예측하려면 구조화된 데이터 또는 언어 모델 분석이 필요합니다.* | - |")
    report_lines.append("\n")

    # Compile 90 Days
    report_lines.append("### 🟢 향후 90일 (주요 이벤트)")
    report_lines.append("| 날짜 | 기업 | 약물명 | 적응증 | 이벤트 유형 | 비고 |")
    report_lines.append("|------|---------|-----------|------------|------------|-------|")
    report_lines.append("| - | - | - | - | *향후 90일 이벤트를 예측하려면 구조화된 데이터 또는 언어 모델 분석이 필요합니다.* | - |")
    report_lines.append("\n")

    # Company specific updates
    report_lines.append("### 📌 Generate Biomedicines 업데이트")
    gen_news = company_updates.get("Generate Biomedicines", [])
    if gen_news:
        for n in gen_news[:3]:
            report_lines.append(f"- {n.get('title', '알 수 없는 뉴스')}")
    else:
        report_lines.append("- 확인된 단기 이벤트 없음.")
    report_lines.append("\n")

    report_lines.append("### 📌 Amgen 업데이트")
    amg_news = company_updates.get("Amgen", [])
    if amg_news:
        for n in amg_news[:3]:
            report_lines.append(f"- {n.get('title', '알 수 없는 뉴스')}")
    else:
        report_lines.append("- 확인된 단기 이벤트 없음.")
    report_lines.append("\n")

    # Market Impact Notes
    report_lines.append("### ⚠️ 시장 영향 참고사항")
    report_lines.append("- 시장 역학에 영향을 미칠 수 있는 삼성바이오에피스(Samsung Bioepis) 바이오시밀러 승인 여부를 주시하세요.")
    report_lines.append("- 리제네론(Regeneron) 파이프라인 이벤트(Dupixent, Eylea 등)는 높은 변동성을 유발할 수 있습니다.")
    
    report_content = "\n".join(report_lines)
    
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    return report_content

if __name__ == "__main__":
    print(generate_report())
