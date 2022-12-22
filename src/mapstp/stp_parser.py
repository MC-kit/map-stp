"""The module defines methods and classes to parse STP file and represent parsing results."""

from typing import Dict, Iterable, List, TextIO, Tuple

import re

from dataclasses import dataclass, field
from pathlib import Path

from mapstp.exceptions import FileError, STPParserError

# Hint: check patterns on https://pythex.org/

_NUMBERED = r"^#(?P<digits>\d+)="
_NAME = r"'(?P<name>(?:''|[^'])+)'"

_SELECT_PATTERN = re.compile(
    _NUMBERED + r"(?P<solid>MANIFOLD_SOLID_BREP|BREP_WITH_VOIDS)|"
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
_BODY_PATTERN = re.compile(
    _NUMBERED + r"(?:MANIFOLD_SOLID_BREP|BREP_WITH_VOIDS)\(" + _NAME + r",.*\);"
)


# noinspection PyClassHasNoInit
@dataclass
class Numbered:
    """The class shares common property of STP objects: number."""

    number: int


# noinspection PyClassHasNoInit
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
            STPParserError: if `text` doesn't match 'PRODUCT_DEFINITION' statement format.

        """
        match = _PRODUCT_PATTERN.search(text)
        if not match:
            raise STPParserError(f"not a 'Product' line: '{text}'")
        number = int(match["digits"])
        name = match["name"]
        return cls(number, name)

    def append(self, body: "Body") -> None:
        """Append body to this product.

        Only applicable to LeafProduct.

        Args:
            body: what to append

        Raises:
            NotImplementedError: always, should be implemented in a subclass
        """
        raise NotImplementedError(f"Cannot add a Body object to {self}")

    @property
    def is_leaf(self) -> bool:
        """Tell if this product is the last in an STP path.

        The Leaf products may have bodies and can be shared between multiple paths in STP.

        Returns:
            False always for non LeafProducts.
        """
        return False


# noinspection PyClassHasNoInit
@dataclass
class LeafProduct(Product):
    """The class to append bodies to "Product definitions"."""

    bodies: List["Body"] = field(default_factory=list)

    def append(self, body: "Body") -> None:
        """Append body to this product.

        Only applicable to LeafProduct.

        Args:
            body: what to append

        """
        self.bodies.append(body)

    @property
    def is_leaf(self) -> bool:
        """Tell if this product is the last in an STP path.

        The Leaf products may have bodies and can be shared between multiple paths in STP.

        Returns:
            True always for LeafProducts
        """
        return True


# noinspection PyClassHasNoInit
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

        Raises:
            STPParserError: on invalid input
        """
        match = _LINK_PATTERN.search(text)
        if not match:
            raise STPParserError(f"not a 'Next assembly usage' line: '{text}'")
        number = int(match["digits"])
        name = match["name"]
        src = int(match["src"])
        dst = int(match["dst"])
        return cls(number, name, src, dst)


# noinspection PyClassHasNoInit
@dataclass
class Body(Numbered):
    """Body (MCNP cell) definition."""

    name: str

    @classmethod
    def from_string(cls, text: str) -> "Body":
        """Parse MANIFOLD_SOLID_BREP line.

        Args:
            text: input text

        Returns:
            The new Body object.

        Raises:
            STPParserError: on invalid input
        """
        match = _BODY_PATTERN.search(text)
        if not match:
            raise STPParserError(f"not a 'solid brep' line: '{text}'")
        number = int(match["digits"])
        name = match["name"]
        return cls(number, name)


LinksList = List[Tuple[int, int]]
ParseResult = Tuple[List[Product], LinksList]

_VALID_FIRST_LINE = "ISO-10303-21;\n"
_VALID_THIRD_LINE = "FILE_DESCRIPTION(('STEP AP214'),'1');\n"


def parse(inp: TextIO) -> ParseResult:
    """Collect products and their links defined in an STP file.

    Args:
        inp: text of STP model.

    Returns:
        Tuple containing list of products and list of links between them.

    Raises:
        FileError: on invalid file header and if STP protocol is not AP214
    """
    products: List[Product] = []
    links: LinksList = []
    check_header(inp)
    # normal stp has links and components,
    # but in q 'simple' case there are bodies only and one product
    may_have_components = True
    for line_no_minus_3, line in enumerate(inp):
        try:
            match = _SELECT_PATTERN.search(line)
            if match:
                group = match.lastgroup
                if group == "solid":
                    body = Body.from_string(line)
                    if not products:
                        # msg = "At least one product is to be loaded at this step"
                        # raise STPParserError(msg)

                        # Case for STP without components, just bodies
                        products.append(LeafProduct(0, "dummy"))
                        may_have_components = False
                    last_product = products[-1]
                    if not last_product.is_leaf:
                        products[-1] = last_product = LeafProduct(
                            last_product.number, last_product.name
                        )
                    last_product.append(body)
                elif group == "link":
                    if not may_have_components:
                        msg = "Unexpected `link` is found in `simple` STP"
                        raise STPParserError(msg)
                    link = Link.from_string(line)
                    links.append((link.src, link.dst))
                elif group == "product":
                    if may_have_components:
                        product = Product.from_string(line)
                        products.append(product)
                else:
                    msg = "Shouldn't be here, check _SELECT_PATTERN"
                    raise STPParserError(msg)
        except STPParserError as exception:
            raise FileError(f"Error in line {line_no_minus_3 + 3}") from exception
    return products, links


def check_header(inp: TextIO) -> None:
    """Check if the inp is a valid STP file.

    Args:
        inp: input text stream

    Raises:
        FileError: if header is invalid or protocol is not AP214.
    """
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


def parse_path(inp: Path) -> ParseResult:
    """Collect products and their links defined in an STP file given by path.

    Prepares and delegates the work to :meth:`parse` method.

    Args:
        inp: path to STP model.

    Returns:
        Tuple containing list of products and list of links between them.

    """
    with inp.open(encoding="cp1251") as _inp:
        return parse(_inp)


def make_index(products: Iterable[Product]) -> Dict[int, Product]:
    """Collect dictionary from a list of Product objects.

    Args:
        products: list of Product objects

    Returns:
        Dictionary product id -> product.
    """
    return {p.number: p for p in products}
