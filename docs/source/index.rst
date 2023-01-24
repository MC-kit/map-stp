====================================================
**mapstp**: a tool to associate  MCNP and STP models
====================================================

.. todo::

    The documentation is under development.

The tool allows associate STP model components and cells of the MCNP model generated from the STP
model with Super MC.
The association implies properties: material, density correction factor and classification tag.
A user can use 3D editor to assign properties in 3D model.

Usage
=====

Command line interface
----------------------

.. click:: mapstp.cli.runner:mapstp
   :prog: mapstp
   :nested: full

Installation
============

From PyPI (recommended):

.. code-block::

   pip install mapstp

With package manager (as dependency):

.. code-block::

   poetry add mapstp

From source:

.. code-block::

   pip install https://github.com/MC-kit/map-stp.git

Details
=======

.. toctree::
   :maxdepth: 2

   readme
   modules
   license
   todo



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
