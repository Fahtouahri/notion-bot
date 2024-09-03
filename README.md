# 📋 Notion Bot Overview

**Notion Bot** is a set of Python scripts designed to automate reminders and notifications for tasks in Notion. These reminders are based on data retrieved from a Snowflake database and are sent via Slack using the Slack API. The bot helps ensure that deadlines are met and that tasks are kept up to date by sending reminders to task creators and reviewers as needed.

## 🗂 Table of Contents
- [Overview](#-notion-bot-overview)
- [Features](#-features)
- [Libraries and Dependencies](#-libraries-and-dependencies)
- [Prerequisites](#-prerequisites)
- [Setup and Installation](#-setup-and-installation)
- [How to Use](#-how-to-use)
  - [Running the Main Script](#-running-the-main-script)
  - [Running the Recommendation Script](#-running-the-recommendation-script)
  - [Running the Requete Script](#-running-the-requete-script)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

## ⭐ Features
- **Automated notifications** for task owners and reviewers on Slack.
- **Reminders based on task deadlines** (lead times), using different conditions such as "On Hold" or "Pending more information."
- **Flexible configuration** using environment variables (e.g., for test mode, Slack tokens, etc.).
- **Automatic handling of overdue tasks**, sending regular reminders until the task is updated.

## 📚 Libraries and Dependencies
The following libraries are used in this project:

- `slack_sdk`: Slack API client used to send messages and reminders to users on Slack.
- `snowflake.connector`: Used to connect to the Snowflake database to retrieve task and recommendation data.
- `os`: For managing environment variables and other system-related tasks.
- `logging`: Used for logging actions, errors, and messages to help monitor the scripts' execution.
- `datetime`: Handles date and time operations for calculating deadlines, overdue tasks, etc.
- `sys`: For system-related functions, like exiting the program in case of errors.

## ⚙️ Prerequisites
Before running the scripts, make sure the following are in place:

- **Python 3.x** installed on your machine.
- A **Snowflake account** with the necessary permissions to query the relevant tables.
- A **Slack workspace** with a bot token. You must create a Slack app and enable permissions to send messages (`chat:write`) and retrieve user information (`users:read`).
- **Environment variables** to store sensitive information like Slack tokens and Snowflake credentials.

### Required Environment Variables

Make sure to set the following environment variables:

```bash
export SLACK_API_TOKEN=your-slack-api-token
export SNOWFLAKE_USER=your-snowflake-username
export SNOWFLAKE_PASSWORD=your-snowflake-password
export SNOWFLAKE_WAREHOUSE=your-snowflake-warehouse
export SNOWFLAKE_ROLE=your-snowflake-role
export SNOWFLAKE_SCHEMA=your-snowflake-schema


🛠️ Setup and Installation
Clone the repository:

bash
Copier le code
git clone https://github.com/yourusername/notion-bot.git
cd notion-bot
Install the required Python libraries:

It is recommended to use a virtual environment to manage dependencies:

bash
Copier le code
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
Configure environment variables:
As mentioned in the Prerequisites section, ensure the required environment variables are set.

🚀 How to Use
Once the setup is complete, you can run the scripts. Make sure to have your environment variables set correctly.

▶️ Running the Main Script
The main.py script is the central piece that processes tasks and recommendations, sending notifications via Slack. To run it:

bash
Copier le code
python main.py
▶️ Running the Recommendation Script
The reco.py script focuses on processing recommendations from Notion, sending reminders for overdue tasks and owner-less cards.

bash
Copier le code
python reco.py
▶️ Running the Requete Script
The requete.py script handles the connection to Snowflake and executes SQL queries to retrieve data from your Notion tasks and recommendations.

bash
Copier le code
python requete.py
🗂 Project Structure
The project is organized as follows:

bash
Copier le code
├── main.py          # Main script to process tasks and send reminders
├── reco.py          # Script to process recommendations
├── requete.py       # Script to connect to Snowflake and execute queries
├── README.md        # This README file
├── requirements.txt # List of dependencies to install
🤝 Contributing
If you'd like to contribute to this project, please submit a pull request or open an issue for discussion. Contributions are welcome!

