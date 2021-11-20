from typing import List, Tuple

from dataclasses import dataclass

import pytest

from mapstp.stp_parser import Body, LeafProduct, Link, Product, parse_path
from mapstp.tree import create_bodies_paths


def test_product():
    actual = Product(2, "test")
    assert 2 == actual.number
    assert "test" == actual.name
    assert not actual.is_leaf
    actual2 = LeafProduct(actual.number, actual.name)
    assert actual2.is_leaf


@pytest.mark.parametrize(
    "text, expected",
    [
        ("#69=PRODUCT_DEFINITION('test1','test1',#136,#1);", Product(69, "test1")),
    ],
)
def test_product_from_string(text, expected):
    actual = Product.from_string(text)
    assert actual == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "#79=NEXT_ASSEMBLY_USAGE_OCCURRENCE('Component1','Component1','Component1',#69,#80,$);",  # noqa
            Link(79, "Component1", 69, 80),
        ),
    ],
)
def test_link_from_string(text, expected):
    actual = Link.from_string(text)
    assert actual == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "#89=MANIFOLD_SOLID_BREP('Body2',#159);",
            Body(89, "Body2"),
        ),
    ],
)
def test_body_from_string(text, expected):
    actual = Body.from_string(text)
    assert actual == expected


@dataclass
class _ParserTestResult:
    components: List[str]
    numbers: List[int]
    links: List[Tuple[int, int]]
    case: str

    def check(self, components, numbers, links):
        assert self.components == components, f"Wrong components, case: {self.case}"
        assert self.numbers == numbers, f"Wrong numbers, case: {self.case}"
        assert self.links == links, f"Wrong links, case: {self.case}"


@pytest.mark.parametrize(
    "stp, expected",
    [
        (
            "test1.stp",
            _ParserTestResult(
                ["test1", "Component1", "Component2"],
                [69, 80, 88],
                [(69, 80), (69, 88)],
                "two plain components",
            ),
        ),
        (
            "test3.stp",
            _ParserTestResult(
                ["Component1", "Component11", "test3", "Component2"],
                [81, 91, 94, 110],
                [(81, 91), (94, 81), (94, 110)],
                "one branch with two components and another with two bodies",
            ),
        ),
        (
            "test3a.stp",
            _ParserTestResult(
                ["Component1", "Component11", "test3", "Component''s 2 replacement"],
                [81, 91, 94, 110],
                [(81, 91), (94, 81), (94, 110)],
                "Same as above, but with apostrophe ('') in a component name",
            ),
        ),
        (
            "test-4-4-components-1-body.stp",
            _ParserTestResult(
                [
                    "Component1",
                    "Component1-1.2",
                    "test-4-4-components-1-body",
                    "Component2",
                    "Pattern",
                    "Component3",
                    "Component4",
                    "Component5",
                ],
                [129, 139, 142, 156, 171, 181, 196, 211],
                [
                    (129, 139),
                    (142, 129),
                    (156, 139),
                    (142, 156),
                    (171, 139),
                    (181, 171),
                    (142, 181),
                    (196, 139),
                    (142, 196),
                    (211, 139),
                    (142, 211),
                ],
                "array of common body",
            ),
        ),
        (
            "test-5-3-components-1-body.stp",
            _ParserTestResult(
                [
                    "Pattern",
                    "Component7",
                    "Component6",
                    "test-5-3-components-1-body",
                    "Component8",
                    "Component9",
                ],
                [99, 109, 112, 122, 134, 149],
                [
                    (99, 109),
                    (112, 99),
                    (122, 112),
                    (134, 109),
                    (122, 134),
                    (149, 109),
                    (122, 149),
                ],
                "one common body over several branches",
            ),
        ),
    ],
)
def test_stp_parser1(data, stp, expected):
    products, links = parse_path(data / stp)
    components = list(map(lambda x: x.name, products))
    numbers = list(map(lambda x: x.number, products))
    expected.check(components, numbers, links)


@dataclass
class _CreateBodiesPathsResult:
    length: int
    first_path: List[str]
    last_path: List[str]

    def check(self, stp, paths):
        assert len(paths) == self.length, f"Wrong length of paths found in {stp}"
        assert paths[0] == self.first_path, f"Wrong first path found in {stp}"
        assert paths[-1] == self.last_path, f"Wrong last path found in {stp}"


@pytest.mark.parametrize(
    "stp, expected",
    [
        (
            "test1.stp",
            _CreateBodiesPathsResult(
                3,
                ["test1", "Component1", "Body1"],
                ["test1", "Component2", "Body3"],
            ),
        ),
        (
            "test3.stp",
            _CreateBodiesPathsResult(
                3,
                ["test3", "Component1", "Component11", "Body1"],
                ["test3", "Component2", "Body3"],
            ),
        ),
        (
            "test-4-4-components-1-body.stp",
            _CreateBodiesPathsResult(
                5,
                ["test-4-4-components-1-body", "Component1", "Component1-1.2", "Body3"],
                ["test-4-4-components-1-body", "Component5", "Component1-1.2", "Body3"],
            ),
        ),
        (
            "test-5-3-components-1-body.stp",
            _CreateBodiesPathsResult(
                3,
                [
                    "test-5-3-components-1-body",
                    "Component6",
                    "Pattern",
                    "Component7",
                    "Solid",
                ],
                ["test-5-3-components-1-body", "Component9", "Component7", "Solid"],
            ),
        ),
    ],
)
def test_create_bodies_paths(data, stp, expected):
    products, links = parse_path(data / stp)
    paths = create_bodies_paths(products, links)
    expected.check(stp, paths)
    # assert len(bodies_paths) == 3
    # assert bodies_paths[0][-1] == "Body1"


def test_file_with_wrong_header(tmp_path):
    p = tmp_path / "test_with_wrong_header.stp"
    p.write_text("this is invalid stp file\nHEADER;")
    with pytest.raises(ValueError) as exc_info:
        parse_path(p)
        assert "Not a valid STP file" in exc_info.value.args[0]


def test_file_with_wrong_protocol(tmp_path):
    p = tmp_path / "test_with_wrong_protocol.stp"
    p.write_text('ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(("STEP AP246"), "1");\n')
    with pytest.raises(ValueError) as exc_info:
        parse_path(p)
        assert "STP protocol AP214 is expected" in exc_info.value.args[0]


if __name__ == "__main__":
    pytest.main()
