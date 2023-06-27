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

# The name of your Netlify site
SITE_NAME = os.environ['NETLIFY_SITE_ID']


app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'], '/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

client.chat_postMessage(channel="#testc", text="ready to go boss")


def list_site_deploys():
    headers = {'Authorization': f"Bearer {API_TOKEN}"}

    url = f"https://api.netlify.com/api/v1/sites/{SITE_NAME}/deploys"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        #response_json = json.loads(response.text)
        #print(response_json[0]) # get first item

        #for dog in response_json:
        #    if dog['state'] == 'ready':
        #        print(dog['id'])
        print("Yay!")
        return response.text
    else:
        print(response.status_code)
        return "error"


def lock_netlify_site(deploy_id):
    headers = {'Authorization': f"Bearer {API_TOKEN}"}

    url = f"https://api.netlify.com/api/v1/deploys/{deploy_id}/lock"

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        print("Site locked successfully.")
    else:
        print("Locking the site failed.")

@app.route('/list-deploys', methods=['GET', 'POST'])
def listDeploys():
    data = request.form
    channel_id = data.get('channel_id')
    siteList = list_site_deploys()
    if siteList == "error":
        client.chat_postMessage(channel=channel_id, text="Error in list response!")
    else:
        response_json = json.loads(siteList)
        entry1 = siteList[0]
    # entry2 = siteList[1]
    # entry3 = siteList[2]
    # entry4 = siteList[3]
    # entry5 = siteList[4]
    # TEXT = {
    #     'type': 'section',
    #     'text': {
    #         'type': 'mrkdwn',
    #         'text': {
    #             '*List of 5 most recent deploys on Netlify:*\n\n'
    #              f'ID: {entry1['id']}\n'
    #              f'Status: {entry1['state']}\n'
    #              f'Deploy Preview Link: {entry1['deploy_url']}'

    #         }
    #     }
    # }
        client.chat_postMessage(channel=channel_id, text="dog")
    return Response(), 200


@app.route('/lock', methods=['POST'])
def lock():
    client.chat_postMessage(channel="#testc", text="Starting lock!")
    lock_netlify_site()
    client.chat_postMessage(channel="#testc", text="Site locked!")
    return Response(), 200


# @app.route('/unlock', methods=['POST'])
# def unlock():
#     return Response(), 200

# @app.route('/deploys', methods=['POST'])
# def deploys():
#     return Response(), 200

# @app.route('/rollback', methods=['POST'])
# def rollback():
#     return Response(), 200



if __name__ == "__main__":
    app.run(debug=True)