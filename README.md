# MMPR - *Matt's Mass Password Resetter*

For mass resetting a local account using Addigy's API.

### Requirements
* Python3
* Python Requests Module
* Run on a device that is enrolled in Addigy (For their user management binary /Library/Addigy/user-manager)


### Settings
The MMPR.json file will be generated on first run, here's a quick breakdown of what does what
* ClientID - This is your Addigy API Client ID
* ClientSecret - This is your Addigy API Secret
* PolicyID - This is the target policy MMPR will run against, this is recursive and will run on policies under it too!
* RefreshTime - How long (in secs) to wait between each password reset run
* Username - The local username you are aiming to reset
* UseStaticPassword - Boolean value of 1 or 0, setting to 1 will mean all devices set the password defined by "StaticPassword", setting 0 will enable randomly generated passwords
* StaticPassword - The password set on all devices if UseStaticPassword is set to 1
* RandomPassLength - The password length of all randomly generated passwords if UseStaticPasswords is set to 0
* RandomPassExtraChars - Additional characters to add to what can be used to make up a random password, all passwords will included the upper and lower case alphabet plus numbers 0-9 as possibilities anyway but here you can add symbols you like (NB avoid ones that may escape the json file like “ )
* WriteRandPassToLogs - If enabled a message will be printed and logged with the device name and the password that is being attempted to set. **CURRENTLY THE ONLY WAY TO STORE RANDOMLY GENERATED PASSWORDS**. I will in the future change this
