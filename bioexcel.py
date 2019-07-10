#!/usr/bin/env python3

from __future__ import print_function
import time
import ecp
import sys
import argparse
import json
import threading
import yaml


class BIEXCEL:

    user = {}
    sessions = None
    bioexcelTools = {}
    nfsClientTools = {}
    launcher = {}
    deployConf = {}
    destroyConf = {}
    nfsServer =None
    status ={}
    deploymentStatus = {}

    def __init__(self):
        self.nfsServer = ""
        self.sessions = 1

    def login(self, username, password, ecp):
        login = ecp.login(username, password)
        if "401" in login:
          print("Login failed! Invalid username or password given.")
          sys.exit(0)
        else:
          print("Login success!!")

    def checkSharedConfig(self, ecp):
        print("Checking shared configuration..")
        member = False
        res = ecp.make_request('get', 'sharedConfig', '')
        resp = res.json()
        if '_embedded' in resp:
            for config in resp['_embedded']['configurationResourceList']:
                # print('- ' + config['name'] + ':')
                if config['name'] == "NFS client BioExcel chrmdn-mug":
                    member = True
                    break
                else:
                    continue
        if member:
            print("Configuration shared with user.")
        else:
            print("Configuration not shared with user.Please make sure to be member of the teams : ")
            print("BioExcel Embassy & NFS Server.")
            sys.exit(0)

    def getUser(self):
        datafh = open('json/user.json', 'r')
        data = datafh.read()
        datafh.close()
        userJson = json.loads(data)
        self.sessions = int(userJson['user-sessions'])
        self.user = userJson['user']

    def getToolsConfig(self):
        datafh = open('json/config.json', 'r')
        data = datafh.read()
        datafh.close()
        jsonData = json.loads(data)
        self.nfsServer = jsonData['nfs_server']
        bioexcel = jsonData['bioexcel']
        for apps in bioexcel:
            self.bioexcelTools[apps['application_name']+"-url"] = apps['image_source_url']
            self.bioexcelTools[apps['application_name'] + "-config"] = apps['configuration_name']
        nfsclient = jsonData['nfsclient']
        for apps in nfsclient:
            self.nfsClientTools[apps['application_name'] + "-url"] = apps['image_source_url']
            self.nfsClientTools[apps['application_name'] + "-config"] = apps['configuration_name']

    def getLauncherData(self):
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

    def getDeployConfig(self):
        datafh = open('json/deploy.json', 'r')
        data = datafh.read()
        datafh.close()
        jsonData = json.loads(data)
        self.deployConf = jsonData['tools']

    def getDestroyConfig(self):
        datafh = open('json/destroy.json', 'r')
        data = datafh.read()
        datafh.close()
        jsonData = json.loads(data)
        self.deployments = jsonData['deployments']

    def getJSONData(self, launcher, toolname):
        jsonData = self.launcher[launcher]
        if launcher == 'bioexcel':
            inputs = [{"inputName": "application_name", "assignedValue": toolname},
                      {"inputName": "image_source_url", "assignedValue": self.bioexcelTools.get(toolname + "-url")},
                      {"inputName": "image_disk_type", "assignedValue": "BioExcel_Embassy_VM"}]
            jsonData["configurationName"] = self.bioexcelTools.get(toolname + "-config")
        elif launcher == 'nfsclient':
            inputs = [{"inputName": "nfs_server_host", "assignedValue": self.nfsServer},
                      {"inputName": "application_name", "assignedValue": toolname}]
            jsonData["configurationName"] = self.nfsClientTools.get(toolname + "-config")
        else:
            inputs = [{"inputName": "disk_image_name", "assignedValue": toolname}]
        jsonDumps = json.dumps(inputs)
        inputJson = json.loads(jsonDumps)
        jsonData["assignedInputs"] = inputJson
        return json.dumps(jsonData)

    def deploy(self, ecpCli, reqID):
        for dep in self.deployConf:
            toolname = dep['tool_name']
            launcher = dep['launcher']
            data = self.getJSONData(launcher, toolname)
            #print(yaml.safe_dump(data, indent=2, default_flow_style=False))
            response = ecpCli.make_request('create', 'deployment', '', data)
            start = time.time()
            res = response.json()
            try:
                reference = res['reference']
            except:
                print("Exception while creating deployment!")
                return "NONE|CREATION_FAILED"
            print("Deployment process started. Reference :- ", reference)
            print("Deployment logs : ")
            logexLen = 0
            while True:
                logs = ecpCli.make_request('get', 'logs', reference, '')
                logText = (logs.text).rstrip('\r\n')
                logTextLen = len(logText)
                logText1 = logText[logexLen:logTextLen].rstrip('\r\n')
                if len(logText1) > 0:
                    print("----Request ID {0} ; log for reference {1} ".format(reqID, reference))
                    print(logText1)
                logexLen = logTextLen
                if('external_ip' in logText):
                    done = time.time()
                    elapsed = done - start
                    print("Request ID {0} Deployment [{1}] started Running!".format(reqID, reference))
                    self.deploymentStatus[reqID] = "{0} : RUNNING   :{1:5.4f}".format(reference, elapsed)
                    break
                elif('error(s) occurred' in logText):
                    done = time.time()
                    elapsed = done - start
                    print("Request ID {0} ; Deployment [{1}] starting failed!".format(reqID, reference))
                    self.deploymentStatus[reqID] = "{0} : FAILED    :{1:5.4f}".format(reference, elapsed)
                    break
                else:
                    time.sleep(5)

    def destroy(self, reference, ecpCli):
        response = ecpCli.make_request('stop', 'deployment', reference, None)
        if response.status_code == 200:
            print("Destroy logs : ")
            logexLen = 0
            count = 0
            while True:
                logs = ecpCli.make_request('get', 'destroylogs', reference, '')
                logText = (logs.text).rstrip('\r\n')
                logTextLen = len(logText)
                logText1 = logText[logexLen:logTextLen].rstrip('\r\n')
                if len(logText1) > 0:
                    print(logText1)
                logexLen = logTextLen
                count += 1
                if('Destroy complete' in logText):
                    return reference+"|DESTROYED"
                    break
                elif('error(s) occurred' in logText):
                    return reference+"|FAILED"
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
        parser.add_argument('--token', help='File containing JWT identity token, is sourced from ECP_TOKEN env var by default')
        args = parser.parse_args()
        self.getUser()
        if args.action == 'deploy':
            self.getToolsConfig()
            self.getDeployConfig()
            self.getLauncherData()
            threads = list()
            for i in range(self.sessions):
                ecpCli = ecp.ECP()
                if args.token == '':
                    self.login(self.user['username'], self.user['password'], ecpCli)
                else:
                    ecpCli.get_token(args.token)
                self.checkSharedConfig(ecpCli)
                x = threading.Thread(target=self.deploy, args=(ecpCli, i), daemon=True)
                threads.append(x)
                x.start()
            threadcount = 0
            for index, thread in enumerate(threads):
                thread.join()
                threadcount += 1
                if threadcount == self.sessions:
                    print(" Results : ")
                    print("No    REFERENCE     STATUS      ELAPSED")
                    print(yaml.safe_dump(self.deploymentStatus, indent=2, default_flow_style=False))
        elif args.action == 'destroy':
            ecpCli = ecp.ECP()
            if args.token == '':
                self.login(self.user['username'], self.user['password'], ecpCli)
            else:
                ecpCli.get_token(args.token)
            self.getDestroyConfig()
            count = 0
            for deployment in self.deployments:
                reference = deployment['reference']
                self.status[count] = self.destroy(reference, ecpCli)
                count += 1
            print("RESULT : ")
            print("---------------------------------------")
            print("-  REFERENCE           -    STATUS    -")
            print("---------------------------------------")
            for i in range(len(self.status)):
                statusSplit = self.status[i].split("|")
                print("-  " + statusSplit[0] + "   -    " + statusSplit[1] + "  -")
                print("-                     -               -")
            print("---------------------------------------")

if __name__ == "__main__":
    bioexcel = BIEXCEL()
    bioexcel.main()
