Thoth's reverse solver
----------------------

.. image:: https://img.shields.io/github/v/tag/thoth-station/revsolver?style=plastic
  :target: https://github.com/thoth-station/revsolver/tags
  :alt: GitHub tag (latest by date)

.. image:: https://quay.io/repository/thoth-station/revsolver/status
  :target: https://quay.io/repository/thoth-station/revsolver?tab=tags
  :alt: Quay - Build

A reverse solver implementation for project Thoth.

Thoth's `solver <https://github.com/thoth-station/solver>`_ can resolve requirements
of Python packages that are subsequently synced into Thoth's knowledge base. Note this
solver operates only one way - from a package to its dependencies. This causes
out-of-date issues when a new release of a dependency is released which would satisfy
version specification of an already solved package. The reverse solver deals with this issue.

The reverse solver checks what packages depend on the given package (dependents) and
re-computes dependency information so that the dependency graph stored in Thoth's knowledge
base is up to date - considering releases.

This is tightly bound to over-pinning and under-pinning issues often seen in Python packages.

See `this intro video for more info <https://www.youtube.com/watch?v=bpDzi_Jaj4M>`__.

Running the reverse solver locally
==================================

This is suitable only for development purposes.

The implementation talks to OpenShift to retrieve solvers installed in a
deployment. You need to be logged into OpenShift cluster and have at least view
permissions to a Thoth deployment (thoth-test-core in this example):

.. code-block::

  THOTH_INFRA_NAMESPACE=thoth-test-core KUBERNETES_VERIFY_TLS=0 PYTHONPATH=. pipenv run python3 ./app.py --package-name tensorflow --package-version 2.0.0

The output of the above command is a JSON document stating what packages depend
on TensorFlow in version 2.0.0. Note the Python ecosystem does not provide any
way how to depend on a particular build available on different package indexes.

Running the reverse solver in the cluster
=========================================

The reverse solver is run in the cluster as part of solver workflow when a new
package release is detected.
