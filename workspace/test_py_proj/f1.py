# from f2 import abc , func1
# import f2
# def abc():
#     print "inside f1.abc()"
#
#
#
# # f2.abc()
# # f2.func1()
# # abc()
#
#
# f2.abc()
# abc()
#
# # output:
# #
# # inside abc
# # func1
# # inside f1.abc()
#
#
# # import f2
# def func1():
#     print "hi there"


# # import cgi
# # form = cgi.FieldStorage()
# # if "name" not in form or "addr" not in form:
# #     print "<H1>Error</H1>"
# #     print "Please fill in the name and addr fields."
# #     return
# # print "<p>name:", form["name"].value
# # print "<p>addr:", form["addr"].value
# print "Content-type:text/html\r\n\r\n"
# print '<html>'
# print '<head>'
# print '<title>Hello Word - First CGI Program</title>'
# print '</head>'
# print '<body>'
# print '<h2>Hello Word! This is my first CGI program</h2>'
# print '</body>'
# print '</html>'

# import time
# def download_file(x,timeout=30):
#         c = 0
#         timeout = abs(int(timeout))
#         start_time = time.time()
#         response = None
#         while (time.time() - start_time) <= timeout:
#             print "try"+str(c)
#             c += 1
#             if response is None:
#                 try:
#                     url = 2/x
#                     response = url
#                     break
#                 except (ZeroDivisionError) as e:
#                     print e
#                     time.sleep(5)
#         return response
#
#
# if __name__ == '__main__':
#     for i in range(1):
#         download_file(i)


# from validate_email import validate_email
# is_valid = validate_email('adrratsdfdfhour@aricent.com')
# print is_valid


# a = int(raw_input('Give amount: '))
#
#
# def fib():
#     a, b = 0, 1#     while 1:
#         yield a
#         a, b = b, a + b
# b = fib()
# for i in range(a):
#     print b.next()


# for i in xrange(110, 100, -2):
#     print(i)

# from copy import deepcopy
# a = [[1, 2, 3], 4]
# b = deepcopy(a)
# a[0].append(5)
# print b
# print a

# Note: Python 2.x only
# def getsum():
#     nums = list(xrange(10))
#     print nums
#     s = sum(nums)
#     print s
#
# if __name__ == '__main__':
#     getsum()

# from flask import Flask, redirect, url_for, request
# app = Flask(__name__)
#
#
# @app.route('/')
# def hello():
#     return "Hello World!"
#
#
# @app.route('/shortlist', methods=['POST', 'GET'])
# def hello2():
#     if request.method == 'POST':
#         return "Hello World post!"
#     else:
#         return "Hello world GET!!"
#
#
# @app.route('/post/<int:post_id>')
# def hello1():
#     return "cloudlet!!"
#
#
# if __name__ == '__main__':
#     app.run()


from flask import Flask, redirect, url_for, request
app = Flask(__name__)


@app.route('/success/<name>')
def success(name):
    return 'welcome %s' % name


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user = request.form['nm']
        return redirect(url_for('success', name=user))
    else:
        user = request.args.get('nm')
        return redirect(url_for('success', name=user))

if __name__ == '__main__':
    app.run(debug=True)
