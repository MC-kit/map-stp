"""The module defines methods and classes to parse STP file and represent parsing results."""
from typing import Dict, Iterable, List, TextIO, Tuple

import re

from dataclasses import dataclass, field
from pathlib import Path

# check patterns on https://pythex.org/

_NUMBERED = r"^#(?P<digits>\d+)="
_NAME = r"'(?P<name>(?:''|[^'])+)'"

_SELECT_PATTERN = re.compile(
    _NUMBERED + r"(?P<solid>MANIFOLD_SOLID_BREP)|"
    r"(?P<link>NEXT_ASSEMBLY_USAGE)|"
    r"(?P<product>PRODUCT_DEFINITION\()"
)

_PRODUCT_PATTERN = re.compile(_NUMBERED + r"PRODUCT_DEFINITION\(" + _NAME + r",.*")
_LINK_PATTERN = re.compile(
    _NUMBERED
    + r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\("
    + _NAME
    + r",.*#(?P<src>\d+),#(?P<dst>\d+),\$\);"
)
_BODY_PATTERN = re.compile(_NUMBERED + r"MANIFOLD_SOLID_BREP\(" + _NAME + r",.*\);")


class FileError(ValueError):
    """STP parser file format error."""


class ParseError(FileError):
    """STP parser syntax error."""


@dataclass
class Numbered:
    """The class shares common property of STP objects: number."""

    number: int


@dataclass
class Product(Numbered):
    """The class to store "Product definitions"."""

    name: str

    @classmethod
    def from_string(cls, text: str) -> "Product":
        """Create Product from a text string.

        Args:
            text: Line with 'PRODUCT_DEFINITION' statement from an STP file.

        Returns:
            New product with given number and name.

        Raises:
            ParseError: if `text` doesn't match 'PRODUCT_DEFINITION' statement format.
            NotImplementedError: on attempt to add Body to this class

        """
        match = _PRODUCT_PATTERN.search(text)
        if not match:
            raise ParseError(f"not a 'Product' line: '{text}'")
        number = int(match["digits"])
        name = match["name"]
        return cls(number, name)

    def append(self, body: "Body"):
        raise NotImplementedError(f"Cannot add a Body object to {self}")

    @property
    def is_leaf(self) -> bool:
        return False


@dataclass
class LeafProduct(Product):
    """The class to append bodies to "Product definitions"."""

    bodies: List["Body"] = field(default_factory=list)

    def append(self, body: "Body"):
        self.bodies.append(body)

    @property
    def is_leaf(self) -> bool:
        return True


@dataclass
class Link(Numbered):
    """Linkage between products."""

    name: str
    src: int
    dst: int

    @classmethod
    def from_string(cls, text: str) -> "Link":
        """Parse STP line with NEXT_OCCURRENCE_USAGE.

        The line specifies a source->destination link between products.

        Args:
            text: line from STP file being parsed.

        Returns:
            new `Link` object.
        """
        match = _LINK_PATTERN.search(text)
        if not match:
            raise ParseError(f"not a 'Next assembly usage' line: '{text}'")
        number = int(match["digits"])
        name = match["name"]
        src = int(match["src"])
        dst = int(match["dst"])
        return cls(number, name, src, dst)


@dataclass
class Body(Numbered):
    """Body (MCNP cell) definition."""

    name: str

    @classmethod
    def from_string(cls, text: str) -> "Body":
        """Parse MANIFOLD_SOLID_BREP line."""
        match = _BODY_PATTERN.search(text)
        if not match:
            raise ParseError(f"not a 'solid brep' line: '{text}'")
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
        raise FileError(
            "Not a valid STP file: the expected first row "
            f"{_VALID_FIRST_LINE[:-1]}, actual {line}"
        )
    next(inp)
    line = next(inp)
    if line != _VALID_THIRD_LINE:
        raise FileError(
            "STP protocol is not AP214, the expected third row "
            f"{_VALID_THIRD_LINE}, actual {line}"
        )
    for line_no_minus_3, line in enumerate(inp):
        try:
            match = _SELECT_PATTERN.search(line)
            if match:
                group = match.lastgroup
                if group == "solid":
                    body = Body.from_string(line)
                    if not products:
                        raise ParseError(
                            "At least one product is to be loaded at this step"
                        )
                    last_product = products[-1]
                    if not last_product.is_leaf:
                        products[-1] = last_product = LeafProduct(
                            last_product.number, last_product.name
                        )
                    last_product.append(body)
                elif group == "link":
                    link = Link.from_string(line)
                    links.append((link.src, link.dst))
                elif group == "product":
                    product = Product.from_string(line)
                    products.append(product)
                else:
                    raise ParseError("Shouldn't be here, check _SELECT_PATTERN")
        except ParseError as exception:
            raise FileError(f"Error in line {line_no_minus_3 + 3}") from exception
    return products, links


def parse_path(inp: Path) -> ParseResult:
    with inp.open(encoding="cp1251") as _inp:
        return parse(_inp)


def make_index(products: Iterable[Product]) -> Dict[int, Product]:
    return dict((p.number, p) for p in products)
