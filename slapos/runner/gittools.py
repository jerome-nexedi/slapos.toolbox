import slapos.slap
import time
import subprocess
import os
import re
import urllib
from flask import jsonify
import shutil
import string
from git import *

class Popen(subprocess.Popen):
  def __init__(self, *args, **kwargs):
    kwargs['stdin'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.STDOUT
    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('close_fds', True)
    subprocess.Popen.__init__(self, *args, **kwargs)
    self.stdin.flush()
    self.stdin.close()
    self.stdin = None
  
def cloneRepo(data):
  workDir = data['path']
  code = 0
  json = ""
  try:
    if os.path.exists(workDir) and len(os.listdir(workDir)) < 2:
      shutil.rmtree(workDir) #delete useless files
    repo = Repo.clone_from(data["repo"], workDir)
    config_writer = repo.config_writer()
    config_writer.add_section("user")
    config_writer.set_value("user", "name", data["user"])
    config_writer.set_value("user", "email", data["email"])
    code = 1
  except Exception, e:
    json = str(e)
    if os.path.exists(workDir):
      shutil.rmtree(workDir)
  return jsonify(code=code, result=json)

def gitStatus(project):
  code = 0
  json = ""
  try:
    repo = Repo(project)
    git = repo.git
    json = git.status().replace('#', '')
    branch = git.branch().replace(' ', '').split('\n')
    isdirty = repo.is_dirty(untracked_files=True)
    code = 1
  except Exception, e:
    json = str(e)
  return jsonify(code=code, result=json, branch=branch, dirty=isdirty)

def switchBranch(project, name):
  code = 0
  json = ""  
  try:
    repo = Repo(project)
    branches = repo.branches
    current_branch = repo.active_branch.name
    if name == current_branch:
      json = "This is already your active branch for this project"
    else:
      branch = none
      for b in branches:
        if b.name == name:
          branch = b
      if branch != none:
        repo.heads.master.checkout()
        repo.heads.branch.checkout()
        code = 1
      else:
        code = 0
        json = "Error: Can not found branch '" + name + "'"
  except Exception, e:
    json = str(e)
  return jsonify(code=code, result=json)