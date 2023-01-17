.. mapstp documentation master file, created by
   sphinx-quickstart on Sat Nov 20 21:18:28 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

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

Usage: mapstp [OPTIONS] <stp-file> [mcnp-file]

  Transfers meta information from STP to MCNP

  For given STP file creates Excel table with a list of STP paths to STP
  components, corresponding to cells in MCNP model, would it be generated from
  the STP with SuperMC.

  If MCNP file is also specified as the second `mcnp-file` argument, then
  produces output MCNP file with STP paths inserted as end of line comments
  after corresponding cells with prefix "sep:". The material numbers and
  densities are set according to the meta information provided in the STP.

Options: ::

     --override / --no-override      Override existing files, (default: no)
     -o, --output <output>           File to write the MCNP with marked cells
                                     (default: stdout)
     -e, --excel <excel-file>        Excel file to write the component paths
     --materials <materials-file>    Text file containing MCNP materials
                                     specifications. If present, the selected
                                     materials present in this file are printed to
                                     the `output` MCNP model, so, it becomes
                                     complete valid model
     -m, --materials-index <materials-index-file>
                                     Excel file containing materials mnemonics
                                     and corresponding materials
                                     and densities for the MCNP model
                                     (default: file from the package internal
                                     data corresponding to ITER C-model)
     --separator <separator>         String to separate components in the STP
                                     path
     --start-cell-number <number>    Number to start cell numbering in the Excel
                                     file (default: the first cell number in
                                     `mcnp` file, if specified, otherwise 1)
     --version                       Show the version and exit.
     --help                          Show this message and exit.





.. todo ::

   * Improve and fix the command line API help.
   * Automate updating of the text above on CLI changes.


Installation
============

From PyPI:

.. code-block ::

   pip install mapstp

With package manager:

.. code-block ::

   poetry add mapstp

From github:

.. code-block ::

   pip install https://github.com/MC-kit/map-stp.git

Details
=======

.. toctree::
   :maxdepth: 1

   license
   modules
   todo
   readme



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
