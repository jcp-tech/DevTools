# This is going to be a Developer Support System it will Include but not Limited to:

> NOTE: Currently going to make for a Django, MySQL System...

## DEBUGGING System:
- This is for Users to Give Details to the the AI Agent like Sreenshot's, The Yellow Error Pages Text or Just Details of what happend and with the Problem.
- The AI will by Understanding the Problem Start Following Standard Debugging Procedure Step by Step (by Providing Tasks to it's Sub Agent's or Tool's).
- Steps:
    - If there is a Link take the Link and Extract the File/Function Location
    - If You have the File or Function Path, read the Function Starting with the `__docs__` and then the Code in Full, IF THERE is any SubFunctions called in the Function which is Referenced read it and Understand what they do, Use All this to Build the Logic of the Function to Understand it more.
    - You may Also have to use the Database Models Understanding what Data Get's Sent in the Function and where.
    - Understanding the Data Flow is Releavant (There will be a Documentation of whatever i can Explain of how the System Works but it will be Limited)
- Tools which will be Given to the Agent:
    - GenAI Toolkit Toolbox to Connect to Read & if needed Write Data to the (MySQL) Database.
    - Custom Build Tool (to be Converted to ADK's MCP Server) which will tell the User what are the Differnt Link's in the System & a Tool which when Giving a Link to it for Debugging, it will return Important Details like Url, FilePath, Name, etc... These Details will Later been Used to Identify and Debugg the Function.
    - File or Function Reading Tools can be done using GitHub MCP &or Some Custom Built Code Parsing Tool.