import boto3
import csv
import time
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

iam = boto3.client('iam')

# Start report generation
print("Requesting credential report...")
iam.generate_credential_report()

# Wait for the report to be ready
while True:
    try:
        response = iam.get_credential_report()
        report_csv = response['Content'].decode('utf-8').splitlines()
        print("Credential report is ready.")
        break
    except ClientError as e:
        if e.response['Error']['Code'] == 'ReportNotPresent' or e.response['Error']['Code'] == 'ReportInProgress':
            print("Waiting for credential report to be ready...")
            time.sleep(2)
        else:
            raise

# Parse CSV report
reader = csv.DictReader(report_csv)
inactive_users = []
threshold = datetime.utcnow() - timedelta(days=60)

for row in reader:
    username = row['user']
    last_active = row['password_last_used']
    if last_active == 'N/A' or (last_active and datetime.strptime(last_active, '%Y-%m-%dT%H:%M:%SZ') < threshold):
        inactive_users.append({
            "user": username,
            "last_active": last_active
        })

# Write to CSV
with open('aws_inactive_users.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['user', 'last_active'])
    writer.writeheader()
    writer.writerows(inactive_users)

print(f"✅ Exported {len(inactive_users)} inactive users to aws_inactive_users.csv")
