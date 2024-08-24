import streamlit as st
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
from openai import OpenAI
import pandas as pd

# 初始化 OpenAI 客戶端
openai_client = OpenAI(
    base_url = "https://integrate.api.nvidia.com/v1",
    api_key=st.secrets["OPENAI_API_KEY"]
)

# 設置 Google 日曆 API
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

@st.cache_resource
def get_calendar_service():
    creds_dict = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"])
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)

def get_events(service, calendar_id, time_min, time_max):
    events_result = service.events().list(calendarId=calendar_id, timeMin=time_min,
                                          timeMax=time_max, singleEvents=True,
                                          orderBy='startTime').execute()
    return events_result.get('items', [])

def generate_reminder(event):
    prompt = f"基於以下事件生成一個溫馨提醒: {event['summary']} 在 {event['start'].get('dateTime', event['start'].get('date'))}"
    response = openai_client.chat.completions.create(
        model="yentinglin/llama-3-taiwan-70b-instruct",
        messages=[
            {"role": "system", "content": "你是一個有助於生成友善提醒的AI助手。"},
            {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def format_event_time(event):
    start = event['start'].get('dateTime', event['start'].get('date'))
    end = event['end'].get('dateTime', event['end'].get('date'))
    if 'T' in start:  # 這是一個日期時間
        start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
        return f"{start_dt.strftime('%Y-%m-%d %H:%M')} 至 {end_dt.strftime('%H:%M')}"
    else:  # 這是一個全天事件
        return f"{start} (全天)"

def main():
    #st.title("Google 日曆事件檢視器(Calendar Viewer)")


    # 使用 markdown 來創建置中的兩行標題
    st.markdown("""
    <h1 style="text-align: center;">日曆事件檢視器</h1>
    <h2 style="text-align: center;">(Calendar Viewer)</h2>
    """, unsafe_allow_html=True)

    # 添加一些間距
    st.markdown("<br>", unsafe_allow_html=True)

    
    # 從 Streamlit secrets 獲取日曆ID
    calendar_id = st.secrets["GOOGLE_CALENDAR_ID"]
    service = get_calendar_service()
    
    option = st.selectbox(
        "選擇查看範圍",
        ("當前行事曆 (Current-3 Days)", "當週行事曆 (Week-Future 7 Days)", "當月行事曆 (Month-Future 30 Days)")
    )
    
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    if option == "當前行事曆 (Current-3 Days)":
        time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=3)).isoformat() + 'Z'
    elif option == "當週行事曆 (Week-Future 7 Days)":
        time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'
    else:
        time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat() + 'Z'
    
    events = get_events(service, calendar_id, now, time_max)
    
    if not events:
        st.write("沒有找到事件(No events)。")
    else:
        for event in events:
            event_time = format_event_time(event)
            summary = event['summary']
            description = event.get('description', '無描述(no descrition)')
            location = event.get('location', '無地點(no locaiton)')
            
            # 使用 Streamlit 的列來創建表格式的布局
            col1, col2, col3, col4 = st.columns([2, 3, 3, 2])
            with col1:
                st.write(f"**時間(Time):**\n{event_time}")
            with col2:
                st.write(f"**摘要(Summary):**\n{summary}")
            with col3:
                st.write(f"**描述(Descrition):**\n{description}")
            with col4:
                st.write(f"**地點(Location):**\n{location}")
            
            if any(keyword in summary for keyword in ["家人", "生日", "紀念日", "預約回診"]):
                reminder = generate_reminder(event)
                # 使用 st.info 來以不同的顏色顯示 AI 提醒
                st.info(f"**AI 提醒(Reminder):** {reminder}")
            
            st.write("---")  # 添加分隔線

if __name__ == '__main__':
    main()
