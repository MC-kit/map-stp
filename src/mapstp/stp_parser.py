"""The module defines methods and classes to parse STP file and represent parsing results."""

from __future__ import annotations

from typing import TYPE_CHECKING, TextIO, cast

import re

from dataclasses import dataclass, field

from mapstp.exceptions import FileError, STPParserError
from mapstp.utils import decode_russian

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

# Hint: check patterns on https://pythex.org/

_NUMBERED = r"^#(?P<digits>\d+)="

# Should match names like 'Component''s 2 replacement'
_NAME = r"'(?P<name>(''|[^'])+)'"

_SELECT_PATTERN = re.compile(
    _NUMBERED + r"(?P<solid>MANIFOLD_SOLID_BREP|BREP_WITH_VOIDS)|"
    r"(?P<link>NEXT_ASSEMBLY_USAGE)|"
    r"(?P<product>PRODUCT_DEFINITION\()",
)

_PRODUCT_PATTERN = re.compile(_NUMBERED + r"PRODUCT_DEFINITION\(" + _NAME + r",.*")
_LINK_PATTERN = re.compile(
    _NUMBERED
    + r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\("
    + _NAME
    + r",.*#(?P<src>\d+),#(?P<dst>\d+),\$\);",
)
_BODY_PATTERN = re.compile(
    _NUMBERED + r"(?:MANIFOLD_SOLID_BREP|BREP_WITH_VOIDS)\(" + _NAME + r",.*\);",
)
# ^#(?P<digits>\d+)=(?:MANIFOLD_SOLID_BREP|BREP_WITH_VOIDS)\('(?P<name>([^']*))',.*\);


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

    @property
    def is_leaf(self: Product) -> bool:
        """Tell if this product is the last in an STP path.

        The Leaf products may have bodies and can be shared between multiple paths in STP.

        Returns:
            False always for non LeafProducts.
        """
        return False

    @classmethod
    def from_string(cls: type[Product], text: str) -> Product:
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
            msg = f"not a 'Product' line: {text!r}"
            raise STPParserError(msg)
        number = int(match["digits"])
        name = match["name"]
        return cls(number, name)


# noinspection PyClassHasNoInit
@dataclass
class LeafProduct(Product):
    """The class to append bodies to "Product definitions"."""

    bodies: list[Body] = field(default_factory=list)

    @property
    def is_leaf(self: Product) -> bool:
        """Tell if this product is the last in an STP path.

        The Leaf products may have bodies and can be shared between multiple paths in STP.

        Returns:
            True always for LeafProducts
        """
        return True

    def append(self: LeafProduct, body: Body) -> None:
        """Append body to this product.

        Only applicable to LeafProduct.

        Args:
            body: what to append
        """
        self.bodies.append(body)


# noinspection PyClassHasNoInit
@dataclass
class Link(Numbered):
    """Linkage between products."""

    name: str
    src: int
    dst: int

    @classmethod
    def from_string(cls: type[Link], text: str) -> Link:
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
        if not match:  # pragma: no cover
            msg = f"not a 'Next assembly usage' line: {text!r}"
            raise STPParserError(msg)
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
    def from_string(cls: type[Body], text: str) -> Body:
        """Parse MANIFOLD_SOLID_BREP line.

        Args:
            text: input text

        Returns:
            The new Body object.

        Raises:
            STPParserError: on invalid input
        """
        match = _BODY_PATTERN.search(text)
        if not match:  # pragma: no cover
            msg = f"not a 'solid brep' line: {text!r}"
            raise STPParserError(msg)
        number = int(match["digits"])
        name = match["name"]
        return cls(number, name)


LinksList = list[Link]
ParseResult = tuple[list[Product], LinksList]

_VALID_FIRST_LINE = "ISO-10303-21;\n"
_VALID_THIRD_LINE = "FILE_DESCRIPTION(('STEP AP214'),'1');\n"


def parse(inp: TextIO) -> ParseResult:
    """Collect products and their links defined in an STP file.

    Args:
        inp: text of STP model.

    Returns:
        Tuple containing list of products and list of links between them.

    Raises:
        FileError: with line number where parsing failed
    """
    products: list[Product] = []
    links: LinksList = []
    check_header(inp)
    # normal stp has links and components,
    # but in 'simple' case there are bodies only and one product
    may_have_components = True
    for line_no_minus_3, line in enumerate(inp):
        match = _SELECT_PATTERN.search(line)
        if match:
            _line = decode_russian(line.rstrip())
            try:
                may_have_components = _process_line(
                    match,
                    _line,
                    links,
                    products,
                    may_have_components=may_have_components,
                )
            except STPParserError as exception:  # pragma: no cover
                msg = f"Error in line {line_no_minus_3 + 3}"
                raise FileError(msg) from exception
    return products, links


def _process_line(
    match: re.Match[str],
    line: str,
    links: list[Link],
    products: list[Product],
    *,
    may_have_components: bool,
) -> bool:
    group = match.lastgroup
    if group == "solid":
        may_have_components = _process_body(line, products, may_have_components=may_have_components)
    elif group == "link":
        _add_link(line, links, may_have_components=may_have_components)
    elif group == "product":
        if may_have_components:
            product = Product.from_string(line)
            products.append(product)
    else:  # pragma: no cover
        msg = "Shouldn't be here, check _SELECT_PATTERN"
        raise STPParserError(msg)
    return may_have_components


def _add_link(line: str, links: list[Link], *, may_have_components: bool) -> None:
    if not may_have_components:  # pragma: no cover
        msg = "Unexpected `link` is found in `simple` STP"
        raise STPParserError(msg)
    link = Link.from_string(line)
    links.append(link)


def _process_body(line: str, products: list[Product], *, may_have_components: bool) -> bool:
    body = Body.from_string(line)
    if not products:
        # Case for STP without components, just bodies
        products.append(LeafProduct(0, "dummy"))
        may_have_components = False
    last_product = products[-1]
    if last_product.is_leaf:
        leaf = cast("LeafProduct", last_product)
    else:
        products[-1] = leaf = LeafProduct(last_product.number, last_product.name)
    leaf.append(body)
    return may_have_components


def check_header(inp: TextIO) -> None:
    """Check if the inp is a valid STP file.

    Args:
        inp: input text stream

    Raises:
        FileError: if header is invalid or protocol is not AP214.
    """
    line = next(inp)
    if line != _VALID_FIRST_LINE:
        msg = f"Not a valid STP file: the expected first row {_VALID_FIRST_LINE[:-1]},actual {line}"
        raise FileError(msg)
    next(inp)
    line = next(inp)
    if line != _VALID_THIRD_LINE:
        msg = f"STP protocol is not AP214, the expected third row {_VALID_THIRD_LINE},actual {line}"
        raise FileError(msg)


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


def make_index(products: Iterable[Product]) -> dict[int, Product]:
    """Collect dictionary from a list of Product objects.

    Args:
        products: list of Product objects

    Returns:
        Dictionary product id -> product.
    """
    return {p.number: p for p in products}
