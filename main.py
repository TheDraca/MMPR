#02/04/21
import os
import JsonControl
import AddigyAPI

#Read the api settings from a txt file
def ReadAPIFile(Option):
    with open(r"/Volumes/OSX/api.txt", "r") as APISettings:
        for line in APISettings:
            if Option in line:
                Result = line.split("=", 1)[1]
                return Result.strip()

#Store all our changeable info for later
ClientID=ReadAPIFile("ClientID")
ClientSecret=ReadAPIFile("ClientSecret")
Username=ReadAPIFile("Username")
Password=ReadAPIFile("Password")
PolicyID=ReadAPIFile("PolicyID")


#Check if json file exits, if it doesn't build it
if os.path.exists("MMPR.json") == True:
    print("MMPR Json already exists, will resume that")
else:
    #Create a empty device json file and wait for completion 
    while os.path.exists("MMPR.json") == False:
        JsonControl.GenJSONFile("MMPR.json")

    #Populate json with all the devices in the given policy
    for Device in AddigyAPI.GetAllDevicesInPolicy(ClientID,ClientSecret,PolicyID):
        JsonControl.SaveFoundDevice("MMPR.json",Device["Device Name"],Device["agentid"])

#Main loop, will run until there are no devices left to do.
while len(JsonControl.GetDevicesToDo("MMPR.json"))  != 0:
    #Compare Online Devices with those in the JSON file, if they are in todo lst then reset the password
    for OnlineDevice in AddigyAPI.GetOnlineDevices(ClientID,ClientSecret):
        if OnlineDevice["Device Name"] in str(JsonControl.GetDevicesToDo("MMPR.json")):
            #Device is online, attempt to reset the password
            print("Device pending: " +OnlineDevice["Device Name"] +" AgentID: " +OnlineDevice["agentid"])

            #Hash our desired password then send it to addigy
            HashedPassword=os.popen("/Library/Addigy/user-manager -update-password -generate-salted-sha512-pbkdf2-plist-b64 {0}".format(Password)).read()
            #Store what out API module says about the reset
            APIResponse=AddigyAPI.ResetPassword(ClientID,ClientSecret,OnlineDevice["agentid"],Username,HashedPassword)
            if APIResponse == "Success":
                print("Password changed for: " +OnlineDevice["Device Name"])
                JsonControl.MarkDeviceAsDone("MMPR.json",OnlineDevice["Device Name"],OnlineDevice["agentid"])
            else:
                print("Failure for device:" +OnlineDevice["Device Name"])
                with open("Errors.txt", "a+") as ErrorFile:
                    ErrorFile.write("{0}\n".format(APIResponse))
