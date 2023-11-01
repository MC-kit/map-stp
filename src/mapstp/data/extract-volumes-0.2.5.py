"""Collect sequence of bodies names, compute volumes and bounding boxes.

Run this in SpaceClaim session.

Works fine with SpaceClaim API V17 - V20.
The API works with IronPython 2.6 through 2.7
"""
from __future__ import annotations

import sqlite3 as sq
import sys

from os.path import splitext

__version__ = "0.2.5"
#
# Changes
# -------
#
# 0.2.5 - dvp
#     Save STP after run.
#     Index cells from 1 in SQL - to avoid fixing on processing
#     Extended cells table - to avoid creating copy with additional columns
#     Add computing and saving bounding box corners for each cell
# 0.2.4 - dvp
#     Add root component name - may be used for default material mapping for all the subcomponents.
# 0.2.3 - dvp
#     fix csv writing on API V17 beta - doesn't support print file parameter.
# 0.2.2 - dvp
#     Get rid of global variables.
#     Reduce complexity.
#     Add warnings and messages.
# 0.2.1 - dvp
#     Add sqlite output.
#


def _are_we_in_space_claim_session():
    to_be_provided = ["Window", "DocumentSave", "Matrix"]
    g = globals()
    for o in to_be_provided:
        if o not in g:
            print("Symbol " + o + " is not defined.")
            print("Run this script from a SpaceClaim session.")
            sys.exit(-1)


_are_we_in_space_claim_session()


class BodiesCollector:
    """Information collected on walk through the bodies and define their volumes and STP paths."""

    def __init__(self):
        self.existing_path = set()
        self.start_index = {}
        self.sequence = []
        self.modified = False

    def walk(self, component, prefix="/"):  # noqa: ANN201
        """Walk through the bodies and define their volumes and STP paths.

        Args:
            component: component in the tree or leaf body
            prefix: accumulated path along the tree
        """
        base_name = self._make_unique_name(component, prefix)

        if hasattr(component, "Components"):
            base_name += "/"

            for comp in component.Components:
                self.walk(comp, base_name)

            bodies = component.GetBodies()
            print(base_name, ": ", len(bodies))

            for body in bodies:
                self.walk(body, base_name)
        else:
            shape = component.Shape
            vol = shape.Volume * 1.0e6  # m^3 -> cm^3
            bounding_box = shape.GetBoundingBox(Matrix.Identity, tight=True)  # noqa: F821
            minx, miny, minz = bounding_box.MinCorner
            maxx, maxy, maxz = bounding_box.MaxCorner
            minx, miny, minz, maxx, maxy, maxz = (
                t * 100.0 for t in (minx, miny, minz, maxx, maxy, maxz)
            )  # m -> cm
            self.sequence.append((vol, minx, miny, minz, maxx, maxy, maxz, base_name))

    def _make_unique_name(self, component, prefix):
        name = initial_name = component.GetName()
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


def _set_suffix(path, suffix):
    return splitext(path)[0] + suffix


def _save_to_csv(document_path, sequence):
    output = _set_suffix(document_path, "-component-volumes.csv")
    with open(output, "w") as f:
        f.write(b"offset,name,volume\n")  # cannot use print on API V17 Beta
        for i, (vol, minx, miny, minz, maxx, maxy, maxz, stp) in enumerate(sequence):
            items = [str(t) for t in (i + 1, vol, minx, miny, minz, maxx, maxy, maxz)] + [stp]
            row = ",".join(items) + "\n"
            f.write(row.encode("utf8"))
    print("Cells and information on them are stored in CSV: " + output)


def _save_to_db(document_path, sequence):
    output = _set_suffix(document_path, ".sqlite")
    con = sq.connect(output)
    cur = con.cursor()
    cur.execute(
        """
        drop table if exists cells;
        """,
    )
    cur.execute(
        """
        create table cells (
            cell integer primary key,
            volume real,      -- volume computed by SpaceClaim
            xmin real,        -- bounding box boundaries
            ymin real,
            zmin real,
            xmax real,
            ymax real,
            zmax real,
            path text unique,   -- path to body in SpaceClaim
            material integer default 0,  -- mapstp will update this and the following
            density real default 0.0,
            correction real,   -- density correction factor
            rwcl text         -- rwcl tag
        );
        """,
    )
    cur.executemany(
        """
            insert into cells
                (cell, volume, xmin, ymin, zmin, xmax, ymax, zmax, path)
            values
                (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ((i + 1), v, x0, y0, z0, x1, y1, z1, p)
            for i, (v, x0, y0, z0, x1, y1, z1, p) in enumerate(sequence)
        ),
    )
    con.commit()
    cur.close()
    con.close()
    print("Cells and information on them are stored in the database: " + output)


def _save_stp(document_path):
    stp_output = _set_suffix(document_path, ".stp")
    DocumentSave.Execute(stp_output)  # noqa: F821
    print("STP file is saved to " + stp_output)


def main():  # noqa: ANN201
    """Extract cell volumes and other information.

    Scans all the bodies in a SpaceClaim active document,
    collecting information on cells:
        - stp path,
        - volume,
        - bounding box boundaries.

    Then stores the information in CSV file and SQLite database.
    Saves STP file automatically.
    If the model component names were modified (to make the paths unique),
    then saves the model with warning.
    """
    print("extract-volumes" + " v" + __version__)
    document = Window.ActiveWindow.Document  # noqa: F821
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
    _save_stp(document_path)

    if collector.modified:
        print("The SpaceClaim model was modified, saving it.")
        DocumentSave.Execute(document_path)  # noqa: F821

    print("Success!")


main()
