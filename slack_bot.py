import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
import requests
import json

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Netlify API token
API_TOKEN = os.environ['NETLIFY_API_TOKEN']

# The ID of your Netlify site
SITE_NAME = os.environ['NETLIFY_SITE_ID']

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'], '/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

# TESTING - delete later
client.chat_postMessage(channel="#testc", text="ready to go boss")

# Increasing this will slow down response time
maxDeploys = 5

def list_site_deploys():
    headers = {'Authorization': f"Bearer {API_TOKEN}"}
    url = f"https://api.netlify.com/api/v1/sites/{SITE_NAME}/deploys?per_page={maxDeploys}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print("List got!")
        return response.text
    else:
        print(response.status_code)
        return "error"


def lock_netlify_site(deploy_id):
    headers = {'Authorization': f"Bearer {API_TOKEN}"}
    url = f"https://api.netlify.com/api/v1/deploys/{deploy_id}/lock"
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print("Locked!")
        return "locked"
    else:
        print("Site lock error!")
        return "lock-error"

def unlock_netlify_site(deploy_id):
    headers = {'Authorization': f"Bearer {API_TOKEN}"}
    url = f"https://api.netlify.com/api/v1/deploys/{deploy_id}/unlock"
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print("Unlocked!")
        return "unlocked"
    else:
        print("Site unlock error!")
        return "unlock-error"

@app.route('/list-deploys', methods=['GET', 'POST'])
def listDeploys():
    data = request.form
    channel_id = data.get('channel_id')
    numOfDeploys = data.get('text')
    if numOfDeploys == "":
        numOfDeploys = 3
    elif not numOfDeploys.isnumeric():
        client.chat_postMessage(channel=channel_id, text=f":robot_face: ERR: When using the `/list-deploys` command pleaese only follow it with an positve integer (max {maxDeploys}) or nothing at all. :robot_face:")
        return Response(), 200
    else:
        numOfDeploys = int(numOfDeploys)
        if numOfDeploys > maxDeploys:
            numOfDeploys = maxDeploys

    siteList = list_site_deploys()
    if siteList == "error":
        client.chat_postMessage(channel=channel_id, text=":robot_face: Error in list_site_deploys response! :robot_face:")
        return Response(), 200

    response_json = json.loads(siteList)
    message = f":robot_face: *List of {numOfDeploys} most recent deploys to Netlify:* :robot_face:\n\n---\n\n"
    for entry in response_json[:numOfDeploys]:
        deploy_id = entry['id']
        status = entry['state']
        deploy_url = entry['deploy_url']
        time_stamp = entry['created_at']
        message += f"Created: {time_stamp}\nBuild ID: {deploy_id}\nStatus: {status}\nDeploy Preview Link: {deploy_url}\n\n---\n\n"
    client.chat_postMessage(channel=channel_id, text=message)
    return Response(), 200


@app.route('/lock', methods=['POST'])
def lock():
    data = request.form
    channel_id = data.get('channel_id')
    siteList = list_site_deploys()
    if siteList == "error":
        client.chat_postMessage(channel=channel_id, text=":robot_face: Error in list_site_deploys response! :robot_face:")
        return Response(), 200

    response_json = json.loads(siteList)
    deploy_id = 'null'
    for entry in response_json[:maxDeploys]:
        if entry['locked'] == True:
            client.chat_postMessage(channel=channel_id, text=f":robot_face: Site is already locked at Build ID = {entry['id']} :robot_face:")
            return Response(), 200

        if entry['state'] != 'ready':
            continue

        if deploy_id == 'null':
            deploy_id = entry['id']

    message = lock_netlify_site(deploy_id)
    if message == "locked":
        client.chat_postMessage(channel=channel_id, text=":robot_face: Site locked! :robot_face:")
    else:
        client.chat_postMessage(channel=channel_id, text=":robot_face: Not locked - ERROR! :robot_face:")
    return Response(), 200

@app.route('/unlock', methods=['POST'])
def unlock():
    data = request.form
    channel_id = data.get('channel_id')
    siteList = list_site_deploys()
    if siteList == "error":
        client.chat_postMessage(channel=channel_id, text=":robot_face: Error in list_site_deploys response! :robot_face:")
        return Response(), 200

    response_json = json.loads(siteList)
    deploy_id = 'null'
    for entry in response_json[:maxDeploys]:
        if entry['locked'] == True:
            deploy_id = entry['id']
            break

    if deploy_id == 'null':
        client.chat_postMessage(channel=channel_id, text=":robot_face: Site is not currently locked! :robot_face:")
        return Response(), 200

    message = unlock_netlify_site(deploy_id)
    if message == "unlocked":
        client.chat_postMessage(channel=channel_id, text=":robot_face: Site unlocked! :robot_face:")
    else:
        client.chat_postMessage(channel=channel_id, text=":robot_face: Not unlocked - ERROR! :robot_face:")
    return Response(), 200


if __name__ == "__main__":
    app.run(debug=True)