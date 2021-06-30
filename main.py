from datetime import datetime
from time import sleep
import os
import JsonControl
import AddigyAPI

#Check we have the required Addigy binary
if os.path.exists("/Library/Addigy/user-manager") != True:
    print("This device is not in Addigy and therefore cannot use this tool")
    exit()

#Funtion for logging and printing outputs with a time stamp
def LogAndPrint(message, File="Log.txt"):
    TimeStamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message=TimeStamp+" - "+message
    print(message)
    with open(File, "a+") as LogFile:
        LogFile.write(message+"\n")

#Check if json file exits, if it doesn't build it
NewAttempt=False #Variable to skip populating the json with online devices if its not a new attempt
if os.path.exists("MMPR.json") == False:
    #Create a empty device json file and wait for completion 
    while os.path.exists("MMPR.json") == False:
        JsonControl.GenJSONFile()
    print("Please fill out the JSON file then re-run this script")
    exit()
elif os.path.exists("MMPR.json") == True and (len(JsonControl.GetDevicesToDo()) != 0 or len(JsonControl.GetDevicesPending()) != 0):
    LogAndPrint("---------------SESSION START---------------")
    LogAndPrint("WARN - MMPR Json already exists with devices left, will resume that")
elif len(JsonControl.GetDevicesToDo())  == 0 and len(JsonControl.GetDevicesDone()) !=0:
    print("You have a json file with a previous run but it looks like there are no devices left to do. Exiting")
    exit()
else:
    NewAttempt=True
    LogAndPrint("---------------SESSION START---------------")
    LogAndPrint("WARN - No previous attempts detected, starting a new session")


#Store all our changeable info for later
ClientID=JsonControl.GetSetting("ClientID")
ClientSecret=JsonControl.GetSetting("ClientSecret")
Username=JsonControl.GetSetting("Username")
Password=JsonControl.GetSetting("Password")
PolicyID=JsonControl.GetSetting("PolicyID")


if NewAttempt == True: 
    #Populate json with all the devices in the given policy
    for Device in AddigyAPI.GetAllDevicesInPolicy(ClientID,ClientSecret,PolicyID):
        JsonControl.SaveFoundDevice(Device["Device Name"],Device["agentid"])


def GetActionID(ResetResponse):
    #Get the action id from the rest response, by making it a json then pulling the actionid key from actionids
    ResetResponse=ResetResponse.json()
    #Get the list that has a list inside of it, turn it into the one list and pull the id
    ActionID=(ResetResponse["actionids"][0])["actionid"]
    return ActionID


#Main loop, will run until there are no devices left to do.
while len(JsonControl.GetDevicesToDo()) != 0 or len(JsonControl.GetDevicesPending()) != 0:
    if len(JsonControl.GetDevicesToDo()) != 0: #Only do the Online Device check if there devices still left to send commands for, if not skip to checking pending commands
    #Compare Online Devices with those in the JSON file, if they are in todo list then reset the password
        for OnlineDevice in AddigyAPI.GetOnlineDevices(ClientID,ClientSecret):
            if OnlineDevice["Device Name"] in JsonControl.GetDevicesToDo() and OnlineDevice["Device Name"] not in JsonControl.GetDevicesPending(): #Check again that device is online to prevent a large list of online devices returning ones that have since gone offline 
                if OnlineDevice["Device Name"] in str(AddigyAPI.GetOnlineDevices(ClientID,ClientSecret)):
                    #Device is online, attempt to reset the password
                    LogAndPrint("INFO - Working on device: {0} AgentID: {1}".format(OnlineDevice["Device Name"],OnlineDevice["agentid"]))
                    #Hash our desired password then send it to addigy
                    HashedPassword=os.popen("/Library/Addigy/user-manager -update-password -generate-salted-sha512-pbkdf2-plist-b64 {0}".format(Password)).read()

                    #Request the API reset the device password 
                    APIResponse=AddigyAPI.ResetPassword(ClientID,ClientSecret,OnlineDevice["agentid"],Username,HashedPassword)

                    if str(APIResponse) != "<Response [200]>":
                        LogAndPrint("ERROR - {0} - Addigy response to reset command was non-success".format(OnlineDevice["Device Name"]))
                        LogAndPrint(str("{0} - {1}").format(OnlineDevice["Device Name"],APIResponse),"Errors.txt")
                    
                    #Store the action ID for the reset command we just sent
                    ActionID=GetActionID(APIResponse)

                    #Log the device as pending so we can check on it later
                    JsonControl.MarkDeviceAsPending(OnlineDevice["Device Name"],OnlineDevice["agentid"],ActionID)

                    #Now check what happened with our reset request
                    APIResponse=AddigyAPI.GetPasswordResetResult(ClientID,ClientSecret,OnlineDevice["agentid"],ActionID)
        
                    if APIResponse == "Success":
                        LogAndPrint("INFO - Password successfully changed for: {0} AgentID: {1}".format(OnlineDevice["Device Name"],OnlineDevice["agentid"]))
                        JsonControl.MarkDeviceAsDone(OnlineDevice["Device Name"],OnlineDevice["agentid"],ActionID)
                    elif APIResponse == "Pending":
                        LogAndPrint("INFO - Device {0} reset command is pending, will be checked later".format(OnlineDevice["Device Name"]))
                    else:
                        LogAndPrint("ERROR - Failure for device {0} See error log for more info".format(OnlineDevice["Device Name"]))
                        LogAndPrint("{0} - {1}".format(OnlineDevice["Device Name"],APIResponse))
                else:
                    LogAndPrint("WARN - Device {0} no longer online, skipping")
        
    #After each loop of online devices, check and see if we have any pending that have since finished
    if len(JsonControl.GetDevicesPending()) != 0:
        LogAndPrint("INFO - Running pending commands checkup")
        
        DevicesPending=JsonControl.GetDevicesPending() #Save the directory of whats still pending
        for DeviceName in JsonControl.GetDevicesPending(): #Loop though each pending device
            AgentID=DevicesPending[DeviceName][0]
            ActionID=DevicesPending[DeviceName][1]

            #Get the status of the command using the action and agent IDs
            Status=AddigyAPI.GetPasswordResetResult(ClientID,ClientSecret,AgentID,ActionID)

            if Status == "Success":
                LogAndPrint("INFO - Pending password change now successful for: {0} AgentID: {1}".format(DeviceName,AgentID))
                JsonControl.MarkDeviceAsDone(DeviceName,AgentID,ActionID)
            elif Status == "Pending":
                LogAndPrint("INFO - Device {0} reset command check came back still pending".format(DeviceName))
            else: #TODO get this to trigger when command is canceled, at the moment both pending and cancled commands return 409 with the same message
                LogAndPrint("ERROR - Unable to check pending status for {0}, Device will be put back into TODO. See error log for more info".format(DeviceName))
                LogAndPrint("{0} - {1}".format(DeviceName,APIResponse))
                JsonControl.ResetPendingDevice(DeviceName,AgentID)

    LogAndPrint("INFO - Devices still to do, but none are avalaible waiting")
    sleep(int(JsonControl.GetSetting("RefreshTime")))

LogAndPrint("---------------SESSION END---------------")
LogAndPrint("No more devies left!")
