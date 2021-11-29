.. image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg
   :target: https://github.com/MC-kit/map-stp/graphs/commit-activity

.. image:: https://github.com/MC-kit/map-stp/workflows/Tests/badge.svg
   :target: https://github.com/MC-kit/map-stp/actions?workflow=Tests
   :alt: Tests

.. image:: https://codecov.io/gh/MC-kit/map-stp/branch/master/graph/badge.svg?token=wlqoa368k8
  :target: https://codecov.io/gh/MC-kit/map-stp

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
    :target: https://pycqa.github.io/isort/


.. image:: https://img.shields.io/github/license/MC-kit/map-stp
   :target: https://github.com/MC-kit/map-stp

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit


Transfer information from STP to MCNP
-------------------------------------

A user can add additional information on components directly to STP file component names with a special label.
The information may contain material, density correction factor, radiation waste checklist classification.
The package transfers this information to MCNP file (which is generated from this STP with SuperMC):

    * sets materials and densities using information from STP labels and Excel material index file,
    * adds $-comment after each cell denoting its path in STP, with tag "stp:",
    * creates accompanying Excel file listing the MCNP cells and their properties: material, density, correction factor,
      RWCL classification, STP path. This file can be used on MCNP results postprocessing.
