# Bioexcel portal client - e2e testing tool
Bioexcel portal client is a command line tool for end to end testing of Bioexcel portal. 
The objective is to test performance of Bioexcel portal backend which is actually EBI cloud portal API server.
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

`json` Directory contains necessary json files for running of Bioexcel portal client.

`deploy.json` Describes What & how many applications should be deployed through which launcher.
              We have four type of launchers for Bioexcel portal's deployment of an application.
				
				bioexcel, nfsclient, ecpimage, ecpapplication

JSON structure:
  
			    {   "deployments" : [{   
			                "application_name":"NAFlex",
					"launcher":"bioexcel",
					"config_name":"bioexcel config",
					"team_name":"Bioexcel"
			    }]}
								 
application - biotools application to be deployed

launcher - one of the four launchers
  
config_name - configuration to be used for deployment
  
team_name - team in which application is shared
  
we can provide n number of deployment object inside deployments array block. 
Deployment will be done one by one.


`destroy.json` Describe what are all the deployments to be destroyed.
      	      
JSON structure:

			  {"deployments":[
			  {"reference":"TSI1583323328233"}
			  ]}
		  
reference - deployment reference to be destroyed
		
we can provide n number of reference object inside deployments array block.

`user.json` Describes user accounts to be used and number concurrent sessions to be created 
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
			  
user-sessions - number of concurrent user sessions to be created from the account of JWT token specified.
                this attributed will be ignored if --token argument is not specified.
						  
username - username for session creation through HTTP login 

password - password for session creation through HTTP login

You can specify n number of user objects inside users array. 
This type of session creation will happen only if --token is not specified.	  
			  

#### Possible application and launcher mappings to use with `deploy.json`
        
		Application name       		Launcher
		  PyMDSetup 			bioexcel
		  Chromatin Dynamics		bioexcel
		  COMPSs			bioexcel
		  NAFlex			nfsclient
		  PyMDSetup			nfsclient
		  Chromatin Dynamics		nfsclient
		  CWL VM environment		ecpapplication
		  Jupyter Server Instance 	ecpapplication
		  
For `bioexcel` and `nfsclient` launcher `team_name` is not required. `config_name` 
is used if specified.It will use default value if `config_name` is not specified.
 
For `ecpimage` launcher `team_name` is not required. `application_name` and `config_name` 
are mandatorily specified on deploy.json
  
For config_name application_name, config_name and team_name are mandatory and must be specified 
in deploy.json.

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
		 