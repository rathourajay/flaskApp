import re


def check_google_emails(email):
    m = email_host_regex.findall(email)
    if m and len(m) > 0:
            host = m[0]
            if host and host != '':
                    host = host.lower()
            print host
            if host == "gmail.com":
                return True
            else:
                return False
                
    return False
    
    
if __name__ == '__main__':
    email_host_regex = re.compile(".*@(.*)$")
    email_lists = ['asr.rathour@gmail.com','adr.rathour@gmail.com','asr.rathour@yahoo.com','asr.rathour@gmail123.com']
    for email in email_lists:
        result = check_google_emails(email)
        
        
        if result:
            print email+" is from gmail"
        else:
            print email+" is not from gmail"
        