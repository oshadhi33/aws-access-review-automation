# --- Imports ---
# Standard and third-party libraries used for AWS, Slack, Google APIs, Excel, and HTTP
import os
import time
import requests
import boto3
import csv
from datetime import datetime
from botocore.exceptions import ClientError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from openpyxl import Workbook

# --- AWS IAM Client ---
iam = boto3.client('iam')

# --- Helper Functions ---

# Extracts roles a user can assume by parsing attached and inline IAM policies
def extract_iam_roles_from_policies(user_name):
    iam_roles = set()

    # Fetch managed policies attached to the user
    try:
        policies = iam.list_attached_user_policies(UserName=user_name)['AttachedPolicies']
        for p in policies:
            policy = iam.get_policy(PolicyArn=p['PolicyArn'])
            version = iam.get_policy_version(
                PolicyArn=p['PolicyArn'],
                VersionId=policy['Policy']['DefaultVersionId']
            )
            doc = version['PolicyVersion']['Document']
            iam_roles.update(find_assumable_roles(doc))
    except ClientError:
        pass  # Skip on permission errors or missing policies

    # Fetch inline policies attached to the user
    try:
        inline_policies = iam.list_user_policies(UserName=user_name)['PolicyNames']
        for policy_name in inline_policies:
            policy_doc = iam.get_user_policy(UserName=user_name, PolicyName=policy_name)['PolicyDocument']
            iam_roles.update(find_assumable_roles(policy_doc))
    except ClientError:
        pass

    return list(iam_roles)

# Parse an IAM policy document for sts:AssumeRole resources
def find_assumable_roles(policy_doc):
    assumable_roles = set()
    statements = policy_doc.get('Statement', [])
    if not isinstance(statements, list):
        statements = [statements]

    for stmt in statements:
        if stmt.get('Effect') != 'Allow':
            continue
        actions = stmt.get('Action', [])
        if isinstance(actions, str):
            actions = [actions]
        if any(action.lower() == 'sts:assumerole' for action in actions):
            resources = stmt.get('Resource', [])
            if isinstance(resources, str):
                resources = [resources]
            assumable_roles.update(resources)

    return assumable_roles

# --- Step 1: Generate IAM Credential Report ---
print("Requesting credential report...")
iam.generate_credential_report()

# Wait until the credential report is available
while True:
    try:
        response = iam.get_credential_report()
        report_csv = response['Content'].decode('utf-8').splitlines()
        print("Credential report is ready.")
        break
    except ClientError as e:
        if e.response['Error']['Code'] in ['ReportNotPresent', 'ReportInProgress']:
            print("Waiting for credential report to be ready...")
            time.sleep(2)
        else:
            raise

# --- Step 2: Parse IAM Users from Report ---
headers = report_csv[0].split(',')
rows = [line.split(',') for line in report_csv[1:]]

users = []

# Extract key information for each IAM user
for row in rows:
    user = dict(zip(headers, row))
    username = user['user']
    mfa_enabled = user['mfa_active'] == 'true'
    last_active = user['password_last_used'] if user['password_last_used'] != 'N/A' else None

    # Get attached policies
    try:
        policies = iam.list_attached_user_policies(UserName=username)['AttachedPolicies']
        policy_names = [p['PolicyName'] for p in policies]
    except ClientError:
        policy_names = []

    # Get assumable roles
    iam_roles = extract_iam_roles_from_policies(username)

    users.append({
        'UserName': username,
        'Arn': user['arn'],
        'MFAEnabled': mfa_enabled,
        'LastActive': last_active or 'N/A',
        'AttachedPolicies': policy_names,
        'IAMRoleAccess': iam_roles
    })

# --- Step 3: Generate Excel Report ---
report_filename = "aws_user_access_review.xlsx"
wb = Workbook()
ws = wb.active
ws.title = "AWS Access Review"
ws.append(["UserName", "ARN", "MFA Enabled", "Last Active", "Permission Policies", "IAM Roles Accessible"])

# Write each user's data into the Excel file
for user in users:
    ws.append([
        user['UserName'],
        user['Arn'],
        "YES" if user['MFAEnabled'] else "NO",
        user['LastActive'],
        ", ".join(user['AttachedPolicies']) if user['AttachedPolicies'] else "None",
        ", ".join(user['IAMRoleAccess']) if user['IAMRoleAccess'] else "None"
    ])

wb.save(report_filename)
print(f"Exported detailed user access report to {report_filename}")

# --- Step 4: Upload Report to Google Drive ---

# Load Google service account credentials
SERVICE_ACCOUNT_FILE = 'credential.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = 'Your google folder ID'  # Replace with your actual folder ID

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Upload Excel file
file_metadata = {
    'name': report_filename,
    'parents': [FOLDER_ID],
    'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
}
media = MediaFileUpload(report_filename, mimetype=file_metadata['mimeType'])

uploaded_file = drive_service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id'
).execute()

file_id = uploaded_file['id']

# Make the file publicly viewable
drive_service.permissions().create(
    fileId=file_id,
    body={"role": "reader", "type": "anyone"},
).execute()

# Generate public link
file_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

# --- Step 5: Lookup Slack Owner (via Google Sheet) ---

def get_owner_for_team(team_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credential.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open("Slack Workflow Owners").sheet1
    records = sheet.get_all_records()

    for row in records:
        if row['Team'].strip().lower() == team_name.strip().lower():
            return {
                'primary_owner': row['Primary Owner'],
                'backup_owner': row['Backup Owner'],
                'slack_id': row['Slack ID']
            }

    raise ValueError(f"No owner found for team: {team_name}")

# --- Step 6: Send Slack Notification with Button ---

# Slack credentials (replace with your actual values)
SLACK_BOT_TOKEN = "Your slack bot ID"
channel_id = "Your channel ID"

client = WebClient(token=SLACK_BOT_TOKEN)

slack_id = get_owner_for_team("AWS")['slack_id']

try:
    response = client.chat_postMessage(
        channel=channel_id,
        text="AWS Access Review report is ready.",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":bell: *AWS Access Review report is ready.*"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📄 Review"
                        },
                        "url": file_link,
                        "action_id": "review_report"
                    }
                ]
            }
        ]
    )
    print("Slack message with buttons sent.")
except SlackApiError as e:
    print(f"Slack API error: {e.response['error']}")
