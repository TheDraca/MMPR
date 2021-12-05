import ldap
import json
import datetime

#Set what our settings file is called
SettingsFile = "ADRead.json"

#Read the file each time an item is used
def GetSetting(Setting, SettingName):
    with open(SettingsFile) as JSONFile:
        SettingsJSON = json.load(JSONFile)
    return SettingsJSON[Setting][SettingName]

#Funtion for logging and printing outputs with a time stamp
def LogAndPrint(message, File="Log.txt"):
    TimeStamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message=TimeStamp+" - "+message
    print(message)
    with open(File, "a+") as LogFile:
        LogFile.write(message+"\n")


#Set all our setting variable
LDAPDomain=GetSetting("LDAP","Domain")
LDAPNetBIOS=GetSetting("LDAP","NetBIOS")
LDAPFriendlyDomain=GetSetting("LDAP","LDAPFriendlyDomain")
LDAPDCToQuery=GetSetting("LDAP","DCToQuery")
LDAPUseSSL=bool(GetSetting("LDAP","UseSSL"))
LDAPSSLFilename=GetSetting("LDAP","SSLFilename")
LDAPUsername=GetSetting("LDAP","Username")
LDAPPassword=GetSetting("LDAP","Password")


def BindToAd():
    #Set LDAP options used regarless of SSL or non-ssl
    ldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3) #Force LDAP V3
    ldap.set_option(ldap.OPT_REFERRALS, 0) # Disable anonymous access
    ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, 5) #Set time out to 5 secs
    
    if LDAPUseSSL == True:
        #Demand SSL, fail if not avaliable
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)

        #Connect to DC with ldaps
        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, LDAPSSLFilename)
        #Define new TLS 
        ldap.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

        #Finally connect
        LDAPConnection = ldap.initialize('ldaps://{0}.{1}:636'.format(LDAPDCToQuery,LDAPDomain))
        
    else:
        #Connect to DC with normal ldap
        LDAPConnection = ldap.initialize("ldap://{0}.{1}".format(LDAPDCToQuery,LDAPDomain))

    #Finally authenticate with the DC
    LDAPConnection.simple_bind_s(r"{0}\{1}".format(LDAPNetBIOS,LDAPUsername),LDAPPassword) # Bind

    return LDAPConnection


def ConvertNT2Normal(NTTime):
    return((datetime.datetime (1601, 1, 1) + datetime.timedelta(seconds=int(NTTime)/10000000)).strftime("%d/%m/%Y %H:%M:%S"))


def ConvertToNTTime(NormalDateTime):
    #Turn the string of date time into a date time object
    NTTime=datetime.datetime.strptime(NormalDateTime,"%d/%m/%Y %H:%M:%S")

    #First turn into time stamp
    NTTime=int(NTTime.timestamp())

    #Next account for gap betwen 1970 in UTC and 1601 in NT time
    NTTime=NTTime+11644473600

    #Turn into nano secs for AD
    NTTime=NTTime*10000000
    
    return NTTime

def GrabAttributeValueFromQuery(result,attribute):
        #First filter result so we're left with just the b'*ValueWeWant*'
        Value=result[0][1][attribute][0]
        #Next split this into an array, with the ' as the separator
        Value=str(Value).split("'")
        #Finally we have the value we want
        Value=Value[1]
        return Value



def GetCurrentLAPS(ComputerName):
    LDAPConnection=BindToAd()
    #Run a query for the mail attrubite then save it as result
    result = LDAPConnection.search_s(LDAPFriendlyDomain,ldap.SCOPE_SUBTREE,'(&(objectCategory=computer)(name={0}))'.format(ComputerName),attrlist=['ms-Mcs-AdmPwd',"ms-Mcs-AdmPwdExpirationTime"])

    #Store the full DN to use to identify what to reset in SetLAPSPassword
    ComputerDN=str(result[0][0])

    if str("CN={0}".format(ComputerName)).lower() not in str(result).lower():
        LogAndPrint("ERORR - Connecting to AD: computer not in AD or missing perms")
        exit(1)
    elif "ms-Mcs-AdmPwd" not in str(result):
        LogAndPrint("ERORR - Error-NoAttrORPerms",ComputerDN)

    LAPSPassword=GrabAttributeValueFromQuery(result,"ms-Mcs-AdmPwd")
    ExpiryDate=GrabAttributeValueFromQuery(result,"ms-Mcs-AdmPwdExpirationTime")
    ExpiryDate=ConvertNT2Normal(ExpiryDate)

    return(LAPSPassword,ComputerDN,ExpiryDate)


def SetLAPSPassword(ComputerName,NewPassword,Expiry):
    ExistingObject=GetCurrentLAPS(ComputerName)
    Expiry=ConvertToNTTime(Expiry)

    LDAPObject=ExistingObject[1]

    LDAPConnection=BindToAd()

    #Set New Password
    LDAPConnection.modify_s(LDAPObject, [ (ldap.MOD_REPLACE, "ms-Mcs-AdmPwd", NewPassword.encode("utf-8")) ])

    #Set Expiry
    LDAPConnection.modify_s(LDAPObject, [ (ldap.MOD_REPLACE, "ms-Mcs-AdmPwdExpirationTime", str(Expiry).encode("utf-8")) ])
