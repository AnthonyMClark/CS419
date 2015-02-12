#!/usr/bin/python
#http://stackoverflow.com/questions/4823574/sending-meeting-invitations-with-python USED FOR EMAIL ATTACHMENTS
import MySQLdb
from optparse import OptionParser
from email.parser import Parser
import os.path
import sys
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import os,datetime
import re
import email

def parseBody(filename):
    #Returns the contents of filename as a string - modified from using a file to the email piping directly.
	body = filename.lower() 
	split = body.split()
	status = ""
	time = ""
	date = ""
	if 'cancelled' in split:
		status = 'cancelled'
	else:
		status = 'confirmed'
	if 'time:' in body:
		time = split[split.index('time:') + 1] 
		date = split[split.index('time:') - 3] + ' ' + split[split.index('time:') - 2] + ' ' + split[split.index('time:') - 1]
	return time, date, status
			
			
			
def parseHeader(filename):
	headers = Parser().parsestr(filename)
	#print emailee
	emailee =  headers['to']
	#print emailer
	emailer = headers['from']
	subject = headers['subject']
	#print subject
	subjectLine = headers['subject']
	headSplit = subjectLine.split()
	#Get the appointment requesters last name from the subject line and remove the ,
	lastName = (headSplit[8])[:-1]
	#Get the appointment requesters first name from the subject line and add item 10 for the middle name
	firstName = headSplit[9] + ' ' + headSplit[10]
	#Get the appointment advisor's last name from the subject line and remove the ,
	advLastName = (headSplit[3])[:-1]
	#Get the appointment advisor's first name from the subject line
	advFirstName = headSplit[4] + ' ' + headSplit[5]
	return firstName, lastName, advFirstName, advLastName, emailee, emailer, subject
	
	
def updateDB(firstName, lastName, advFirstName, advLastName, emailee, emailer, subject, date, time, status):
	# Open database connection host, user, pwd, db
	db = MySQLdb.connect("mysql.eecs.oregonstate.edu", "cs419-group8", "XRjPU38XAnEXEtjZ", "cs419-group8") 
	# prepare a cursor object using cursor() method to execute queries 
	cursor = db.cursor()
	#print status
	if status == 'confirmed':
		try:
		   #Execute the SQL command
			cursor.execute('INSERT INTO appointment (stuFirstName, stuLastName, stuEmail, advFirstName, advLastName, advEmail, date, time, status )	VALUES ("%s","%s","%s","%s","%s","%s","%s","%s","%s")' % (firstName,lastName,emailer,advFirstName,advLastName,emailee,date,time,status))
		   #Commit your changes in the database
			db.commit()
		except:
		   # Rollback in case there is any error
		   db.rollback()
		# disconnect from server
		db.close()
	elif status == 'cancelled':
		try:
		   #Execute the SQL command
			#cursor.execute('DELETE FROM appointment WHERE stuFirstName, stuLastName, stuEmail, advFirstName, advLastName, advEmail, date, time, status = "%s","%s","%s","%s","%s","%s","%s","%s","%s"' % firstName,lastName,emailer,advFirstName,advLastName,emailee,date,time,status)
		   #Commit your changes in the database
			cursor.execute ("""UPDATE appointment SET status = %s WHERE date=%s AND time=%s""", (date, time))
			db.commit()
		except:
		   # Rollback in case there is any error
		   db.rollback()
		# disconnect from server
		db.close()
def retDate(date, time):
	splitTime = time.split('-')
	startTime = splitTime[0]
	#endTime = splitTime[1]
	#print endTime
	date_in = date + ' ' + startTime
	date_in = re.sub(r"(st|nd|rd|th),", ",", date_in)
	dt = datetime.datetime.strptime(date_in, '%B %d, %Y %I:%M%p')
	return dt
	
def sendEmail(firstName, lastName, advFirstName, advLastName, emailee, emailer, subject, date, time, status):
	#open and write nothing to the file, so that it deletes and we can rewrite into it for testing
	#open('testFile.txt', 'w').close()
	dt = retDate(date, time)
	#print dt
	if status == 'confirmed':
		subject = ("Advising Signup with %s, %s confirmed for %s, %s" % (advLastName, advFirstName, lastName, firstName))
		body = """
		Advising Signup with %s, %s %s confirmed
		<br>Name: %s 
		<br>Email: %s  
		<br>Date: %s  
		<br>Time: %s  
		<br><br>Please contact support@engr.oregonstate.edu if you experience problems
		"""
		body = body % (advLastName, advFirstName, status, firstName + lastName, emailer, date, time)
	else: 
		subject = 'Advising Signup Cancellation'
		body = """
		Advising Signup with %s, %s %s CANCELLED
		<br>Name: %s 
		<br>Email: %s 
		<br>Date: %s 
		<br>Time: %s 
		<br><br>Please contact support@engr.oregonstate.edu if you experience problems
		"""
		body = body % (advLastName, advFirstName, status, firstName + ' ' + lastName, emailer, date, time)

	 
	body = "" + body + ""
	#SET UP THE ATTACHMENT 
	CRLF = "\r\n"
	login = "sender@onid.oregonstate.edu"
	password = "emailPW"
	attendees = ["receiver@gmail.com"]
	organizer = "ORGANIZER;CN=organiser:mailto:first"+CRLF+" @gmail.com"
	fro = emailer
	
	ddtstart = dt
	dur = datetime.timedelta(hours = .25)
	dtend = ddtstart + dur
	dtstamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
	dtstart = ddtstart.strftime("%Y%m%dT%H%M%S")
	dtend = dtend.strftime("%Y%m%dT%H%M%S")
	description = "DESCRIPTION: Advising appointment scheduled"+CRLF
	attendee = ""
	#REQUEST = 0 MOTHOD:REQUEST
	#CANCEL = 1  METHOD:CANCEL
	if(status == 'confirmed'):
		methodType = 'REQUEST'
		seqType = '0'
	if(status == 'cancelled'):
		methodType = 'CANCEL'
		seqType = '1'
	
	for att in attendees:
		attendee += "ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-    PARTICIPANT;PARTSTAT=ACCEPTED;RSVP=TRUE"+CRLF+" ;CN="+att+";X-NUM-GUESTS=0:"+CRLF+" mailto:"+att+CRLF
	ical = "BEGIN:VCALENDAR"+CRLF+"PRODID:pyICSParser"+CRLF+"VERSION:2.0"+CRLF+"CALSCALE:GREGORIAN"+CRLF
	ical+="METHOD:"+methodType+CRLF+"BEGIN:VEVENT"+CRLF+"DTSTART:"+dtstart+CRLF+"DTEND:"+dtend+CRLF+"DTSTAMP:"+dtstart+CRLF+organizer+CRLF
	ical+= "UID:FIXMEUID"+dtstamp+CRLF
	ical+= attendee+"CREATED:"+dtstamp+CRLF+description+"LAST-MODIFIED:"+dtstamp+CRLF+"LOCATION:"+CRLF+"SEQUENCE:"+seqType+CRLF+"STATUS:CONFIRMED"+CRLF
	ical+= "SUMMARY:"+subject+CRLF+"TRANSP:OPAQUE"+CRLF+"END:VEVENT"+CRLF+"END:VCALENDAR"+CRLF

	eml_body = body
	eml_body_bin = "This is the email body in binary - two steps"
	msg = MIMEMultipart('mixed')
	msg['Reply-To']=fro
	msg['Date'] = date
	msg['Subject'] = subject
	msg['From'] = fro
	msg['To'] = ",".join(attendees)

	part_email = MIMEText(eml_body,"html")
	part_cal = MIMEText(ical,'calendar;method=REQUEST')

	msgAlternative = MIMEMultipart('alternative')
	msg.attach(msgAlternative)

	ical_atch = MIMEBase('application/ics',' ;name="%s"'%("invite.ics"))
	ical_atch.set_payload(ical)
	Encoders.encode_base64(ical_atch)
	ical_atch.add_header('Content-Disposition', 'attachment; filename="%s"'%("invite.ics"))

	eml_atch = MIMEBase('text/plain','')
	Encoders.encode_base64(eml_atch)
	eml_atch.add_header('Content-Transfer-Encoding', "")

	msgAlternative.attach(part_email)
	msgAlternative.attach(part_cal)

	mailServer = smtplib.SMTP('smtp.gmail.com', 587)
	mailServer.ehlo()
	mailServer.starttls()
	mailServer.ehlo()
	mailServer.login(login, password)
	mailServer.sendmail(fro, attendees, msg.as_string())
	mailServer.close()
	#END ATTACHMENT
	
if __name__ == '__main__':
	full_email = sys.stdin.read()
	arg = full_email
	
	path = os.getcwd()
	#FOR TESTING
	#Path to file that will hold the email (be written to)
	path += '/419/test/testFile.txt'
	#open and write to file
	word = open(path, 'a')
	word.write(arg)
	#close the file
	word.close()
	
	parseHeader(arg) # get emails from header
	firstName, lastName, advFirstName, advLastName, emailee, emailer, subject = parseHeader(arg) #set fields returned by func
	parseBody(arg) # get the body
	time, date, status = parseBody(arg) #set fields returned by function
	updateDB(firstName, lastName, advFirstName, advLastName, emailee, emailer, subject, date, time, status)
	sendEmail(firstName, lastName, advFirstName, advLastName, emailee, emailer, subject, date, time, status)
 