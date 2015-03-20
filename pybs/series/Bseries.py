from fractions import Fraction

from pybs.utils import LinearCombination
from pybs.combinations import empty_tree, Forest
from pybs.unordered_tree import UnorderedTree, leaf


class BseriesRule(object):
    """This is the docstring for BseriesRule! YEA!!"""
    def __init__(self, arg=None, quadratic_vectorfield=False):
        if arg is None:
            self._call = lambda x: 0
        elif isinstance(arg, LinearCombination):
            self._call = lambda tree: arg[tree]  # TODO: Check that there are no non-trees.
        elif callable(arg):
            self._call = arg

            self.quadratic_vectorfield = quadratic_vectorfield

    def __call__(self, arg):
        if isinstance(arg, UnorderedTree) or arg == empty_tree:
            return self._call(arg)
        elif isinstance(arg, Forest):
#            if self._call(empty_tree) == 1 or arg.number_of_trees() == 1:  # TODO: Do nicer.
            result = 1
            for tree, multiplicity in arg.items():
                result *= self._call(tree) ** multiplicity
                # TODO: Use reduce() or something?
            return result
#            else:
#                return 0
        elif isinstance(arg, LinearCombination):
            result = 0
            for elem, multiplicity in arg.items():
                result += self(elem) * multiplicity
            return result


class VectorfieldRule(object):
    def __init__(self, arg=None, quadratic_vectorfield=False):
        if arg is None:
            self._call = lambda x: 0
        elif isinstance(arg, LinearCombination):
            self._call = lambda tree: arg[tree]  # TODO: Check that this is reasonable.
        elif callable(arg):
            self._call = arg

            self.quadratic_vectorfield = quadratic_vectorfield

    def __call__(self, arg):
        if isinstance(arg, UnorderedTree) or arg == empty_tree:
            return self._call(arg)
        elif isinstance(arg, Forest):
            if arg.number_of_trees() == 1:  # TODO: Do nicer.
                for elem in arg:
                    return self._call(elem)
            else:
                return 0
        elif isinstance(arg, LinearCombination):
            result = 0
            for elem, multiplicity in arg.items():
                result += self(elem) * multiplicity
            return result


class ForestRule(object):
#  Results on forests are not deducable from results on trees.
    def __init__(self, arg=None, quadratic_vectorfield=False):
        if arg is None:
            self._call = lambda x: 0
        elif isinstance(arg, LinearCombination):
            self._call = lambda forest: arg[forest]
        elif callable(arg):
            self._call = arg

            self.quadratic_vectorfield = quadratic_vectorfield

    def __call__(self, arg):
        if isinstance(arg, (UnorderedTree, Forest)):
            return self._call(arg)
        elif isinstance(arg, LinearCombination):
            result = 0
            for elem, multiplicity in arg.items():
                result += self(elem) * multiplicity
            return result


def _zero(tree):
    return 0


def _unit(tree):
    if tree == empty_tree:
        return 1
    else:
        return 0


def _exact(tree):
    if tree == empty_tree:
        return 1
    return Fraction(1, tree.density())


def _kahan(tree):
    'Directly from Owren'  # TODO: Test
    if tree == empty_tree:
        return 1
    if tree.is_tall():
        return Fraction(1, (2 ** (tree.order()-1)) * tree.symmetry())
    else:
        return 0


def _AVF_old(a, tree):
    'Directly from Owren'  # TODO: Test
    if tree == empty_tree:
        return 1
    if tree == leaf:
        return 1
    elif not tree.is_binary():
        return 0
    else:
        if tree.number_of_children() == 1:
            return Fraction(_AVF(a, tree.keys()[0]), 2)
        elif tree.number_of_children() == 2:
            alpha = Fraction(2*a + 1, 4)
            if len(tree._ms) == 2:
                return alpha * _AVF(a, tree.keys()[0]) * \
                    _AVF(a, tree.keys()[1])
            else:
                return alpha * _AVF(a, tree.keys()[0]) ** 2


def _AVF(tree):
    "According to ENERGY-PRESERVING RUNGE-KUTTA METHODS, Celledoni et al."
    if tree == empty_tree:
        return 1
    if tree == leaf:
        return 1
    else:
        result = Fraction(1, tree.number_of_children() + 1)
        for child_tree, multiplicity in tree.items():
            result *= _AVF(child_tree) ** multiplicity
        return result


def _unit_field(tree):
    if tree == leaf:
        return 1
    return 0

exponential = BseriesRule(_exact)
zero = BseriesRule(_zero)
unit = BseriesRule(_unit)
unit_field = BseriesRule(_unit_field)
AVF = BseriesRule(_AVF)
