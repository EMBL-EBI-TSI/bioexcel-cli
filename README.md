# Bioexcel portal client - e2e testing tool
Bioexcel portal client is a command line tool for end to end testing of Bioexcel portal. 
The objective is to test performance of Bioexcel portal backend, which is actually EBI cloud portal API server.
The testing is focused on Cloud Portal's deployment with multiple concurrent user sessions 
and destruction process.

## Requirement 
python 3.6

ecp-cli module

install from github: 

pip3 install git+https://github.com/EMBL-EBI-TSI/ecp-cli/

## Installation
pip3 install git+https://github.com/EMBL-EBI-TSI/bioexcel-cli/

## Synopsis

The CLI tries to simulate the behaviour and configuration of the BioExcel Cloud Portal. There are some configurations in the project that reflect hardcoded information in the BioExcel Portal itself and configuration that is stored in `bio.tools` and used by the portal as additional source of information. This CLI talks only to the ECP API and does not use any information stored in `bio.tools`.

The documentation below uses the term `launcher`. Launchers correspond to 4 types of applications available in BioExcel Portal:
* `bioexcel` - application uploading and launching an image. Requires a link with the image to run and a configuration. Application type is hardcoded. Default URLs and configurations are defined in [the config](json/config/input.json). If you want to use a different than default configuration, it can be provided as a part of [the deployment descriptor](json/deploy.json)  
* `nfsclient` - application installing an NFS Client on top of image configured as a part of the configuration. Requires the configuration and inputs with NFS Server location. Default values for both are defined in [the config](json/config/input.json).  Application type is hardcoded. The configuration can be changed as a part of [the deployment descriptor](json/deploy.json)
* `ecpimage` - application just running an instance of an image defined as a part of configuration. Defaults are not provided, as currently `bio.tools` have no entries of that type. You can provide your own configuration as a part of  [the deployment descriptor](json/deploy.json)
* `ecpapplication` - application that is not hardcoded and needs: application name, configuration name and team name, where both are shared. There are applications of that type in the current portal, but the default config at the moment does not have that type of applications and you have to provide all details via  [the deployment descriptor](json/deploy.json)

[`json`](json) Directory contains necessary json files for running of Bioexcel portal client.

[`config\input.json`](config\input.json) stores information that in the real BioExcel Portal comes from bio.tools (this at the moment is done only for applications of the 2 types used in BioExcel 1). You need to change this file, if your NFS server is exposed under a different IP than the default and when you want to upload an image from a different URL. All other changes can be done via `deploy.json` 

[`deploy.json`](deploy.json) Describes which & how many applications should be deployed through which launcher.
             
JSON structure:
  
			    {   "deployments" : [{   
			                "application_name":"NAFlex",
					"launcher":"bioexcel",
					"config_name":"bioexcel config",
					"team_name":"Bioexcel"
			    }]}
								 
* `application` - biotools application to be deployed. For `bioexcel`, `nfsclient` and `ecpimage` only creates metadata (does not matter that much). For `ecpapplication` must be a name of a real ECP application.

* `launcher` - one of the four launchers
  
* `config_name` - configuration to be used for deployment. If empty the dafault will be used, if exists in `config/input.json`.
  
* `team_name` - team in which application is shared. Relevan only for `ecpapplication`.
  
We can provide n number of deployment object inside deployments array block. 
Deployment will be done one by one.


[`destroy.json`](destroy.json) Describe what are all the deployments to be destroyed.
      	      
JSON structure:

			  {"deployments":[
			  {"reference":"TSI1583323328233"}
			  ]}
		  
* `reference` - deployment reference to be destroyed
		
We can provide n number of reference object inside deployments array block.

[`user.json`](user.json) Describes user accounts to be used and number concurrent sessions to be created 
while doing deployment.There are two ways that user sessions can be created. 
One is from given JWT token. The other way is through HTTP login from credentials specified on user.json.
You can give JWT token by arugument.`--token` #JWT token saved file path relative#.
If user is not member of the BioExcel Embassy team, user will be added to before deployment 
by supplying team owner's JWT token with --owner argument.
			 
JSON structure:

			  {
				"user-sessions":1,
				"users": [{
				"username":"bioexcel1",
				"password":"bioexcel123"
				}
			  }
			  
* `user-sessions` - number of concurrent user sessions to be created from the account of JWT token specified.
                this attributed will be ignored if --token argument is not specified.
						  
* `username` - username for session creation through HTTP login 

* `password` - password for session creation through HTTP login

You can specify n number of user objects inside users array. 
This type of session creation will happen only if --token is not specified.	  
			  

## Usage
		  
		  bioexcel-cli *argument* [*action*]
              Actions :
    		deploy
			destroy

arguments

--token: Optional argument. Relative path of the text file content which is JWT token from AAP authentication server.
		         Credentials on user.json will be looked if this is specified.
		         
--owner: Optional argument. Relative path of the text file content which is JWT token of BioExcel Embassy team owner's account.
			 Owner token is required in case of user not member of the team and User will be added to team automatically.


## Examples:

  1.Deploy `PyMDSetup` application through BioExcel launcher with 5 concurrent user sessions 
          Get the JWT of a user who is a member of BioExcel Embassy team. Copy the content to file called token.txt.
		   Use following contents with json files.

user.json :-
		    
		     {
				"user-sessions":5,
				"users": [{
				 "username":"",
				 "password":""
				}]
			 }
			 
deploy.json :-
		    
		    {
				"deployments": [
				{
				 "application_name":"PyMDSetup",
				 "launcher":"bioexcel",
				 "config_name":"",
				 "team_name":""
				}
				]
			}
				
Execute :- 

	        bioexcel-cli –-token token.txt deploy
			 
		
   2.Deploy `NAFlex` application through NFS Client launcher with given 3 user accounts of concurrent sessions.
		   Assuming 3 users are member of BioExcel Embassy team.
		   
user.json :-
		     
		     {
				"user-sessions":1,
				"users": [{
				 "username":"bioexcel1",
				 "password": "password"
				},{
				 "username":"bioexcel2",
				 "password": "password"
				},{
				 "username":"bioexcel3",
				 "password": "password"
				}]
			 }
			 
deploy.json :-
		    
		    {
				"deployments": [
				{
				 "application_name": "NAFlex",
				 "launcher": "nfsclient",
				 "config_name": "",
				 "team_name": ""
				}
				]
			}
		   
Execute:-

            bioexcel-cli deploy
				
   3.Deploy `Jupyter Server Instance` application through ECP application launcher with a user who is not member of the team.
		   Get the JWT of the user account and copy the content to file called token.txt. 
		   Get the JWT of the team owner's and copy the content to file called owner.txt.
		   
user.json :-
		    
		     {
				"user-sessions":1,
				"users" : [{
				 "username":"",
				 "password":""
				}]
			 }
			 
deploy.json :-
		    
            {
                "deployments" : [
                {
                 "application_name": "Jupyter Server Instance",
                 "launcher": "ecpapplication",
                 "config_name": "Jupyter biobb_wf_md_setup",
                 "team_name": "BioExcel Embassy"
                }
                ]
            }
		   	
Execute:-
	 
	         bioexcel-cli –-token token.txt --owner owner.txt deploy
Once user added to team, you can execute the same without giving --owner argument.
		 
   4.Destroy some deployments by giving deployment references.
			
user.json :-
			
		     {
				"user-sessions":1,
				"users": [{
				 "username":"bioexcel1",
				 "password": "password"
				}]
			 }
			 
destroy.json :-
		
		    {
				"deployments": [
				{
				 "reference":"TSI1583323328233"
				},
				{
				"reference":"TSI1583323325989"
				},
				{
				"reference":"TSI1583323325989"
				}
				]
			}
			
Execute: 
	
    	   bioexcel-cli destroy
		 
