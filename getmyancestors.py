#!/usr/bin/env python3
"""
   getmyancestors.py - Retrieve GEDCOM data from FamilySearch Tree
   Copyright (C) 2014-2016 Giulio Genovese (giulio.genovese@gmail.com)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

   Written by Giulio Genovese <giulio.genovese@gmail.com>
"""

from __future__ import print_function
import sys, argparse, getpass, time

try:
    import requests
except ImportError:
    sys.stderr.write('You need to install the requests module first\n')
    sys.stderr.write('(run this in your terminal: "python3 -m pip install requests" or "python3 -m pip install --user requests")\n')
    exit(2)

# FamilySearch session class
class Session:
    def __init__(self, username, password, verbose = False, logfile = sys.stderr, timeout = 60):
        self.username = username
        self.password = password
        self.verbose = verbose
        self.logfile = logfile
        self.timeout = timeout
        self.login()

    # retrieve FamilySearch session ID (https://familysearch.org/developers/docs/guides/oauth2)
    def login(self):
        while True:
            try:
                url = 'https://familysearch.org/auth/familysearch/login'
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Downloading: ' + url + '\n')
                r = requests.get(url, params = {'ldsauth': False}, allow_redirects = False)

                url = r.headers['Location']
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Downloading: ' + url + '\n')
                r = requests.get(url, allow_redirects = False)
                idx = r.text.index('name="params" value="')
                span = r.text[idx+21:].index('"')
                params = r.text[idx+21:idx+21+span]

                url = 'https://ident.familysearch.org/cis-web/oauth2/v3/authorization'
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Downloading: ' + url + '\n')
                r = requests.post(url, data = {'params': params, 'userName': self.username, 'password': self.password}, allow_redirects = False)

                if 'The username or password was incorrect' in r.text:
                    if self.verbose:
                        self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: The username or password was incorrect\n')
                    exit()

                if 'Invalid Oauth2 Request' in r.text:
                    if self.verbose:
                        self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Invalid Oauth2 Request\n')
                    time.sleep(self.timeout)
                    continue

                url = r.headers['Location']
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Downloading: ' + url + '\n')
                r = requests.get(url, allow_redirects = False)
                self.fssessionid = r.cookies['fssessionid']
            except requests.exceptions.ReadTimeout:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Read timed out\n')
                continue
            except requests.exceptions.ConnectionError:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Connection aborted\n')
                time.sleep(self.timeout)
                continue
            except requests.exceptions.HTTPError:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: HTTPError\n')
                time.sleep(self.timeout)
                continue
            except KeyError:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: KeyError\n')
                time.sleep(self.timeout)
                continue
            except ValueError:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: ValueError\n')
                time.sleep(self.timeout)
                continue
            if self.verbose:
                self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: FamilySearch session id: ' + self.fssessionid + '\n')
            return

    # retrieve FamilySearch developer key (wget -O- --max-redirect 0 https://familysearch.org/auth/familysearch/login?ldsauth=false)
    def get_key(self):
        url = 'https://familysearch.org/auth/familysearch/login'
        while True:
            if self.verbose:
                self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Downloading: ' + url + '\n')
            try:
                r = requests.get(url, params = {'ldsauth': False}, allow_redirects = False, timeout = self.timeout)
                location = r.headers['Location']
                idx = location.index('client_id=')
                key = location[idx+10:idx+49]
            except ValueError:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: FamilySearch developer key not found\n')
                time.sleep(self.timeout)
                continue
            if self.verbose:
                self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: FamilySearch developer key: ' + key + '\n')
            return key

    # retrieve FamilySearch session ID (https://familysearch.org/developers/docs/guides/oauth1/login)
    def old_login(self, oldmethod = False):
        url = 'https://api.familysearch.org/identity/v2/login'
        data = {'key' : self.key, 'username' : self.username, 'password' : self.password}
        while True:
            if self.verbose:
                self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Downloading: ' + url + '\n')
            try:
                r = requests.post(url, data, timeout = self.timeout)
            except requests.exceptions.ReadTimeout:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Read timed out\n')
                continue
            except requests.exceptions.ConnectionError:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Connection aborted\n')
                time.sleep(self.timeout)
                continue
            if self.verbose:
                self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Status code: ' + str(r.status_code) + '\n')
            if r.status_code == 401:
                self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Login failure\n')
                raise Exception('Login failure')
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: HTTPError\n')
                time.sleep(self.timeout)
                continue
            self.fssessionid = r.cookies['fssessionid']
            if self.verbose:
                self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: FamilySearch session id: ' + self.fssessionid + '\n')
            return

    # retrieve JSON structure from FamilySearch URL
    def get_url(self, url):
        while True:
            try:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Downloading: ' + url + '\n')
                # r = requests.get(url, cookies = { 's_vi': self.s_vi, 'fssessionid' : self.fssessionid }, timeout = self.timeout)
                r = requests.get(url, cookies = { 'fssessionid' : self.fssessionid }, timeout = self.timeout)
            except requests.exceptions.ReadTimeout:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Read timed out\n')
                continue
            except requests.exceptions.ConnectionError:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Connection aborted\n')
                time.sleep(self.timeout)
                continue
            if self.verbose:
                self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: Status code: ' + str(r.status_code) + '\n')
            if r.status_code == 204 or r.status_code == 410:
                return None
            if r.status_code == 401:
                self.login()
                continue
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                if self.verbose:
                    self.logfile.write('[' + time.strftime("%Y-%m-%d %H:%M:%S") + ']: HTTPError\n')
                time.sleep(self.timeout)
                continue
            return r.json()
    
    # retrieve FamilySearch current user ID
    def get_userid(self):
        url = 'https://familysearch.org/platform/users/current.json'
        data = self.get_url(url)
        return data['users'][0]['personId'] if data else None



# GEDCOM individual class
class Indi:

    counter = 0

    # initialize individual
    def __init__(self, fid = None, fs = None, num = None):
        if num:
            self.num = num
        else:
            Indi.counter += 1
            self.num = Indi.counter
        self.fid = fid
        self.famc_fid = set()
        self.fams_fid = set()
        self.famc_num = set()
        self.fams_num = set()
        self.given = ''
        self.surname = 'Unknown'
        self.gender = self.birtdate = self.birtplac = self.deatdate = self.deatplac = None
        self.chrdate = self.chrplac = self.buridate = self.buriplac = None
        if fid and fs:
            url = 'https://familysearch.org/platform/tree/persons/' + self.fid + '.json'
            data = fs.get_url(url)
            if data:
                x = data['persons'][0]
                if x['names'] and 'parts' in x['names'][0]['nameForms'][0]:
                    for y in x['names'][0]['nameForms'][0]['parts']:
                        if y['type'] == u'http://gedcomx.org/Given':
                            self.given = y['value']
                        if y['type'] == u'http://gedcomx.org/Surname':
                            self.surname = y['value']
                if 'gender' in x:
                    if x['gender']['type'] == "http://gedcomx.org/Male":
                        self.gender = "M"
                    elif x['gender']['type'] == "http://gedcomx.org/Female":
                        self.gender = "F"
                else:
                    self.gender = None
                for y in x['facts']:
                    if y['type'] == u'http://gedcomx.org/Birth':
                        self.birtdate = y['date']['original'] if 'date' in y and 'original' in y['date'] else None
                        self.birtplac = y['place']['original'] if 'place' in y and 'original' in y['place'] else None
                    if y['type'] == u'http://gedcomx.org/Christening':
                        self.chrdate = y['date']['original'] if 'date' in y and 'original' in y['date'] else None
                        self.chrplac = y['place']['original'] if 'place' in y and 'original' in y['place'] else None
                    if y['type'] == u'http://gedcomx.org/Death':
                        self.deatdate = y['date']['original'] if 'date' in y and 'original' in y['date'] else None
                        self.deatplac = y['place']['original'] if 'place' in y and 'original' in y['place'] else None
                    if y['type'] == u'http://gedcomx.org/Burial':
                        self.buridate = y['date']['original'] if 'date' in y and 'original' in y['date'] else None
                        self.buriplac = y['place']['original'] if 'place' in y and 'original' in y['place'] else None
        self.parents = None
        self.children = None
        self.spouses = None

    # add a fams to the individual
    def add_fams(self, fams):
        if not fams in self.fams_fid:
            self.fams_fid.add(fams)

    # add a famc to the individual
    def add_famc(self, famc):
        if not famc in self.famc_fid:
            self.famc_fid.add(famc)

    # retrieve parents
    def get_parents(self, fs):
        if not self.parents:
            url = 'https://familysearch.org/platform/tree/persons/' + self.fid + '/parents.json'
            data = fs.get_url(url)
            if data:
                x = data['childAndParentsRelationships'][0]
                self.parents = (x['father']['resourceId'] if 'father' in x else None,
                                x['mother']['resourceId'] if 'mother' in x else None)
            else:
                self.parents = (None, None)
        return self.parents

    # retrieve children relationships
    def get_children(self, fs):
        if not self.children:
            url = 'https://familysearch.org/platform/tree/persons/' + self.fid + '/children.json'
            data = fs.get_url(url)
            if data:
                self.children = [(x['father']['resourceId'] if 'father' in x else None,
                                  x['mother']['resourceId'] if 'mother' in x else None,
                                  x['child']['resourceId']) for x in data['childAndParentsRelationships']]
        return self.children

    # retrieve spouse relationships
    def get_spouses(self, fs):
        if not self.spouses:
            url = 'https://familysearch.org/platform/tree/persons/' + self.fid + '/spouses.json'
            data = fs.get_url(url)
            if data and 'relationships' in data:
                self.spouses = [(x['person1']['resourceId'], x['person2']['resourceId'], x['id']) for x in data['relationships']]
        return self.spouses

    # print individual information in GEDCOM format
    def print(self, file = sys.stdout):
        file.write('0 @I' + str(self.num) + '@ INDI\n')
        file.write('1 NAME ' + self.given + ' /' + self.surname + '/\n')
        if self.gender:
            file.write('1 SEX ' + self.gender + '\n')
        if self.birtdate or self.birtplac:
            file.write('1 BIRT\n')
            if self.birtdate:
                file.write('2 DATE ' + self.birtdate + '\n')
            if self.birtplac:
                file.write('2 PLAC ' + self.birtplac + '\n')
        if self.chrdate or self.chrplac:
            file.write('1 CHR\n')
            if self.chrdate:
                file.write('2 DATE ' + self.chrdate + '\n')
            if self.chrplac:
                file.write('2 PLAC ' + self.chrplac + '\n')
        if self.deatdate or self.deatplac:
            file.write('1 DEAT\n')
            if self.deatdate:
                file.write('2 DATE ' + self.deatdate + '\n')
            if self.deatplac:
                file.write('2 PLAC ' + self.deatplac + '\n')
        if self.buridate or self.buriplac:
            file.write('1 BURI\n')
            if self.buridate:
                file.write('2 DATE ' + self.buridate + '\n')
            if self.buriplac:
                file.write('2 PLAC ' + self.buriplac + '\n')
        for num in self.fams_num:
            file.write('1 FAMS @F' + str(num) + '@\n')
        for num in self.famc_num:
            file.write('1 FAMC @F' + str(num) + '@\n')
        file.write('1 _FSFTID ' + self.fid + '\n')



# GEDCOM family class
class Fam:
    counter = 0

    # initialize family
    def __init__(self, husb = None, wife = None, num = None):
        if num:
            self.num = num
        else:
            Fam.counter += 1
            self.num = Fam.counter
        self.husb_fid = husb if husb else None
        self.wife_fid = wife if wife else None
        self.husb_num = self.wife_num = self.fid = self.marrdate = self.marrplac = None
        self.chil_fid = set()
        self.chil_num = set()

    # add a child to the family
    def add_child(self, child):
        if not child in self.chil_fid:
            self.chil_fid.add(child)

    # retrieve and add marriage information
    def add_marriage(self, fs, fid):
        if not self.fid:
            self.fid = fid
            url = 'https://familysearch.org/platform/tree/couple-relationships/' + self.fid + '.json'
            data = fs.get_url(url)
            if data and 'facts' in data['relationships'][0]:
                x = data['relationships'][0]['facts'][0]
                self.marrdate = x['date']['original'] if 'date' in x and 'original' in x['date'] else None
                self.marrplac = x['place']['original'] if 'place' in x and 'original' in x['place'] else None
            else:
                self.marrdate = self.marrplac = None

    # print family information in GEDCOM format
    def print(self, file = sys.stdout):
        file.write('0 @F' + str(self.num) + '@ FAM\n')
        if self.husb_num:
            file.write('1 HUSB @I' + str(self.husb_num) + '@\n')
        if self.wife_num:
            file.write('1 WIFE @I' + str(self.wife_num) + '@\n')
        for num in self.chil_num:
            file.write('1 CHIL @I' + str(num) + '@\n')
        if self.marrdate or self.marrplac:
            file.write('1 MARR\n')
            if self.marrdate:
                file.write('2 DATE ' + self.marrdate + '\n')
            if self.marrplac:
                file.write('2 PLAC ' + self.marrplac + '\n')
        if self.fid:
            file.write('1 _FSFTID ' + self.fid + '\n')



# family tree class
class Tree:
    def __init__(self, fs = None):
        self.fs = fs
        self.indi = dict()
        self.fam = dict()

    # add individual to the family tree
    def add_indi(self, fid):
        if fid and not fid in self.indi:
            self.indi[fid] = Indi(fid, self.fs)

    # add family to the family tree
    def add_fam(self, father, mother):
        if not (father, mother) in self.fam:
            self.fam[(father, mother)] = Fam(father, mother)

    # add a children relationship (possibly incomplete) to the family tree
    def add_trio(self, father, mother, child):
        self.add_indi(father)
        self.add_indi(mother)
        self.add_indi(child)
        if father:
            self.indi[father].add_fams((father, mother))
        if mother:
            self.indi[mother].add_fams((father, mother))
        self.indi[child].add_famc((father, mother))
        self.add_fam(father, mother)
        self.fam[(father, mother)].add_child(child)

    # retrieve and add parents relationships
    def add_parents(self, fid):
        father, mother = self.indi[fid].get_parents(self.fs)
        if father or mother:
            self.add_trio(father, mother, fid)
        return filter(None, (father, mother))

    # retrieve and add spouse relationships
    def add_spouses(self, fid):
        rels = self.indi[fid].get_spouses(self.fs)
        if rels:
            for father, mother, relfid in rels:
                self.add_indi(father)
                self.add_indi(mother)
                self.indi[father].add_fams((father, mother))
                self.indi[mother].add_fams((father, mother))
                self.add_fam(father, mother)
                self.fam[(father, mother)].add_marriage(self.fs, relfid)

    # retrieve and add children relationships
    def add_children(self, fid):
        children = list()
        rels = self.indi[fid].get_children(self.fs)
        if rels:
            for father, mother, child in rels:
                self.add_trio(father, mother, child)
                children.append(child)
        return children

    def reset_num(self):
        for husb, wife in self.fam:
            self.fam[(husb, wife)].husb_num = self.indi[husb].num if husb else None
            self.fam[(husb, wife)].wife_num = self.indi[wife].num if wife else None
            self.fam[(husb, wife)].chil_num = set([self.indi[chil].num for chil in self.fam[(husb, wife)].chil_fid])
        for fid in self.indi:
            self.indi[fid].famc_num = set([self.fam[(husb, wife)].num for husb, wife in self.indi[fid].famc_fid])
            self.indi[fid].fams_num = set([self.fam[(husb, wife)].num for husb, wife in self.indi[fid].fams_fid])

    # print GEDCOM file
    def print(self, file = sys.stdout):
        file.write('0 HEAD\n')
        file.write('1 CHAR UTF-8\n')
        file.write('1 GEDC\n')
        file.write('2 VERS 5.5\n')
        file.write('2 FORM LINEAGE-LINKED\n')
        for fid in sorted(self.indi, key = lambda x: self.indi.__getitem__(x).num):
            self.indi[fid].print(file)
        for husb, wife in sorted(self.fam, key = lambda x: self.fam.__getitem__(x).num):
            self.fam[(husb, wife)].print(file)
        file.write('0 TRLR\n')
        
class Defaults:
    def __init__(self):
        self.num_gen_ascend = 4
        self.num_gen_descend = 0
        self.add_spouses_couples_info = False
        self.verbose = False
        self.timeout_seconds = 60
        self.gedcom_output_file = sys.stdout
        self.log_output_file = sys.stderr
        
class CLI:
    def __init__(self):
        self.defaults = Defaults()
        self.create_parser()
        self.extract_cli_arguments()
        self.get_username()
        self.get_password()
        self.store_run_parameters()
        
    def create_parser(self):
        self.parser = argparse.ArgumentParser(description = 
            'Retrieve GEDCOM data from FamilySearch Tree (4 Jul 2016)', 
            add_help = False, 
            usage = 'getmyancestors.py -u username -p password [options]')
        self.parser.add_argument('-u', metavar = '<STR>', type = str, 
                            help = 'FamilySearch username')
        self.parser.add_argument('-p', metavar = '<STR>', type = str, 
                            help = 'FamilySearch password')
        self.parser.add_argument('-i', metavar = '<STR>', nargs='+', 
                            type = str, 
                            help = ('List of individual FamilySearch IDs for '
                                    'whom to retrieve ancestors'))
        self.parser.add_argument('-a', metavar = '<INT>', type = int, 
                            default = self.defaults.num_gen_ascend, 
                            help = 'Number of generations to ascend [4]')
        self.parser.add_argument('-d', metavar = '<INT>', type = int, 
                            default = self.defaults.num_gen_descend, 
                            help = 'Number of generations to descend [0]')
        self.parser.add_argument('-m', action = "store_true", 
                            default = self.defaults.add_spouses_couples_info, 
                            help = ('Add spouses and '
                                    'couples information [False]'))
        self.parser.add_argument("-v", action = "store_true", 
                            default = self.defaults.verbose, 
                            help = "Increase output verbosity [False]")
        self.parser.add_argument('-t', metavar = '<INT>', type = int, 
                            default = self.defaults.timeout_seconds, 
                            help = 'Timeout in seconds [60]')
        try:
            self.parser.add_argument('-o', metavar = '<FILE>', 
                type = argparse.FileType('w', encoding = 'UTF-8'), 
                default = self.defaults.gedcom_output_file, 
                help = 'output GEDCOM file [stdout]')
            self.parser.add_argument('-l', metavar = '<FILE>', 
                type = argparse.FileType('w', encoding = 'UTF-8'), 
                default = self.defaults.log_output_file, 
                help = 'output log file [stderr]')
        except TypeError:
            sys.stderr.write('Python >= 3.4 is required to run this script\n')
            sys.stderr.write(('(see https://docs.python.org/3/'
                              'whatsnew/3.4.html#argparse)\n'))
            exit(2)
            
    def extract_cli_arguments(self):
        # extract arguments from the command line
        try:
            self.parser.error = self.parser.exit
            self.args = self.parser.parse_args()
        except SystemExit:
            self.parser.print_help()
            exit(2)
            
    def get_username(self):
        if self.args.u:
            self.username = self.args.u
        else:
            self.username = input("Enter FamilySearch username: ")
            
    def get_password(self):
        if self.args.p:
            self.password = self.args.p
        else:
            self.password = getpass.getpass("Enter FamilySearch password: ")
            
    def store_run_parameters(self):
        self.run_parameters = {}
        self.run_parameters['starting_individuals'] = self.args.i
        self.run_parameters['num_gen_ascend'] = self.args.a
        self.run_parameters['num_gen_descend'] = self.args.d
        self.run_parameters['add_spouses_couples_info'] = self.args.m
        self.run_parameters['verbose'] = self.args.v
        self.run_parameters['timeout_seconds'] = self.args.t
        self.run_parameters['gedcom_output_file'] = self.args.o
        self.run_parameters['log_output_file'] = self.args.l
        self.run_parameters['username'] = self.username
        self.run_parameters['password'] = self.password

    def get_run_parameters(self):
        return self.run_parameters

def main():
    cli = CLI()
    rps = cli.get_run_parameters()
    # initialize a FamilySearch session and a family tree object
    fs = Session(rps['username'], rps['password'], 
                 rps['verbose'], rps['log_output_file'], 
                 rps['timeout_seconds'])
    tree = Tree(fs)

    # add list of starting individuals to the family tree
    if rps['starting_individuals']:
        todo = set(rps['starting_individuals'])
    else:
        todo = set([fs.get_userid()])
    for fid in todo:
        tree.add_indi(fid)

    # download ancestors
    done = set()
    for i in range(rps['num_gen_ascend']):
        next_todo = set()
        for fid in todo:
            done.add(fid)
            for parent in tree.add_parents(fid):
                next_todo.add(parent)
        todo = next_todo - done

    # download descendants
    todo = set(tree.indi.keys())
    done = set()
    for i in range(rps['num_gen_descend']):
        next_todo = set()
        for fid in todo:
            done.add(fid)
            for child in tree.add_children(fid):
                next_todo.add(child)
        todo = next_todo - done

    # download spouses
    if rps['add_spouses_couples_info']:
        todo = set(tree.indi.keys())
        for fid in todo:
            tree.add_spouses(fid)

    # compute number for family relationships and print GEDCOM file
    tree.reset_num()
    tree.print(rps['gedcom_output_file'])


if __name__ == '__main__':
    main()