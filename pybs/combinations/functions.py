from itertools import product
from pybs.utils import memoized2 as memoized, LinearCombination
from pybs.unordered_tree import UnorderedTree, leaf
from pybs.combinations import Forest as Forest
from pybs.combinations import empty_tree


@memoized
def graft(other, base):
    r"""Grafting *other* :math:`\curvearrowright` *base*."""
    result = LinearCombination()
    if base == empty_tree:
        result += other
    elif other == empty_tree:
        result += base
    else:
        result += base.butcher_product(other)
        for subtree, multiplicity1 in base.items():
            amputated_tree = base.sub(subtree)
            replacements = graft(other, subtree)
            for replacement, multiplicity2 in replacements.items():
                new_tree = amputated_tree.add(replacement)
                result[new_tree] += multiplicity1 * multiplicity2
    return result


def split(tree, truncate=False):
    """Return the splittings of a tree as a linear combination.

    The return value is a linear combination of tuples.
    The 0th element is the cutting, the 1st element is the subtree.
    Both elements are :class:`UnorderedTree`, except if it is the empty tree.
    """
    result = _split(tree)
    if not truncate:
        result[(tree, empty_tree)] = 1
    return result


def symp_split(tree):
    """Perform the split needed for symplecticity checks.

    It differs from the ``split``-function
    by only splitting off leaves."""
    result = LinearCombination()
    for childtree, multiplicity in tree.items():
        amputated_tree = tree.sub(childtree)
        if childtree == leaf:
            result[amputated_tree] += multiplicity
        else:
            child_splits = symp_split(childtree)
            for tree2, multiplicity2 in child_splits.items():
                new_tree = amputated_tree.add(tree2)
                result[new_tree] += multiplicity * multiplicity2
    return result


def subtrees(tree):
    """Return the HCK coproduct.

    This is function does the heavy lifting when composing B-series.
    The return value is a :class:`LinearCombination` of 2 tuples.
    The 0th element in the tuples are the forests of cutting,
    while the 1st element is the subtree.
    """
    result = LinearCombination()
    if tree == empty_tree:
        result += (empty_tree, empty_tree)
        return result
    elif isinstance(tree, Forest):
        if tree.number_of_trees() == 1:
            for elem in tree:
                return subtrees(elem)
        else:  # several trees.
            for elem in tree:
                amputated_forest = tree.sub(elem)
                break
            for pair1, multiplicity1 in subtrees(elem).items():
                for pair2, multiplicity2 in subtrees(amputated_forest).items():
                    if isinstance(pair1[1], UnorderedTree):
                        pair1_1 = Forest((pair1[1],))
                    else:
                        pair1_1 = pair1[1]
                    if isinstance(pair2[1], UnorderedTree):
                        pair2_1 = Forest((pair2[1],))
                    else:
                        pair2_1 = pair2[1]  # TODO: Nasty workaround.
                    pair = (pair1[0] * pair2[0], pair1_1 * pair2_1)
                    result[pair] += multiplicity1 * multiplicity2
            return result
    result[(Forest((tree,)), empty_tree)] = 1
    if tree == leaf:
        result[(empty_tree, tree)] = 1
        return result
    tmp = [subtrees(child_tree) for child_tree in tree.elements()]
    # TODO: more efficient looping.
    # TODO: The multiplicities in "tree" are accounted for by "elements()".
    tmp = [elem.items() for elem in tmp]  # TODO: Try using iterators.
    for item in product(*tmp):  # iterator over all combinations.
        tensorproducts, factors = zip(*item)
        multiplicity = 1
        for factor in factors:
            multiplicity *= factor
        cuttings, to_be_grafted = zip(*tensorproducts)
        with Forest().clone() as forest_of_cuttings:
            for forest in cuttings:
                forest_of_cuttings.inplace_multiset_sum(forest)
        result[(forest_of_cuttings, UnorderedTree(to_be_grafted))] += \
            multiplicity
    return result


def antipode_ck(tree):
    """Return the antipode in the Butcher, Connes, Kreimer Hopf-algebra."""
    # TODO: Should be memoized, but linearCOmbination is mutable.
    # Make LinComb clonable??
    result = LinearCombination()
    if tree == empty_tree:
        result[empty_tree] = 1
        return result
    elif isinstance(tree, Forest):
        result[empty_tree] = 1
        for tree1, multiplicity in tree.items():
            for i in range(multiplicity):
                tmp = LinearCombination()
                for forest1, multiplicity1 in antipode_ck(tree1).items():
                    for forest2, multiplicity2 in result.items():
                        tmp[forest1 * forest2] += multiplicity1 * multiplicity2
                result = tmp
        return result
        # TODO: implement multiplication of LinComb.
    result[Forest((tree,))] -= 1
    for (forest, subtree), multiplicity in _subtrees_for_antipode(tree).items():
        for forest2, coefficient in antipode_ck(forest).items():
            result[forest2.add(subtree)] -= coefficient * multiplicity
    return result


def differentiate(thing):
    """performs grafting corresponding to
    derivate once more with respect to *t*."""
    if isinstance(thing, LinearCombination):
        result = LinearCombination()
        for tree, factor in thing.items():
            result += treeD(tree) * factor
    elif isinstance(thing, UnorderedTree):
        result = treeD(thing)
    elif thing == empty_tree:
        result = LinearCombination()
        result += leaf
    return result


def treeD(tree):
    return graft(leaf, tree)


def linCombCommutator(op1, op2, max_order=None):
    """Tree commutator for linear combinations of trees."""
    if isinstance(op1, UnorderedTree) or op1 == empty_tree:
        tmp = LinearCombination()
        tmp += op1
        op1 = tmp
    if isinstance(op2, UnorderedTree) or op2 == empty_tree:
        tmp = LinearCombination()
        tmp += op2
        op2 = tmp
    result = LinearCombination()
    for tree1, factor1 in op1.items():
        for tree2, factor2 in op2.items():
            if (not max_order) or tree1.order() + tree2.order() <= max_order:
                result += (factor1 * factor2) * tree_commutator(tree1, tree2)
    return result


def tree_commutator(op1, op2):
    """Return :math:`op1 \curvearrowright op2 - op2 \curvearrowright op1`
    as a :class:`LinearCombination`."""
    return graft(op1, op2) - graft(op2, op1)


def _subtrees_for_antipode(tree):
    r"""Slightly modified edition of ``subtrees`` used by ``antipode_ck``

    Does not include
    :math:`\tau \otimes \emptyset` and
    :math:`\emptyset \otimes \tau`.
    """
    result = LinearCombination()
    # TODO: more efficient looping.
    tmp = [subtrees(child_tree) for child_tree in tree.elements()]
    if tmp:
        tmp = [elem.items() for elem in tmp]  # TODO: Try using iterators.
        for item in product(*tmp):  # iterator over all combinations.
            tensorproducts, factors = zip(*item)
            multiplicity = 1
            for factor in factors:
                multiplicity *= factor
            cuttings, to_be_grafted = zip(*tensorproducts)
            with Forest().clone() as forest_of_cuttings:
                for forest in cuttings:
                    forest_of_cuttings.inplace_multiset_sum(forest)
            result[(forest_of_cuttings, UnorderedTree(to_be_grafted))] += multiplicity
    result[(empty_tree, tree)] = 0  # TODO: FIND NICER WAY.
    return result


def _split(tree):
    """Return the splitting of tree except for :math:`tree \otimes \emptyset`.

    Used by `split()`.
    """
    result = LinearCombination()
    for childtree, multiplicity in tree.items():
        amputated_tree = tree.sub(childtree)
        result[(childtree, amputated_tree)] = multiplicity
        childSplits = _split(childtree)
        for pair, multiplicity2 in childSplits.items():
            new_tree = amputated_tree.add(pair[1])
            new_pair = (pair[0], new_tree)
            result[new_pair] = multiplicity * multiplicity2
    return result
