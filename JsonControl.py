import json

def GenJSONFile(Filename="MMPR.json"):
    with open(Filename, "w") as JSONFile:
        FileContents={
            "Settings": {
                "ClientID" : "",
                "ClientSecret" : "",
                "Username" : "LocalAccount",
                "Password" : "SuperSecretPasswd",
                "PolicyID" : "TargetPolicyIDHere"
            },
            "DevicesToDo": {},
            "DevicesDone": {}
            }
        json.dump(FileContents,JSONFile)

def GetSetting(SettingName,Filename="MMPR.json"):
    with open(Filename, "r") as JSONFile:
        return (json.load(JSONFile)["Settings"][SettingName])

def GetCurrentContents(Filename="MMPR.json"):
    with open(Filename, "r") as JSONFile:
        return json.load(JSONFile)

def GetDevicesToDo(Filename="MMPR.json"):
    with open(Filename, "r") as JSONFile:
        return (json.load(JSONFile)["DevicesToDo"])

def SaveFoundDevice(DeviceName, AgentID, Filename="MMPR.json"):
    with open(Filename, "r+") as JSONFile:
        Contents=GetCurrentContents(Filename)
        (Contents["DevicesToDo"])[DeviceName] = [AgentID]
        json.dump(Contents,JSONFile)

def MarkDeviceAsDone(DeviceName, AgentID, Filename="MMPR.json"):
    Contents=GetCurrentContents(Filename)
    with open(Filename, "w+") as JSONFile:
        del Contents["DevicesToDo"][DeviceName]
        Contents["DevicesDone"][str(DeviceName)] = [str(AgentID)]
        json.dump(Contents,JSONFile)
