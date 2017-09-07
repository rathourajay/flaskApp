import urllib
import xlrd
import MySQLdb
import urllib2
import os
import sys
import time
import os.path

from pyvirtualdisplay import Display
from selenium import webdriver
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from sec_data_app.models import get_xbrl, get_xbrl_only_date, get_xbrl_10Q, get_xbrl_only_date_10Q
from lxml import html
from sec_data import settings

PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))

import csv

database = MySQLdb.connect (host=settings.DATABASES['default']['HOST'], 
                            user = settings.DATABASES['default']['USER'], 
                            passwd = settings.DATABASES['default']['PASSWORD'], 
                            db = settings.DATABASES['default']['NAME'])
cursor = database.cursor()
def get_xbrlmain(request):
#     import pdb;pdb.set_trace()
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        text_ticker = request.POST.get('ticker') 
        text_ticker= text_ticker.split(',')
        if request.FILES:

            docfile = request.FILES.get('file1')
            data_file = docfile.readlines()
            data_file = [data.replace('\n','') for data in data_file if data]
#             data_file = data_file[0].split('\r')
            get_document_link(data_file,request,start_date,end_date)
        elif text_ticker:
            get_document_link(text_ticker,request,start_date,end_date)
    return render_to_response(
        'sec_data.html','',
       context_instance=RequestContext(request))

def get_parsed_source(base_url, target_url, raw=False):
#     import ipdb;ipdb.set_trace()
    html_opener = urllib2.urlopen(target_url)
    html_code = html_opener.read()
    if raw:
        return html_code
    parsed_source = html.fromstring(html_code, base_url)
    parsed_source.make_links_absolute()
    return parsed_source

def getText(src, xpath, index=0):
    tmp = src.xpath(xpath)
    if tmp and len(tmp) > index:
        return tmp[index].strip()
    else:
        return ""

# start_date = '20090101'
# end_date = '20141231'

base_url = 'http://www.sec.gov/'

def get_document_link(data_file,request,start_date,end_date):

    for ticker in data_file:

        print "Running for Ticker --->",ticker
        print "/n"
        if request.method == 'POST':
            form_type = request.POST.get('form_type')
            if form_type == "10-K":
                target_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+ticker.upper()+"&type=10-K&datea="+start_date+"&dateb="+end_date+"&owner=exclude&count=300"
                print target_url
            if form_type == "10-Q":
                target_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+ticker.upper()+"&type=10-Q&datea="+start_date+"&dateb="+end_date+"&owner=exclude&count=300"
            if form_type == "10-K/A":
                target_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+ticker.upper()+"&type=10-K/A&datea="+start_date+"&dateb="+end_date+"&owner=exclude&count=300" 
            if form_type == "10-Q/A":
                target_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+ticker.upper()+"&type=10-Q/A&datea="+start_date+"&dateb="+end_date+"&owner=exclude&count=300"
            if form_type == 'all':
                target_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+ticker.upper()+"&type=10-&datea="+start_date+"&dateb="+end_date+"&owner=exclude&count=300"
            parsed_source = get_parsed_source(base_url, target_url)
            all_document = parsed_source.xpath("//div[@id='seriesDiv']/table[@class='tableFile2']//tr[position()>=2]")
            document= []

            if not all_document:
                    
                    print "No such Ticker ---->",ticker
                    document.append(ticker)
                    print document
                    continue
            for document in all_document:
                ticker_not_found = []
                form_type_in_doc = document.xpath(".//td[1]/text()")[0]
                interactive_data_url = document.xpath(".//a[@id='interactiveDataBtn']/@href")
                interactive_data_url = "".join(interactive_data_url)
                if not interactive_data_url:
                    print "No such Ticker ---->",ticker
                    ticker_not_found.append(ticker)
                    print ticker_not_found
                    continue
                
                documents_url = document.xpath(".//a[@id='documentsbutton']/@href")
                if not documents_url:
                    print "No such Ticker ---->",ticker
                    ticker_not_found.append(ticker)
                    print ticker_not_found
                    continue
                else: 
                    if form_type == "10-K":
                        filing_dates_list = document.xpath(".//td[5]/text()")
#                         filing_dates_list = "".join(filing_dates_list)
                    if form_type == "10-Q":
                        filing_dates_list = document.xpath(".//td[5]/text()")
#                         filing_dates_list = "".join(filing_dates_list)
                    if form_type == "10-K/A":
                        filing_dates_list = document.xpath(".//td[5]/text()")
#                         filing_dates_list = "".join(filing_dates_list)
                    if form_type == "10-Q/A":
                        filing_dates_list = document.xpath(".//td[5]/text()")
#                         filing_dates_list = "".join(filing_dates_list)
                    if form_type == "all":
                        filing_dates_list = document.xpath(".//td[5]/text()")
#                         filing_dates_list = "".join(filing_dates_list)
        #                 
                
                
                    combo = zip(filing_dates_list, documents_url)
                    unavailable_data_urls = [] 
                    for i in range(len(combo)):
                        url = combo[i][1]
                        filing_date = combo[i][0]
                        parsed_source = get_parsed_source(base_url, url)
                       
    #                     display = Display(visible=0, size=(1024, 768))
    #                     display.start()
                        browser = webdriver.Firefox()
                        browser.set_page_load_timeout(40)
                        browser.get(interactive_data_url)
                        try:
                            browser.execute_script('javascript:loadReport("0");')
                            time.sleep(2)
                        except:
                            browser.refresh()
                            time.sleep(2)
                            try:
                                browser.execute_script('javascript:loadReport("0");')
                            except Exception as e:
                                print "Exception"
                                print e
                                print url
#                         import pdb;pdb.set_trace()
                        interactive_parsed_source = html.fromstring(browser.page_source)
                        quarter_type = getText(interactive_parsed_source, 
                                                "//tr[td[a[text()='Document Fiscal Period Focus' or"\
                                                "text()='Document Fiscal Period Focus (Q1,Q2,Q3,FY)' or "\
                                                "text()='Document period focus' or"\
                                                "text()='Document type' or"\
                                                "text()='Document Type' or"\
                                                "text()='Document fiscal period focus' or"\
                                                "text()='Document Period end focus']]]/td[2]/text()")
                        if not quarter_type:
                            quarter_type = getText(interactive_parsed_source, 
                                                      "//tr[td[a[text()='Document Fiscal Period Focus' or"\
                                                      "text()='Document Fiscal Period Focus (Q1,Q2,Q3,FY)' or"\
                                                      "text()='Document Period end focus' or"\
                                                      "text()='Document type' or"\
                                                      "text()='Document Type' or"\
                                                      "text()='Document fiscal period focus' or"\
                                                      "text()='Document period focus']]]/td[3]/text()" )                                           
                        browser.quit()
                        print "Filing Type",quarter_type
                        xbrl_name_ticker= ticker.upper()#Ticker_name to pass in database
                        company_Name=getText(parsed_source, "//div[@class='companyInfo']/span[@class='companyName']/text()[1]")
                        company_Name = company_Name.replace('Filer','').replace('()','')
                        if not company_Name:
                            print "XBRL data does not exist for %s for filing date %s"%(company_Name)
                            continue# company name to pass in database
                        print company_Name
                        
                        CIK= getText(parsed_source, "//div[@class='companyInfo']//a/text()")
                        CIK = CIK.split(' ')[0]# CIK 

                        SIC = getText(parsed_source, "//p[@class='identInfo']//b//text()")

                        SIC_name =getText(parsed_source, "//p[@class='identInfo']//b/following-sibling::text()")

                        filing_date_year = getText(parsed_source, "//div[@class='formGrouping'][2]/div[@class='info'][1]/text()")
                        filing_date_year = "".join(filing_date_year)
                        filing_year= filing_date_year[0:4]
                        filing_date = filing_date_year.replace('-','')
                        filing_date = filing_date_year[4:]
                        ticker_xbrl_url = getText(parsed_source, "//td[contains(text(),'EX-101.INS')]/preceding-sibling::td/a/@href")
                        if ticker_xbrl_url == '':
                            ticker_xbrl_url = getText(parsed_source, "//td[contains(text(),'EX-100.INS')]/preceding-sibling::td/a/@href")
                            if not ticker_xbrl_url:
                                print "XBRL data does not exist for %s for filing date %s"%(company_Name, filing_date_year)
                                continue
            # XBRL (XML) document url,name and spliting that name to get month and year   
                        xbrl_name_only = getText(parsed_source, "//td[contains(text(),'EX-101.INS')]/preceding-sibling::td/a/text()")
                        if xbrl_name_only == '':
                            xbrl_name_only = getText(parsed_source, "//td[contains(text(),'EX-100.INS')]/preceding-sibling::td/a/text()")
                            if xbrl_name_only == '':
                                xbrl_name_year= 'N/A' 
                                xbrl_name_date = 'N/A'
                                pass
                        else:
                            xbrl_name_split=xbrl_name_only.split('-')
                            if xbrl_name_split == '':
                                xbrl_name_split = 'N/A'
                            xbrl_name_year_date = xbrl_name_split[1].split('.')[0]
                            if xbrl_name_year_date == '':
                                xbrl_name_year_date = 'N/A'
                            xbrl_name_year = xbrl_name_year_date[0:4]
                            if xbrl_name_year == '':
                                xbrl_name_year = 'N/A'
                            xbrl_name_date = xbrl_name_year_date[4:]
                            if xbrl_name_date== '':
                                xbrl_name_date= 'N/A'
                        if  form_type_in_doc == "10-K" or form_type_in_doc == "10-K/A":
                            duplicate_xml="SELECT * FROM get_xbrl_only_date WHERE ticker_name = %s and xbrl_name_year=%s " #To check if any duplicate ticker data is there in database
                            cursor.execute(duplicate_xml,(xbrl_name_ticker,xbrl_name_year))
                            duplicate_xml_data=cursor.fetchall()
                            if  duplicate_xml_data: # passing if any duplicate data is there otherwise storing in database
                                pass
                            else:
                                if form_type_in_doc == "10-K" or form_type_in_doc == "10-K/A":
                                    query1 = "INSERT INTO get_xbrl_only_date(ticker_name,xbrl_name_year,xbrl_name_date,company_Name,CIK,SIC, SIC_name) VALUES (%s,%s,%s,%s,%s,%s,%s)"
                                    values = (xbrl_name_ticker,xbrl_name_year,xbrl_name_date,company_Name,CIK,SIC,SIC_name)
                                    cursor.execute(query1,values)
#                                     database.commit()
#                                     print  query1%(values)
                                else:
                                    pass
                        if  form_type_in_doc == "10-Q" or form_type_in_doc == "10-Q/A":       
                            duplicate_xml="SELECT * FROM get_xbrl_only_date_10Q WHERE ticker_name = %s and xbrl_name_year=%s " #To check if any duplicate ticker data is there in database
                            cursor.execute(duplicate_xml,(xbrl_name_ticker,xbrl_name_year))
                            duplicate_xml_data=cursor.fetchall()
                            if  duplicate_xml_data: # passing if any duplicate data is there otherwise storing in database
                                pass
                            else:
                                if form_type_in_doc == "10-Q" or form_type_in_doc == "10-Q/A":
                                    query1 = """INSERT INTO get_xbrl_only_date_10Q(ticker_name,xbrl_name_year,xbrl_name_date,company_Name,CIK,SIC, SIC_name) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
                                    values = (xbrl_name_ticker,xbrl_name_year,xbrl_name_date,company_Name,CIK,SIC,SIC_name)
                                    cursor.execute(query1,values)
#                                     database.commit()
                                    print  query1%(values)
                                else:
                                    pass
                                    
    
                                   
                # XBRL (CAL) document url,name, document type, filing date,form-type  
                        
                        else:
                                unavailable_data_urls.append((ticker, filing_date, url))
                                print unavailable_data_urls
              
                    database.commit()

    return render_to_response(
                'sec_data.html','',
                context_instance=RequestContext(request))
    
def select_commaseperated(request):
    data_exists = False
    data_false = None
    emp_details=[] 
    total_data = [] 
    connection =MySQLdb.connect (host=settings.DATABASES['default']['HOST'], 
                            user = settings.DATABASES['default']['USER'], 
                            passwd = settings.DATABASES['default']['PASSWORD'], 
                            db = settings.DATABASES['default']['NAME'])
    cursor1 = connection.cursor()
    if request.method == 'GET':
        text_ticker = request.GET.get('data')
        if text_ticker:
            query = "select ticker_name,form_type,doc_type,document,filing_date,converted_flag,graphdb,finif_flag from get_xbrl where ticker_name=%s" 
            cursor1.execute(query,(text_ticker,))
            total_data = cursor1.fetchall()
            if not total_data:
                data_false = True
                emp_details.append({'text_ticker':text_ticker})
            else:
                data_exists = True
                for total in total_data:
                    ticker_name = total[0]
                    form_type = total[1]
                    doc_type = total[2]
                    document = total[3]
                    filing_date =total[4]
                    converted_flag = total[5]
                    graphdb = total[6]
                    finif_flag = total[7]
                    emp_details.append({'ticker_name' : ticker_name,'form_type':form_type, 'doc_type':doc_type ,'document' : document, 'filing_date':filing_date, 'converted_flag':converted_flag, 'graphdb':graphdb, 'finif_flag':finif_flag})
            query1 = "select ticker_name,form_type,doc_type,document,filing_date,converted_flag,graphdb,finif_flag from get_xbrl_10Q where ticker_name=%s"
            cursor1.execute(query1,(text_ticker,))
            total_data1= cursor1.fetchall() 
            if not total_data1:
                data_false = True
                emp_details.append({'text_ticker':text_ticker})
            else:
                data_exists = True
                for total in total_data1:
                    ticker_name = total[0]
                    form_type = total[1]
                    doc_type = total[2]
                    document = total[3]
                    filing_date =total[4]
                    converted_flag = total[5]
                    graphdb = total[6]
                    finif_flag = total[7]
                    emp_details.append({'ticker_name' : ticker_name,'form_type':form_type, 'doc_type':doc_type ,'document' : document, 'filing_date':filing_date, 'converted_flag':converted_flag, 'graphdb':graphdb,'finif_flag':finif_flag}) # to render in to template to get ticker_name , form-type, doc-type, document with a hyperlink
            context_dict = {'emp_details' : emp_details,
                            'data_exists': data_exists,
                            'data_false':data_false}
            cursor1.close()
            connection.commit()
            connection.close()
            return render_to_response('sec_data.html', context_dict,context_instance=RequestContext(request))
        context_dict= {}
        return render_to_response('sec_data.html', context_dict,context_instance=RequestContext(request))


