#!/usr/bin/python3

import os
import yaml
import time
import shutil
import logging
import zipfile
import subprocess

class MasterBackup:
    
    # General tool settings
    settings = dict()
    
    tmpPaths = dict()
    
    timestamp = None
    
    active_client = dict()
    
    logger = None
    
    backup_dir = str()
    
    def __init__(self):
        self.logger = logging
        self.timestamp = time.strftime('%Y-%m-%d-%I:%M:%S')
        self.load_settings()
        self.active_client = self.get_specific_client(os.getenv('ACTIVE_CLIENT'))
        self.backup_dir = "{backup_dir}{client}_{timestamp}".format(
            backup_dir=self.active_client['backup_dir']['default'],
            client=self.active_client['name'],
            timestamp=self.timestamp
        )
        self.create_backup_dir()
    
    def create_backup_dir(self):
        if(os.path.isdir(self.backup_dir)):
            return self.backup_dir
        else:
            try:
                os.mkdir(self.backup_dir)
                self.logger.info("Created new BK directory in {dir}".format(
                    dir=self.backup_dir
                ))
                if(os.path.isdir(self.backup_dir)):
                    return self.backup_dir
            except:
                msg = "Failed creating BK directory in {dir}".format(
                    dir=self.backup_dir
                )
                self.logger.warn(msg)
                raise Exception(msg)
        
    def load_settings(self):
        with open(os.getenv('GENERAL_SETTINGS')) as settings:
            settings_file = yaml.full_load(settings)
            for item, doc in settings_file.items():
                self.settings[item] = doc
        active_client = self.get_specific_client(os.getenv('ACTIVE_CLIENT'))
        self.logger.basicConfig(
            filename=active_client['log_file'],
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=self.logger.DEBUG)
        self.logger.info('Loaded enviroment and databases config')
                
    def get_specific_client(self, client: str):
        if client in self.settings['databases']:
            return self.settings['databases'][client]
        return None
    
    def do_sql_backup(self):
        try:
            self.logger.info('SQL Backup [START] on {backup_dir}'.format(
                backup_dir=self.backup_dir
            ))
        
            dest_folder = '{dest}/{name}_{time}.sql'.format(
                dest=self.backup_dir,
                name=self.active_client['name'],
                time=self.timestamp
            )
        
            task = os.popen("mysqldump -u {user} -p{password} -e --opt -c {database} > {backup}".format(
                 host=self.active_client['host'],
                 user=self.active_client['username'],
                 password=self.active_client['password'],
                 database=self.active_client['database'],
                 backup=dest_folder
            ))
        
            self.tmpPaths['db'] = dest_folder
            
            self.logger.info('SQL Backup [SUCCESS]')
        
            return True
        except:
            msg = 'Error ocurred on SQL backup action'
            self.logger.warn(msg)
            raise Exception(msg)
    
    def do_project_backup(self):
        if(os.path.isdir(self.active_client['working_dir'])):
            try:
                destPath = "{dest}/{name}/".format(
                    dest=self.backup_dir,
                    name=self.active_client['name']
                )
                
                self.logger.info('Project backup [START] on {path}'.format(
                    path=destPath
                ))
                
                taskPath = shutil.copytree(
                    src=self.active_client['working_dir'], 
                    dst=destPath,
                    symlinks=True
                )
                
                if(destPath == taskPath):
                    self.logger.info('Project backup [SUCCESS] in {path}'. format(
                        path=taskPath
                    ))
                    self.tmpPaths['project'] = taskPath
                    return True
            except:
                msg = 'Error ocurred on project backup action'
                self.logger.warn(msg)
                raise Exception(msg)
            
    def get_file_paths(self, path: str):
        # Files paths
        filePaths = []
        
        for root, dirs, files in os.walk(path):
            for filename in files:
                filePath = os.path.join(root, filename)
                filePaths.append(filePath)
        
        return filePaths
            
    def compress_and_save(self):
        if(len(self.tmpPaths.keys()) > 0):
            try:
                self.logger.info('ZIP Compression [START]')
                zip_file_name = "{base}{name}_{timestamp}.zip".format(
                    base=self.active_client['backup_dir']['default'],
                    name=self.active_client['name'],
                    timestamp=self.timestamp
                )
                
                zip_file = zipfile.ZipFile(
                    zip_file_name,
                    'w',
                    zipfile.ZIP_DEFLATED
                )
                
                filePaths = self.get_file_paths(self.backup_dir)
                
                # Patch timestamps before 1980 error
                timestamp = time.mktime((1980, 1, 1, 0, 0, 0, 0, 0, 0))
                
                with zip_file:
                    for path in filePaths:
                        os.utime(path, (timestamp, timestamp))
                        zip_file.write(path)
                
                        
                self.logger.info('ZIP Compression [SUCCESS]')
                
                shutil.rmtree(self.backup_dir)
            except:
                raise Exception('Compression task failed')
        else:
            raise Exception('Compression task [ERROR]')
                                    
if __name__ == '__main__':
    settings = MasterBackup()
    if(settings.do_sql_backup() and settings.do_project_backup()):
        settings.compress_and_save()
