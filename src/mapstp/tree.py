"""Data structures and algorithms to store and process STP nodes and their links."""
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Iterator, cast

from dataclasses import dataclass

from mapstp.exceptions import STPParserError
from mapstp.stp_parser import LeafProduct, make_index

if TYPE_CHECKING:
    from mapstp.stp_parser import LinksList, Product


@dataclass
class Node:
    """Node for the following `Tree` class.

    Stores the references to a `Product` corresponding to a number
    presented in a `Link` as source or destination.
    Also stores reference to its parent node. Only upward search
    is necessary in this application, so, there's no references to childes.
    """

    product: Product
    parent: Node | None = None

    def collect_parents(self) -> Iterator[Product]:
        """Iterate through the parents of the node from root parent to this node.

        Yields:
            Chain of products starting from the topmost node.
        """
        if self.parent is not None:
            yield from self.parent.collect_parents()
        yield self.product


class Tree:
    """Upward directed tree: it is used to find only the parents from a given node.

    Indexes and stores results of STP file parsing.
    """

    def __init__(self, products: Iterable[Product], links: LinksList) -> None:
        """Create tree from objects found in an STP file.

        Args:
            products: list of product found on parsing STP
            links: pairs denoting links between the products.
        """
        self._product_index: dict[int, Product] = make_index(products)
        self._node_index: dict[int, Node] = {}
        self._body_links: LinksList = []
        for link in links:
            self._create_nodes_from_link(link)

    def create_bodies_paths(self) -> list[list[str]]:
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
                path = [parent.name for parent in node.collect_parents()]
                path.append(product.name)
                # TODO dvp: design flaw: separate indexes for
                #           Products and LeafProducts to avoid cast
                for b in cast(LeafProduct, product).bodies:
                    bodies_paths.append(
                        [*path, b.name],
                    )  # TODO dvp: add transliteration for Russian names
        return bodies_paths

    def _create_nodes_from_link(self, link: tuple[int, int]) -> None:
        src, dst = link
        product = self._product_index[dst]
        parent = self._node_index.get(src)
        if parent is None:
            parent = self._create_node(self._product_index[src])
        if product.is_leaf:
            self._body_links.append(link)
        else:
            self._add_or_update_intermediate_node(dst, parent, product)

    def _add_or_update_intermediate_node(self, dst: int, parent: Node, product: Product) -> None:
        node = self._node_index.get(dst)
        if node is None:
            self._create_node(product, parent)
        else:
            if node.parent is not None:  # pragma: no cover
                raise STPParserError
            node.parent = parent

    def _create_node(self, product: Product, parent: Node | None = None) -> Node:
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


def create_bodies_paths(products: Iterable[Product], links: LinksList) -> list[list[str]]:
    """Create list of paths for each body in STP file.

    A path is in turn a list of strings - parts of the path.

    Args:
        products: list of product found on parsing STP
        links: pairs denoting links between the products.

    Returns:
        The list of paths.

    Raises:
        ValueError: if more than one product is found in STP without components
    """
    if links:
        tree = Tree(products, links)
        return tree.create_bodies_paths()

    ps = list(products)

    if len(ps) != 1:  # pragma: no cover
        msg = "Only one product is expected for `simple` stp"
        raise ValueError(msg)

    product = cast(LeafProduct, ps[0])
    bodies_paths = []

    for b in product.bodies:
        bodies_paths.append([b.name])  # TODO dvp: add transliteration for Russian names

    return bodies_paths
