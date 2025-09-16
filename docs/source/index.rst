====================================================
**mapstp**: a tool to associate  MCNP and STP models
====================================================

.. note::

   This documentation is currently under active development.

The tool allows associate STP model components and cells of the MCNP model generated from the STP
model with Super MC or GEOUNED.
The association implies properties: material, density correction factor and radwaste classification tag.
A user can use 3D editor to assign properties in 3D model. The properties propagate through the
tree hierarchy from top to bottom and can be refined on lower levels, if needed.
So, one can define that almost everything in the model is steel, inserting `[m-steel]` label on the top of hierarchy
and set more proper value, like `[m-water]` or whatever, on some components or even `[m-void]` to define
bodies as empty spaces.

.. todo::

  Improve description, give examples and add links.


Usage
=====

Command line interface
----------------------

.. click:: mapstp.cli.runner:mapstp
   :prog: mapstp
   :nested: full

.. todo::

  Describe CLI in details.

Installation
============

**From PyPI (recommended):**

.. code-block:: bash

   pip install mapstp
   # or
   uv pip install mapstp

**With package manager (as dependency):**

.. code-block:: bash

   # uv
   uv add mapstp

   # pixi
   pixi add --pypi mapstp

   # poetry
   poetry add mapstp

   # ...

**From source:**

.. code-block:: bash

   uv pip install https://github.com/MC-kit/map-stp.git
   # or
   pip install https://github.com/MC-kit/map-stp.git


Roadmap & Future Development
============================

   
Planned Features:
-----------------

- ☐ Harmonize with GEOUNED
- ☐ Harmonize with Radmodelling


API Reference
=============

.. For detailed API documentation, please refer to the :doc:`api` section.

Examples
========

.. Basic usage examples and tutorials will be available in the :doc:`examples` section.

Contributing
============

We welcome contributions! Please see our GitHub repository for contribution guidelines.

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
