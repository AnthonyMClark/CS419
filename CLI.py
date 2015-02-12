import curses, time, subprocess
from curses import panel
import MySQLdb
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import os,datetime
import re
import email

color= curses.initscr()
curses.start_color()
curses.init_pair(1,curses.COLOR_BLACK, curses.COLOR_WHITE) 
curses.init_pair(2,curses.COLOR_WHITE, curses.COLOR_BLUE)
curses.init_pair(3,curses.COLOR_WHITE, curses.COLOR_CYAN)
textcolor = curses.color_pair(1) 
bcolor = curses.color_pair(2)
altcolor = curses.color_pair(3)

def retDate(date, time):
	splitTime = time.split('-')
	startTime = splitTime[0]
	date_in = date + ' ' + startTime
	date_in = re.sub(r"(st|nd|rd|th),", ",", date_in)
	dt = datetime.datetime.strptime(date_in, '%B %d, %Y %I:%M%p')
	return dt
def sendEmail(r):

	subject = 'Advising Signup Cancellation'
	body = """
	Advising Signup with %s, %s %s CANCELLED
	<br>Name: %s %s
	<br>Email: %s 
	<br>Date: %s 
	<br>Time: %s 
	<br><br>Please contact support@engr.oregonstate.edu if you experience problems
	"""
	body = body % (r['advLastName'], r['advFirstName'], r['status'], r['stuFirstName'], r['stuLastName'], r['stuEmail'], r['date'], r['time'])
	#SET SOME VARS AND PASS TO GET DATE/TIME
	date = r['date']
	time = r['time']
	dt = retDate(date, time)
	body = "" + body + ""
	#SET UP THE ATTACHMENT 
	emailer = r['stuEmail']
	emailed = r['advEmail']
	CRLF = "\r\n"
	login = "senderEmail@onid.oregonstate.edu"
	password = "senderEmailPW"
	attendees = ["receiverEmail@gmail.com"]
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

class Show(object):

	def __init__(self, items, stdscreen):
		self.window = stdscreen.subwin(0,0)
		self.window.keypad(1)		
		self.panel = panel.new_panel(self.window)
		self.panel.hide()
		panel.update_panels()
		
		self.position = 0
		self.items = items
		self.items.append(('exit','exit'))
		
	def navigate(self, n):
		self.position += n
		if self.position < 0:
			self.position = 0
		elif self.position >= len(self.items):
			self.position = len(self.items)-1 
	
	def display(self):
		self.panel.top()
		self.panel.show()
		self.window.clear()
		list = []
		r = 'stop'
		db = MySQLdb.connect("mysql.eecs.oregonstate.edu", "cs419-group8", "XRjPU38XAnEXEtjZ", "cs419-group8")
		cursor = db.cursor()
		# Prepare SQL query to INSERT a record into the database.
		sql = "SELECT * FROM appointment WHERE status = 'confirmed'"
		cursor.execute(sql)
		# Fetch all the rows in a list of lists.
		for row in cursor.fetchall():
			appt = {
				'id' : row[0],
				'date' : row[1],
				'advFirstName' : row[2],
				'advLastName' : row[3],
				'advEmail' : row[4],
				'stuFirstName' : row[5],
				'stuLastName' : row[6],
				'stuEmail' : row[7],
				'status' : row[8],
				'time' : row[9]
			}
			list.append(appt)
		search_term = None	
		
		while search_term != 'q':
			color.border('|', '|', '-', '-', '+', '+', '+', '+')
			#break out of the while loop on q
			self.window.addstr(2, 25, 'Enter q to quit listing appointments')
			#PRINT THE RECORDS WE WANT FROM THE DB
			for index,record in enumerate(list):
				self.window.addstr(index+4, 2, str(record['id']))
				self.window.addstr(index+4, 6, str(record['date']))
				self.window.addstr(index+4, 29, str(record['stuFirstName']))
				self.window.addstr(index+4, 51, str(record['stuLastName']))
				self.window.addstr(index+4, 68, str(record['time']))
			search_term = None
			#GET ID INPUT FROM USER
			self.window.addstr(1, 25, 'Enter appointment to delete:')
			curses.curs_set(1)	
			curses.echo()
			search_term = self.window.getstr(1,53,4)			
			self.window.addstr(1, 54, search_term)
			self.window.clear()
			curses.doupdate()
			curses.curs_set(0)
			#CHANGE TO CANCELLED WITH ID SPECIFIED
			cursor.execute ("""UPDATE appointment SET status = 'cancelled' WHERE id=%s""", (search_term))
			#Email notification needs to be sent for cancelled appointment
			if(search_term != '\n' or search_term != 'q'): 
				for index,record in enumerate(list):	
					if search_term in str(record['id']):
						r = record
						break
				if(r == 'stop'):
					r = ''
				else:
					sendEmail(r)
					if(len(list) != 0):
						if(search_term != 'q'):
							list.pop(index)
					
			self.window.clear()
			

			

				
		self.window.clear()
		self.panel.hide()
		panel.update_panels()
		curses.doupdate()	


class Menu(object):

	def __init__(self, items, stdscreen):
		self.window = stdscreen.subwin(0,0)
		self.window.keypad(1)		
		self.panel = panel.new_panel(self.window)
		self.panel.hide()
		panel.update_panels()
		
		self.position = 0
		self.items = items
		self.items.append(('exit','exit'))
		
	def navigate(self, n):
		self.position += n
		if self.position < 0:
			self.position = 0
		elif self.position >= len(self.items):
			self.position = len(self.items)-1 
	
	def display(self):
		self.panel.top()
		self.panel.show()
		self.window.clear()
		
		while True:
			self.window.refresh()
			curses.doupdate()
			color.border('|', '|', '-', '-', '+', '+', '+', '+')
			string = 'Simplified Advising Appointment Management'
			self.window.addstr(1, 22, string, textcolor)
			credit = 'CS419 Final Project: Anthony Clark, Jennifer Anderson, Ryan Farber'
			self.window.addstr(2, 10, credit, textcolor)
			
			for index, item in enumerate(self.items):
				if index == self.position:
					font = textcolor
				else:
					font = curses.A_NORMAL
					
				msg = '%d. %s' % (index, item[0])
				self.window.addstr(5+index, 1, msg, font)
			
			key = self.window.getch()
		
			if key in [curses.KEY_ENTER, ord('\n')]:
				if self.position == len(self.items)-1:
					break
				else:
					self.items[self.position][1]()
			
			elif key == curses.KEY_UP:
				self.navigate(-1)
				
			elif key == curses.KEY_DOWN:
				self.navigate(1)
				
		self.window.clear()
		self.panel.hide()
		panel.update_panels()
		curses.doupdate()		
		
class Project(object):



	def __init__(self, stdscreen):
		self.screen = stdscreen
		color.bkgdset(bcolor)
		curses.curs_set(0)
		 
		showz = []
		creditz = []
		 
		showing = Show(showz, self.screen) 
		menu_items = [
				('Remove Appointment', showing.display)
				]
			
		main_menu = Menu(menu_items, self.screen)
		main_menu.display()
		
		
if __name__ == '__main__':
	curses.wrapper(Project)