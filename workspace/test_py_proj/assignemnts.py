# """
# Q3
# """ 
# 
# global a
# a  = 3
# print hex(id(a))
#   
# def other_func():
#     return a
#  
# def abc():
# #     global a
#     a = 4
#     print a
#     print hex(id(a))
#      
#     a = other_func()
#     print a
#      
# abc()
# print a
# 
# """ output"""
# """
# 0x56fe08
# 4
# 0x56fdfc
# 3
# 3
# """


# x = 0   # The initial value of x, with global scope
# 
# def other_function():
#     global x
#     x = x + 5
# 
# def main_function():
#     print x    # Just printing - no need to declare global yet
#     global x   # So we can change the global x
#     x = 10
#     print x
#     other_function()
#     print x
#     
# main_function()

# dic = {1:'w',2:'c'}
# print dic.keys()




# """Q-1"""
# 
# tup1  = ('a','b','c')
# dict1 = {}
# value = 1
# for item in tup1:
#     dict1[item] = value
#     value += 1
#      
# print dict1
# 
# """output {'a': 1, 'c': 3, 'b': 2}"""



"""
Q-2
"""
import sys
# x = file("testfile.txt", 'w')
# y = file("testfile.txt", 'w')
# print sys.getrefcount(y) 
# x.close()
# print sys.getrefcount(x)
# exit
# print sys.getrefcount(x) 

# 
# 
# n_1 = 10
# n_2 = 10
  
# # print sys.getrefcount(n_1) 
# a= 10921.09
# # b = 10
# print hex(id(a))
# # print hex(id(b)) 
# print sys.getrefcount(a) 
# 
# """ 
# output
# 
# 0x3ffdb4
# 0x3ffdb4
# 
# """

# test_list = [1,10]
# print test_list
# print [hex(id(value)) for value in test_list]




# def addsomething(str1):
#     def first_wrapper(fun):
#         def wrapper(str):
#             return str1 +'<b>'+fun(str)+'</b>'
#         return wrapper
#     return first_wrapper
# 
# 
# @addsomething('hi')
# def printhello(str):
#     return str
# 
# 
# print printhello('hello')


dic = {i:i+1 for i in range(10)}
print dic

s = {x for x in range(4)}
print s
