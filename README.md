# Bioexcel portal client - e2e testing tool
A Bioexcel portal client command line tool for end to end testing.
Define user credentials and number of sessions in `user.json`.If you want to use token directly ,paste token to a file and pass
argument `--token` pointing to relative path.Generate session token for owner of `BioExcel Embassy` team and
copy to a file pass it with argument `--owner`,  or it will look for `owner.txt` in current directory.
It will look up `json` directory in current directory by default or you can pass `config json` directory with `--json` argument.

## Requirement 
python 3.6

ecp-cli module

install from github: 

pip3 install git+https://github.com/EMBL-EBI-TSI/ecp-cli/

## Install
pip3 install git+https://github.com/EMBL-EBI-TSI/bioexcel-cli/

## Synopsis
Main commands can be run as 

`bioexcel-cli *argument* [*action*]`. 

Actions are: 
 - deploy
 - destroy

argument: 
  
  --token: session token file relative path
  
  --json: folder containing all configuration json. 
  
  --owner: `BioExcel Embassy` team owner's account session token file path  

## Configurations
By default all json will be looked under `json` directory in current directory.

`user.json` :  Contains list of user credentials & number of sessions

`config.json` :  Contains NFS server details, application name and corresponding image source URL to deploy through launcher.

`deploy.json` :  Contains launcher application with tool to be installed/uploaded on cloud.
                      
                      launcher : bioexcel, nfsclient, ecpimage
                      
                      tool_name : see application_name in config.json

`destroy.json`: Contains deployment references to be destroyed.


## Examples
Deploy tools from the `deploy.json` file, create sessions from `user.json`.

`bioexcel-cli deploy`

Destroy deployment reference defined in `destroy.json`, create session from `user.json` file.

`bioexcel-cli destroy`

Deploy tools from the `deploy.json` file and use token.txt for session.

`bioexcel-cli –-token token.txt deploy`

Destroy deployments defined in `destroy.json` file, locate json from given path.

`bioexcel-cli –-json config-dir destroy`
