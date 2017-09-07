import urllib2
url = "http://www.webstercare.com.au/list?post_code=1&submit=GO&zoom=13"
out = urllib2.urlopen(url).read()
print out
