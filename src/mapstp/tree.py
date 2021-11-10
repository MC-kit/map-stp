from typing import Dict, Optional, cast

from dataclasses import dataclass

from mapstp.stp_parser import LeafProduct, Product, make_index


@dataclass
class Node:
    """Node for the following `Tree` class.

    Stores the references to a `Product` corresponding to a number presented in a `Link` as source or destination.
    Also stores reference to its parent node. Only upward search is necessary in this application,
    so, there's no references to childes.
    """

    product: Product
    parent: Optional["Node"] = None

    def collect_parents(self):
        """Iterates through the parents of the node from root parent to this node"""
        if self.parent is not None:
            yield from self.parent.collect_parents()
        yield self.product


class Tree:
    """Upward directed tree: it has to find only the parents from a given node.

    Indexes and stores results of STP file parsing.

    """

    def __init__(self, products, links):
        self._product_index: Dict[int, Product] = make_index(products)
        self._node_index = dict()
        self._body_links = []
        for link in links:
            src, dst = link
            product = self._product_index[dst]
            if product.is_leaf:
                self._body_links.append(link)
                parent = self._node_index.get(src)
                if parent is None:
                    self._create_node(self._product_index[src])
            else:
                parent = self._node_index.get(src)
                if parent is None:
                    parent = self._create_node(self._product_index[src])
                node = self._node_index.get(dst)
                if node is None:
                    self._create_node(product, parent)
                else:
                    assert node.parent is None, "Tree hierarchy in STP is invalid"
                    node.parent = parent

    def _create_node(self, product: Product, parent: Node = None) -> Node:
        node = Node(product, parent)
        self._node_index[product.number] = node
        return node

    def create_bodies_paths(self):
        bodies_paths = []
        for link in self._body_links:
            src, dst = link
            product = self._product_index[dst]
            if product.is_leaf:
                node = self._node_index[src]
                parents = node.collect_parents()
                path = list(
                    map(lambda parent: self._product_index[parent.number].name, parents)
                )
                path.append(product.name)
                for b in cast(
                    LeafProduct, product
                ).bodies:  # TODO dvp: design flaw: separate indexes for Products and LeafProducts to avoid cast
                    bodies_paths.append(
                        path + [b.name]
                    )  # TODO dvp: add transliteration for Russian names
        return bodies_paths


def create_bodies_paths(products, links):
    tree = Tree(products, links)
    return tree.create_bodies_paths()
