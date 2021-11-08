from typing import Dict, Iterable, List, TextIO, Tuple

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


LinksList = List[Tuple[int, int]]
ParseResult = Tuple[List[Product], LinksList]

_VALID_FIRST_LINE = "ISO-10303-21;\n"
_VALID_THIRD_LINE = "FILE_DESCRIPTION(('STEP AP214'),'1');\n"


def parse(inp: TextIO) -> ParseResult:
    products: List[Product] = []
    links: LinksList = []
    line = next(inp)
    if line != _VALID_FIRST_LINE:
        raise ValueError("Not a valid STP file")
    next(inp)
    line = next(inp)
    if line != _VALID_THIRD_LINE:
        raise ValueError("STP protocol AP214 is expected")
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


def collect_parents(src: int, links_index):
    parents = [src]
    while True:
        src = links_index.get(src, None)
        if src is None:
            break
        parents.append(src)
    return parents[::-1]


def create_inner_nodes_index(links, products_index):
    index = dict()
    for src, dst in links:
        if not products_index[dst].bodies:
            index[dst] = src
    return index


def create_bodies_paths(products, links):
    products_index = make_index(products)
    links_index = create_inner_nodes_index(links, products_index)
    bodies_paths = []
    for link in links:
        src, dst = link
        product = products_index[dst]
        if product.bodies:
            parents = collect_parents(src, links_index)
            path = list(map(lambda number: products_index[number].name, parents))
            path.append(product.name)
            for b in product.bodies:
                bodies_paths.append(
                    path + [b.name]
                )  # TODO dvp: add transliteration for Russian names
    return bodies_paths
