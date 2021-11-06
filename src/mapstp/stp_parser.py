from typing import Dict, Iterable, List, TextIO

import re

from collections import defaultdict
from dataclasses import dataclass, field
from functools import singledispatch
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


@singledispatch
def parse(inp: TextIO):
    products = []  # this list maintains sequence of products and bodies in the products
    graph = defaultdict(list)
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
                graph[link.src].append(link.dst)
            elif groups[2] is not None:  # product
                product = Product.from_string(line)
                products.append(product)
            else:
                assert False, "Shouldn't be here, check _SELECT_PATTERN"
    return products, graph


def make_index(products: Iterable[Numbered]) -> Dict[int, Numbered]:
    return dict((p.number, p) for p in products)


def invert_graph(graph: Dict[int, List[int]]) -> Dict[int, int]:
    inverted_graph = dict()
    for k, v in graph.items():
        for i in v:
            assert i not in inverted_graph, "The parents in a tree should be unique"
            inverted_graph[i] = k
    return inverted_graph


def create_bodies_paths(products, graph):
    inverted_graph = invert_graph(graph)
    products_index = make_index(products)
    bodies_paths = []
    body_id = 0
    for p in products:
        inverted_path = [p.name]
        pp: int = inverted_graph.get(p.number)
        while pp:
            inverted_path.append(products_index[pp].name)
            pp = inverted_graph.get(pp)
        path = inverted_path[::-1]
        for b in p.bodies:
            bodies_paths.append(path + [b.name + f"{++body_id}"])
    return bodies_paths


@parse.register
def _(inp: Path):
    with inp.open(encoding="utf8") as _inp:
        return parse(_inp)
