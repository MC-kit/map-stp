from typing import Dict, Iterable, List, Optional, TextIO, Tuple

import re

from dataclasses import dataclass, field
from pathlib import Path

_SELECT_PATTERN = re.compile(
    r"(?P<solid>MANIFOLD_SOLID_BREP)|(?P<link>NEXT_ASSEMBLY_USAGE)|(?P<product>PRODUCT_DEFINITION\()"
)

# check patterns on https://pythex.org/

# _NUMBERED_PATTERN = re.compile(r"^#(?P<digits>\d+)=")
_PRODUCT_PATTERN = re.compile(
    r"^#(?P<digits>\d+)=PRODUCT_DEFINITION\('(?P<name>[^']+)',.*"
)
_LINK_PATTERN = re.compile(
    r"^#(?P<digits>\d+)=NEXT_ASSEMBLY_USAGE_OCCURRENCE\('(?P<name>[^']+)',.*#(?P<src>\d+),#(?P<dst>\d+),\$\);"
)
_BODY_PATTERN = re.compile(
    r"^#(?P<digits>\d+)=MANIFOLD_SOLID_BREP\('(?P<name>[^']+)',.*\);"
)

# 89=MANIFOLD_SOLID_BREP('Body2',#159);


@dataclass
class Numbered:
    number: int

    # @classmethod
    # def from_string(cls, text: str) -> "Numbered":
    #     match = _NUMBERED_PATTERN.search(text)
    #     if not match:
    #         raise ValueError(f"not a numbered line: '{text}'")
    #     number = int(match["digits"])
    #     return cls(number)


@dataclass
class Product(Numbered):
    """
    The class to store "Product definitions"

    #69=PRODUCT_DEFINITION('test1','test1',#136,#1);

    """

    name: str
    bodies: list = field(default_factory=list)

    @classmethod
    def from_string(cls, text: str) -> "Product":
        match = _PRODUCT_PATTERN.search(text)
        if not match:
            raise ValueError(f"not a 'Product' line: '{text}'")
        number = int(match["digits"])
        name = match["name"]
        return cls(number, name)


@dataclass
class Link(Numbered):
    """
    Linkage between products.


    """

    name: str
    src: int
    dst: int

    @classmethod
    def from_string(cls, text: str) -> "Link":
        match = _LINK_PATTERN.search(text)
        if not match:
            raise ValueError(f"not a 'Next assembly usage' line: '{text}'")
        number = int(match["digits"])
        name = match["name"]
        src = int(match["src"])
        dst = int(match["dst"])
        return cls(number, name, src, dst)


@dataclass
class Body(Numbered):
    """
    Body (MCNP cell) definition

    #89=MANIFOLD_SOLID_BREP('Body2',#159);
    """

    name: str

    @classmethod
    def from_string(cls, text: str) -> "Body":
        match = _BODY_PATTERN.search(text)
        if not match:
            raise ValueError(f"not a 'solid brep' line: '{text}'")
        number = int(match["digits"])
        name = match["name"]
        return cls(number, name)


# def parse(inp: TextIO) -> Tuple[List[Product], Dict[int, List[int]]]:
#     products = []  # this list maintains sequence of products and bodies in the products
#     graph = defaultdict(list)
#     for line in inp:
#         match = _SELECT_PATTERN.search(line)
#         if match:
#             groups = match.groups()
#             if groups[0] is not None:  # solid
#                 body = Body.from_string(line)
#                 assert products, "At least one product is to be loaded at this step"
#                 last_product = products[-1]
#                 last_product.bodies.append(body)
#             elif groups[1] is not None:  # link
#                 link = Link.from_string(line)
#                 graph[link.src].append(link.dst)
#             elif groups[2] is not None:  # product
#                 product = Product.from_string(line)
#                 products.append(product)
#             else:
#                 assert False, "Shouldn't be here, check _SELECT_PATTERN"
#     return products, graph


LinksList = List[Tuple[int, int]]
ParseResult = Tuple[List[Product], LinksList]


def parse(inp: TextIO) -> ParseResult:
    products: List[Product] = []
    links: LinksList = []
    for line in inp:
        match = _SELECT_PATTERN.search(line)
        if match:
            groups = match.groups()
            if groups[0] is not None:  # solid
                body = Body.from_string(line)
                assert products, "At least one product is to be loaded at this step"
                last_product = products[-1]
                last_product.bodies.append(body)
            elif groups[1] is not None:  # link
                link = Link.from_string(line)
                links.append((link.src, link.dst))
            elif groups[2] is not None:  # product
                product = Product.from_string(line)
                products.append(product)
            else:
                assert False, "Shouldn't be here, check _SELECT_PATTERN"
    return products, links


def parse_path(inp: Path) -> ParseResult:
    with inp.open(encoding="utf8") as _inp:
        return parse(_inp)


def make_index(products: Iterable[Product]) -> Dict[int, Product]:
    return dict((p.number, p) for p in products)


# def invert_graph(graph: Dict[int, List[int]]) -> Dict[int, int]:
#     inverted_graph = dict()
#
#     for parent, childes in graph.items():
#         for i in childes:
#             if (
#                 i in inverted_graph
#             ):  # products may be duplicated
#                 prev_parent = inverted_graph[i]
#                 if prev_parent != parent:  # this actually can happen
#                     raise ValueError(
#                         f"Node {i} already has parent specified: {i}->{prev_parent} and {i}->{parent}"
#                     )
#             inverted_graph[i] = parent
#     return inverted_graph
#
#
# def create_bodies_paths(products, graph):
#     inverted_graph = invert_graph(graph)
#     products_index = make_index(products)
#     bodies_paths = []
#     for p in products:
#         inverted_path = [p.name]
#         pp: int = inverted_graph.get(p.number)
#         while pp:
#             inverted_path.append(products_index[pp].name)
#             pp = inverted_graph.get(pp)
#         path = inverted_path[::-1]
#         for b in p.bodies:
#             bodies_paths.append(path + [b.name])
#     return bodies_paths


@dataclass
class Node(Numbered):
    parent: "Node" = None
    childes: Dict[int, "Node"] = field(default_factory=dict)


def build_tree(links: LinksList) -> Tuple[Node, Dict[int, Node]]:
    nodes_index: Dict[int, Node] = dict()
    root: Optional[Node] = None
    for src, dst in links:
        assert src != dst, "I'm paranoiac after reading STP file"
        node: Node = nodes_index.get(src)
        if node is None:
            node = Node(src)
            nodes_index[src] = node
        if root is None:
            root = node
        child = nodes_index.get(dst)
        if child is None:
            child = Node(dst, parent=node)
            nodes_index[dst] = child
        else:
            if child.parent is None:
                child.parent = node
                if root is child:
                    root = node
            else:
                raise ValueError(f"Child {dst} already has parent {child.number}")
        if dst in node.childes:
            raise ValueError(f"Child {dst} is already added to parent {src}")
        node.childes[dst] = child
    return root, nodes_index


def collect_parents(number: int, nodes_index: Dict[int, Node]):
    node = nodes_index[number]
    parents = [node]
    while node.parent is not None:
        node = node.parent
        parents.append(node)
    return parents


def create_bodies_paths(products, links):
    root, nodes_index = build_tree(links)
    products_index = make_index(products)
    bodies_paths = []
    for link in links:
        src, dst = link
        product = products_index[dst]
        if product.bodies:
            parents = collect_parents(dst, nodes_index)
            inverted_path = list(
                map(lambda node: products_index[node.number].name, parents)
            )
            path = inverted_path[::-1]
            for b in product.bodies:
                bodies_paths.append(
                    path + [b.name]
                )  # TODO dvp: add transliteration for Russian names
    return bodies_paths
