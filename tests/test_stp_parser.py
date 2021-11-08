from typing import List, Tuple

from dataclasses import dataclass

import pytest

from mapstp.stp_parser import Body, Link, Product, create_bodies_paths, parse_path

# def test_numbered():
#     actual = Numbered(1)
#     assert actual.number == 1


# @pytest.mark.parametrize(
#     "text, expected",
#     [
#         ("#69=xxx", 69),
#     ],
# )
# def test_numbered_from_string(text, expected):
#     actual = Numbered.from_string(text)
#     assert actual.number == expected


def test_product():
    actual = Product(2, "test")
    assert actual.number == 2
    assert actual.name == "test"
    assert len(actual.bodies) == 0


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
            "#79=NEXT_ASSEMBLY_USAGE_OCCURRENCE('Component1','Component1','Component1',#69,#80,$);",
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
class ParserTestResult:
    components: List[str]
    numbers: List[int]
    links: List[Tuple[int, int]]

    def check(self, components, numbers, links):
        assert self.components == components, "Wrong components"
        assert self.numbers == numbers, "Wrong numbers"
        assert self.links == links, "Wrong links"


@pytest.mark.parametrize(
    "stp, expected",
    [
        (
            "test1.stp",
            ParserTestResult(
                ["test1", "Component1", "Component2"],
                [69, 80, 88],
                [(69, 80), (69, 88)],
            ),
        ),
        (
            "test3.stp",
            ParserTestResult(
                ["Component1", "Component11", "test3", "Component2"],
                [81, 91, 94, 110],
                [(81, 91), (94, 81), (94, 110)],
            ),
        ),
        (
            "test-4-4-components-1-body.stp",
            ParserTestResult(
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
            ),
        ),
        (
            "test-5-3-components-1-body.stp",
            ParserTestResult(
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
class CreateBodiesPathsResult:
    length: int
    first_path: List[str]
    last_path: List[str]

    def check(self, stp, paths):
        assert self.length == len(paths), f"Wrong length of paths found in {stp}"
        assert self.first_path == paths[0], f"Wrong first path found in {stp}"
        assert self.last_path == paths[-1], f"Wrong last path found in {stp}"


@pytest.mark.parametrize(
    "stp, expected",
    [
        # (
        #     "test1.stp",
        #     CreateBodiesPathsResult(
        #         3,
        #         ["test1", "Component1", "Body1"],
        #         ["test1", "Component2", "Body3"],
        #     ),
        # ),
        # (
        #     "test3.stp",
        #     CreateBodiesPathsResult(
        #         3,
        #         ["test3", "Component1", "Component11", "Body1"],
        #         ["test3", "Component2", "Body3"],
        #     ),
        # ),
        (
            "test-4-4-components-1-body.stp",
            CreateBodiesPathsResult(
                5,
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


if __name__ == "__main__":
    pytest.main()
