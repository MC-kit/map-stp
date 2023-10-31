"""Collect sequence of component names and compute volumes.

Works fine with SpaceClaim API V17 - V20.
"""
from __future__ import annotations

import sqlite3 as sq
import sys

from os.path import splitext

__version__ = "0.2.4"
#
# Changes
# -------
#
# 0.2.4 - dvp
#     Add root component name - may be used for default material mapping for all the subcomponents.
# 0.2.3 - dvp
#     fix csv writing on API V17 beta - doesn't support print file parameter.
# 0.2.2 - dvp
#     Get rid off global variables.
#     Reduce complexity.
#     Add warnings and messages.
# 0.2.1 - dvp
#     Add sqlite output.
#


class BodiesCollector:
    """Walk through the bodies and define their volumes and STP paths."""

    def __init__(self):
        self.existing_path = set()
        self.start_index = {}
        self.sequence = []
        self.modified = False

    def make_unique_name(self, component, prefix):
        initial_name = component.GetName()
        base_name = prefix + initial_name
        i = self.start_index.get(base_name, 0)

        while base_name in self.existing_path:
            name = initial_name + str(i)
            base_name = prefix + name
            i += 1

        self.existing_path.add(base_name)

        if i > 0:
            self.start_index[prefix + initial_name] = i
            component.SetName(name)
            self.modified = True
            print("Create unique component name", name)

        return base_name

    def walk(self, component, prefix="/"):
        base_name = self.make_unique_name(component, prefix)

        if hasattr(component, "Components"):
            base_name += "/"

            for comp in component.Components:
                self.walk(comp, base_name)

            bodies = component.GetBodies()
            print(base_name, ": ", len(bodies))

            for body in bodies:
                self.walk(body, base_name)
        else:
            vol = component.Shape.Volume * 1.0e6  # -> cm^3
            self.sequence.append((base_name, vol))


def _set_suffix(path, suffix):
    return splitext(path)[0] + suffix


def _save_to_csv(document_path, sequence):
    output = _set_suffix(document_path, "-component-volumes.csv")
    with open(output, "w") as f:
        f.write(b"offset,name,volume\n")  # cannot use print on API V17 Beta
        for i, (stp, vol) in enumerate(sequence):
            row = str(i + 1) + "," + stp + "," + str(vol) + "\n"
            f.write(row.encode("utf8"))
    print("Components and volumes are stored in CSV: " + output)


def _save_to_db(document_path, sequence):
    output = _set_suffix(document_path, ".sqlite")
    con = sq.connect(output)
    cur = con.cursor()
    cur.execute(
        """
        drop table if exists number_path_volume;
        """,
    )
    cur.execute(
        """
     create table number_path_volume (
        number integer primary key,
        path text unique,
        volume real
     );
      """,
    )
    cur.executemany(
        """
      insert into number_path_volume
      (number, path, volume)
      values (?, ?, ?)
      """,
        ((i, p, v) for i, (p, v) in enumerate(sequence)),
    )
    con.commit()
    cur.close()
    con.close()
    print("Components and volumes are stored in the database: " + output)


if "Window" not in globals():
    print("Run this script from SpaceClaim session.")
    sys.exit(-1)


def main():
    print("extract-volumes" + " v" + __version__)
    document = Window.ActiveWindow.Document
    document_path = document.Path

    if not document_path:
        print("Document is to be saved to scdoc file before running this script")
        sys.exit(-1)

    print("Processing document ", document_path)

    collector = BodiesCollector()
    main_part = document.MainPart

    for component in main_part.Components:
        collector.walk(component, main_part.GetName() + "/")

    print("Scan is complete")

    sequence = collector.sequence

    _save_to_csv(document_path, sequence)
    _save_to_db(document_path, sequence)

    if collector.modified:
        print("The SpaceClaim model was modified, don't forget to save it.")

    print("Success!")


main()
