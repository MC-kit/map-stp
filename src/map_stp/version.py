import importlib.metadata as meta  # type: ignore

__title__ = "map_stp"
__distribution__ = meta.distribution(__title__)
__meta_data__ = __distribution__.metadata
__author__ = __meta_data__["Author"]
__author_email__ = __meta_data__["Author-email"]
__license__ = __meta_data__["License"]
__summary__ = __meta_data__["Summary"]
#  __copyright__ = (
#  "Copyright 2018-2020 Roman Rodionov"  TODO dvp: move to meta (project.toml)
#  )
__version__ = __distribution__.version

# def list_packages():
#   return sorted(map(lambda x: x.metadata["Name"], meta.distributions()))

if __name__ == "__main__":
    print(f"version: {__version__}")
