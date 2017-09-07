"""
checking import from one module to another module and verify if pyc is generated.
Also test use of main function in python
"""
# from advance_practice import foo
import advance_practice


def test():
    print "this is my test in new file"

if __name__ == '__main__':
    #     print advance_practice.__name__
    print __name__
    test()


"""
checking for global variables/scope
"""
# def foo(x, y):
#     global a
#     a = 42
#     x,y = y,x
#     b = 33
#     b = 17
#     c = 100
#     print a,b,x,y
#
# a,b,x,y = 1,15,3,4
# foo(17,4)
# print a,b,x,y
# print s


"""
list methods/usages
"""
# l1 = [1,2,3,4,5]
# l2 = [10,20,30,40,50]
# l3 = [100,200,300,400,500]
# l4 = []
# for i in zip(l1,l2,l3):
#     l4.append(i)
# print l4


# a = [x*x  for x in range(10) if x >= 2 else x = 0]
# print a

# l = [22, 13, 45, 50, 98, 69, 43, 44, 1,43]
#
# print set([x for x in l if l.count(x) > 1])

# a = [1,2,3,2,1,5,6,5,5,5]
#
# import collections
# print [item for item, count in collections.Counter(a).items() if count > 1]


"""
dict operation
"""
# dic = {'c':4,'b':7}
# # for k in dic:
# #     print k
# #     print dic[k]
# #     print v
#
# # s_dict = sorted(dic.items(),key = operator.itemgetter(1))
# s_dict = sorted(dic.items(),key = dic.get)
# print s_dict


"""
tuple operation
"""

# dict = {(1,2):'tuple as key',(2,3):'tuple2'} #possible
# print dict

# dict = {([1,2]):'tuple as key',([2,3]):'tuple2'} # not possible
# print dict
# l1 = [1,2]
# l2 = [2,3]
# dict = {tuple(l1):'this is test'}
# print dict

"""
list dict and set comprehension
"""


# l1 = [i*2 for i in range(10) if i%2==0]
# print l1

# d1 = {i:i+2 for i in range(4)}
# print d1


# print set(i for i in 'aabc')
# print {i:ord(i) for i in 'abc'}


"""
frozen set
"""

# simple_set = {'ajay','boby','rsr'}
# froz_set = frozenset(simple_set)
# print froz_set


"""
python supports named arguments
"""
# def foo(x= 0,y=1):
#     print x ,y
#
# foo(y=10,x=2)
