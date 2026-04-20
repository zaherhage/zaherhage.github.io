import os
import json
from datetime import datetime, timezone, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ── Auth ──────────────────────────────────────────────────────────────────────
sa_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
calendar_id = os.environ["GOOGLE_CALENDAR_ID"]

creds = service_account.Credentials.from_service_account_info(
    json.loads(sa_json),
    scopes=["https://www.googleapis.com/auth/calendar.readonly"],
)
service = build("calendar", "v3", credentials=creds)

# ── Time range: today in US/Eastern ──────────────────────────────────────────
eastern = timezone(timedelta(hours=-4))  # EDT; adjust to -5 for EST in winter
now_et = datetime.now(eastern)
start_of_day = now_et.replace(hour=0, minute=0, second=0, microsecond=0)
end_of_day   = now_et.replace(hour=23, minute=59, second=59, microsecond=0)

# ── Fetch events ──────────────────────────────────────────────────────────────
result = service.events().list(
    calendarId=calendar_id,
    timeMin=start_of_day.isoformat(),
    timeMax=end_of_day.isoformat(),
    singleEvents=True,
    orderBy="startTime",
    maxResults=20,
).execute()

raw_events = result.get("items", [])

# ── Normalize ─────────────────────────────────────────────────────────────────
events = []
for ev in raw_events:
    start = ev.get("start", {})
    end   = ev.get("end", {})
    events.append({
        "id":       ev.get("id", ""),
        "summary":  ev.get("summary", "Untitled"),
        "location": ev.get("location", ""),
        "start":    start.get("dateTime") or start.get("date", ""),
        "end":      end.get("dateTime")   or end.get("date", ""),
        "allDay":   "dateTime" not in start,
        "color":    ev.get("colorId", ""),
    })

# ── Write output ──────────────────────────────────────────────────────────────
output = {
    "fetched_at": datetime.now(timezone.utc).isoformat(),
    "events": events,
}

with open("data.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Wrote {len(events)} events to data.json")
