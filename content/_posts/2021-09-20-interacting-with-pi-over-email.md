---
title: Interacting with Raspberry Pi over Email
cover: /assets/images/email-icon.jpg
tags: coding
---


If you are using a Raspberry Pi as a server for your trading, it is not always convenient to `ssh` in. For example, if 
you are not on the same network as your Pi. Regardless, it is important that you are always able to manage your trading bots. 
The most robust method to do this is to use a third-party service to gain remote access, as explained in 
[this article](https://magpi.raspberrypi.org/articles/remote-access-your-raspberry-pi-securely). 
However, this can be slow and tedious, especially for benign tasks, such as checking on actively deployed bots or reading log 
files. To get around this, you can use a simple Python script to read a dedicated email inbox, and use this as a gateway to the 
command line. Read on to find out how.


## The General Idea
The general idea behind this script involves a `while True` conditional, allowing the script to run perpetually. When the script
first starts up, it will count the total number of emails in the inbox. Each loop will repeat this, counting how many emails there 
are. Then, if the number of emails change from one iteration to the next, it implies that a new email has been recieived. In this case,
the latest email will be downloaded and read. 

In the example script below, the subject line is used to tell the code what action to perform. In this case, an email with a subject of
'run' will indicate that the body contains a command to be run. So that is what happens - the body of the email will be passed into 
`subprocess.check_output()`. This method runs the input on the command line, and takes note of the output. The script will then send 
an email to the address specified in `receiver_email` containing the command line output. 


## Dependencies
The following dependencies are required for this to work.

```py
import email
import imaplib
import time
import subprocess
import smtplib, ssl
```

## The Script
An example script is provided below.

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
    receiver_email = "your_email@gmail.com"  # Enter receiver address
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
Since we want the script to continue running, even after we exit ssh session, we need to use the `nohup` command when running it.
This stands for 'no hangup', as it will allow a process to continue to run after logging out. The ampersand `&` at the end of the command
signals to run it as a background process, meaning you can comtinue to use the same terminal after hitting enter.

```
nohup python3 receive_email.py &
```
