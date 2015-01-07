# This Python file uses the following encoding: utf-8
import operator
import numpy as np


from pybs.utils import memoized as memoized
from pybs.trees import ButcherTree, ButcherEmptyTree, density, order
from pybs.combinations import treeGenerator
from pybs.series import BseriesRule, equal_up_to_order
#  Note the use of dtype=object. It allows for exact algebra.
#  However it is much slower since numpy will call Python code.


class RK_method(object):
    def __init__(self, A, b):
        self.A = A  # np array
        self.b = b  # np array
        self._s = self.b.size

    def printMe(self):  # Simple thing. Look into prettyPrint
        print 'A ='
        print self.A
        print 'b =', self.b

    @property
    @memoized
    def order(self):
        a = BseriesRule('exact')
        b = BseriesRule(self.phi)
        return equal_up_to_order(a, b)

    def phi(self, tree):
        'elementary weight'
        if isinstance(tree, ButcherEmptyTree):
            return 1  # We haven't even allowed for non-consistent RK-methods.
        return np.dot(self.b, self.g_vector(tree))[0]

    @memoized
    def g_vector(self, tree):
        g_vector = np.ones((self._s, 1), dtype=object)

        def u_vector((subtree, multiplicity)):
            return np.dot(self.A,
                          self.g_vector(subtree)) ** multiplicity
        return reduce(operator.__mul__, map(u_vector, tree.items()), g_vector)