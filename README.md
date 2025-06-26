# AWS IAM User Access Review Automation

This project automates the generation, analysis, and distribution of an **AWS IAM User Access Review Report**. It identifies inactive users, exports results to a report file, and optionally integrates with **Slack** and **Google Drive** for distribution.

---

## Features

- Automatically generates the **AWS IAM credential report**
- Identifies inactive IAM users based on last activity (>60 days)
- Outputs a clean CSV report of inactive users
- Ready to integrate with:
  - Google Drive for report uploads
  - Slack for sending review alerts with action buttons
- Easy to customize and extend for multi-cloud reviews

---

## Technologies Used

- Python 3
- AWS SDK (boto3)
- Slack SDK
- Google API Python client
- `openpyxl` for Excel report creation
- `csv` module for parsing and exporting

---

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```
Contents of requirements.txt:
- boto3
- slack_sdk
- gspread
- google-api-python-client
- oauth2client
- openpyxl
- requests

---

## Configuration

| Component         | Key / Setup                              | Description                                                                                                      |
| ----------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **AWS IAM**       | IAM user with programmatic access        | Required IAM permissions: `iam:GenerateCredentialReport`, `iam:GetCredentialReport`, `iam:ListUsers`, `iam:Get*` |
| **Google Drive**  | `credential.json`                        | Service account key file for Drive API access                                                                    |
| **Slack**         | `SLACK_BOT_TOKEN`, `channel_id`          | Send report notifications via Slack                                                                              |
| **Google Sheets** | (Optional) `Slack Workflow Owners` Sheet | For mapping report ownership to Slack users                                                                      |


---

## Report Format

Example output (aws_inactive_users.csv):

| user  | last\_active         |
| ----- | -------------------- |
| alice | 2024-02-01T12:45:00Z |
| bob   | N/A                  |

Users with no login in the last 60 days are flagged.

---

## Usage

To run the report generation:
```bash
python aws_access_review.py
```
If integrated with the full pipeline, the script will:

    1. Generate the IAM credential report
    
    2. Parse users and last active dates
    
    3. Export inactive users to CSV
    
    4. (Optional) Upload to Google Drive
    
    5. (Optional) Send a Slack message with a review button

---

## Project Structure

    aws-access-review/
    ├── aws_access_review.py        # Main logic script
    ├── credential.json             # Google service account key (not committed)
    ├── aws_inactive_users.csv      # Output report
    ├── requirements.txt            # Python dependencies
    └── README.md

---

## Ownership Lookup

To assign review responsibility, a Google Sheet can be used with:

| Team   | Primary Owner | Backup Owner | Slack ID  |
| ------ | ------------- | ------------ | --------- |
| DevOps | Alice         | Bob          | U12345678 |

Used for routing Slack alerts to the correct reviewers.

---

## Slack Notification

Slack message includes a report summary and a button to open the Drive file:

    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": ":bell: *AWS Access Review report is ready.*"
      },
      "accessory": {
        "type": "button",
        "text": {
          "type": "plain_text",
          "text": "View Report"
        },
        "url": "https://drive.google.com/..."
      }
    }

---

## Sample CLI Output

    Requesting credential report... 
    Waiting for credential report to be ready...
    Credential report is ready.
    ✅ Exported 6 inactive users to aws_inactive_users.csv

---

## Troubleshooting

| Issue                     | Solution                                    |
| ------------------------- | ------------------------------------------- |
| `ReportNotPresent`        | Wait and retry, report is still generating  |
| `SlackApiError`           | Check token and channel permissions         |
| Google Drive upload fails | Check folder ID and service account sharing |
| Sheet not found           | Ensure correct spreadsheet and tab name     |


---

## License

This project is provided for educational and internal security use. Customize and adapt it to your organization’s compliance and review processes.


---


## Contact

For any questions, feel free to reach me via my GitHub profile.
    
