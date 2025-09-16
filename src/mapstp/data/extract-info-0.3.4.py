"""Collect sequence of bodies names, compute volumes and bounding boxes.

Run this in SpaceClaim session.

Works fine with SpaceClaim API V17 - V20.
The API works with IronPython 2.6 through 2.7
"""

from __future__ import annotations

import re
import sqlite3 as sq
import sys

from os.path import splitext

__version__ = "0.3.4"

#
# Changes
# -------
#
# 0.3.4 - dvp
#     Fix name modification reporting
#
# 0.3.3 - dvp
#     Fix column names on CSV output
#
# 0.3.2 - dvp
#     Use SpaceClaim native functionality to scan bodies - for less complexity and better performance
#     Add versions table to facilitate compatibility with future changes
# 0.3.1 - dvp
#     Message on saving to scscript to enable automatic STP saving
# 0.3.0 - dvp
#     Fix bodies name output on automatic saving.
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


version_info = tuple(int(x) for x in __version__.split("."))
DIGITS_AT_END = re.compile(r"(?P<digits>(\d+))$")


def _are_we_in_space_claim_session():
    to_be_provided = ["Window", "DocumentSave", "Matrix"]
    g = globals()
    for o in to_be_provided:
        if o not in g:
            print("Symbol " + o + " is not defined.")
            print("Run this script from a SpaceClaim session.")
            sys.exit(-1)


_are_we_in_space_claim_session()


def scan_bodies(model):
    """Collect the information on the bodies in a ``model``.

    Extract information on a body, path, volume, bounding box.
    Sets paths to the bodies in a ``model`` to unique values.

    Args:
        model: SpaceClaim model to process.

    Returns:
        list with tuples with the information, model modification flag
    """
    bodies = model.MainPart.GetAllBodies()
    size = len(bodies)
    paths_seen = set()
    bodies_table = []
    names_modified = False
    for body in bodies:
        path, modified = _make_unique_path(body, paths_seen)
        names_modified |= modified
        shape = body.Shape
        vol = shape.Volume * 1.0e6  # m^3 -> cm^3
        bounding_box = shape.GetBoundingBox(Matrix.Identity, tight=True)  # noqa: F821
        minx, miny, minz = bounding_box.MinCorner
        maxx, maxy, maxz = bounding_box.MaxCorner
        minx, miny, minz, maxx, maxy, maxz = (
            t * 100.0 for t in (minx, miny, minz, maxx, maxy, maxz)
        )  # m -> cm
        cell = len(bodies_table) + 1
        bodies_table.append((cell, vol, minx, miny, minz, maxx, maxy, maxz, path))
        print("% 5.1f%%" % (100.0 * cell / size) + ": " + path)

    return bodies_table, names_modified


def _make_unique_path(body, paths_seen):
    path = _get_path(body)
    names_modified = False

    while path in paths_seen:
        body_name = body.GetName()
        match = DIGITS_AT_END.match(body_name)
        if match:
            i = int(match["digits"]) + 1
            body_name = body_name[: match.span()[0]] + str(i)
        else:
            body_name = body_name + "1"
        body.SetName(body_name)
        names_modified = True
        path = _get_path(body)

    paths_seen.add(path)

    return path, names_modified


def _get_path(body):
    path = [body.Root.GetName()]
    path.extend(x.GetName() for x in body.GetPathToMaster())
    path.append(body.GetName())
    return "/".join(path)


def _set_suffix(path, suffix):
    return splitext(path)[0] + suffix


def _save_to_csv(document_path, sequence):
    output = _set_suffix(document_path, "-component-volumes.csv")
    with open(output, "w") as f:
        f.write(
            b"offset,name,volume,xmin,ymin,zmin,xmax,ymax,zmax,path\n"
        )  # cannot use print on API V17 Beta
        for i, vol, minx, miny, minz, maxx, maxy, maxz, stp in sequence:
            items = [str(t) for t in (i, vol, minx, miny, minz, maxx, maxy, maxz)] + [
                stp
            ]
            row = ",".join(items) + "\n"
            f.write(row.encode("utf8"))
    print("Cells and information on them are stored in CSV: " + output)


# noinspection SqlDialectInspection
def _save_to_db(document_path, sequence):
    output = _set_suffix(document_path, ".sqlite")
    con = sq.connect(output)
    cur = con.cursor()
    cur.execute(
        """
        drop table if exists versions;
        """,
    )
    cur.execute(
        """
        create table versions (  -- the applications may store their DB schema version here
            application text primary key,
            major int,
            minor int,
            patch int
        )
        """,
    )
    major, minor, patch = version_info
    cur.execute(
        """
        insert into versions
        (application, major, minor, patch)
        values 
        (?, ?, ?, ?)
        """,
        ("extract-spaceclaim-info", major, minor, patch),
    )
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
            material integer,  -- mapstp will update this and the following
            density real,
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
        sequence,
    )
    con.commit()
    cur.close()
    con.close()
    print("Cells and information on them are stored in the database: " + output)


def main():
    """Extract cell volumes and other information.

    Scans all the bodies in a SpaceClaim active model,
    collecting information on cells:
        - stp path,
        - volume,
        - bounding box boundaries.

    Then stores the information in CSV file and SQLite database.
    Saves STP file automatically.
    If the model component names were modified (to make the paths unique),
    then saves the model with warning.
    """
    print("extract-info" + " v" + __version__)
    document = Window.ActiveWindow.Document  # noqa: F821
    document_path = document.Path

    if not document_path:
        print("Document is to be saved to scdoc file before running this script")
        sys.exit(-1)

    print("Processing model ", document_path)

    sequence, modified = scan_bodies(document)

    print("Scan is complete")

    _save_to_csv(document_path, sequence)
    _save_to_db(document_path, sequence)

    if modified:
        print("The SpaceClaim model was modified, saving it.")
        DocumentSave.Execute(document_path)  # noqa: F821

    print("Save to STP manually! Automatic saving doesn't work yet.")
    print("Success!")


main()
