---
title: Interacting with a Raspberry Pi Over Email
cover: /assets/images/email-icon.jpg
tags: coding
---


If you are using a Raspberry Pi as a server for your trading, 


## Dependencies

```py
import email
import imaplib
import time
import subprocess
import smtplib, ssl
```


## The Script
```py
# receive_email.py

import email
import imaplib
import time
import subprocess
import smtplib, ssl

EMAIL = 'email@gmail.com'
PASSWORD = 'password'
SERVER = 'imap.gmail.com'

def send_response(response):
    
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = EMAIL  # Enter your address
    receiver_email = "kemackle98@gmail.com"  # Enter receiver address
    password = PASSWORD
    message = str(response)
    
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

prev_emails = 0
while True:
    # Refresh
    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select('inbox')
    status, data = mail.search(None, 'ALL')
    mail_ids = []
    
    for block in data:
        mail_ids += block.split()
    
    # Count current emails in inbox
    current_emails = len(mail_ids)
    
    if current_emails != prev_emails:
        # New email detected
        print("New email recieved.")
        
        i = mail_ids[-1]
        status, data = mail.fetch(i, '(RFC822)')
        
        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                mail_from = message['from']
                mail_subject = message['subject']
                
                if message.is_multipart():
                    mail_content = ''
        
                    for part in message.get_payload():
                        if part.get_content_type() == 'text/plain':
                            mail_content += part.get_payload()
                else:
                    mail_content = message.get_payload()
                
                # Process email
                if mail_subject.lower() == 'run':
                    print("Run command received:")
                    print(mail_content)
                    
                    # Run command 
                    print("Running...")
                    try:
                        raw_response = subprocess.check_output(mail_content.strip('\r\n').split())
                        print("Done.")
                        response = raw_response.decode("utf-8")
                        
                    except:
                        print("Exception occurred.")
                        response = 'Exception occurred. Check command and try again.'
                    
                    
                elif mail_subject.lower() == 'status':
                    raw_response = 0 # what do i want this to mean?
                    response = None
                    
                else:
                    print("Ignoring.")
                    response = None
                
                
                # Reply back
                if response is not None:
                    print("Sending response...")
                    send_response(response)
                    print("Done.\n") 
                    
        # Update email count
        prev_emails = current_emails
    
    # Sleep for 30 seconds
    time.sleep(10)
```


## Running the Script


```
nohup python3 receive_email.py &
```
