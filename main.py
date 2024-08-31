import os
import sys
import logging
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from requete import get_snowflake_connection, execute_query

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
SLACK_TOKEN = os.getenv('SLACK_API_TOKEN')
TEST_MODE = False
TEST_EMAIL = 'test@example.com'  # Anonymized test email
ADMIN = 'admin_username'  # Anonymized admin username
POC_REGULATORY = 'poc_username'  # Anonymized POC username

# Verify Slack token
if not SLACK_TOKEN:
    logging.error("SLACK_TOKEN is not set. Please set the SLACK_TOKEN environment variable.")
    sys.exit(1)

client = WebClient(token=SLACK_TOKEN)

# Store cards with LEAD_TIME >= 12
cards_over_12_days = {}

def send_to_slack(email, message, link):
    if TEST_MODE:
        email = TEST_EMAIL
    try:
        response = client.users_lookupByEmail(email=email)
        if response['ok']:
            user_id = response['user']['id']
            blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": message}},
                {"type": "actions", "elements": [{"type": "button", "text": {"type": "plain_text", "text": "View in Notion"}, "url": link}]}
            ]
            response = client.chat_postMessage(channel=user_id, blocks=blocks)
            if response['ok']:
                logging.info(f"Message sent successfully to {email}")
            else:
                logging.error(f"Error sending message to {email}: {response['error']}")
                send_to_slack(f"{ADMIN}@example.com", f"Error sending message to {email}: {response['error']}", "")
        else:
            logging.error(f"Error finding user: {response['error']} for email {email}")
            send_to_slack(f"{ADMIN}@example.com", f"Error finding user: {response['error']} for email {email}", "")
    except SlackApiError as e:
        logging.error(f"Error sending message to {email}: {e.response['error']}")
        send_to_slack(f"{ADMIN}@example.com", f"Error sending message to {email}: {e.response['error']}", "")

def get_recipients(row):
    if TEST_MODE:
        return [TEST_EMAIL]
    return [row.get('MAIL')] if row.get('MAIL') else [f"{POC_REGULATORY}@example.com"]

def notify_reviewers(row, message, link):
    logging.info(f"Checking reviewers for card: {row.get('REQUEST')}")
    
    lead_time = row.get('LEAD_TIME')
    if lead_time == 4:
        message = "⏳ This request is under review. Could you please double-check to make sure everything looks good?"
    elif lead_time == 8:
        message = "⏳ Just a heads-up, the deadline for this request is coming up soon. Let's make sure we get it done on time!"
    elif lead_time == 10 or (lead_time >= 12 and lead_time % 2 == 0):
        message = "🚨 Oops! The deadline for this request has passed. Please respond as soon as you can. Thanks!"
    
    validations = [
        ('REGULATORY_FINAL_VALIDATION', 'REGULATORY_REVIEWER_EMAIL'),
        ('FC_FINAL_VALIDATION', 'FINANCIAL_CRIME_REVIEWER_EMAIL'),
        ('SECURITY_FINAL_VALIDATION', 'SECURITY_REVIEWER_EMAIL'),
        ('FINANCE_FINAL_VALIDATION', 'FINANCE_REVIEWER_EMAIL'),
        ('LEGAL_FINAL_VALIDATION', 'LEGAL_REVIEWER_EMAIL'),
        ('RISK_FINAL_VALIDATION', 'RISK_REVIEWER_EMAIL'),
        ('IC_FINAL_VALIDATION', 'INTERNAL_CONTROL_REVIEWER_EMAIL')
    ]

    for validation, email_field in validations:
        if row.get(validation) is None or row.get(validation) == '':
            reviewer_email = row.get(email_field)
            if reviewer_email:
                reviewer_slack = reviewer_email.split('@')[0]
                reviewer_message = f"*Reviewer Reminder:* Hey @{reviewer_slack},\n\n{message}\nThanks 😉.\n\n<{link}|{row.get('REQUEST')}>"
                logging.info(f"Sending reminder to {reviewer_email} for {validation} with message: Reviewer Reminder: {message}")
                send_to_slack(reviewer_email, reviewer_message, link)
            else:
                logging.info(f"No email found for {email_field}")
        else:
            logging.info(f"{validation} is not empty, no reminder sent")

def process_row(row):
    lead_time = row.get('LEAD_TIME')
    status = row.get('STATUS')
    link = row.get('LINK')
    sla_put_on_hold_on = row.get('SLA_PUT_ON_HOLD_ON')
    request_name = row.get('REQUEST')
    creator_email = row.get('MAIL')
    
    creator_slack = creator_email.split('@')[0] if creator_email else None
    
    logging.info(f"Processing row: LEAD_TIME={lead_time}, STATUS={status}, REQUEST={request_name}")
    
    if status == '💪 Reviewers on it':
        should_send = False
        
        if lead_time == 4:
            message = "⏳ This request is under review. Could you please double-check to make sure everything looks good?"
            should_send = True
        elif lead_time == 8:
            message = "⏳ Just a heads-up, the deadline for this request is coming up soon. Let's make sure we get it done on time!"
            should_send = True
        elif lead_time == 10:
            message = "🚨 Oops! The deadline for this request has passed. Please respond as soon as you can. Thanks!"
            should_send = True
        elif lead_time >= 12 and lead_time % 2 == 0:
            message = "🚨 Oops! The deadline for this request has passed. Please respond as soon as you can. Thanks!"
            should_send = True
        
        if should_send:
            if creator_slack:
                formatted_message = f"Hey @{creator_slack}\n\n{message}\n\n<{link}|{request_name}>"
                recipients = get_recipients(row)
            else:
                formatted_message = f"Hey @{POC_REGULATORY}\n\n*Issue : {status}*\nThis card doesn't have a creator - Please take care of it\n\n{message}\n\n<{link}|{request_name}>"
                recipients = [f"{POC_REGULATORY}@example.com"]
            
            logging.info(f"Sending message for LEAD_TIME={lead_time}")
            for recipient in recipients:
                send_to_slack(recipient, formatted_message, link)
            
            notify_reviewers(row, message, link)
            
            if lead_time >= 12 and lead_time % 2 == 0:
                cards_over_12_days[row.get('ID')] = (datetime.now(), creator_email)
        else:
            logging.info(f"No action needed for LEAD_TIME={lead_time} in '💪 Reviewers on it' status")
    
    elif status == '😴 On Hold':
        if sla_put_on_hold_on:
            if isinstance(sla_put_on_hold_on, str):
                sla_date = datetime.strptime(sla_put_on_hold_on, "%Y-%m-%d").date()
            elif isinstance(sla_put_on_hold_on, datetime):
                sla_date = sla_put_on_hold_on.date()
            else:
                sla_date = sla_put_on_hold_on
            
            days_since_sla = (datetime.now().date() - sla_date).days
            if days_since_sla % 30 == 0 and days_since_sla > 0:
                if not creator_slack:
                    message = f"Hey @{POC_REGULATORY}\n\n*Issue : {status}*\n⚠️ Error: This card doesn't have a creator - Please take care of it\n\n😴 This request is on hold for now. Could you please provide an update?"
                    recipient = f"{POC_REGULATORY}@example.com"
                else:
                    message = f"Hey @{creator_slack}\n\n😴 This request is on hold for now. Could you please provide an update?"
                    recipient = creator_email
                
                formatted_message = f"{message}\n\n<{link}|{request_name}>"
                
                logging.info(f"Sending message for SLA = {days_since_sla} days")
                send_to_slack(recipient, formatted_message, link)
                notify_reviewers(row, message, link)
            else:
                logging.info(f"No action needed for 'On Hold' status, SLA = {days_since_sla} days (not a multiple of 30)")
        else:
            message = f"Hey @{POC_REGULATORY}\n\n*Issue : {status}*\n⚠️ Error: This card has no SLA - Please take care of it\n\n😴 This request is on hold for now. Could you please provide an update?"
            formatted_message = f"{message}\n\n<{link}|{request_name}>"
            logging.info("SLA_PUT_ON_HOLD_ON is null, sending message to POC Regulatory")
            send_to_slack(f"{POC_REGULATORY}@example.com", formatted_message, link)
            notify_reviewers(row, message, link)

        # Additional check for SLA presence but missing creator email
        if sla_put_on_hold_on and not creator_email:
            message = f"Hey @{POC_REGULATORY}\n\n*Issue : {status}*\n⚠️ Error: This card has a SLA but no creator - Please take care of it\n\n😴 This request is on hold for now. Could you please provide an update?"
            formatted_message = f"{message}\n\n<{link}|{request_name}>"
            logging.info("SLA exists but creator is missing, sending message to POC Regulatory")
            send_to_slack(f"{POC_REGULATORY}@example.com", formatted_message, link)
            notify_reviewers(row, message, link)
    
    elif status == '⏳ Pending more information':
        message = "👀 This request needs a bit more information to be processed. Could you please take a look and make sure everything looks good?"
        
        if sla_put_on_hold_on:
            if isinstance(sla_put_on_hold_on, str):
                sla_date = datetime.strptime(sla_put_on_hold_on, "%Y-%m-%d").date()
            elif isinstance(sla_put_on_hold_on, datetime):
                sla_date = sla_put_on_hold_on.date()
            else:
                sla_date = sla_put_on_hold_on
            
            days_since_sla = (datetime.now().date() - sla_date).days
            
            if days_since_sla >= 5 and (days_since_sla - 5) % 5 == 0:
                if creator_slack:
                    formatted_message = f"Hey @{creator_slack}\n\n{message}\n\n<{link}|{request_name}>"
                    recipient = creator_email
                else:
                    formatted_message = f"Hey @{POC_REGULATORY}\n\n*Issue : {status}*\nThis card doesn't have creator - Please take care of it\n\n{message}\n\n<{link}|{request_name}>"
                    recipient = f"{POC_REGULATORY}@example.com"
                
                logging.info(f"Sending message for Pending Information (Days since SLA: {days_since_sla})")
                send_to_slack(recipient, formatted_message, link)
                notify_reviewers(row, message, link)
            else:
                logging.info(f"No action needed for 'Pending more information', Days since SLA: {days_since_sla}")
        else:
            logging.info("SLA_PUT_ON_HOLD_ON is null, sending message to POC Regulatory")
            formatted_message = f"Hey @{POC_REGULATORY}\n\n*Issue : {status}*\n⚠️ This card has no SLA - Please Take Care of It\n\n{message}\n\n<{link}|{request_name}>"
            send_to_slack(f"{POC_REGULATORY}@example.com", formatted_message, link)
            notify_reviewers(row, message, link)
    
    else:
        logging.info(f"No action needed for STATUS={status}")

def check_overdue_cards():
    current_time = datetime.now()
    for card_id, card_info in list(cards_over_12_days.items()):
        last_sent, creator_email = card_info
        if current_time - last_sent >= timedelta(days=2):
            if creator_email:
                creator_slack = creator_email.split('@')[0]
                message = f"Hey @{creator_slack}\n\n🚨 Reminder: Your card {card_id} is still overdue. Please respond as soon as you can. Thanks!"
                send_to_slack(creator_email, message, "")
                cards_over_12_days[card_id] = (current_time, creator_email)
            else:
                message = f"Hey @{POC_REGULATORY}\n\n🚨 Reminder: Card {card_id} is still overdue and has no creator. Please check and take necessary action. Thanks!"
                send_to_slack(f"{POC_REGULATORY}@example.com", message, "")
            logging.info(f"Sent overdue reminder for card {card_id}")

def main():
    try:
        conn = get_snowflake_connection()
        results = execute_query(conn)
        
        logging.info(f"Total rows retrieved: {len(results)}")
        
        for row in results:
            process_row(row)
        
        check_overdue_cards()
        
        logging.info(f"Processed all {len(results)} rows.")
    
    except Exception as e:
        error_message = f"Error executing query or processing results: {str(e)}"
        logging.error(error_message)
        send_to_slack(f"{ADMIN}@example.com", error_message, "")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
