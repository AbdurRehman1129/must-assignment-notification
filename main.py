import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_env_var(var_name):
    value = os.environ.get(var_name)
    if not value:
        raise ValueError(f"Missing environment variable: {var_name}")
    return value

# Load credentials from Heroku Config Vars
CMS_URL = "https://cms.must.edu.pk:8082/login.aspx"
ROLL_NO = get_env_var("ROLL_NO")
PASSWORD = get_env_var("PASSWORD")
EMAIL_SENDER = get_env_var("EMAIL_SENDER")
EMAIL_PASSWORD = get_env_var("EMAIL_PASSWORD")
EMAIL_TO = get_env_var("EMAIL_TO")
SESSION = get_env_var("SESSION")
PROGRAM = get_env_var("PROGRAM")

def login_and_get_session():
    session = requests.Session()
    response = session.get(CMS_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract ASP.NET hidden fields
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"] if soup.find("input", {"name": "__VIEWSTATE"}) else ""
    viewstategen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"] if soup.find("input", {"name": "__VIEWSTATEGENERATOR"}) else ""
    eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"] if soup.find("input", {"name": "__EVENTVALIDATION"}) else ""

    data = {
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstategen,
        "__EVENTVALIDATION": eventvalidation,
        "ddl_Session": SESSION,
        "ddl_Program": PROGRAM,
        "txt_RollNo": ROLL_NO,
        "txt_Password": PASSWORD,
        "btn_StudentSignIn": "Sign In"
    }

    response = session.post(CMS_URL, data=data)
    if response.status_code == 200 and "DashBoard.aspx" in response.text:
        print("Login successful.")
        return session
    else:
        print("Login failed.")
        exit()

def check_assignments():
    session = login_and_get_session()  # Always re-login
    assignments_url = "https://cms.must.edu.pk:8082/CoursePortalPendingAssignments.aspx"
    response = session.get(assignments_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        assignments_table = soup.find("table", {"id": "ctl00_DataContent_gvPortalSummary"})
        if assignments_table:
            rows = assignments_table.find_all("tr", class_=["GridItem", "GridAlternatingItem"])
            assignments = []
            for row in rows:
                columns = row.find_all("td")
                course_title = columns[1].text.strip()
                assignment_title = columns[2].text.strip()
                deadline = columns[3].text.strip()
                assignments.append(f"Course: {course_title}, Assignment: {assignment_title}, Deadline: {deadline}")
            send_email(assignments)
        else:
            print("No pending assignments found.")
    else:
        print("Failed to fetch assignments page.")

def send_email(assignments):
    subject = "Pending Assignments Notification"
    body = "\n".join(assignments)
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_TO, msg.as_string())
        print("Email notification sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    check_assignments()