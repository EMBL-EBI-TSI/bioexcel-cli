# Bioexcel portal app command line tool
An Bioexcel portal app command line tool, make executable and stick it in your `PATH`.
Define user credentials on `json/user.json`, If you want to use a token from a different source,
stick it in a file and use the `--token` flag to pass it. 

## Requirement 
Install ecp-cli module from github repository.

pip install git+https://github.com/EMBL-EBI-TSI/ecp-cli/


## Synopsis
Main commands are run as `bioexcel *argument* [*action*]`. 
Actions are: 
 - deploy
 - destroy
 argument: 
  --token: file name relative path

## Configurations
`json/user.json` :  User credentials
`json/config.json` :  NFS server details, application name and corresponding image source URL to deploy through launcher.
`json/deploy.json` :  Launcher application with tool name defined on the config.json
`json/destroy.json`: Deployment references to destroy.

## Examples
Deploy tools from the `json/deploy.json` file.
`bioexcel deploy`
Deploy tools from the `json/deploy.json` file and use token.txt for session.
`bioexcel –token=token.txt deploy`
Destroy deployments defined in `json/destroy.json` file and use token.txt for session.
`bioexcel –token=token.txt destroy`

## Side notes for Mac OS X

The `python3` is required. Installed it with:

`brew install python3`

if needed.  

It is a good idea to keep the default version unchanged.

Modules `requests` and `yaml` are not installed by default. Run:

`sudo pip3 install requests`

and

`sudo pip3 install pyyaml`

as necessary.
