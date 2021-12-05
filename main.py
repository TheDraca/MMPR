from datetime import datetime, timedelta
from time import sleep
import os
import JsonControl
import AddigyAPI
import ADRead


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
    LogAndPrint("WARN - MMPR Json already exists with {0} devices left, will resume that".format(len(JsonControl.GetDevicesToDo())))
elif len(JsonControl.GetDevicesToDo())  == 0 and len(JsonControl.GetDevicesDone()) !=0:
    print("You have a json file with a previous run but it looks like there are no devices left to do. Exiting")
    exit()
else:
    NewAttempt=True
    LogAndPrint("---------------SESSION START---------------")
    LogAndPrint("WARN - No previous attempts detected, starting a new session")


#Check if we're using a static password or generating random ones for each device
if JsonControl.GetSetting("UseStaticPassword") == False:
    import random, string #Import needed modules for GenNewPassword if random passwords are enabled
else:
    LogAndPrint("Static Password is enabled, the StaticPassword value in MMPR.json will be used for all passwords")


#Store all our changeable info for later
ClientID=JsonControl.GetSetting("ClientID")
ClientSecret=JsonControl.GetSetting("ClientSecret")
Username=JsonControl.GetSetting("Username")
PolicyID=JsonControl.GetSetting("PolicyID")

if NewAttempt == True: 
    #Populate json with all the devices in the given policy
    for Device in AddigyAPI.GetAllDevicesInPolicy(ClientID,ClientSecret,PolicyID):
        if "macOS" in Device["System Version"]: #Ensure we only add devices that are identified as MacOS, iOS won't work!
            JsonControl.SaveFoundDevice(Device["Device Name"],Device["agentid"])
    LogAndPrint("INFO - {0} Devices found and marked as to do from Policy ID: {1}".format(len(JsonControl.GetDevicesToDo()),PolicyID))

#Function for returning what password is set. The "StaticPassword" in MMPR.json is always returned if "UserStaticPassword" = 1, otherwise a random pass is generated
def GetNewPassword(DeviceName):
    #First check if we're only using one password for all devices, if so just return that
    if JsonControl.GetSetting("UseStaticPassword") == True:
        Password=JsonControl.GetSetting("StaticPassword")
    else:
        #Create a set of characters to be used for the random password, always includes alpha numeric then adds anything extra from RandomPassExtraChars in MMPR.json
        RandomPassCharSet=string.ascii_letters + string.digits + JsonControl.GetSetting("RandomPassExtraChars")

        RandomPassLength=JsonControl.GetSetting("RandomPassLength") #Set the desired legth of the password
        random.seed = (os.urandom(4096)) # Set random string of 4096 characters as the seed for generation
        
        Password=""
        while len(Password) < RandomPassLength:
            #Add a random character from RandomPassCharSet to the password string in a loop until we hit the desired length
            Password+=random.choice(RandomPassCharSet)
        
        if JsonControl.GetSetting("WriteRandPassToLogs") == True:
            LogAndPrint("INFO - Random Password {0} has been generated for {1}".format(Password,DeviceName))
    return Password

#Function for checking and reseting expired passwords
def RestExpiredPassword(DeviceName,AgentID,PasswordLifeTime=JsonControl.GetSetting("PasswordLifeTime")):
    #Get Reset Date of DeviceName
    ResetDate = datetime.strptime(JsonControl.GetDoneDeviceDateReset(DeviceName),"%d/%m/%Y %H:%M:%S")

    CurrentDate=datetime.now().strftime("%d/%m/%Y %H:%M:%S") #Get current date and time in a DD/MM/YYY HH/MM/SS formated string
    CurrentDate=datetime.strptime(str(CurrentDate), "%d/%m/%Y %H:%M:%S") #Turn the above string into a datetime type

    #Get Diffrence between the Current Date and the day reset
    DateDiff = CurrentDate - ResetDate

    #Turn the diffrence into just days
    DateDiff=DateDiff.days

    if DateDiff>PasswordLifeTime:
        LogAndPrint("INFO - {0}'s password is older than {1} days, moving into DevicesToDo".format(DeviceName,PasswordLifeTime))
        JsonControl.ResetDoneDevice(DeviceName,AgentID)



def GetActionID(ResetResponse):
    #Get the action id from the rest response, by making it a json then pulling the actionid key from actionids
    ResetResponse=ResetResponse.json()
    #Get the list that has a list inside of it, turn it into the one list and pull the id
    ActionID=(ResetResponse["actionids"][0])["actionid"]
    return ActionID


#Main loop, will run until there are no devices left to do.
while True:
    if len(JsonControl.GetDevicesToDo()) != 0: #Only do the Online Device check if there devices still left to send commands for, if not skip to checking pending commands
    #Compare Online Devices with those in the JSON file, if they are in todo list then reset the password
        for OnlineDevice in AddigyAPI.GetOnlineDevices(ClientID,ClientSecret):
            if OnlineDevice["Device Name"] in JsonControl.GetDevicesToDo() and OnlineDevice["Device Name"] not in JsonControl.GetDevicesPending(): #Check again that device is online to prevent a large list of online devices returning ones that have since gone offline 
                if OnlineDevice["Device Name"] in str(AddigyAPI.GetOnlineDevices(ClientID,ClientSecret)):
                    #Device is online, attempt to reset the password
                    LogAndPrint("INFO - Working on device: {0} AgentID: {1}".format(OnlineDevice["Device Name"],OnlineDevice["agentid"]))

                    #Get our desired password from the GetNewPassword function
                    Password=GetNewPassword(OnlineDevice["Device Name"])

                    #Hash our desired password then send it to addigy
                    HashedPassword=os.popen('''/Library/Addigy/user-manager -update-password -generate-salted-sha512-pbkdf2-plist-b64="{0}"'''.format(Password)).read()

                    #Request the API reset the device password 
                    APIResponse=AddigyAPI.ResetPassword(ClientID,ClientSecret,OnlineDevice["agentid"],Username,HashedPassword)

                    if str(APIResponse) != "<Response [200]>":
                        LogAndPrint("ERROR - {0} - Addigy response to reset command was non-success".format(OnlineDevice["Device Name"]))
                        LogAndPrint(str("{0} - {1}").format(OnlineDevice["Device Name"],APIResponse),"Errors.txt")
                    
                    #Store the action ID for the reset command we just sent
                    ActionID=GetActionID(APIResponse)

                    #Log the device as pending so we can check on it later
                    JsonControl.MarkDeviceAsPending(OnlineDevice["Device Name"],OnlineDevice["agentid"],ActionID,Password)
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

                #Store when the success occured
                PasswordChangeTime=datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                if JsonControl.GetSetting("PasswordExpiry") == True:
                    #Work out when the password is due to expire
                    PasswordExpiryTime=datetime.strptime(PasswordChangeTime, "%d/%m/%Y %H:%M:%S") + timedelta(JsonControl.GetSetting("PasswordLifeTime"))
                    #Set it to the same format as everything else
                    PasswordExpiryTime=PasswordExpiryTime.strftime("%d/%m/%Y %H:%M:%S")
                    try:
                        #Write this to LAPS
                        ADRead.SetLAPSPassword(DeviceName,str(JsonControl.GetPendingDevicePassword(DeviceName)),PasswordExpiryTime)
                    except:
                        LogAndPrint("ERROR - Can't save password {0} for {1} to LAPS attribute, devices is marked as done anyway".format(str(JsonControl.GetPendingDevicePassword(DeviceName)),DeviceName))
                    
                JsonControl.MarkDeviceAsDone(DeviceName,AgentID,ActionID,PasswordChangeTime,JsonControl.GetPendingDevicePassword(DeviceName))

            elif Status == "Pending":
                LogAndPrint("INFO - Device {0} reset command check came back still pending".format(DeviceName))
            else: #TODO get this to trigger when command is canceled, at the moment both pending and cancled commands return 409 with the same message
                LogAndPrint("ERROR - Unable to check pending status for {0}, Device will be put back into TODO. See error log for more info".format(DeviceName))
                LogAndPrint("{0} - {1}".format(DeviceName,Status))
                JsonControl.ResetPendingDevice(DeviceName,AgentID)

    #After each loop, if password expiry is enabled, move any expired devices back into ToDo
    if JsonControl.GetSetting("PasswordExpiry") == True:
        DoneDevices=JsonControl.GetDevicesDone() #Store Dict of devices done
        for DeviceName in DoneDevices:
            RestExpiredPassword(DeviceName,DoneDevices[DeviceName][0])#Pass the device name and agent id though the reset expired password checker
        
        #If both password expiry and learn new devices is true then check if we can add more devices into DeviceToDo
        if JsonControl.GetSetting("LearnNewDevices") ==True:
            #Populate json with all the devices in the given policy
            for Device in AddigyAPI.GetAllDevicesInPolicy(ClientID,ClientSecret,PolicyID):
                if "macOS" in Device["System Version"] and Device["agentid"] not in str(JsonControl.GetCurrentContents()): #Ensure we only add devices that are identified as MacOS and it isn't anywhere in our json file
                    JsonControl.SaveFoundDevice(Device["Device Name"],Device["agentid"])
                    LogAndPrint("INFO - New device {0} found from Policy ID {1} added into DevicesToDo for next run".format(Device["Device Name"],PolicyID))


    if len(JsonControl.GetDevicesToDo()) != 0 or len(JsonControl.GetDevicesPending()) != 0:
        LogAndPrint("INFO - {0} devices still to do and {1} pending... Waiting {2} secs".format(len(JsonControl.GetDevicesToDo()),len(JsonControl.GetDevicesPending()),JsonControl.GetSetting("RefreshTime")))
        sleep(int(JsonControl.GetSetting("RefreshTime")))

    else:
        if JsonControl.GetSetting("PasswordExpiry") == True:
            LogAndPrint("---------------SESSION PAUSE---------------")
            LogAndPrint("INFO - All devices have had passwords reset but expiry is enabled... Waiting {0} secs".format(JsonControl.GetSetting("RefreshTime")))
            sleep(int(JsonControl.GetSetting("RefreshTime")))

        else:
            LogAndPrint("---------------SESSION END---------------")
            LogAndPrint("INFO  - No more devies left and passwords do not expire... Quitting")
            break #Leave the while true loop as we're done here
