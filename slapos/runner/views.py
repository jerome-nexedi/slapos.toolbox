from flask import Flask, request, redirect, url_for, \
         render_template, flash, jsonify, session
from utils import *
import os
import shutil
import md5
from gittools import cloneRepo, gitStatus, switchBranch, addBranch, getDiff, \
     gitPush, gitPull

app = Flask(__name__)

@app.before_request
def before_request():
  session['title'] = getProjectTitle(app.config)

# general views
@app.route('/')
def home():
  if not os.path.exists(app.config['workspace']) or len(os.listdir(app.config['workspace'])) == 0:
    return redirect(url_for('configRepo'))
  return render_template('index.html')

@app.route('/configRepo')
def configRepo():
  public_key = open(app.config['public_key'], 'r').read()
  return render_template('cloneRepository.html', workDir='workspace', public_key=public_key)

# software views
@app.route('/editSoftwareProfile')
def editSoftwareProfile():
  profile = getProfilePath(app.config['runner_workdir'], app.config['software_profile'])
  if profile == "":
    flash('Error: can not open profile, please select your project first')
  return render_template('updateSoftwareProfile.html', workDir='workspace',
      profile=profile, projectList=getProjectList(app.config['workspace']))

@app.route('/inspectSoftware', methods=['GET'])
def inspectSoftware():
  if not os.path.exists(app.config['software_root']):
    result = ""
  else:
    result = app.config['software_root']
  return render_template('runResult.html', softwareRoot='software_root',
                         softwares=loadSoftwareData(app.config['runner_workdir']))

@app.route('/removeSoftware')
def removeSoftware():
  file_config = os.path.join(app.config['runner_workdir'], ".softdata")
  if isSoftwareRunning(app.config) or isInstanceRunning(app.config):
    flash('Software installation or instantiation in progress, cannot remove')
  elif os.path.exists(file_config):
    svcStopAll(app.config)
    shutil.rmtree(app.config['software_root'])
    os.remove(os.path.join(app.config['runner_workdir'], ".softdata"))
    flash('Software removed')
  return redirect(url_for('inspectSoftware'))

@app.route('/runSoftwareProfile', methods=['POST'])
def runSoftwareProfile():
  if runSoftwareWithLock(app.config):
    return  jsonify(result = True)
  else:
    return  jsonify(result = False)

@app.route('/viewSoftwareLog', methods=['GET'])
def viewSoftwareLog():
  if os.path.exists(app.config['software_log']):
    result = tail(open(app.config['software_log'], 'r'), lines=1500)
  else:
    result = 'Not found yet'
  return render_template('viewLog.html', type='software',
      result=result)

# instance views
@app.route('/editInstanceProfile')
def editInstanceProfile():
  profile = getProfilePath(app.config['runner_workdir'], app.config['instance_profile'])
  if profile == "":
    flash('Error: can not open instance profile for this Software Release')
  return render_template('updateInstanceProfile.html', workDir='workspace',
      profile=profile, projectList=getProjectList(app.config['workspace']))

@app.route('/inspectInstance', methods=['GET'])
def inspectInstance():
  file_content = ''
  result = ''
  if os.path.exists(app.config['instance_root']):
    file_content = 'instance_root'
    result = getSvcStatus(app.config)
    if len(result) == 0:
      result = []  
  return render_template('instanceInspect.html',
      file_path=file_content, supervisor=result, slap_status=getSlapStatus(app.config),
      supervisore=result, partition_amount=app.config['partition_amount'])

@app.route('/removeInstance')
def removeInstance():
  if isInstanceRunning(app.config):
    flash('Instantiation in progress, cannot remove')
  else:
    removeInstanceRoot(app.config)
    flash('Instance removed')
  return redirect(url_for('inspectInstance'))

@app.route('/runInstanceProfile', methods=['POST'])
def runInstanceProfile():
  if not os.path.exists(app.config['instance_root']):
    os.mkdir(app.config['instance_root'])
  if runInstanceWithLock(app.config):
    return  jsonify(result = True)
  else:
    return  jsonify(result = False)

@app.route('/viewInstanceLog', methods=['GET'])
def viewInstanceLog():
  if os.path.exists(app.config['instance_log']):
    result = open(app.config['instance_log'], 'r').read()
  else:
    result = 'Not found yet'
  return render_template('viewLog.html', type='instance',
      result=result)

@app.route('/stopAllPartition', methods=['GET'])
def stopAllPartition():
  svcStopAll(app.config)
  return redirect(url_for('inspectInstance'))

@app.route('/tailProcess/name/<process>', methods=['GET'])
def tailProcess(process):
  return render_template('processTail.html',
      process_log=getSvcTailProcess(app.config, process), process=process)

@app.route('/startStopProccess/name/<process>/cmd/<action>', methods=['GET'])
def startStopProccess(process, action):
  svcStartStopProcess(app.config, process, action)
  return redirect(url_for('inspectInstance'))

@app.route('/showBuildoudAnnotate', methods=['GET'])
def showBuildoudAnnotate():
  if runBuildoutAnnotate(app.config):
    flash('Started.')
  else:
    flash('Please run software before')
  return redirect(url_for('viewBuildoudAnnotate'))

@app.route('/viewBuildoudAnnotate', methods=['GET'])
def viewBuildoudAnnotate():
  if os.path.exists(app.config['annotate_log']):
    result = open(app.config['annotate_log'], 'r').read()
  else:
    result = 'Not found yet'
  return render_template('viewLog.html', type='Instance',
      result=result, running=isInstanceRunning(app.config))

@app.route('/openProject/<method>', methods=['GET'])
def openProject(method):
  return render_template('projectFolder.html', method=method,
                         workDir='workspace')

@app.route('/cloneRepository', methods=['POST'])
def cloneRepository():
  path = realpath(app.config, request.form['name'], False)
  data = {"repo":request.form['repo'], "user":request.form['user'],
          "email":request.form['email'], "path":path}
  return cloneRepo(data)

@app.route('/readFolder', methods=['POST'])
def readFolder():
  return getFolderContent(app.config, request.form['dir'])

@app.route('/openFolder', methods=['POST'])
def openFolder():
  return getFolder(app.config, request.form['dir'])

@app.route('/createSoftware', methods=['POST'])
def createSoftware():
  return newSoftware(request.form['folder'], app.config, session)

@app.route("/checkFolder", methods=['POST'])
def checkFolder():
  return checkSoftwareFolder(request.form['path'], app.config)

@app.route("/setCurrentProject", methods=['POST'])
def setCurrentProject():
  if configNewSR(app.config, request.form['path']):
    session['title'] = getProjectTitle(app.config)
    return jsonify(code=1, result="")
  else:
    return jsonify(code=0, result=("Can not setup this Software Release"))

@app.route("/manageProject", methods=['GET'])
def manageProject():
  return render_template('manageProject.html', workDir='workspace',
                         project=getProjectList(app.config['workspace']))

@app.route("/getProjectStatus", methods=['POST'])
def getProjectStatus():
  path = realpath(app.config, request.form['project'])
  if path:
    return gitStatus(path)
  else:
    return jsonify(code=0, result="Can not read folder: Permission Denied")

@app.route("/editCurrentProject")
def editCurrentProject():
  project = os.path.join(app.config['runner_workdir'], ".project")
  if os.path.exists(project):
    return render_template('softwareFolder.html', workDir='workspace',
                           project=open(project).read(),
                           projectList=getProjectList(app.config['workspace']))
  return redirect(url_for('configRepo'))

@app.route("/createFile", methods=['POST'])
def createFile():
  path = realpath(app.config, request.form['file'], False)
  if not path:
    return jsonify(code=0, result="Error when creating your " + \
                   request.form['type'] + ": Permission Denied")
  try:
    if request.form['type'] == "file":
      f = open(path, 'w').write(" ")
    else:
      os.mkdir(path)
    return jsonify(code=1, result="")
  except Exception, e:
    return jsonify(code=0, result=str(e))

@app.route("/removeFile", methods=['POST'])
def removeFile():
  try:
    if request.form['type'] == "folder":
      shutil.rmtree(request.form['path'])
    else:
      os.remove(request.form['path'])
    return jsonify(code=1, result="")
  except Exception, e:
    return jsonify(code=0, result=str(e))

@app.route("/removeSoftwareDir", methods=['POST'])
def removeSoftwareDir():
  return removeSoftwareByName(app.config, request.form['name'])

@app.route("/getFileContent", methods=['POST'])
def getFileContent():
  file_path = realpath(app.config, request.form['file'])
  if file_path:
    if not request.form.has_key('truncate'):
      return jsonify(code=1, result=open(file_path, 'r').read())
    else:
      content = tail(open(file_path, 'r'), int(request.form['truncate']))
      return jsonify(code=1, result=content)
  else:
    return jsonify(code=0, result="Error: No such file!")

@app.route("/saveFileContent", methods=['POST'])
def saveFileContent():
  file_path = realpath(app.config, request.form['file'])
  if file_path:
    open(file_path, 'w').write(request.form['content'])
    return jsonify(code=1, result="")
  else:
    return jsonify(code=0, result="Error: No such file!")

@app.route("/changeBranch", methods=['POST'])
def changeBranch():
  path = realpath(app.config, request.form['project'])
  if path:
    return switchBranch(path, request.form['name'])
  else:
    return jsonify(code=0, result="Can not read folder: Permission Denied")

@app.route("/newBranch", methods=['POST'])
def newBranch():
  path = realpath(app.config, request.form['project'])
  if path:
    if request.form['create'] == '1':
      return addBranch(path, request.form['name'])
    else:
      return addBranch(path, request.form['name'], True)
  else:
    return jsonify(code=0, result="Can not read folder: Permission Denied")

@app.route("/getProjectDiff/<project>", methods=['GET'])
def getProjectDiff(project):
  path = os.path.join(app.config['workspace'], project)
  return render_template('projectDiff.html', project=project,
                           diff=getDiff(path))

@app.route("/pushProjectFiles", methods=['POST'])
def pushProjectFiles():
  path = realpath(app.config, request.form['project'])
  if path:
    return gitPush(path, request.form['msg'])
  else:
    return jsonify(code=0, result="Can not read folder: Permission Denied")

@app.route("/pullProjectFiles", methods=['POST'])
def pullProjectFiles():
  path = realpath(app.config, request.form['project'])
  if path:
    return gitPull(path)
  else:
    return jsonify(code=0, result="Can not read folder: Permission Denied")

@app.route("/checkFileType", methods=['POST'])
def checkFileType():
  path = realpath(app.config, request.form['path'])
  if not path:
    return jsonify(code=0, result="Can not open file: Permission Denied!")
  if isText(path):
    return jsonify(code=1, result="text")
  else:
    return jsonify(code=0, result="Can not open a binary file, please select a text file!")

@app.route("/getmd5sum", methods=['POST'])
def getmd5sum():
  realfile = realpath(app.config, request.form['file'])
  if not realfile:
    return jsonify(code=0, result="Can not open file: Permission Denied!")
  md5 = md5sum(realfile)
  if md5:
    return jsonify(code=1, result=md5)
  else:
    return jsonify(code=0, result="Can not get md5sum for this file!")

@app.route("/slapgridResult", methods=['POST'])
def slapgridResult():
  software_state = isSoftwareRunning(app.config)
  instance_state = isInstanceRunning(app.config)
  log_result = {"content":"", "position":0}
  if request.form['log'] == "software"  or\
     request.form['log'] == "instance":
    log_file = request.form['log'] + "_log"
    if os.path.exists(app.config[log_file]):
      log_result = readFileFrom(open(app.config[log_file], 'r'),
                            int(request.form['position']))
  return  jsonify(software=software_state, instance=instance_state,
                  result=(instance_state or software_state), content=log_result)

@app.route("/stopSlapgrid", methods=['POST'])
def stopSlapgrid():
  result = killRunningSlapgrid(app.config, request.form['type'])
  return jsonify(result=result)

@app.route("/getPath", methods=['POST'])
def getPath():
  files = request.form['file'].split('#')
  list = []
  for p in files:
    path = realpath(app.config, p)
    if not p:
      list = []
      break
    else:
      list.append(path)
  realfile = string.join(list, "#")
  if not realfile:
    return jsonify(code=0, result="Can not access to this file: Permission Denied!")
  else:
    return jsonify(code=1, result=realfile)

@app.route("/saveParameterXml", methods=['POST'])
def redParameterXml():
  project = os.path.join(app.config['runner_workdir'], ".project")
  if not os.path.exists(project):
    return jsonify(code=0, result="Please first open a Software Release")
  content = request.form['parameter']
  param_path = os.path.join(app.config['runner_workdir'], ".parameter.xml")
  f = open(param_path, 'w')
  f.write(content)
  f.close()
  result = readParameters(param_path)
  if type(result) == type(''):
    return jsonify(code=0, result="XML Error: " + result)
  else:
    try:
      updateProxy(app.config)
    except Exeption:
      return jsonify(code=0, result="An error occurred while applying your settings!")
    return jsonify(code=1, result="")

@app.route("/getParameterXml", methods=['GET'])
def getParameterXml():
  param_path = os.path.join(app.config['runner_workdir'], ".parameter.xml")
  if os.path.exists(param_path):
    content = open(param_path, 'r').read()
    return html_escape(content)
  else:
    return "&lt;?xml version='1.0' encoding='utf-8'?&gt;"