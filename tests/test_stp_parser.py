import pytest

from mapstp.stp_parser import Body, Link, Product, create_bodies_paths, parse

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


def test_stp_parser1(data):
    products, graph = parse(data / "test1.stp")  # noqa
    assert len(products) == 3
    components = list(map(lambda x: x.name, products))
    assert components == ["test1", "Component1", "Component2"]
    numbers = list(map(lambda x: x.number, products))
    assert numbers == [69, 80, 88]
    assert graph[69] == [80, 88]


def test_stp_parser2(data):
    products, graph = parse(data / "test2.stp")  # noqa
    assert len(products) == 4
    components = list(map(lambda x: x.name, products))
    assert components == ["Component1", "Component11", "test2", "Component2"]
    numbers = list(map(lambda x: x.number, products))
    assert numbers == [81, 91, 94, 110]
    assert graph[94] == [81, 110]
    assert graph[81] == [91]


def test_create_bodies_paths(data):
    products, graph = parse(data / "test1.stp")  # noqa
    bodies_paths = create_bodies_paths(products, graph)
    assert len(bodies_paths) == 3
    assert bodies_paths[0][-1] == "Body1"


if __name__ == "__main__":
    pytest.main()
