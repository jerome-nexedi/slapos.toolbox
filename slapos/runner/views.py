from flask import Flask, request, redirect, url_for, \
         render_template, flash
from utils import getProfile, runInstanceWithLock, runSoftwareWithLock, Popen, isInstanceRunning, isSoftwareRunning, getSvcStatus, getSlapStatus, svcStopAll
import os
import shutil

app = Flask(__name__)

# general views
@app.route('/')
def home():
  return render_template('index.html')

# software views
@app.route('/editSoftwareProfile')
def editSoftwareProfile():
  return render_template('updateSoftwareProfile.html',
      profile=getProfile(app.config['software_profile']), instance_url=url_for('getInstance', _external=True))

@app.route('/software.cfg', methods=['GET', 'POST'])
def getSoftware():
  return getProfile(app.config['software_profile'])

@app.route('/inspectSoftware', methods=['GET'])
def inspectSoftware():
  if not os.path.exists(app.config['software_root']):
    result = "Does not exists yet"
  else:
    process = Popen(['find'], cwd=app.config['software_root'])
    result = process.communicate()[0]
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
  open(app.config['software_profile'], 'w').write(request.form['content'])
  return redirect(url_for('editSoftwareProfile'))

# instance views
@app.route('/editInstanceProfile')
def editInstanceProfile():
  return render_template('updateInstanceProfile.html',
      profile=getProfile(app.config['instance_profile']))

@app.route('/instance.cfg', methods=['GET', 'POST'])
def getInstance():
  return getProfile(app.config['instance_profile'])

@app.route('/inspectInstance', methods=['GET'])
def inspectInstance():
  file_content = 'Does not exists yet.'
  if os.path.exists(app.config['instance_root']):
    process = Popen(['find'], cwd=app.config['instance_root'])
    file_content = process.communicate()[0]
  return render_template('instanceInspect.html',
      file_content=file_content, supervisor=getSvcStatus(app.config), slap_status=getSlapStatus(app.config))

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
  open(app.config['instance_profile'], 'w').write(request.form['content'])
  return redirect(url_for('editInstanceProfile'))

@app.route('/stopAllPartition', methods=['GET'])
def stopAllPartition():
  svcStopAll(app.config)
  return redirect(url_for('inspectInstance'))
