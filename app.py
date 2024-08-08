import streamlit as st
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime

# 设置页面标题
st.set_page_config(page_title="Google Calendar API 测试")

st.title("Google Calendar API 测试应用")

# 测试 GOOGLE_APPLICATION_CREDENTIALS
st.header("1. 测试 Google 应用凭证")
try:
    creds_dict = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"])
    st.success("成功解析 GOOGLE_APPLICATION_CREDENTIALS")
    st.write(f"项目 ID: {creds_dict.get('project_id')}")
    st.write(f"客户端邮箱: {creds_dict.get('client_email')}")
except json.JSONDecodeError:
    st.error("GOOGLE_APPLICATION_CREDENTIALS 不是有效的 JSON")
except KeyError:
    st.error("GOOGLE_APPLICATION_CREDENTIALS 未在 Streamlit Secrets 中设置")

# 测试 GOOGLE_CALENDAR_ID
st.header("2. 测试日历 ID")
calendar_id = st.secrets.get("GOOGLE_CALENDAR_ID")
if calendar_id:
    st.success(f"找到日历 ID: {calendar_id}")
else:
    st.error("GOOGLE_CALENDAR_ID 未在 Streamlit Secrets 中设置")

# 尝试获取日历事件
st.header("3. 尝试获取日历事件")

def get_calendar_service():
    creds = service_account.Credentials.from_service_account_info(
        json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]),
        scopes=['https://www.googleapis.com/auth/calendar.readonly']
    )
    return build('calendar', 'v3', credentials=creds)

try:
    service = get_calendar_service()
    st.success("成功创建日历服务")

    # 获取当前时间和未来7天
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    seven_days_later = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        timeMax=seven_days_later,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        st.info("未来7天没有找到事件。")
    else:
        st.success(f"成功获取事件！找到 {len(events)} 个事件。")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            st.write(f"{start}: {event['summary']}")

except HttpError as error:
    st.error(f"发生错误: {error}")
    st.error("请检查您的日历 ID 和权限设置。")
except Exception as e:
    st.error(f"发生未预期的错误: {e}")

st.header("4. 故障排除提示")
st.markdown("""
如果您遇到问题：
1. 确保 GOOGLE_APPLICATION_CREDENTIALS 包含完整的服务账号 JSON。
2. 验证 GOOGLE_CALENDAR_ID 是正确的。
3. 检查服务账号是否有权限访问指定的日历。
4. 在 Google Cloud Console 中确保 Calendar API 已启用。
""")
