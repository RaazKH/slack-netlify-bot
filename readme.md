# Netlify Slack Bot

This is a Slack bot that integrates with Netlify. The bot allows users to perform various actions on Netlify deployments directly from Slack, such as listing recent deploys, locking and unlocking a site, rolling back to a previous deploy, and setting the live deploy.

## Prerequisites

Before running the bot, make sure you have the following set up:

- Python 3.x installed on your machine
- Slack API token: Obtain a Slack API token by creating a new Slack app and going to the `OAuth & Permissions` section, make sure it has the `chat:write` Bot Token Scope
- Slack signing secret: Can be found under "App Credentials" on the "Basic Information" tab in the Slack app web settings
- Netlify Site ID: Check the site settings on netlify to find the ID for the site you want to control with this bot
- Netlify API token: Generate a Netlify API token from the Netlify account settings

## Installation

1. Clone the repository to your local machine
2. Navigate to the project directory
3. Create a virtual environment (optional but recommended)
4. Install the required Python packages by running the following command:
```
pip install -r requirements.txt
```
5. Create a `.env` file in the project directory and add the following environment variables:
```
NETLIFY_API_TOKEN=<Netlify API token>
NETLIFY_SITE_ID=<Netlify site ID>
SLACK_TOKEN=<Slack API token>
SIGNING_SECRET=<Slack signing secret>
```
6. Replace `<Netlify API token>` with your Netlify API token
7. Replace `<Netlify site ID>` with the ID of your Netlify site
8. Replace `<Slack API token>` with your Slack API token
9. Replace `<Slack signing secret>` with your Slack signing secret

## Available Commands

The bot supports the following commands:

- `/list-deploys [numOfDeploys]`: Lists the most recent Netlify deploys. `numOfDeploys` is an optional parameter to specify the number of deploys to retrieve (default is 3).
- `/lock`: Locks the Netlify site to prevent further deploys.
- `/unlock`: Unlocks the Netlify site to allow deploys.
- `/rollback`: Rolls back the Netlify site to the previous deploy.
- `/set-live [deployID]`: Sets the live deploy for the Netlify site. `deployID` is an optional parameter to specify a specific deploy ID. If not provided, the bot will choose the most recent deploy with a "ready" status.

## Usage

1. Start the bot by running `python3 slack_bot.py`
2. Use a localhost to web forwarding tool such as `Pinggy.io`, `ngrok`, `Localtunnel`, or `localhost.run`
3. Configure all the `Slash Commands` in the Slack app settings to point to the web endpoint with each command endpoint followed by the command itself. So `/lock` command endpoint would be `https://some-endpoint.com/lock`
4. Install the bot to your Slack workspace
5. Add the bot to a channel and start messaging!

## Contributing

Contributions to the project are welcome. If you find any issues or want to add new features, feel free to open a pull request.

## HELP!

If you need help setting this up you can follow [this playlist](https://www.youtube.com/playlist?list=PLzMcBGfZo4-kqyzTzJWCV6lyK-ZMYECDc).