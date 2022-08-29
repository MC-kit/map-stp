==========================================================
*mapstp*: link STP and MCNP models
==========================================================

|Maintained| |License| |Versions| |PyPI| |Docs|


.. contents::


Description
-----------

Problem #1
~~~~~~~~~~

You are an MCNP model developer. You have created simplified 3D CAD model using SpaceClaim, saved it to STP file, then converted
it using SuperMC to an MCNP model. At this moment the MCNP model doesn't have any information on relation of the MCNP
came from cells to the CAD components, there's no materials and densities in the cell specifications.
The SuperMC (for the time of writing this) doesn't transfer this information on exporting to MCNP model.

Problem #2
~~~~~~~~~~

You have to provide results of neutron analysis in correspondence with 3D CAD model
components. For example, you have to create a table describing activation of every component.
To do this, you need some tools to associate CAD component with corresponding MCNP cells.
Using this table the results of computation for MCNP cells can be aggregated to values for
corresponding CAD component.


Solution
~~~~~~~~

Using SpaceClaim you can add additional properties to components directly in STP file.
The properties include: used material, density correction factor, classification tag.
The properties are specified as a special label, which you can add to the components names.
The properties are propagated over the CAD tree hierarchy from top to down and can be overridden
on lower levels with more specific values. Using SpaceClaim for this is rather intuitive.

The using *mapstp* you can transfer this information from STP to MCNP:
The  *mapstp*:

* sets material numbers and densities in all the cells, where it was specified
* adds $-comment after each cell denoting its path in STP, with tag "stp:",this lines can be easily removed later, if not needed
* adds materials specifications, if they are available for *mapstp*
* creates separate accompanying excel file with list of cells, applied materials, densities and correction factors, classification tag, and paths in STP


Installation
------------

Documentation
-------------

Contributing
------------

.. image:: https://github.com/MC-kit/map-stp/workflows/Tests/badge.svg
   :target: https://github.com/MC-kit/map-stp/actions
   :alt: Tests
.. image:: https://codecov.io/gh/MC-kit/map-stp/branch/master/graph/badge.svg?token=wlqoa368k8
  :target: https://codecov.io/gh/MC-kit/map-stp
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
.. image:: https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
   :target: https://pycqa.github.io/isort/
.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. image:: https://img.shields.io/badge/try%2Fexcept%20style-tryceratops%20%F0%9F%A6%96%E2%9C%A8-black
   :target: https://github.com/guilatrova/tryceratops
   :alt: try/except style: tryceratops

.. .. image:: https://img.shields.io/badge/security-bandit-yellow.svg
    :target: https://github.com/PyCQA/bandit
    :alt: Security Status

.. Substitutions

.. |Maintained| image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg
   :target: https://github.com/MC-kit/map-stp/graphs/commit-activity
.. |Tests| image:: https://github.com/MC-kit/map-stp/workflows/Tests/badge.svg
   :target: https://github.com/MC-kit/map-stp/actions?workflow=Tests
   :alt: Tests
.. |License| image:: https://img.shields.io/github/license/MC-kit/map-stp
   :target: https://github.com/MC-kit/map-stp
.. |Versions| image:: https://img.shields.io/pypi/pyversions/mapstp
   :alt: PyPI - Python Version
.. |PyPI| image:: https://img.shields.io/pypi/v/mapstp
   :target: https://pypi.org/project/mapstp/
   :alt: PyPI
.. |Docs| image:: https://readthedocs.org/projects/mapstp/badge/?version=latest
   :target: https://mapstp.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
