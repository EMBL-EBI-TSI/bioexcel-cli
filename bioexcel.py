#!/usr/bin/env python

from __future__ import print_function
import time
from ecpcli import ecp
import sys
import argparse
import json

class BIEXCEL:
    bioexcel = {}
    nfsimage = {}
    nfsServer =None
    nfsRemoteFolder =None
    status ={}
    ecp = ecp.ECP()

    def __init__(self):
        self.nfsServer = ""
        self.nfsExportFolder = "/var/nfs"

    def login(self, username, password):

        login = self.ecp.login(username, password)
        if "401" in login:
          print("Login failed! Invalid username or password given.")
          sys.exit(0)
        else:
          print("Login success!!")

    def checkShared(self):
        print("Checking shared configuration..")
        member = False
        res = self.ecp.make_request('get', 'sharedConfig', '')
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

    def deploy(self, data):
        response = self.ecp.make_request('create', 'deployment', '', data)
        res = response.json()
        try:
            reference = res['reference']
        except:
            print("Exception while creating deployment!")
            return "NONE|CREATION_FAILED"
        print("Deployment process started. Reference :- ", reference)
        print("Deployment logs : ")
        logex = ""
        count = 0
        while True:
            logs = self.ecp.make_request('get', 'logs', reference, '')
            logText = (logs.text).rstrip()
            logexLen = len(logex)
            logTextLen = len(logText)
            logText1 = logText[logexLen:logTextLen]
            print(logText1)
            logex = logText1
            count += 1
            if('external_ip' in logex):
                return reference+"|RUNNING"
                break
            elif('error(s) occurred' in logex):
                return reference+"|FAILED"
                break
            else:
                if count == 60:
                    return reference + "|TIME_OUT"
                    break
                else:
                    time.sleep(5)

    def destroy(self, reference):
        response = self.ecp.make_request('stop', 'deployment', reference, None)
        if response.status_code == 200:
            print("Destroy logs : ")
            logex = ""
            count = 0
            while True:
                logs = self.ecp.make_request('get', 'destroylogs', reference, '')
                logText = (logs.text).rstrip()
                logexLen = len(logex)
                logTextLen = len(logText)
                logText1 = logText[logexLen:logTextLen]
                print(logText1)
                logex = logText1
                count += 1
                if('Destroy complete' in logex):
                    return reference+"|DESTROYED"
                    break
                elif('error(s) occurred' in logex):
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

    def bioexcelInputs(self, toolname):
        imageUrl = self.bioexcel.get(toolname + "-url")
        inputs = [{"inputName": "application_name", "assignedValue": toolname},
                  {"inputName": "image_source_url", "assignedValue": imageUrl},
                  {"inputName": "image_disk_type", "assignedValue": "BioExcel_Embassy_VM"}]
        return inputs

    def nfsInputs(self, toolname):
        imageUrl = self.nfsimage.get(toolname + "-url")
        inputs = [{"inputName": "nfs_server_host", "assignedValue": self.nfsServer},
                  #{"inputName": "image_source_url", "assignedValue": imageUrl},
                  #{"inputName": "application_name", "assignedValue": toolname},
                  #{"inputName": "image_disk_type", "assignedValue": "BioExcel_Embassy_NFS_Image"},
                  {"inputName": "remote_folder", "assignedValue": self.nfsExportFolder}
                  ]
        return inputs

    def ecpImageInputs(self, toolname):
        inputs = [{"inputName": "disk_image_name", "assignedValue": toolname}]
        return inputs

    def getLogin(self):
        datafh = open('json/user.json', 'r')
        data = datafh.read()
        datafh.close()
        userData = (json.loads(data))['users']
        return userData

    def getConfig(self):
        datafh = open('json/config.json', 'r')
        data = datafh.read()
        datafh.close()
        jsonData = json.loads(data)
        self.nfsServer = jsonData['nfs_server']
        self.nfsRemoteFolder = jsonData['nfs_remote_folder']
        bioexcel = jsonData['bioexcel']
        for apps in bioexcel:
            self.bioexcel[apps['application_name']+"-url"] = apps['image_source_url']
        nfsclient = jsonData['nfsclient']
        for apps in nfsclient:
            self.nfsimage[apps['application_name'] + "-url"] = apps['image_source_url']

    def getDeploy(self):
        datafh = open('json/deploy.json', 'r')
        data = datafh.read()
        datafh.close()
        jsonData = json.loads(data)
        return jsonData

    def getDestroy(self):
        datafh = open('json/destroy.json', 'r')
        data = datafh.read()
        datafh.close()
        jsonData = json.loads(data)
        return jsonData['deployments']

    def getData(self, launcher, toolname):
        file = 'json/launcher/'+launcher+'.json'
        datafh = open(file, 'r')
        data = datafh.read()
        datafh.close()
        jsonData = json.loads(data)
        if launcher == 'bioexcel':
            inputs = self.bioexcelInputs(toolname)
        elif launcher == 'nfsclient':
            inputs = self.nfsInputs(toolname)
        else:
            inputs = self.ecpImageInputs(toolname)
        jsonDumps = json.dumps(inputs)
        inputJson = json.loads(jsonDumps)
        jsonData["assignedInputs"] = inputJson
        jsonString = json.dumps(jsonData)
        return jsonString

    def main(self):
        parser = argparse.ArgumentParser(description='Bioexcel Cloud Portal Test Client')
        parser.add_argument('action', help='Action to perform : deploy/destroy')
        parser.add_argument('--token', help='File containing JWT identity token, is sourced from ECP_TOKEN env var by default')
        args = parser.parse_args()
        self.getConfig()
        if args.action == 'deploy':
            if args.token == '':
                users = self.getLogin()
                self.login(users[0]['username'], users[0]['password'])
            else:
                self.ecp.get_token(args.token)
            self.checkShared()
            deploy = self.getDeploy()
            deployConf = deploy['tools']
            count = 0
            for dep in deployConf:
                toolName = dep['tool_name']
                launcher = dep['launcher']
                data = self.getData(launcher, toolName)
                self.status[count] = self.deploy(data)
                count += 1
        else:
            if args.token == '':
                users = self.getLogin()
                self.login(users[0]['username'], users[0]['password'])
            else:
                self.ecp.get_token(args.token)
            deployments = self.getDestroy()
            count = 0
            for deployment in deployments:
                reference = deployment['reference']
                self.status[count] = self.destroy(reference)
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
