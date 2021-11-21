"""Data structures and algorithms to store and process STP nodes and their links."""

from typing import Any, Dict, Generator, Iterable, List, Optional, cast

from dataclasses import dataclass

from mapstp.exceptions import ParseError
from mapstp.stp_parser import LeafProduct, LinksList, Product, make_index


@dataclass
class Node:
    """Node for the following `Tree` class.

    Stores the references to a `Product` corresponding to a number
    presented in a `Link` as source or destination.
    Also stores reference to its parent node. Only upward search
    is necessary in this application, so, there's no references to childes.
    """

    product: Product
    parent: Optional["Node"] = None

    def collect_parents(self) -> Generator[Product, Any, Any]:
        """Iterate through the parents of the node from root parent to this node.

        Yields:
            Chain of products starting from the topmost node.
        """
        if self.parent is not None:
            yield from self.parent.collect_parents()
        yield self.product


class Tree:
    """Upward directed tree: it has to find only the parents from a given node.

    Indexes and stores results of STP file parsing.

    """

    def __init__(self, products: Iterable[Product], links: LinksList) -> None:
        """Create tree from objects found in an STP file.

        Args:
            products: list of product found on parsing STP
            links: pairs denoting links between the products.

        Raises:
            ParseError: if the information is screwed.
        """
        self._product_index: Dict[int, Product] = make_index(products)
        self._node_index: Dict[int, Node] = dict()
        self._body_links = []
        for link in links:
            src, dst = link
            product = self._product_index[dst]
            if product.is_leaf:
                self._body_links.append(link)
                parent = self._node_index.get(src)
                if parent is None:
                    self.__create_node(self._product_index[src])
            else:
                parent = self._node_index.get(src)
                if parent is None:
                    parent = self.__create_node(self._product_index[src])
                node = self._node_index.get(dst)
                if node is None:
                    self.__create_node(product, parent)
                else:
                    if node.parent is not None:
                        raise ParseError("Tree hierarchy in STP is invalid")
                    node.parent = parent

    def __create_node(self, product: Product, parent: Node = None) -> Node:
        """Create and register a node.

        Args:
            product: data associated with the new Node
            parent: its parent Node

        Returns:
            new Node

        """
        node = Node(product, parent)
        self._node_index[product.number] = node
        return node

    def create_bodies_paths(self) -> List[List[str]]:
        """Create list of paths for each body in STP file.

        A path is in turn a list of strings - parts of the path.

        Returns:
            The list of paths.
        """
        bodies_paths = []
        for link in self._body_links:
            src, dst = link
            product = self._product_index[dst]
            if product.is_leaf:
                node = self._node_index[src]
                path = list(map(lambda parent: parent.name, node.collect_parents()))
                path.append(product.name)
                # TODO dvp: design flaw: separate indexes for
                #           Products and LeafProducts to avoid cast
                for b in cast(LeafProduct, product).bodies:
                    bodies_paths.append(
                        path + [b.name]
                    )  # TODO dvp: add transliteration for Russian names
        return bodies_paths


def create_bodies_paths(
    products: Iterable[Product], links: LinksList
) -> List[List[str]]:
    """Create list of paths for each body in STP file.

    A path is in turn a list of strings - parts of the path.

    Args:
        products: list of product found on parsing STP
        links: pairs denoting links between the products.


    Returns:
        The list of paths.
    """
    tree = Tree(products, links)
    return tree.create_bodies_paths()
