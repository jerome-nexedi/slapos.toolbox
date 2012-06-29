# -*- coding: utf-8 -*-

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
  """Clonne a repository
  Args:
    data: a dictionnary of parameters to use:
      data['path'] is the path of the new project
      data['repo'] is the url of the repository to be cloned
      data['email'] is the user email
      data['user'] is the name of the user
  Returns:
    a jsonify data"""
  workDir = data['path']
  if not workDir:
    return jsonify(code=0,
                   result="Can not create project folder: Permission Denied")
  code = 0
  json = ""
  try:
    if os.path.exists(workDir) and len(os.listdir(workDir)) < 2:
      shutil.rmtree(workDir) #delete useless files
    repo = Repo.clone_from(data["repo"], workDir)
    config_writer = repo.config_writer()
    config_writer.add_section("user")
    if data["user"] != "":
      config_writer.set_value("user", "name", data["user"].encode("utf-8"))
    if data["email"] != "":
      config_writer.set_value("user", "email", data["email"])
    code = 1
  except Exception, e:
    json = safeResult(str(e))
    if os.path.exists(workDir):
      shutil.rmtree(workDir)
  return jsonify(code=code, result=json)

def gitStatus(project):
  """Run git status and return status of specified project folder
  Args:
    project: path of the projet ti get status
  Returns:
    a parsed string that contains the result of git status"""
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
    json = safeResult(str(e))
  return jsonify(code=code, result=json, branch=branch, dirty=isdirty)

def switchBranch(project, name):
  """Switch a git branch
  Args:
    project: directory of the local git repository
    name: switch from current branch to `name` branch
  Returns:
    a jsonify data"""
  code = 0
  json = ""
  try:
    repo = Repo(project)
    branches = repo.branches
    current_branch = repo.active_branch.name
    if name == current_branch:
      json = "This is already your active branch for this project"
    else:
      git  = repo.git
      git.checkout(name)
      code = 1
  except Exception, e:
    json = safeResult(str(e))
  return jsonify(code=code, result=json)

def addBranch(project, name, onlyCheckout=False):
  """Add new git branch to the repository
  Args:
    project: directory of the local git repository
    name: name of the new branch
    onlyCheckout: if True then the branch `name` is created before checkout
  Returns:
    a jsonify data"""
  code = 0
  json = ""
  try:
    repo = Repo(project)
    git  = repo.git
    if not onlyCheckout:
      git.checkout('-b', name)
    else:
      git.checkout(name)
    code = 1
  except Exception, e:
    json = safeResult(str(e))
  return jsonify(code=code, result=json)

def getDiff(project):
  """Get git diff for the specified project directory"""
  result = ""
  try:
    repo = Repo(project)
    git = repo.git
    current_branch = repo.active_branch.name
    result = git.diff(current_branch)
  except Exception, e:
    result = safeResult(str(e))
  return result

def gitPush(project, msg):
  """Commit and Push changes for the specified repository
  Args:
    project: directory of the local repository
    msg: commit message"""
  code = 0
  json = ""
  undo_commit = False
  try:
    repo = Repo(project)
    if repo.is_dirty:
      git = repo.git
      current_branch = repo.active_branch.name
      #add file to be commited
      files = repo.untracked_files
      for f in files:
        git.add(f)
      #Commit all modified and untracked files
      git.commit('-a', '-m', msg)
      undo_commit = True
      #push changes to repo
      git.push('origin', current_branch)
      code = 1
    else:
      json = "Nothing to be commited"
      code = 1
  except Exception, e:
    if undo_commit:
      git.reset("HEAD~") #undo previous commit
    json = safeResult(str(e))
  return jsonify(code=code, result=json)

def gitPull(project):
  result = ""
  code = 0
  try:
    repo = Repo(project)
    git = repo.git
    current_branch = repo.active_branch.name
    git.pull()
    code = 1
  except Exception, e:
    result = safeResult(str(e))
  return jsonify(code=code, result=result)

def safeResult(result):
  """Parse string and remove credential of the user"""
  regex=re.compile("(https:\/\/)([\w\d\._-]+:[\w\d\._-]+)\@([\S]+\s)", re.VERBOSE)
  return regex.sub(r'\1\3', result)