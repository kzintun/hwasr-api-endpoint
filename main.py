import os
import uuid
#import magic
import urllib.request
from app import app
from flask import Flask, flash, request, redirect, render_template
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import subprocess
import time

CORS(app, support_credentials=True)

# temp fix
KW_FST_PATH="/local/deliverables-hh/ws-online-asr/mipiworkerbin/asrres/16k-ENG-2019-OCTv4.4-AM-2020-LEX-LM-SEPT/kwfsts/keywords.fsts"
LOG_PATH="/local/deliverables-hh/ws-online-asr/mipiworkerbin/asrres/16k-ENG-2019-OCTv4.4-AM-2020-LEX-LM-SEPT/log"

ALLOWED_EXTENSIONS = set(['txt'])
STATUS = 0 # default success

def convert_to_dos(file_):
	dos2unixCmd = ["dos2unix", file_]      
	process = subprocess.Popen(dos2unixCmd, stdout=subprocess.PIPE)
	process.wait()
	return process.returncode

def validate_hotwordFile(hwfile):
	#print(hwfile)
	msg = convert_to_dos(hwfile)
	if msg > 0:
		return msg

	return msg

def update_hotword_ASR(hwfile):
	print("-updating hw asr")

	beg_moddate=0
	cur_moddate=0
	IN_PROG=True

	# get message from ASR
	# get the FST modify date - to find update completion event
	if os.path.exists(KW_FST_PATH):
		beg_moddate = os.stat(KW_FST_PATH)[8]

	# update process
	cwd = os.getcwd()
	SCRIPT_DIR = "/local/deliverables-hh/ws-online-asr/mipiworkerbin"
	os.chdir(SCRIPT_DIR)
	#cmd = ["bash"," ./wschange-kwlist", " ws://localhost:9997/client/ws/speech" , hwfile]
	cmd = ["pwd >> abc.txt"]
	#bashcmd = "./wschange-kwlist ws://localhost:9997/client/ws/speech " + hwfile	
	bashcmd = "./wsupdate-hotword-list --update-hotword-engine=true --use-phonetic-lexicon --hotword-list-file=" + hwfile + " ws://localhost:9997/client/ws/speech "	# update hw + 9998+9997
	#bashcmd-deactivate = "./wsupdate-hotword-list --update-hotword-engine=false ws://localhost:9997/client/ws/speech "	#only 9998
	#bashcmd-activate = "./wsupdate-hotword-list --update-hotword-engine=true ws://localhost:9997/client/ws/speech "	#9998+9997
	#print(os.getcwd())
	os.system(bashcmd)	
	#process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	#process.wait()
	os.chdir(cwd)

	# check if update process from worker is completed - i.e. fst file is modified
	while(IN_PROG):
		cur_moddate= os.stat(KW_FST_PATH)[8]
		if cur_moddate != beg_moddate:
			IN_PROG=False
	
	#return process.returncode
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def message_parse(msg_code):

	if msg_code == 0:
		return { "message" : "Success"}
	elif msg_code == 1:
		return { "message" : "Only allow txt file" }
	elif msg_code == 2:
		return { "message" : "Invalid txt file"}
	elif msg_code == 3:
		return { "message" : "Invalid hotword string"}
	elif msg_code == 4:
		return { "message" : "Invalid/Long input string. Add comma or newline between each hotword"}
	
@app.route('/')
def upload_form():
	return render_template('upload.html')

@app.route('/update', methods=['POST'])
@cross_origin(supports_credentials=True)
def upload_file():
	if request.method == 'POST':
        # check if the post request has the file part
		#print(request.form)
		# File upload - request.file; String upload = request.form
		if 'file' not in request.files and 'file' not in request.form:
			STATUS=1
			print(request.form['file'])
			return message_parse(STATUS)

		# String upload
		if 'file' in request.form:
			hotword_tokens = []
			hotword_string = request.form['file']
			if "," in hotword_string:
				hotword_tokens = hotword_string.split(",")
				for hword in hotword_tokens:
					if len(hword.split()) > 5:
						STATUS=4
						return message_parse(STATUS)
			elif "\n" in hotword_string:
				hotword_tokens = hotword_string.split("\n")
				for hword in hotword_tokens:
					if len(hword.split()) > 5:
						STATUS=4
						return message_parse(STATUS)
			else:
				STATUS=3
				return message_parse(STATUS)
			filename = str(uuid.uuid4()) + ".txt"
			outfile=os.path.join(app.config['UPLOAD_FOLDER'], filename)
			with open(outfile, "w") as hf:
				for hword in hotword_tokens:
					hf.write(hword.lower().strip() + "\n")
			
			# validate file
			STATUS = validate_hotwordFile(outfile)

			# update hotword list			
			if STATUS == 0:
				update_hotword_ASR(outfile)

			return message_parse(STATUS)

		# File upload
		file = request.files['file']

		if file.filename == '':
			STATUS=1
			return message_parse(STATUS)

		if file and allowed_file(file.filename):
		
			# 1. save uploaded file
			filename = secure_filename(file.filename)
			outfile=os.path.join(app.config['UPLOAD_FOLDER'], filename)
			file.save(outfile)
		
			# 2. validate file
			STATUS = validate_hotwordFile(outfile)
			
			# 3. update hotword list
			if STATUS == 0:
				update_hotword_ASR(outfile)
				
			return message_parse(STATUS)
		else:
			STATUS = 1
			return message_parse(STATUS)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
