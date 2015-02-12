#!/usr/bin/python
#THIS FILE IS FOR TESTING ONLY, IT IS NOT REQUIRED FOR INSTALLATION. Switch the confirmed in line 13 to cancelled to test cancellations
import smtplib

server = 'smtp.gmail.com'
port = 587
password = 'password'

sender = 'sender@onid.oregonstate.edu'
recipient = 'receiver@engr.orst.edu'
subject = 'Advising Signup with McGrath, D Kevin confirmed for Brabham, Matthew Lawrence'
body = """
Advising Signup with McGrath, D Kevin confirmed 
Name: REDACTED 
Email: REDACTED @oregonstate.edu
Date: Wednesday, November 21st, 2012
Time: 1:00pm - 1:15pm


Please contact support@engr.oregonstate.edu if you experience problems
"""
 
body = "" + body + ""

headers = ["From: " + sender,
          "Subject: " + subject,
          "To: " + recipient,
          "MIME-Version: 1.0",
          "Content-Type: text/html"]
headers = "\r\n".join(headers)

session = smtplib.SMTP(server, port)

session.ehlo()
session.starttls()
session.ehlo
session.login(sender, password)

session.sendmail(sender, recipient, headers + "\r\n\r\n" + body)
session.quit()
