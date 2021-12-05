import json

def GenJSONFile(Filename="MMPR.json"):
    with open(Filename, "w") as JSONFile:
        FileContents={
            "Settings": {
                "ClientID" : "",
                "ClientSecret" : "",
                "PolicyID" : "TargetPolicyIDHere",
                "RefreshTime": "600",
                "Username" : "LocalAccount",
                "UseStaticPassword": 0,
                "StaticPassword": "SuperSecretPasswd",
                "RandomPassLength": 10,
                "RandomPassExtraChars": "!",
                "WriteRandPassToLogs": 1,
                "PasswordExpiry": 1,
                "PasswordLifeTime": 20,
                "LearnNewDevices": 1
            },
            "DevicesToDo": {},
            "DevicesPending": {},
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

def GetDevicesDone(Filename="MMPR.json"):
    with open(Filename, "r") as JSONFile:
        return (json.load(JSONFile)["DevicesDone"])

def GetDevicesPending(Filename="MMPR.json"):
    with open(Filename, "r") as JSONFile:
        return (json.load(JSONFile)["DevicesPending"])

def SaveFoundDevice(DeviceName, AgentID, Filename="MMPR.json"):
    Contents=GetCurrentContents(Filename)
    with open(Filename, "w+") as JSONFile:
        (Contents["DevicesToDo"])[DeviceName] = AgentID
        json.dump(Contents,JSONFile)

def MarkDeviceAsDone(DeviceName, AgentID, ActionID, DateReset, Passwd, Filename="MMPR.json"):
    Contents=GetCurrentContents(Filename)
    with open(Filename, "w+") as JSONFile:
        del Contents["DevicesToDo"][DeviceName]
        del Contents["DevicesPending"][DeviceName]
        (Contents["DevicesDone"])[DeviceName] = AgentID,ActionID,DateReset,Passwd
        json.dump(Contents,JSONFile)

def MarkDeviceAsPending(DeviceName, AgentID, ActionID, Passwd, Filename="MMPR.json"):
    Contents=GetCurrentContents(Filename)
    with open(Filename, "w+") as JSONFile:
        (Contents["DevicesPending"])[DeviceName] = AgentID,ActionID,Passwd
        json.dump(Contents,JSONFile)

def ResetPendingDevice(DeviceName, AgentID, Filename="MMPR.json"):
    Contents=GetCurrentContents(Filename)
    with open(Filename, "w+") as JSONFile:
        del Contents["DevicesPending"][DeviceName]
        json.dump(Contents,JSONFile)
    SaveFoundDevice(DeviceName,AgentID)

def ResetDoneDevice(DeviceName, AgentID, Filename="MMPR.json"):
    Contents=GetCurrentContents(Filename)
    with open(Filename, "w+") as JSONFile:
        del Contents["DevicesDone"][DeviceName]
        json.dump(Contents,JSONFile)
    SaveFoundDevice(DeviceName,AgentID)

def GetDoneDeviceDateReset(DeviceName,Filename="MMPR.json"):
    Contents=GetCurrentContents(Filename)
    return Contents["DevicesDone"][DeviceName][2]

def GetPendingDevicePassword(DeviceName,Filename="MMPR.json"):
    Contents=GetCurrentContents(Filename)
    return Contents["DevicesPending"][DeviceName][2]
