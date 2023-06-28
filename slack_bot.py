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
client.chat_postMessage(channel="#testc", text=":robot_face: ready to go boss :robot_face:")

# Increasing this will slow down response time
# make this an env variable?
maxDeploys = 5

def list_site_deploys():
    headers = {'Authorization': f"Bearer {API_TOKEN}"}
    url = f"https://api.netlify.com/api/v1/sites/{SITE_NAME}/deploys?per_page={maxDeploys}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return response.text
    except requests.exceptions.RequestException as e:
        print("Error in list_site_deploys:", e)
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print("Error parsing API response:", e)
        return None


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

def rollback_netlify_site():
    headers = {'Authorization': f"Bearer {API_TOKEN}"}
    url = f"https://api.netlify.com/api/v1/sites/{SITE_NAME}/rollback"
    response = requests.put(url, headers=headers)
    if response.status_code == 204:
        print("Rolled back!")
        return "roll"
    else:
        print("Site unlock error!")
        return "roll-error"

def set_netlify_live_deploy(deploy_id):
    headers = {'Authorization': f"Bearer {API_TOKEN}"}
    url = f"https://api.netlify.com/api/v1/sites/{SITE_NAME}/deploys/{deploy_id}/restore"

    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print("Restored!")
        return "restored"
    else:
        print("Restore site deploy error!")
        return "restore-error"

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
    if siteList is None:
        client.chat_postMessage(channel=channel_id, text=":robot_face: Error in list_site_deploys response! :robot_face:")
        return Response(), 200

    response_json = json.loads(siteList)
    message = f":robot_face: *List of {numOfDeploys} most recent deploys to Netlify* :robot_face:\n\n---\n\n"
    for entry in response_json[:numOfDeploys]:
        time_stamp = entry['created_at']
        deploy_id = entry['id']
        status = entry['state']
        deploy_url = entry['deploy_url']
        message += f"Created: {time_stamp}\nBuild ID: {deploy_id}\nStatus: `{status}`\nDeploy Preview Link: {deploy_url}\n\n---\n\n"
    client.chat_postMessage(channel=channel_id, text=message)
    return Response(), 200


@app.route('/lock', methods=['POST'])
def lock():
    data = request.form
    channel_id = data.get('channel_id')
    siteList = list_site_deploys()
    if siteList is None:
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
    if siteList is None:
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

@app.route('/rollback', methods=['POST'])
def rollback():
    data = request.form
    channel_id = data.get('channel_id')
    message = rollback_netlify_site()
    if message == "roll":
        client.chat_postMessage(channel=channel_id, text=":robot_face: Site rolled back! :robot_face:")
    else:
        client.chat_postMessage(channel=channel_id, text=":robot_face: Not rolled back - ERROR! :robot_face:")
    return Response(), 200

@app.route('/set-live', methods=['POST'])
def setLive():
    data = request.form
    channel_id = data.get('channel_id')
    deploy_id = data.get('text')

    if deploy_id != "":
        if len(deploy_id) != 24:
            client.chat_postMessage(channel=channel_id, text=":robot_face: Please enter valid deploy ID or don't follow the command with any text; you can see the most recent deploys using the list-deploys command! :robot_face:")
            return Response(), 200

    siteList = list_site_deploys()
    if siteList is None:
        client.chat_postMessage(channel=channel_id, text=":robot_face: Error in list_site_deploys response! :robot_face:")
        return Response(), 200

    response_json = json.loads(siteList)

    # case 1: no deploy ID was passed
    if deploy_id == "":
        for entry in response_json[:maxDeploys]:
            if entry['state'] == 'ready':
                message = set_netlify_live_deploy(entry['id'])
                if message == "restored":
                    client.chat_postMessage(channel=channel_id, text=f":robot_face: Site live deploy set to: {deploy_id}! :robot_face:")
                else:
                    client.chat_postMessage(channel=channel_id, text=":robot_face: Deploy not updated - ERROR! :robot_face:")
                return Response(), 200
        client.chat_postMessage(channel=channel_id, text=f":robot_face: No deploys found in {maxDeploys} most recent deploys which are eligable for publishing, please contact one of the Devs! :robot_face:")
        return Response(), 200

    # case 2: deploy ID was passed
    for entry in response_json[:maxDeploys]:
        if deploy_id == entry['id']:
            if entry['state'] != 'ready':
                client.chat_postMessage(channel=channel_id, text=f":robot_face: Deploy requested currently has the `{entry['state']}` status, deploy must have `ready` status! :robot_face:")
                return Response(), 200

            message = set_netlify_live_deploy(entry['id'])
            if message == "restored":
                client.chat_postMessage(channel=channel_id, text=f":robot_face: Site live deploy set to: {deploy_id}! :robot_face:")
            else:
                client.chat_postMessage(channel=channel_id, text=":robot_face: Deploy not updated - ERROR! :robot_face:")
            return Response(), 200
    client.chat_postMessage(channel=channel_id, text=f":robot_face: Deploy not found, please choose from one of the {maxDeploys} most recent deploys! :robot_face:")
    return Response(), 200

if __name__ == "__main__":
    app.run(debug=True)