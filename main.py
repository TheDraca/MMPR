import os
import JsonControl
import AddigyAPI

#Check we have the required Addigy binary
if os.path.exists("/Library/Addigy/user-manager") != True:
    print("This device is not in Addigy and therefore cannot use this tool")
    exit()

#Check if json file exits, if it doesn't build it
if os.path.exists("MMPR.json") == False:
    #Create a empty device json file and wait for completion 
    while os.path.exists("MMPR.json") == False:
        JsonControl.GenJSONFile()
    print("Please fill out the JSON file then re-run this script")
    exit()
elif os.path.exists("MMPR.json") == True and len(JsonControl.GetDevicesToDo())  != 0:
    print("MMPR Json already exists with devices left, will resume that")
elif len(JsonControl.GetDevicesToDo())  == 0 and len(JsonControl.GetDevicesDone()) !=0:
    print("You have a json file with a previous run but it looks like there are no devices left to do. Exiting")
    exit()
else:
   print("Looks like you have no previous attempts, starting a new session")


#Store all our changeable info for later
ClientID=JsonControl.GetSetting("ClientID")
ClientSecret=JsonControl.GetSetting("ClientSecret")
Username=JsonControl.GetSetting("Username")
Password=JsonControl.GetSetting("Password")
PolicyID=JsonControl.GetSetting("PolicyID")
   
#Populate json with all the devices in the given policy
for Device in AddigyAPI.GetAllDevicesInPolicy(ClientID,ClientSecret,PolicyID):
    JsonControl.SaveFoundDevice(Device["Device Name"],Device["agentid"])


#Main loop, will run until there are no devices left to do.
while len(JsonControl.GetDevicesToDo())  != 0:
    #Compare Online Devices with those in the JSON file, if they are in todo lst then reset the password
    for OnlineDevice in AddigyAPI.GetOnlineDevices(ClientID,ClientSecret):
        if OnlineDevice["Device Name"] in str(JsonControl.GetDevicesToDo()):
            #Device is online, attempt to reset the password
            print("Device pending: " +OnlineDevice["Device Name"] +" AgentID: " +OnlineDevice["agentid"])

            #Hash our desired password then send it to addigy
            HashedPassword=os.popen("/Library/Addigy/user-manager -update-password -generate-salted-sha512-pbkdf2-plist-b64 {0}".format(Password)).read()
            #Store what out API module says about the reset
            APIResponse=AddigyAPI.ResetPassword(ClientID,ClientSecret,OnlineDevice["agentid"],Username,HashedPassword)
            if APIResponse == "Success":
                print("Password changed for: " +OnlineDevice["Device Name"])
                JsonControl.MarkDeviceAsDone(OnlineDevice["Device Name"],OnlineDevice["agentid"])
            else:
                print("Failure for device:" +OnlineDevice["Device Name"])
                with open("Errors.txt", "a+") as ErrorFile:
                    ErrorFile.write("{0} - {1}\n".format(OnlineDevice["Device Name"],APIResponse))
