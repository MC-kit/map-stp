from typing import Optional

from dataclasses import dataclass

from mapstp.stp_parser import Product, make_index


@dataclass
class Node:
    product: Product
    parent: Optional["Node"] = None

    def collect_parents(self):
        if self.parent is not None:
            yield from self.parent.collect_parents()
        yield self.product


class Tree:
    """
    Upward directed tree: it has to find only the parents from a given node.
    """

    def __init__(self, products, links):
        self.product_index = make_index(products)
        self.node_index = dict()
        self.body_links = []
        for link in links:
            src, dst = link
            product = self.product_index[dst]
            if product.is_leaf:
                self.body_links.append(link)
                parent = self.node_index.get(src)
                if parent is None:
                    self._create_node(self.product_index[src])
            else:
                parent = self.node_index.get(src)
                if parent is None:
                    parent = self._create_node(self.product_index[src])
                node = self.node_index.get(dst)
                if node is None:
                    self._create_node(product, parent)
                else:
                    assert node.parent is None, "Tree hierarchy in STP is invalid"
                    node.parent = parent

    def _create_node(self, product: Product, parent: Node = None) -> Node:
        node = Node(product, parent)
        self.node_index[product.number] = node
        return node

    def create_bodies_paths(self):
        bodies_paths = []
        for link in self.body_links:
            src, dst = link
            product = self.product_index[dst]
            if product.is_leaf:
                node = self.node_index[src]
                parents = node.collect_parents()
                path = list(
                    map(lambda parent: self.product_index[parent.number].name, parents)
                )
                path.append(product.name)
                for b in product.bodies:
                    bodies_paths.append(
                        path + [b.name]
                    )  # TODO dvp: add transliteration for Russian names
        return bodies_paths


def create_bodies_paths(products, links):
    tree = Tree(products, links)
    return tree.create_bodies_paths()
