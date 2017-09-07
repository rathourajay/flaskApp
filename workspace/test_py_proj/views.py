from django.shortcuts import render
from django.shortcuts import render_to_response
import re
import dns.resolver

###################### first time go to the home page##############
def first_page(request):     
    return render_to_response('gmail_app/home1.html')

def gmail_scanner(request):
    flag = 0
    email_host_regex = re.compile(".*@(.*)$")
    gmail_servers_regex = re.compile("(.google.com.|.googlemail.com.|.psmtp.com.|hostedemail.com.)$", re.IGNORECASE)
    context_dict = {}
    if request.method == 'GET':
        all_emails = request.GET.get('mytextbox')
        email_list = all_emails.split(',')
        google_mail = []
        for email in email_list:
            m = email_host_regex.findall(email)
            email_host_regex = re.compile(".*@(.*)$")
            if m and len(m) > 0:
                    host = m[0]
                    if host and host != '':
                            host = host.lower()
                    if host == "gmail.com":
                        google_mail.append(email)
                    else:
                        answers = dns.resolver.query(host, 'MX')
                        for rdata in answers:
                                m = gmail_servers_regex.findall(str(rdata.exchange))
                                if m and len(m) > 0:
                                    flag = 1
                                else:
                                    flag = 0
                                    print "not hosted on gmail"
                        if flag == 1:
                            google_mail.append(email)
        context_dict['total_data'] = google_mail
    return render(request, 'gmail_app/home1.html',{
        'emails': google_mail,
    })
