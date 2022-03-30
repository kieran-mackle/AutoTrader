# Setting up a Host Email Account


To send emails from python, you will need to configure a host email account which allows sending emails over python. See [here](https://realpython.com/python-send-email/#option-1-setting-up-a-gmail-account-for-development) for more information.

Once you have your host account set up, you can add the details to the global configuration file, as shown below. Note that the key 
`MAILING_LIST` can contain as many emails as you would like.

```yaml
EMAILING:
  HOST_ACCOUNT:
    email: "host_email@gmail.com"
    password: "password123"
  MAILING_LIST:
    FirstName_LastName: 
      title: "Mr"
      email: "your_personal_email@gmail.com"
```
