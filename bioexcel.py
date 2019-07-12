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
    user = {}
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

    def __init__(self):
        self.nfsserver = ""
        self.sessions = 1
        self.ownertoken = "token/owner.txt"

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
        nfsconfig = False
        res = ecpcli.make_request('get', 'sharedconfig', '')
        resp = res.json()
        if '_embedded' in resp:
            for config in resp['_embedded']['configurationResourceList']:
                if config['name'] == "NFS client BioExcel chrmdn-mug":
                    bioexcelconfig = True
                if config['name'] == "NFS server CRUK":
                    nfsconfig = True
        if bioexcelconfig & nfsconfig:
            print("Configurations shared with user.")
            return True
        else:
            print("Configuration not shared with user.")
            if not bioexcelconfig:
                ecpowner = ecp.ECP()
                ecpowner.get_token(self.ownertoken)
                email = self.get_email(ecpcli)
                bioexcelconfig = self.join_team("BioExcel Embassy", email, ecpowner)
            if not nfsconfig:
                ecpowner = ecp.ECP()
                ecpowner.get_token(self.ownertoken)
                email = self.get_email(ecpcli)
                nfsconfig = self.join_team("NFS Server", email, ecpowner)

        if bioexcelconfig & nfsconfig:
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

    def get_user(self):
        datafh = open('json/user.json', 'r')
        data = datafh.read()
        datafh.close()
        userjson = json.loads(data)
        self.sessions = int(userjson['user-sessions'])
        self.user = userjson['user']

    def get_tools_config(self):
        datafh = open('json/config.json', 'r')
        data = datafh.read()
        datafh.close()
        jsondata = json.loads(data)
        self.nfsserver = jsondata['nfs_server']
        bioexcel = jsondata['bioexcel']
        for apps in bioexcel:
            self.bioexceltools[apps['application_name'] + "-url"] = apps['image_source_url']
            self.bioexceltools[apps['application_name'] + "-config"] = apps['configuration_name']
        nfsclient = jsondata['nfsclient']
        for apps in nfsclient:
            self.nfsclienttools[apps['application_name'] + "-url"] = apps['image_source_url']
            self.nfsclienttools[apps['application_name'] + "-config"] = apps['configuration_name']

    def get_launcher_data(self):
        file = 'json/launcher/bioexcel.json'
        datafh = open(file, 'r')
        data = datafh.read()
        self.launcher['bioexcel'] = json.loads(data)

        file = 'json/launcher/nfsclient.json'
        datafh = open(file, 'r')
        data = datafh.read()
        self.launcher['nfsclient'] = json.loads(data)

        file = 'json/launcher/ecpimage.json'
        datafh = open(file, 'r')
        data = datafh.read()
        datafh.close()
        self.launcher['ecpimage'] = json.loads(data)

    def get_deploy_config(self):
        datafh = open('json/deploy.json', 'r')
        data = datafh.read()
        datafh.close()
        jsondata = json.loads(data)
        self.deployConf = jsondata['tools']

    def get_destroy_config(self):
        datafh = open('json/destroy.json', 'r')
        data = datafh.read()
        datafh.close()
        jsondata = json.loads(data)
        self.deployments = jsondata['deployments']

    def get_json_data(self, launcher, toolname):
        jsonData = self.launcher[launcher]
        if launcher == 'bioexcel':
            inputs = [{"inputName": "application_name", "assignedValue": toolname},
                      {"inputName": "image_source_url", "assignedValue": self.bioexceltools.get(toolname + "-url")},
                      {"inputName": "image_disk_type", "assignedValue": "BioExcel_Embassy_VM"}]
            jsonData["configurationName"] = self.bioexceltools.get(toolname + "-config")
        elif launcher == 'nfsclient':
            inputs = [{"inputName": "nfs_server_host", "assignedValue": self.nfsServer},
                      {"inputName": "application_name", "assignedValue": toolname}]
            jsonData["configurationName"] = self.nfsClienttools.get(toolname + "-config")
        else:
            inputs = [{"inputName": "disk_image_name", "assignedValue": toolname}]
        jsondumps = json.dumps(inputs)
        inputjson = json.loads(jsondumps)
        jsonData["assignedInputs"] = inputjson
        return json.dumps(jsonData)

    def deploy(self, ecpcli, reqid):
        for dep in self.deployConf:
            toolname = dep['tool_name']
            launcher = dep['launcher']
            data = self.get_json_data(launcher, toolname)
            # print(yaml.safe_dump(data, indent=2, default_flow_style=False))
            response = ecpcli.make_request('create', 'deployment', '', data)
            start = time.time()
            res = response.json()
            try:
                reference = res['reference']
            except:
                print("Exception while creating deployment!")
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

    def main(self):
        parser = argparse.ArgumentParser(description='Bioexcel Cloud Portal Test Client')
        parser.add_argument('action', help='Action to perform : deploy/destroy')
        parser.add_argument('--token',
                            help='File containing JWT identity token, is sourced from ECP_TOKEN env var by default')
        args = parser.parse_args()
        self.get_user()
        if args.action == 'deploy':
            self.get_tools_config()
            self.get_deploy_config()
            self.get_launcher_data()
            ecpcli = ecp.ECP()
            if args.token is None:
                self.login(self.user['username'], self.user['password'], ecpcli)
            else:
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
            if args.token == '':
                self.login(self.user['username'], self.user['password'], ecpcli)
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


if __name__ == "__main__":
    bioexcel = BIEXCEL()
    bioexcel.main()
