import streamlit as st
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
from openai import OpenAI

# Initialize OpenAI client
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set up Google Calendar API
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
    prompt = f"基于以下事件生成一个温馨提醒: {event['summary']} 在 {event['start'].get('dateTime', event['start'].get('date'))}"
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一个有助于生成友好提醒的AI助手。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def main():
    st.title("Google Calendar Event Viewer")

    # 从 Streamlit secrets 获取日历ID
    calendar_id = st.secrets["GOOGLE_CALENDAR_ID"]

    service = get_calendar_service()

    option = st.selectbox(
        "选择查看范围",
        ("当前行事历 (今天和未来三天)", "当周行事历 (未来七天)", "当月行事历 (未来30天)")
    )

    now = datetime.datetime.utcnow().isoformat() + 'Z'
    if option == "当前行事历 (今天和未来三天)":
        time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=3)).isoformat() + 'Z'
    elif option == "当周行事历 (未来七天)":
        time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'
    else:
        time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat() + 'Z'

    events = get_events(service, calendar_id, now, time_max)

    if not events:
        st.write("没有找到事件。")
    else:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event['summary']
            st.write(f"{start}: {summary}")

            if any(keyword in summary for keyword in ["家人", "生日", "紀念日", "看診"]):
                st.write("特别提醒!")
                reminder = generate_reminder(event)
                st.write(f"AI 提醒: {reminder}")

if __name__ == '__main__':
    main()
