
"""
oops concept
"""
# class TestAccessibility:
#     def __init__(self):
#         self.value = 4
#         
#     def __del__(self):
#         return self
#     
#     def findresult(self):
#         print "hi"
#     
# obj1 = TestAccessibility()
# print dir(obj1)
    
"""
class intro
"""

# class Customer:
#     def __init__(self,name):
#         self.name = name 
#         self.balance = 0
#         
#     def setbalance(self,balance = 0):
#         self.balance = balance
#         print self.balance
#         
#     def withdraw(self,amt):
#         self.balance -= amt
#         print self.balance
#         
#     def deposit(self,amt):
#         self.balance = self.balance + amt
#         print self.balance
#         
# obj1 = Customer('ajay')
# obj1.setbalance(200)
# obj1.deposit(1000)
# obj1.withdraw(200)

"""
abstract class
"""

# from abc import ABCMeta, abstractmethod
#  
# class Animal:
#     __metaclass__ = ABCMeta
#  
#     @abstractmethod
#     def say_something(self): print "hi"
#  
# class Cat(Animal):
#     def say_something(self):
#         return "Miauuu!"
#      
# # anim_obj = Animal()
# # anim_obj.say_something()
# c = Cat()
# print c.say_something()
    
"""
usage of super
"""

# class TestSuper(object):
#     def __init__(self):
#         print "hi"
#     def saysomething(self):
#         print "inside TestSuper"
#         
#         
# class UseSuper(TestSuper):
#     def __init__(self):
#         print "loop inside"
# #         super(UseSuper,self).__init__()
#     def saysomething(self):
#         print "inside reestSuper"
# obj = UseSuper()
# obj.saysomething()

"""
mro/inheritence in python
"""

# class A(object):
#     def saysomething(self):
#         print "A"
#     
# class B(A):
#         pass
# 
# class C(A):
#     pass
# #     def saysomething(self):
# #         print "C"
#     
# class D(B,C):
# #     def saysomething(self):
#         pass
#     
# d = D()
# d.saysomething()
#     
 
 
"""
mro in python
it will print first value match according to mro
"""
# class Base1(object):  
#     def amethod(self): print "Base1"  
# 
# class Base2(Base1):  
#     pass
# 
# class Base3(Base1):  
#     def amethod(self): print "Base3"
# 
# class Derived(Base2,Base3):  
#     pass
# 
# # instance = Derived()  
# # instance.amethod()  
# print Derived.__mro__ 
# """above line support only if you  have written like class_name(object)""" 

# class A:
#     x = 'a'
# class B(A): 
#     pass
# class C(A): 
#     pass
# class D(B, C): 
#     x = 'd'
# # print D.__mro__
# print D.x
 
"""
Assignment questions on module/scoping/memory management
"""

"""
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


# print sys.getsizeof({})
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


"""
lambda filter map reduce
"""
# l1 = map(lambda x:x+2, [1,2,3]) 
# print l1
# 
# l2 = filter(lambda x:x%2 ==0, [1,2,3]) 
# print l2
# 
# l3 = reduce(lambda x,y:x+y,[2,3,4,5]) 
# print l3





class A(object):
    def __init__(self):
        print "A.__init__()"

class B(A):
    def __init__(self):
        print "B.__init__()"
        super(B, self).__init__()
        
b = B()