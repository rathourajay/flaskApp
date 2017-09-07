from django.shortcuts import render
import time
import random
from django.shortcuts import render_to_response
import requests
import json
import os
from os.path import expanduser

###################### first time go to the home page##############


def first_page(request):
    return render_to_response('gmail_app/home1.html')


def gmail_scanner(request):
    count = 0
    if request.method == 'POST':
        mail_addr = request.POST.get('mytextbox')
        if '@' in mail_addr:
            #         if mail_addr and not ',' in mail_addr:
            msg = ''
            msg = 'valid'
#             final_resp, msg = get_server_response(gmail_addr)

            return render(request, 'gmail_app/home1.html', {
                'msg': msg,
            })

        elif request.FILES:
            docfile = request.FILES.get('file1')
            data_file = docfile.readlines()
            completeName = expanduser("~\Desktop\gmail_scanner_output.txt")
            fop = open(completeName, 'wb')
            data_file = [data.replace('\n', '') for data in data_file if data]
            for email in data_file:
                msg = ''
                sleep_time = random.randint(2, 7)
                time.sleep(sleep_time)
                gmail_addr = email.replace('\n', '').replace(
                    '\r', '').replace('\t', '').strip()
                count += 1
                msg = 'valid'
#                 final_resp, msg = get_server_response(gmail_addr)
                msg = gmail_addr + " ====>> " + msg
                fop.write(msg)
                fop.write('\n')
                sleep_time1 = random.randint(1, 5)
                time.sleep(sleep_time1)
            return render(request, 'gmail_app/home1.html', {
                'msg': 'Your file has been downloaded to your desktop',
            })

    return render(request, 'gmail_app/home1.html', {
        'msg': 'Please provide valid input, Do not use ,',
    })


def get_server_response(gmail_addr):
    url = 'https://accounts.google.com/InputValidator?resource=SignUp&service=mail'
    payload = {"input01": {"Input": "GmailAddress", "GmailAddress":
                           gmail_addr, "FirstName": "", "LastName": ""}, "Locale": "en"}
    headers = {'Content-type': 'application/json',
               'Accept': 'application/json'}

    r = requests.post(url, data=json.dumps(payload), headers=headers)
    final_resp = r.json()
    if final_resp['input01']['Valid'] == 'true':
        msg = "Email not associated with gmail"
    else:
        msg = final_resp['input01']['ErrorMessage']
    return final_resp, msg
