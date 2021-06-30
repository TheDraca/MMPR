from requests import request
from time import sleep
import json


def GetAllDevicesInPolicy(ClientID,ClientSecret,PolicyID):
    #Send our request out to the api and save what comes back as response
    Response = request("GET", "https://prod.addigy.com/api/policies/devices?policy_id={0}&client_id={1}&client_secret={2}".format(PolicyID,ClientID,ClientSecret))

    #Return this response in json format
    return Response.json()


def GetOnlineDevices(ClientID,ClientSecret):
    #Setup the payload and headers the request
    payload = {}
    headers = {
    'Content-Type': 'application/json',
    'client-id': ClientID,
    'client-secret': ClientSecret
    }
    #Send our request out to the api and save what comes back as response
    Response = request("GET", "https://prod.addigy.com/api/devices/online", headers=headers, data=payload)

    #Return this response as a json file but only if its not empty
    try:
        if len((Response.json())[0]) >0:
            return Response.json()
    except IndexError:
        print("Index Error, addigy didn't return anything")
        return ""

def GetPasswordResetResult(ClientID,ClientSecret,AgentID,ActionID):
    sleep(5) #Wait a few secs for the command to run
    #Send our request out to the api and save what comes back as response
    Response = request("GET", "https://prod.addigy.com/api/devices/output?client_id={0}&client_secret={1}&actionid={2}&agentid={3}".format(ClientID,ClientSecret,ActionID,AgentID))

    #Make sure the command has finished before trying to return the output
    if str(Response.text) == '"Command not finished executing. Please try again later"':
        return "Pending"
    elif Response.json()["exitstatus"] == 0: #On a success return the word "Success" to ResetPassword if not dump the response for logging
        return "Success"
    else: #If its not success or pending must be an error, return it to log
        return (Response.text)


def ResetPassword(ClientID,ClientSecret,AgentID,Username,HashedPassword):
    #Store the full command to reset the users password
    ResetCommand='''/Library/Addigy/user-manager -update-password -username="{0}" -salted-sha512-pbkdf2-plist-b64="{1}"'''.format(Username,HashedPassword)

    #Setup our payload and header info for our post request
    payload = json.dumps({
    "agents_ids": [AgentID],
    "command": ResetCommand
    })

    headers = {
    'Content-Type': 'application/json',
    'agents_ids': '[{AgentID}]',
    "command": ResetCommand,
    'client-id': ClientID,
    'client-secret': ClientSecret
    }

    #Send the request off to addigy and save the response
    Response = request("POST", "https://prod.addigy.com/api/devices/commands", headers=headers, data=payload)

    return Response

