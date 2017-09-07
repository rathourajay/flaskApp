import urllib2
import re
import csv


class Postalinfo(object):

    def __init__(self):
        self.file_name = "output.csv"
        resultFile = open(self.file_name, 'wb')
        self.wr = csv.writer(resultFile, dialect='excel')
        self.wr.writerow(('id', 'lat', 'lon', 'address', 'name', 'content'))
        self.unique_dict = {}

    def fetch_postal_info(self, url):
        out = urllib2.urlopen(url).read()
        format_out = out.replace('\n', '').replace(
            '\r', '').replace('\t', '').strip()
        postal_info = re.findall(r'locate\((.*?)\<a', format_out)
        for unique_post_item in postal_info:
            unique_post_item = unique_post_item + '"'
            unique_post_item = eval(unique_post_item)
            if unique_post_item[0] in self.unique_dict.keys():
                break
            else:
                self.unique_dict[unique_post_item[0]] = 1
                print "Executing.."
                self.wr.writerow(unique_post_item)


if __name__ == "__main__":
    postal_obj = Postalinfo()
    for i in range(5):
        url = "http://www.webstercare.com.au/list?post_code=%s&submit=GO&zoom=13" % i
        postal_obj.fetch_postal_info(url)
    print "Completed!!"
