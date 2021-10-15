import json
import os
from flask import Flask, Response, request
from twilio import twiml
from twilio.rest import Client
from twilio.rest.taskrouter.v1.workspace.activity import ActivityInstance
from twilio.rest.taskrouter.v1.workspace.worker import WorkerInstance
from werkzeug.datastructures import auth_property


ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
SUPPORT_DESK_NUMBER = os.environ.get('SUPPORT_DESK_NUMBER', '')
WORKSPACE_SID = os.environ.get('WORKSPACE_SID', '')
WORKFLOW_SID = os.environ.get('WORKFLOW_SID', '')


XML_CONTENT_TYPE = 'application/xml'
JSON_CONTENT_TYPE = 'application/json'

client = Client(account_sid=ACCOUNT_SID, password=AUTH_TOKEN, region='us2')
app = Flask(__name__)


@app.route('/')
def working():
    return "Service desk up and running!"

@app.route('/call', methods=['GET', 'POST'])
def call():
    r = twiml.Response()
    r.enqueue('', workflowSid=WORKFLOW_SID)
    return Response(str(r), content_type=XML_CONTENT_TYPE)


@app.route('/assign', methods=['POST'])
def assign():
    task_attrs = json.loads(request.form['TaskAttributes'])
    if 'training' in task_attrs and task_attrs['training'] == 'sms':
        number = json.loads(request.form['WorkerAttributes'])['phone_number']
        instruction = {"instruction": "accept"}
        client.messages.create(from_=SUPPORT_DESK_NUMBER, to=number,
            body='Text {0} asking "{1}"'.format(task_attrs['phone_number'],
                                                task_attrs['body']))
        return Response(json.dumps(instruction),
                        content_type=JSON_CONTENT_TYPE)
    # defaults to voice call
    number = json.loads(request.form['WorkerAttributes'])['phone_number']
    instruction = {
        "instruction": "dequeue",
        "to": number,
        "from": SUPPORT_DESK_NUMBER
    }
    return Response(json.dumps(instruction), content_type=JSON_CONTENT_TYPE)


@app.route('/message', methods=['POST'])
def message():
    # check if one of our workers is completing a task
    if request.form['Body'] == 'DONE':
        from_number = request.form['From']
        # Get workers from the workspace
        workers = client.taskrouter.workspaces(WORKSPACE_SID).workers.list()
        w:WorkerInstance
        for w in workers:
            if from_number == json.loads(w.attributes)['phone_number']:
                # Get activities in the task router
                activities = client.taskrouter.workspaces(WORKSPACE_SID).activities.list()
                activity:ActivityInstance
                # update worker status back to idle
                for activity in activities:
                    if activity.friendly_name == 'Idle':
                        w.update(activity_sid=activity.sid)
                        break
                r = twiml.Response()
                r.message("Ticket closed.")
                return Response(str(r), content_type=XML_CONTENT_TYPE)

    task_attributes = {
        "training" : "sms",
        "phone_number" : request.form['From'],
        "body": request.form['Body']
    }
    # Create tasks
    tasks = client.taskrouter.workspaces(WORKSPACE_SID).tasks.create(
        workflowSid=WORKFLOW_SID, taskChannel='voice', attributes=task_attributes)
        
    # Print the tasks in an easy to read format
    print(json.dumps(tasks.__dict__, indent=2))

    r = twiml.Response()
    r.message("Thanks. You'll hear back from us soon.")
    return Response(str(r), content_type=XML_CONTENT_TYPE)


if __name__ == '__main__':
    # first attempt to get the PORT environment variable, 
    # otherwise default to port 5000
    port = int(os.environ.get("PORT", 5000))
    if port == 5000:
        app.debug = True
    app.run(host='0.0.0.0', port=port)

