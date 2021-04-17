#02/04/21
import json

def GenJSONFile(Filename):
    with open(Filename, "w") as JSONFile:
        FileContents={
            "DevicesToDo": {},
            "DevicesDone": {}
            }
        json.dump(FileContents,JSONFile)

def GetCurrentContents(Filename):
    with open(Filename, "r") as JSONFile:
        return json.load(JSONFile)

def GetDevicesToDo(Filename):
    with open(Filename, "r") as JSONFile:
        return (json.load(JSONFile)["DevicesToDo"])

def SaveFoundDevice(Filename, DeviceName, AgentID):
    with open(Filename, "r+") as JSONFile:
        Contents=GetCurrentContents(Filename)
        (Contents["DevicesToDo"])[DeviceName] = [AgentID]
        json.dump(Contents,JSONFile)

def MarkDeviceAsDone(Filename, DeviceName, AgentID):
    Contents=GetCurrentContents(Filename)
    with open(Filename, "w+") as JSONFile:
        del Contents["DevicesToDo"][DeviceName]
        Contents["DevicesDone"][str(DeviceName)] = [str(AgentID)]
        json.dump(Contents,JSONFile)