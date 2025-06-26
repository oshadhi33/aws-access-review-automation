# AWS IAM User Access Review Report Automation

This project automates the generation, analysis, and distribution of an **AWS IAM User Access Review Report**. The script gathers IAM user data, creates a detailed Excel report, uploads it to Google Drive, and notifies stakeholders on Slack with a convenient button to review the report.

---

## Features

- Generates AWS IAM credential report.
- Extracts user details including MFA status, last active time, attached and inline IAM policies, and assumable IAM roles.
- Creates an Excel report summarizing user access.
- Uploads the report to a specified Google Drive folder.
- Sends a Slack notification with a button linking to the report.
- Dynamically assigns report owners based on a Google Sheet.

---

## Requirements

### Python Packages

Install dependencies with:

```bash
pip install -r requirements.txt
```

Contents of requirements.txt:

    boto3
    slack_sdk
    gspread
    google-api-python-client
    oauth2client
    openpyxl
    requests

Or individually:

    pip install slack_sdk gspread google-api-python-client oauth2client boto3 openpyxl requests

### Credentials and Access

-  AWS IAM: Permissions to generate and read IAM credential reports, list user policies, and access role information.
-  Google API: A service account JSON key (credential.json) with access to:
-  Google Drive folder for uploading reports.
-  Google Sheets containing team owner information.
-  Slack: A Slack Bot Token with permissions to post messages to the target channel.

---

## Configuration

| Configuration Item | Description                                 | Where to Set                               |
| ------------------ | ------------------------------------------- | ------------------------------------------ |
| `credential.json`  | Google service account key file             | Root of the project                        |
| `FOLDER_ID`        | Google Drive folder ID to upload the report | Inside script (`FOLDER_ID` variable)       |
| Slack Bot Token    | Slack bot OAuth token to send messages      | Inside script (`SLACK_BOT_TOKEN` variable) |
| Slack Channel ID   | Channel ID to post the Slack notification   | Inside script (`channel_id` variable)      |


---

## Repository Structure

    aws-access-review/
    ├── credential.json          # Google service account credentials
    ├── aws_access_review.py     # Main Python script
    ├── requirements.txt         # Python dependencies
    └── aws_user_access_review.xlsx (generated report)

---

## How to Run

1. Place your Google service account JSON file as credential.json in the repo root.
2. Update the script variables for Google Drive folder ID, Slack bot token, and Slack channel ID.
3. Install Python dependencies.
4. Run the script:
```bash
python aws_access_review.py
```
The script will generate the IAM access report, upload it to Google Drive, and send a Slack notification with a review button.

---

## Google Sheets Owner Lookup

- The script looks up report owners dynamically in a Google Sheet titled Slack Workflow Owners.
- Sheet must include columns: Team, Primary Owner, Backup Owner, Slack ID.
- This enables assigning notification ownership dynamically based on teams.

---

## Troubleshooting

| Issue                       | Solution / Checkpoints                                   |
| --------------------------- | -------------------------------------------------------- |
| Credential report not ready | Wait a few seconds, script retries automatically         |
| Slack API errors            | Validate bot token, channel permissions                  |
| Google Drive upload failure | Verify service account permissions and correct folder ID |
| Owner lookup failure        | Confirm Google Sheet title and columns are accurate      |


---

## Future Improvements

- Add scheduled automation via AWS Lambda or GitHub Actions.
- Extend support for GCP and Azure IAM role audits.
- Add detailed logging and error alerts.


---


## License

This project is provided as-is for personal and professional use.

---

## Contact

Feel free to reach out via GitHub for questions or suggestions.












