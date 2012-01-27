from flask import Flask, request, redirect, url_for, \
         render_template, flash, jsonify, session
from utils import *
import os
import shutil
from gittools import cloneRepo, gitStatus

app = Flask(__name__)

# general views
@app.route('/')
def home():
  if not os.path.exists(app.config['workspace']) or len(os.listdir(app.config['workspace'])) == 0:
    session['title'] = "No project"
    return redirect(url_for('configRepo'))
  session['title'] = getProjectTitle(app.config)
  return render_template('index.html')

@app.route('/configRepo')
def configRepo():
  public_key = open(app.config['public_key'], 'r').read()
  return render_template('cloneRepository.html', workDir=app.config['workspace'], public_key=public_key)

# software views
@app.route('/editSoftwareProfile')
def editSoftwareProfile():
  profile = getProfile(app.config['runner_workdir'], app.config['software_profile'])
  if profile == "":
    flash('Error: can not open profile, please select your project first')
  return render_template('updateSoftwareProfile.html',
      profile=profile, 
      instance_url=url_for('getInstance', _external=True))

@app.route('/software.cfg', methods=['GET', 'POST'])
def getSoftware():
  return getProfile(app.config['runner_workdir'], app.config['software_profile'])

@app.route('/inspectSoftware', methods=['GET'])
def inspectSoftware():
  if not os.path.exists(app.config['software_root']):
    result = ""
  else:
    #process = Popen(['find'], cwd=app.config['software_root'])
    result = app.config['software_root']    
  return render_template('runResult.html', type='Software',
      result=result)

@app.route('/removeSoftware')
def removeSoftware():
  if isSoftwareRunning(app.config) or isInstanceRunning(app.config):
    flash('Software installation or instantiation in progress, cannot remove')
  elif os.path.exists(app.config['software_root']):
    svcStopAll(app.config)
    shutil.rmtree(app.config['software_root'])
    flash('Software removed')
  return redirect(url_for('inspectSoftware'))

@app.route('/runSoftwareProfile', methods=['GET'])
def runSoftwareProfile():
  if runSoftwareWithLock(app.config):
    flash('Started.')
  else:
    flash('Already running.')
  return redirect(url_for('viewSoftwareLog'))

@app.route('/viewSoftwareLog', methods=['GET'])
def viewSoftwareLog():
  if os.path.exists(app.config['software_log']):
    result = open(app.config['software_log'], 'r').read()
  else:
    result = 'Not found yet'
  return render_template('viewLog.html', type='Software',
      result=result, running=isSoftwareRunning(app.config))

@app.route('/updateSoftwareProfile', methods=['POST'])
def updateSoftwareProfile():
  profile = getProfilePath(app.config['runner_workdir'], app.config['software_profile'])
  if profile != "":
    open(profile, 'w').write(request.form['content'])
  return redirect(url_for('editSoftwareProfile'))

# instance views
@app.route('/editInstanceProfile')
def editInstanceProfile():
  profile = getProfile(app.config['runner_workdir'], app.config['instance_profile'])
  if profile == "":
    flash('Error: can not open profile, please select your project first') 
  return render_template('updateInstanceProfile.html',
      profile=profile)

@app.route('/instance.cfg', methods=['GET', 'POST'])
def getInstance():
  return getProfile(app.config['runner_workdir'], app.config['instance_profile'])

@app.route('/inspectInstance', methods=['GET'])
def inspectInstance():
  file_content = ''
  result = ''
  if os.path.exists(app.config['instance_root']):
    file_content = app.config['instance_root']
    result = getSvcStatus(app.config)
  return render_template('instanceInspect.html',
      file_path=file_content, supervisor=result, slap_status=getSlapStatus(app.config),
      supervisore=result)

@app.route('/removeInstance')
def removeInstance():
  if isInstanceRunning(app.config):
    flash('Instantiation in progress, cannot remove')
  elif os.path.exists(app.config['instance_root']):
    svcStopAll(app.config)
    for root, dirs, files in os.walk(app.config['instance_root']):
      for fname in dirs:
        fullPath = os.path.join(root, fname)
        if not os.access(fullPath, os.W_OK) :
          # Some directories may be read-only, preventing to remove files in it
          os.chmod(fullPath, 0744)
    shutil.rmtree(app.config['instance_root'])
    flash('Instance removed')
  return redirect(url_for('inspectInstance'))

@app.route('/runInstanceProfile', methods=['GET'])
def runInstanceProfile():
  if not os.path.exists(app.config['instance_root']):
    os.mkdir(app.config['instance_root'])
  if runInstanceWithLock(app.config):
    flash('Started.')
  else:
    flash('Already running.')
  return redirect(url_for('viewInstanceLog'))

@app.route('/viewInstanceLog', methods=['GET'])
def viewInstanceLog():
  if os.path.exists(app.config['instance_log']):
    result = open(app.config['instance_log'], 'r').read()
  else:
    result = 'Not found yet'
  return render_template('viewLog.html', type='Instance',
      result=result, running=isInstanceRunning(app.config))

@app.route('/updateInstanceProfile', methods=['POST'])
def updateInstanceProfile():
  profile = getProfilePath(app.config['runner_workdir'], app.config['instance_profile'])
  if profile != "":  
    open(profile, 'w').write(request.form['content'])
  return redirect(url_for('editInstanceProfile'))

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
                         workDir=app.config['workspace'])

@app.route('/cloneRepository', methods=['POST'])
def cloneRepository():
  data = {"repo":request.form['repo'], "user":request.form['user'], 
          "email":request.form['email']}
  name = request.form['name']
  data['path'] = os.path.join(app.config['workspace'], name)
  return cloneRepo(data)

@app.route('/readFolder', methods=['POST'])
def readFolder():
  return getFolderContent(request.form['dir'])

@app.route('/openFolder', methods=['POST'])
def openFolder():
  return getFolder(request.form['dir'])

@app.route('/createSoftware', methods=['POST'])
def createSoftware():
  return newSoftware(request.form['folder'], app.config, session)

@app.route("/checkFolder", methods=['POST'])
def checkFolder():
  return checkSoftwareFolder(request.form['path'], app.config)

@app.route("/setCurentProject", methods=['POST'])
def setCurentProject():
  folder = request.form['path']
  if os.path.exists(folder):
    open(os.path.join(app.config['runner_workdir'], ".project"), 'w').write(folder)
    session['title'] = getProjectTitle(app.config)
    return jsonify(code=1, result="")
  else:
    return jsonify(code=0, result=("Can not open '" + folder + "'"))

@app.route("/manageProject", methods=['GET'])
def manageProject():
  return render_template('manageProject.html', workDir=app.config['workspace'],
                         project=getProjectList(app.config['workspace']))

@app.route("/getProjectStatus", methods=['POST'])
def getProjectStatus():
  return gitStatus(request.form['project'])

@app.route("/curentSoftware")
def curentSoftware():
  project = os.path.join(app.config['runner_workdir'], ".project")
  if os.path.exists(project):
    return render_template('softwareFolder.html', workDir=app.config['workspace'],
                           project=open(project).read())
  return redirect(url_for('configRepo'))

@app.route("/createFile", methods=['POST'])
def createFile():
  try:
    if request.form['type'] == "file":
      f = open(request.form['file'], 'w').write(" ")
    else:
      os.mkdir(request.form['file'])
    return jsonify(code=1, result="")
  except Exception, e:
    return jsonify(code=0, result=str(e))

@app.route("/getFileContent", methods=['POST'])
def getFileContent():
  if os.path.exists(request.form['file']):
    return jsonify(code=1, result=open(request.form['file'], 'r').read())
  else:
    return jsonify(code=0, result="Error: No such file!")
  
@app.route("/saveFileContent", methods=['POST'])
def saveFileContent():
  if os.path.exists(request.form['file']):
    open(request.form['file'], 'w').write(request.form['content'])
    return jsonify(code=1, result="")
  else:
    return jsonify(code=0, result="Error: No such file!")  