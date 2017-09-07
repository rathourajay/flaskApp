"""
try except else block
"""

# def divide(x, y):
#     
#     try:
#         result = x / y
# #         print result
#     except ZeroDivisionError:
#         print "division by zero!"
#     else:
# #         import pdb;pdb.set_trace()
#         print "result is", result
#     finally:
#         print "executing finally clause"
#          
# divide(10, 2)

# Note--- else block above will exceute only when exception wont occur.


# for i in range(2):
#     try:
#         x = int(raw_input("Please enter a number: "))
#         break
#     except ValueError:
#         print "s no valid number.  Try again"



# def catch():
#     try:
#         asd()
#     except Exception as e:
#         print e.message, e.args
#  
# catch()
# it doesn't catch BaseException or the system-exiting exceptions SystemExit, KeyboardInterrupt and GeneratorExit:

# Note :  accepts all exceptions, whereas except Exception as e: only accepts exceptions that you're meant to catch.. 




"""user-defined exceptions"""

# class Error(Exception):
#     pass
# 
# class ValueTooSmallError(Error):
#     pass
# 
# class ValueTooLargeError(Error):
#     pass
# 
# number = 10
# 
# while True:
#     try:
#         i_num = int(input("Enter a number: "))
#         if i_num < number:
#             raise ValueTooSmallError
#         elif i_num > number:
#             raise ValueTooLargeError
#         break
#     except ValueTooSmallError:
#         print "This value is too small, try again!"
#     except ValueTooLargeError:
#         print "This value is too large, try again!"
# 
# print "Congratulations! You guessed it correctly."


"""
logger module
"""
# import logging
# import otherMod2
#  
# def main():
#     """
#     The main entry point of the application
#     """
#     logging.basicConfig(filename="test.log", level=logging.INFO)
#     logging.info("Program started")
#     result = otherMod2.add(17, 28)
#     logging.info("Done!")
#  
# if __name__ == "__main__":
#     main()


# import logging
# LOG_FILENAME = 'example.log'
# logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
# 
# logging.debug('This message should go to the log file')



"""
globlas and locals, locals are read only while globals can be updated.
"""
# def test_locals_globals(arg): 
#     x = 1
#     z = 2
# #     print globals()
# #     print locals()
#     locals()["x"] = 2
#     print "x=",x 
# #     print locals()
#     
#     globals()["z"] = 8 
#     print "z=",z 
#     print globals()
# test_locals_globals(5)



"""
file operation/read heavy file/check if file exists
"""

# fp = open('testfile.txt')
# for item in fp.readlines():
#     print type(item)
#     

# def readInChunks(fileObj, chunkSize=2048):
#     """
#     Lazy function to read a file piece by piece.
#     Default chunk size: 2kB.
#     """
#     while True:
#         data = fileObj.read(chunkSize)
#         if not data:
#             break
#         yield data
# 
# f = open('bigFile')
# for chuck in readInChunks(f):
#     do_something(chunk)

# import os.path
# print os.path.isfile('testfile1.txt')


# with open('testfile1.txt', 'w') as f:
#     f.write('Hi there!')

#Note :- It will autometically close the file



"""
python supports named arguments
"""
# def foo(x= 0,y=1):
#     print x ,y
# 
# foo(y=10,x=2)

"""
inner function scoping, call goes sequentially ,first outer get called later inner , scope of variable will remain same
"""
# def outer():
#     x = 1
#     print "inside outer"
#     
#      
#     def inner():
#         print "inside inner"
#         print x
#     return inner
# 
# if __name__ == '__main__':
# #     import pdb;pdb.set_trace()
#     foo = outer()
#  