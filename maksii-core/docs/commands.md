//This is a list of commands that maksii-core will (hopefully) understand.

Structure:
Name of Command - What it does 

**Main Command List**
- maksii-core : If the app is installed and functional says *Hello! This is maksii-core.*

- maksii-core -version : Says the simple version of the app (Ex: Version: 0.1.0)

- maksii-core --version : States detailed version of the app (Ex: Version 0.1.0, Last updated : 4/2/2026, Tester version : Nay/Yay (So yes or no depending if it is a test version))

- maksii-core --help : Displays a list of available commands and brief descriptions.

- maksii-core push : Uploads the current project state to the configured server as a new snapshot. (NOTE: This will replace the current version with the smallest number until 10 is reached, for example, if you upload a file in version 1.0, this push will update it to version 1.1, when the number reaches 1.10, it will automatically convert it to 2.0)

- maksii-core push -v "1.0" : Does the same thing, uploads the project state to the server, BUT changes the version to the one stated in the bracets so for example "1.0"

- maksii-core pull : Downloads the latest snapshot of the project from the server. (It will always download the latest version.)

- maksii-core pull -v "1.0.1" : Pulls the specified version of the project from the database, which is stated in the brackets.

- maksii-core status
Shows the current sync status of the project.
Example output:
Project: fireside-core
Local version: 11
Remote version: 12
Status: Out of sync
Changed files: 5

- maksii-core init
Initializes a directory as a maksii-core project.
Actions:
- Creates local metadata
- Links the project to a server
- Generates a project identifier-

**Utility & Debug Commands**

- maksii-core list
Lists all versions available on the server for the current project.

- maksii-core verify 
Verifies integrity of the local project against stored hashes.

- maksii-core ping
Checks connectivity to the configured server.

