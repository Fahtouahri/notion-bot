import os
import sys
import logging
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from requete import get_snowflake_connection, execute_query_recommandation

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
SLACK_TOKEN = os.getenv('SLACK_API_TOKEN')
TEST_MODE = False  
TEST_EMAIL = 'test@example.com'  # Anonymized test email
ADMIN = 'admin_username'  # Anonymized admin username
POC_team = 'poc_username'  # Anonymized POC team username

# Verify Slack token
if not SLACK_TOKEN:
    logging.error("SLACK_TOKEN is not set. Please set the SLACK_TOKEN environment variable.")
    sys.exit(1)

client = WebClient(token=SLACK_TOKEN)

def send_to_slack(email, message, link):
    if TEST_MODE:
        email = TEST_EMAIL
    
    try:
        response = client.users_lookupByEmail(email=email)
        if response['ok']:
            user_id = response['user']['id']
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View in Notion"
                            },
                            "url": link
                        }
                    ]
                }
            ]
            response = client.chat_postMessage(channel=user_id, blocks=blocks)
            if response['ok']:
                logging.info(f"Message sent successfully to {email}")
            else:
                logging.error(f"Error sending message to {email}: {response['error']}")
                # Send an error message to the admin
                error_message = f"Error sending message to {email}: {response['error']}"
                send_to_slack(f"{ADMIN}@example.com", error_message, "")
        else:
            logging.error(f"Error finding user: {response['error']} for email {email}")
            # Send an error message to the admin
            error_message = f"Error finding user: {response['error']} for email {email}"
            send_to_slack(f"{ADMIN}@example.com", error_message, "")
    except SlackApiError as e:
        logging.error(f"Error sending message to {email}: {e.response['error']}")
        # Send an error message to the admin
        error_message = f"Error sending message to {email}: {e.response['error']}"
        send_to_slack(f"{ADMIN}@example.com", error_message, "")

def process_recommendation(row):
    logging.info(f"Processing recommendation: {row}")
    reco_link = row.get('RECO')
    owner_reco = row.get('OWNER_RECO')
    creator_reco = row.get('CREATOR_RECO')
    condition = row.get('CONDITION')
    formatted_initial_eta = row.get('FORMATTED_INITIAL_ETA')
    formatted_eta_postponed = row.get('FORMATTED_ETA_POSTPONED')
    
    logging.info(f"Extracted values: owner_reco={owner_reco}, creator_reco={creator_reco}, initial_eta={formatted_initial_eta}, postponed_eta={formatted_eta_postponed}")
    
    if not owner_reco:
        message = f"*Issue 🚨 : No Owner*\nHey @{POC_team}, This card has no owner. Please have a look.\n\nLink = <{reco_link}|{condition}>"
        send_to_slack(f"{POC_team}@example.com", message, reco_link)
        return

    eta_date = datetime.strptime(formatted_eta_postponed or formatted_initial_eta, "%d/%m/%Y").date()
    today = datetime.now().date()
    days_until_eta = (eta_date - today).days

    def send_messages(recipient, is_creator=False):
        if days_until_eta == 10:
            if is_creator:
                message = f"Hey @{recipient.split('@')[0]}\n\n⏳ Your recommendation card is waiting for you! Please do not forget to contact the @{owner_reco.split('@')[0]} of the card to make sure it is currently being implemented."
            else:
                message = f"Hey @{recipient.split('@')[0]}\n\n⏳ Your recommendation card is waiting for you! Please do not forget to contact the Requestor of the card to keep him informed of the progress of the recommendation's implementation and, if necessary, ask him questions to implement it properly."
        elif days_until_eta == 0:
            if is_creator:
                message = f"Hey @{recipient.split('@')[0]}\n\n⚠️ Your recommendation's ETA is coming to an end. Please do not forget to complete it with your rationale for closure, or to postpone the ETA if needed."
            else:
                message = f"Hey @{recipient.split('@')[0]}\n\n⚠️ Your recommendation's ETA is coming to an end. Please do not forget to complete it with your audit trail, or to notify the Requestor that the implementation of your recommendation has to be postponed."
        elif days_until_eta < 0 and abs(days_until_eta) % 2 == 0:
            message = f"Hey @{recipient.split('@')[0]}\n\n🚨 Your recommendation card is late! Please have a look and update it accordingly."
        else:
            return

        message += f"\n\nLink = <{reco_link}|{condition}>"
        send_to_slack(recipient, message, reco_link)

    # Send messages for owner
    if owner_reco:
        send_messages(owner_reco)

    # Send messages for creator if exists
    if creator_reco:
        send_messages(creator_reco, is_creator=True)

def main():
    try:
        conn = get_snowflake_connection()
        results = execute_query_recommandation(conn)
        
        logging.info(f"Total recommendations retrieved: {len(results)}")
        
        for row in results:
            process_recommendation(row)
        
        logging.info(f"Processed all {len(results)} recommendations.")
    
    except Exception as e:
        error_message = f"Error executing query or processing results: {str(e)}"
        logging.error(error_message)
        # Send an error message to the admin
        send_to_slack(f"{ADMIN}@example.com", error_message, "")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
