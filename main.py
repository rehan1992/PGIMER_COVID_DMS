from flask import Flask, render_template, request, redirect, url_for, send_file, session, g
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

from datetime import date, time, datetime, timedelta
from waitress import serve

import pandas
import imgkit

app = Flask(__name__)
app.secret_key = 'MaximusDecimusMeridiusCovid190089!'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://sql12384356:A22IAvmrwC@sql12.freemysqlhosting.net:3306/sql12384356'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

path_wkthmltoimage = "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltoimage.exe"
config=imgkit.config(wkhtmltoimage=path_wkthmltoimage)

db = SQLAlchemy(app)

class  User:
	"""A user for login"""
	def __init__(self, id, username, password):
		self.id = id
		self.username = username
		self.password = password

class PatientData(db.Model):
	CRnum = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	PR = db.Column(db.Float)
	BP_SYSTOLIC = db.Column(db.Float)
	BP_DIASTOLIC = db.Column(db.Float)
	TEMPERATURE = db.Column(db.Float)
	RR = db.Column(db.Float)
	SPO2 = db.Column(db.Float)
	RBS = db.Column(db.Integer)
	Oxygen_Device = db.Column(db.String(200))
	FIO2 = db.Column(db.Float)
	OTHER = db.Column(db.String(1000))
	REMARKS = db.Column(db.String(1000))
	GCS = db.Column(db.String(100))
	URINE = db.Column(db.Float)
	INOTROPE = db.Column(db.String(100))
	POSITION = db.Column(db.String(100))
	INTAKE = db.Column(db.String(100))
	STEROIDS = db.Column(db.String(200)) # none
	ANTIBIOTICS = db.Column(db.String(200)) # These three can be null
	CLEXANE = db.Column(db.String(200)) # null
	DATE = db.Column(db.Date, primary_key=True)
	TIME = db.Column(db.Time, primary_key=True)
	Discharged = db.Column(db.Boolean)


users = []
users.append(User(id=1,username="icu",password="Deci9!"))
users.append(User(id=2,username="admin",password="Meri19!"))

@app.before_request
def before_request():
	g.user = None

	if 'user_id' in session:
		user = [x for x in users if x.id == session['user_id']][0]
		g.user = user

@app.route("/")
def home():
	if not g.user:
		return redirect(url_for('login'))

	alldata = PatientData.query.filter_by(Discharged=False).order_by(PatientData.DATE,PatientData.TIME).all()
	return render_template("home.html", alldata=alldata)

@app.route("/login", methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		session.pop('user_id', None)

		username = request.form['username']
		password = request.form['password']

		userA = [x for x in users if x.username == username]
		if userA and userA[0].password == password:
			session['user_id'] = userA[0].id
			return redirect(url_for('home'))

		return redirect(url_for('login'))

	return render_template("login.html")

@app.route("/addpatient")
def addpatient():
	if not g.user:
		return redirect(url_for('login'))

	return render_template("addpatient.html")

@app.route("/viewpatient")
def viewpatient():
	if not g.user:
		return redirect(url_for('login'))

	crnum = request.args.get('crnum', default='', type=int)
	patiententries = PatientData.query.filter_by(CRnum=crnum).order_by(PatientData.DATE,PatientData.TIME).all()
	return render_template("viewpatient.html", patiententries=patiententries)

@app.route("/editpatient")
def editpatient():
	if not g.user:
		return redirect(url_for('login'))

	crnum = request.args.get('crnum', default='', type=int)
	name = request.args.get('name', default='', type=str)
	return render_template("editpatient.html", crnum=crnum, name=name)

@app.route("/dischargepatient")
def dischargepatient():
	if not g.user:
		return redirect(url_for('login'))

	crnum = request.args.get('crnum', default='', type=int)
	patiententries = PatientData.query.filter_by(CRnum=crnum).order_by(PatientData.DATE,PatientData.TIME).all()
	return render_template("dischargepatient.html", crnum=crnum, patiententries=patiententries)

@app.route("/exportdata")
def exportdata():
	if not g.user:
		return redirect(url_for('login'))

	startdate = datetime.today().date()
	enddate = startdate

	starttime = (datetime.now()-timedelta(hours=3)).time()
	endtime = datetime.now().time()

	shiftdata = PatientData.query.filter(PatientData.DATE == startdate,
		PatientData.TIME.between(starttime, endtime)).order_by(PatientData.DATE,PatientData.TIME).all()
	
	if endtime < starttime:
		startdate = (datetime.today()-timedelta(days=1)).date()
		shiftdata1 = PatientData.query.filter(PatientData.DATE == startdate,
			PatientData.TIME.between(starttime, time(hour=23,minute=59,second=59))).order_by(PatientData.DATE,PatientData.TIME).all()
		shiftdata2 = PatientData.query.filter(PatientData.DATE == enddate,
			PatientData.TIME.between(time(hour=0,minute=0,second=0), endtime)).order_by(PatientData.DATE,PatientData.TIME).all()
		shiftdata = shiftdata1 + shiftdata2

	return render_template("exportdata.html", shiftdata=shiftdata)

@app.route("/generatejpeg", methods=['POST'])
def generatejpeg():
	if not g.user:
		return redirect(url_for('login'))
	
	startdate = datetime.today().date()
	enddate = startdate

	starttime = (datetime.now()-timedelta(hours=3)).time()
	endtime = datetime.now().time()

	shiftdata = PatientData.query.filter(PatientData.DATE == startdate,
		PatientData.TIME.between(starttime, endtime)).order_by(PatientData.DATE,PatientData.TIME).all()
	
	if endtime < starttime:
		startdate = (datetime.today()-timedelta(days=1)).date()
		shiftdata1 = PatientData.query.filter(PatientData.DATE == startdate,
			PatientData.TIME.between(starttime, time(hour=23,minute=59,second=59))).order_by(PatientData.DATE,PatientData.TIME).all()
		shiftdata2 = PatientData.query.filter(PatientData.DATE == enddate,
			PatientData.TIME.between(time(hour=0,minute=0,second=0), endtime)).order_by(PatientData.DATE,PatientData.TIME).all()
		shiftdata = shiftdata1 + shiftdata2

	currshift = request.form['currshift']
	nextshift = request.form['nextshift']

	imgkit.from_string(render_template("makedatafile.html", startdate=startdate.strftime("%b %d %Y"), enddate=enddate.strftime("%b %d %Y"), 
	starttime=starttime.strftime("%H:%M:%S"), endtime=endtime.strftime("%H:%M:%S"),
	 shiftdata=shiftdata, currshift=currshift, nextshift=nextshift), 
	 "outputdata.jpg", options={"format" : "jpg"}, config=config)

	#fp = open("outputdata.html", "w")
	#print("Trying to write")
	#fp.write(render_template("makedatafile.html", shiftdata=shiftdata, currshift=currshift, nextshift=nextshift))
	#fp.close()

	#print("Trying to make image")
	#imgkit.from_file("outputdata.html", "outputdata.jpg", options={"format" : "jpg"})

	try:
		return send_file("outputdata.jpg",attachment_filename='outputdata.jpg')
		#return redirect(url_for('home'))
	except Exception as e:
		return str(e)


@app.route("/enternewpatientdata", methods=['POST'])
def enternewpatientdata():
	if not g.user:
		return redirect(url_for('login'))

	#ID name PR BP_SYSTOLIC BP_DIASTOLIC TEMPERATURE RR SPO2 RBS Oxygen_Device FIO2 OTHER REMARKS GCS URINE INOTROPE POSITION INTAKE STEROIDS ANTIBIOTICS CLEXANE DATE TIME Discharged
	CRnum = request.form['CRnum']
	name = request.form['name']
	PR = request.form["PR"]
	BP_SYSTOLIC = request.form['BP_SYSTOLIC']
	BP_DIASTOLIC = request.form['BP_DIASTOLIC']
	TEMPERATURE = request.form['TEMPERATURE']
	RR = request.form['RR']
	SPO2 = request.form['SPO2']
	RBS = request.form['RBS']
	Oxygen_Device = request.form['Oxygen_Device']
	FIO2 = request.form['FIO2']
	OTHER = request.form['OTHER']
	REMARKS = request.form['REMARKS']
	GCS = request.form['GCS']
	URINE = request.form['URINE']
	INOTROPE = request.form['INOTROPE']
	POSITION = request.form['POSITION']
	INTAKE = request.form['INTAKE']
	STEROIDS = request.form['STEROIDS']
	ANTIBIOTICS = request.form['ANTIBIOTICS']
	CLEXANE = request.form['CLEXANE']
	DATE = date.today()
	TIME = datetime.now().time()
	Discharged = False

	newpatientdata = PatientData(CRnum=CRnum, name=name, PR=PR, BP_SYSTOLIC=BP_SYSTOLIC, BP_DIASTOLIC=BP_DIASTOLIC, TEMPERATURE=TEMPERATURE, RR=RR, SPO2=SPO2, RBS=RBS, Oxygen_Device=Oxygen_Device, FIO2=FIO2, OTHER=OTHER, REMARKS=REMARKS, GCS=GCS, URINE=URINE, INOTROPE=INOTROPE, POSITION=POSITION, INTAKE=INTAKE, STEROIDS=STEROIDS, ANTIBIOTICS=ANTIBIOTICS, CLEXANE=CLEXANE, DATE=DATE, TIME=TIME, Discharged=Discharged)
	db.session.add(newpatientdata)
	db.session.commit()
	return redirect(url_for('home'))
	#return str(CRnum)+ "<br>" + name + "<br>" + str(PR) + "<br>" + str(BP_SYSTOLIC) + "<br>" + str(BP_DIASTOLIC) + "<br>" + str(TEMPERATURE) + "<br>" + str(RR) + "<br>" + str(SPO2) + "<br>" + str(RBS) + "<br>" + Oxygen_Device + "<br>" + str(FIO2) + "<br>" + OTHER + "<br>" + REMARKS + "<br>" + GCS + "<br>" + str(URINE) + "<br>" + INOTROPE + "<br>" + POSITION + "<br>" + INTAKE + "<br>" + STEROIDS + "<br>" + ANTIBIOTICS + "<br>" + CLEXANE + "<br>" + str(DATE) + "<br>" + TIME + "<br>" + str(Discharged)
 
@app.route("/enterpatientdata", methods=['POST'])
def enterpatientdata():
	if not g.user:
		return redirect(url_for('login'))

	crnum = request.args.get('crnum', default='', type=int)
	name = request.args.get('name', default='', type=str)
	PR = request.form["PR"]
	BP_SYSTOLIC = request.form['BP_SYSTOLIC']
	BP_DIASTOLIC = request.form['BP_DIASTOLIC']
	TEMPERATURE = request.form['TEMPERATURE']
	RR = request.form['RR']
	SPO2 = request.form['SPO2']
	RBS = request.form['RBS']
	Oxygen_Device = request.form['Oxygen_Device']
	FIO2 = request.form['FIO2']
	OTHER = request.form['OTHER']
	REMARKS = request.form['REMARKS']
	GCS = request.form['GCS']
	URINE = request.form['URINE']
	INOTROPE = request.form['INOTROPE']
	POSITION = request.form['POSITION']
	INTAKE = request.form['INTAKE']
	STEROIDS = request.form['STEROIDS']
	ANTIBIOTICS = request.form['ANTIBIOTICS']
	CLEXANE = request.form['CLEXANE']
	DATE = date.today()
	TIME = datetime.now().time()
	Discharged = False

	newpatientdata = PatientData(CRnum=crnum, name=name, PR=PR, BP_SYSTOLIC=BP_SYSTOLIC, BP_DIASTOLIC=BP_DIASTOLIC, TEMPERATURE=TEMPERATURE, RR=RR, SPO2=SPO2, RBS=RBS, Oxygen_Device=Oxygen_Device, FIO2=FIO2, OTHER=OTHER, REMARKS=REMARKS, GCS=GCS, URINE=URINE, INOTROPE=INOTROPE, POSITION=POSITION, INTAKE=INTAKE, STEROIDS=STEROIDS, ANTIBIOTICS=ANTIBIOTICS, CLEXANE=CLEXANE, DATE=DATE, TIME=TIME, Discharged=Discharged)
	db.session.add(newpatientdata)
	db.session.commit()
	return redirect(url_for('home'))

@app.route("/discharge", methods=['POST'])
def discharge():
	if not g.user:
		return redirect(url_for('login'))

	crnum = request.args.get('crnum', default='', type=int)
	patiententries = PatientData.query.filter_by(CRnum=crnum).order_by(PatientData.DATE,PatientData.TIME).all()
	for entry in patiententries:
		entry.Discharged = True
	db.session.commit()
	return redirect(url_for('home'))

#if __name__ == "__main__":
#	app.run(debug=True)

serve(app, host='192.168.42.153', port=80, threads=1)
