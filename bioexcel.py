#!/usr/bin/env python3

from __future__ import print_function
import time
import ecp
import sys
import argparse
import json
import threading
import yaml
import jwt


class BIEXCEL:
    users = []
    sessions = None
    bioexceltools = {}
    nfsclienttools = {}
    launcher = {}
    deployconf = {}
    destroyconf = {}
    nfsserver = None
    status = {}
    deploymentstatus = {}
    ownertoken = None
    jsondir = None

    def __init__(self):
        self.nfsserver = ""
        self.nfsremotedir = "/var/nfs"
        self.sessions = 1
        self.ownertoken = "owner.txt"
        self.jsondir = "json/"
        self.inputjson = self.jsondir+"config/input.json";

    def login(self, username, password, ecpcli):
        login = ecpcli.login(username, password)
        if "401" in login:
            print("Login failed! Invalid username or password given.")
            sys.exit(0)
        else:
            print("Login success!!")

    def check_shared_config(self, ecpcli):
        print("Checking shared configuration..")
        bioexcelconfig = False
        res = ecpcli.make_request('get', 'sharedconfig', '')
        resp = res.json()
        if '_embedded' in resp:
            for config in resp['_embedded']['configurationResourceList']:
                if config['name'] == "BioExcel CPMD license on Embassy Cloud":
                    bioexcelconfig = True
        if bioexcelconfig:
            print("Configurations shared with user.")
            return True
        else:
            print("Configuration not shared with user.")
            ecpowner = ecp.ECP()
            ecpowner.get_token(self.ownertoken)
            email = self.get_email(ecpcli)
            bioexcelconfig = self.join_team("BioExcel Embassy", email, ecpowner)
            if bioexcelconfig:
                print("Adding to team success !!")
                return True
            else:
                print("Adding to team failed !!")
                sys.exit(0)

    def get_email(self, ecpcli):
        token = ecpcli.get_session_token()
        decoded = jwt.decode(token, verify=False)
        email = decoded['email']
        return email

    def join_team(self, teamname, email, ecpowner):
        data = {"name": "" + teamname + "", "memberAccountEmails": ["" + email + ""]}
        datajson = json.dumps(data)
        response = ecpowner.make_request('create', 'jointeam', '', datajson)
        if response.status_code == 200:
            return True
        else:
            return False

    def get_users(self):
        datafh = open(self.jsondir+'user.json', 'r')
        data = datafh.read()
        datafh.close()
        userjson = json.loads(data)
        self.sessions = int(userjson['user-sessions'])
        self.users = userjson['users']

    def get_tools_config(self):
        datafh = open(self.inputjson, 'r')
        data = datafh.read()
        datafh.close()
        jsondata = json.loads(data)
        self.nfsserver = jsondata['nfs_server']
        self.nfsremotedir = jsondata['nfs_remote_folder']
        bioexcel = jsondata['bioexcel']
        for apps in bioexcel:
            self.bioexceltools[apps['application_name'] + "-url"] = apps['image_source_url']
            self.bioexceltools[apps['application_name'] + "-config"] = apps['configuration_name']
        nfsclient = jsondata['nfsclient']
        for apps in nfsclient:
            self.nfsclienttools[apps['application_name'] + "-url"] = apps['image_source_url']
            self.nfsclienttools[apps['application_name'] + "-config"] = apps['configuration_name']

    def get_launcher_data(self):
        file = self.jsondir+'launcher/bioexcel.json'
        datafh = open(file, 'r')
        data = datafh.read()
        self.launcher['bioexcel'] = json.loads(data)

        file = self.jsondir+'launcher/nfsclient.json'
        datafh = open(file, 'r')
        data = datafh.read()
        self.launcher['nfsclient'] = json.loads(data)

        file = self.jsondir+'launcher/ecpimage.json'
        datafh = open(file, 'r')
        data = datafh.read()
        datafh.close()
        self.launcher['ecpimage'] = json.loads(data)

        file = self.jsondir + 'launcher/ecpapplication.json'
        datafh = open(file, 'r')
        data = datafh.read()
        datafh.close()
        self.launcher['ecpapplication'] = json.loads(data)

    def get_deploy_config(self):
        datafh = open(self.jsondir+'deploy.json', 'r')
        data = datafh.read()
        datafh.close()
        jsondata = json.loads(data)
        self.deployConf = jsondata['deployments']

    def get_destroy_config(self):
        datafh = open(self.jsondir+'destroy.json', 'r')
        data = datafh.read()
        datafh.close()
        jsondata = json.loads(data)
        self.deployments = jsondata['deployments']

    def get_json_data(self, launcher, toolname, configname):
        jsonData = self.launcher[launcher]
        if launcher == 'bioexcel':
            inputs = [{"inputName": "application_name", "assignedValue": toolname},
                      {"inputName": "image_source_url", "assignedValue": self.bioexceltools.get(toolname + "-url")},
                      {"inputName": "image_disk_type", "assignedValue": "BioExcel_Embassy_VM"}]
            if configname == '':
                jsonData["configurationName"] = self.bioexceltools.get(toolname + "-config")
            else:
                jsonData["configurationName"] = configname
        elif launcher == 'nfsclient':
            inputs = [{"inputName": "nfs_server_host", "assignedValue": self.nfsserver},
                      {"inputName": "remote_folder", "assignedValue": self.nfsremotedir},
                      {"inputName": "application_name", "assignedValue": toolname}]
            if configname == '':
                jsonData["configurationName"] = self.nfsclienttools.get(toolname + "-config")
            else:
                jsonData["configurationName"] = configname
        elif launcher == 'ecpimage':
            inputs = [{"inputName": "application_name", "assignedValue": toolname}]
            jsonData["configurationName"] = configname
        else:
            jsonData["applicationName"] = toolname
            jsonData["configurationName"] = configname
            inputs = []

        jsondumps = json.dumps(inputs)
        inputjson = json.loads(jsondumps)
        jsonData["assignedInputs"] = inputjson
        return json.dumps(jsonData)

    def deploy(self, ecpcli, reqid):
        for dep in self.deployConf:
            toolname = dep['application_name']
            launcher = dep['launcher']
            configname = dep['config_name']
            teamname = dep['team_name']
            data = self.get_json_data(launcher, toolname, configname)
            print(yaml.safe_dump(data, indent=2, default_flow_style=False))
            if launcher == 'ecpapplication':
                response = ecpcli.make_request('create', 'deployment?teamName', teamname, data)
            else:
                response = ecpcli.make_request('create', 'deployment', '', data)
            start = time.time()
            res = response.json()
            try:
                reference = res['reference']
            except:
                print("Exception while creating deployment!")
                print("Response status : ", response.status_code)
                print("Response from server : ", res)
                return "NONE|CREATION_FAILED"
            print("Deployment process {0} started. Reference :- {1}".format(reqid, reference))
            print("Deployment logs : ")
            logexLen = 0
            while True:
                logs = ecpcli.make_request('get', 'logs', reference, '')
                logText = (logs.text).rstrip('\r\n')
                logTextLen = len(logText)
                logText1 = logText[logexLen:logTextLen].rstrip('\r\n')
                if len(logText1) > 0:
                    print("----Request ID {0} ; log for reference {1} ".format(reqid, reference))
                    print(logText1)
                logexLen = logTextLen
                if ('external_ip' in logText):
                    done = time.time()
                    elapsed = done - start
                    print("Request ID {0} Deployment [{1}] started Running!".format(reqid, reference))
                    self.deploymentstatus[reqid] = "{0} : RUNNING   :{1:5.4f}".format(reference, elapsed)
                    break
                elif ('error(s) occurred' in logText):
                    done = time.time()
                    elapsed = done - start
                    print("Request ID {0} ; Deployment [{1}] starting failed!".format(reqid, reference))
                    self.deploymentstatus[reqid] = "{0} : FAILED    :{1:5.4f}".format(reference, elapsed)
                    break
                else:
                    time.sleep(5)

    def destroy(self, reference, ecpcli):
        response = ecpcli.make_request('stop', 'deployment', reference, None)
        if response.status_code == 200:
            print("Destroy logs : ")
            logexLen = 0
            count = 0
            while True:
                logs = ecpcli.make_request('get', 'destroylogs', reference, '')
                logText = (logs.text).rstrip('\r\n')
                logTextLen = len(logText)
                logText1 = logText[logexLen:logTextLen].rstrip('\r\n')
                if len(logText1) > 0:
                    print(logText1)
                logexLen = logTextLen
                count += 1
                if ('Destroy complete' in logText):
                    return reference + "|DESTROYED"
                    break
                elif ('error(s) occurred' in logText):
                    return reference + "|FAILED"
                    break
                else:
                    if count == 60:
                        return reference + "|TIME_OUT"
                        break
                    else:
                        time.sleep(5)
        else:
            return reference + "|FAILED"

    def main(self, argv):
        parser = argparse.ArgumentParser(description='Bioexcel Cloud Portal e2e test Client')
        parser.add_argument('action', help='Action to perform : deploy/destroy')
        parser.add_argument('--token', help='File contains JWT identity token, Optional.')
        parser.add_argument('--json', help='directory contains all config jsons, Optional, '
                                               'it will look up "json" folder in current directory by default.')
        parser.add_argument('--owner', help='File contains "BioExcel Embassy" team owner account JWT ,'
                                                'it will look up "owner.txt" in current directory by default.')
        args = parser.parse_args()
        if args.owner is not None:
            self.ownertoken = args.owner
        if args.json is not None:
            self.jsondir = args.json+"/"
        self.get_users()
        if args.action == 'deploy':
            self.get_tools_config()
            self.get_deploy_config()
            self.get_launcher_data()
            if args.token is None:
                threads = list()
                usercount = 0
                for user in self.users:
                    ecpcli = ecp.ECP()
                    usercount += 1
                    self.login(user['username'], user['password'], ecpcli)
                    self.check_shared_config(ecpcli)
                    x = threading.Thread(target=self.deploy, args=(ecpcli, usercount), daemon=True)
                    threads.append(x)
                    x.start()
            else:
                ecpcli = ecp.ECP()
                ecpcli.get_token(args.token)
                self.check_shared_config(ecpcli)
                sessiontoken = ecpcli.get_session_token()
                threads = list()
                for i in range(self.sessions):
                    ecpclisession = ecp.ECP()
                    ecpclisession.set_token(sessiontoken)
                    x = threading.Thread(target=self.deploy, args=(ecpclisession, i), daemon=True)
                    threads.append(x)
                    x.start()
            threadcount = 0
            for index, thread in enumerate(threads):
                thread.join()
                threadcount += 1
                if threadcount == self.sessions:
                    print(" Results : ")
                    print("No    REFERENCE     STATUS      ELAPSED")
                    print(yaml.safe_dump(self.deploymentstatus, indent=2, default_flow_style=False))
        elif args.action == 'destroy':
            ecpcli = ecp.ECP()
            if args.token is None:
                self.login(self.users[0]['username'], self.users[0]['password'], ecpcli)
            else:
                ecpcli.get_token(args.token)
            self.get_destroy_config()
            count = 0
            for deployment in self.deployments:
                reference = deployment['reference']
                self.status[count] = self.destroy(reference, ecpcli)
                count += 1
            print("RESULT : ")
            print("---------------------------------------")
            print("-  REFERENCE           -    STATUS    -")
            print("---------------------------------------")
            for i in range(len(self.status)):
                statusspl = self.status[i].split("|")
                print("-  " + statusspl[0] + "   -    " + statusspl[1] + "  -")
                print("-                     -               -")
            print("---------------------------------------")
def run():
  """Run bioexcel cli"""
  bioexcel = BIEXCEL()
  sys.exit(bioexcel.main(sys.argv))

if __name__ == "__main__":
    bioexcel = BIEXCEL()
    bioexcel.main(sys.argv)
