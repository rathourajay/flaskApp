"""
Dacorator/parameterized decorator
"""

# def logging_decorator(func):
# #     import pdb;pdb.set_trace()
#     def wrapper():
#         wrapper.count += 1
#         print "The function I modify has been called {0} times(s).".format(
#               wrapper.count)
#         func()
#     wrapper.count = 0
#     return wrapper
#  
#  
# def a_function():
#     print "I'm a normal function."
#  
# modified_function = logging_decorator(a_function)
# print modified_function()
# # modified_function()

# def addbonus(func):
#     def wrapper(x,y):
#         return 12+func(x,y)
#     return wrapper
# 
# @addbonus
# def add(x,y):
#     return x+y
# 
# print add(10,20)

#parameterized
# def addbonus(str_abc):
#     def first_wrap(fun):
#         def wrapper(x,y):
#             return str_abc+str(fun(x,y))
#         return wrapper
#     return first_wrap
#  
# @addbonus('percentage')
# def add(x,y):
#     return x+y
#  
# print add(10,20)



"""
more on logger
"""
# records = {'john': 55, 'tom': 66}
# logger.info('Records: %s', records)
# logger.info('Updating records ...')
# # update records here
# 
# logger.info('Finish updating records')


# import logging
# logging.basicConfig(filename='example2.log',level=logging.DEBUG)
# # logging.debug('This message should go to the log file')
# # logging.info('So should this')
# # logging.warning('And this, too')
# records = []
# j = 0
# for i in range(10):
#     try:
#         result = i / j
#         
#         logging.info(result)
#     except ZeroDivisionError:
#         logging.info("division by zero!")
#         j += 1
# #     records.append(i)
# #     logging.info('Records: %s', records)
#     print "written"


"""
custom iterator by class and via generator method
"""


# class Counter:
#     def __init__(self, low, high):
#         self.current = low
#         self.high = high
#  
#     def __iter__(self):
#         return self
#  
#     def next(self): # Python 3: def __next__(self)
#         if self.current > self.high:
#             raise StopIteration
#         else:
#             self.current += 1
#             return self.current - 1
#  
#  
# for c in Counter(3, 8):
#     print c

# def counter(low, high):
#     current = low
#     while current <= high:
#         yield current
#         current += 1
# 
# for c in counter(3, 8):
#     print c



"""
fibonaccii by generator
"""
# from _collections import defaultdict
# from __builtin__ import globals

# def fib():
# 
#     a, b = 0, 1
# 
#     while 1:
# 
#         yield a
# 
#         a, b = b, a + b
# a = fib()
# 
# 
# for i in range(10):
# 
#     print a.next(),

"""
shallow vs deep copy
"""
import copy
# # 
# a = [1,2,3]
# print "before copy address of a.."
# print hex(id(a))
# # b = ['x','y','z']
# # print "before copy address of b.."
# # print hex(id(b))
# # b = copy.copy(a) 
# # a = copy.copy(b)
# b = a
# print "after copy address of a.."
# # print hex(id(a))
# print "after copy address of b.."
# print hex(id(b))
# print hex(id(a))
# 
# 
# b[1] = 5
# b = ['a']
# print b
# print a

colours1 = ["red", "green"]
colours2 = colours1
# colours2 = ["rouge", "vert"]
print colours1
print colours2
colours1[0] = 'blue'
print colours1 
print colours2

 
 
# l = ['abc','def' ]
# dup = l
# 
# print 'l  :', l
# print 'dup:', dup
# print 'dup is l:', (dup is l)
# print 'dup == l:', (dup == l)
# print 'dup[0] is l[0]:', (dup[0] is l[0])
# print 'dup[0] == l[0]:', (dup[0] == l[0])
# # import copy
# 
# class MyClass:
#     def __init__(self, name):
#         self.name = name
#     def __cmp__(self, other):
#         return cmp(self.name, other.name)
# 
# a = MyClass('a')
# l = [ a ]
# dup = copy.deepcopy(l)
# 
# print 'l  :', l
# print 'dup:', dup
# print 'dup is l:', (dup is l)
# print 'dup == l:', (dup == l)
# print 'dup[0] is l[0]:', (dup[0] is l[0])
# print 'dup[0] == l[0]:', (dup[0] == l[0])

    