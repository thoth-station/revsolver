#!/usr/bin/env python3
# Copyright(C) 2020 Fridolin Pokorny
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""A reverse solver implementation for project Thoth."""

from typing import Any
from typing import Dict
from typing import List
import logging
import os
import sys
import time

import click

from thoth.analyzer import print_command_result
from thoth.common import init_logging
from thoth.common import OpenShift
from thoth.common import __version__ as __common__version__
from thoth.python import PackageVersion
from thoth.storages import GraphDatabase
from thoth.storages import __version__ as __storages__version__


__title__ = "thoth-revsolver"
__version__ = "0.2.0"
__component_version__ = f"{__version__}+storage.{__storages__version__}.common.{__common__version__}"

init_logging()


_LOGGER = logging.getLogger("thoth.revsolver")
_QUERY_COUNT = int(os.getenv("THOTH_REVSOLVER_QUERY_COUNT", GraphDatabase.DEFAULT_COUNT))


def do_solve(package_name: str, package_version: str) -> List[Dict[str, Any]]:
    """Obtain dependent packages for the given package, respect registered solvers in Thoth."""
    graph = GraphDatabase()
    graph.connect()

    openshift = OpenShift()

    result = []
    for solver_name in openshift.get_solver_names():
        _LOGGER.info("Obtaining dependencies for environment used by solver %r", solver_name)

        solver_info = openshift.parse_python_solver_name(solver_name)

        start_offset = 0
        while True:
            dependents = graph.get_python_package_version_dependents_all(
                package_name=package_name,
                os_name=solver_info["os_name"],
                os_version=solver_info["os_version"],
                python_version=solver_info["python_version"],
                start_offset=start_offset,
                count=_QUERY_COUNT,
            )

            for dependent in dependents:
                if (
                    dependent["version_range"]
                    and dependent["version_range"] != "*"
                    and package_version not in PackageVersion.parse_semantic_version(dependent["version_range"])
                ):
                    _LOGGER.info(
                        "Package %r in version %r from %r ignored, not matching version specifier %r in environment %r",
                        dependent["package_name"],
                        dependent["package_version"],
                        dependent["index_url"],
                        package_version,
                        solver_name,
                    )
                    continue

                _LOGGER.info(
                    "Found dependent %r in version %r from %r in environment %r",
                    dependent["package_name"],
                    dependent["package_version"],
                    dependent["index_url"],
                    solver_name,
                )
                result.append(
                    {
                        "os_name": solver_info["os_name"],
                        "os_version": solver_info["os_version"],
                        "python_version": solver_info["python_version"],
                        "solver_name": solver_name,
                        **dependent,
                    }
                )

            if len(dependents) < _QUERY_COUNT:
                break

            # Adjust for the next round.
            start_offset += _QUERY_COUNT

    return result


def _print_version(ctx, _, value):
    """Print version and exit."""
    if not value or ctx.resilient_parsing:
        return

    click.echo(__component_version__)
    ctx.exit()


@click.command()
@click.pass_context
@click.option(
    "-v", "--verbose", is_flag=True, envvar="THOTH_REVSOLVER_VERBOSE", help="Be verbose about what's going on.",
)
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    callback=_print_version,
    expose_value=False,
    help="Print version and exit.",
)
@click.option(
    "--package-name",
    "-p",
    type=str,
    required=True,
    envvar="THOTH_REVSOLVER_PACKAGE_NAME",
    metavar="PKG",
    help="Package name for which the reverse solver should be run.",
)
@click.option(
    "--package-version",
    "-r",
    type=str,
    metavar="VER",
    required=True,
    envvar="THOTH_REVSOLVER_PACKAGE_VERSION",
    help="Package version for which the reverse solver should be run (version identifier).",
)
@click.option(
    "--output",
    "-o",
    type=str,
    metavar="OUTPUT",
    envvar="THOTH_REVSOLVER_OUTPUT",
    default="-",
    show_default=True,
    help="Output file or remote API to print results to, in case of URL a POST request is issued.",
)
@click.option("--no-pretty", "-P", is_flag=True, help="Do not print results nicely.")
def cli(
    click_ctx: click.Context,
    output: str,
    package_name: str,
    package_version: str,
    no_pretty: bool = False,
    verbose: bool = False,
) -> None:
    """Obtain dependent packages for the given package, respect registered solvers in Thoth.

    The result of reverse solver is a list of dependencies that depend on the given package.
    """
    if click_ctx:
        click_ctx.auto_envvar_prefix = "THOTH_REVSOLVER"

    if verbose:
        _LOGGER.setLevel(logging.DEBUG)

    _LOGGER.debug("Debug mode is on")
    _LOGGER.debug("Version: %s", __component_version__)

    start_time = time.monotonic()

    result = do_solve(package_name=package_name, package_version=package_version)

    print_command_result(
        click_ctx,
        result,
        analyzer=__title__,
        analyzer_version=__component_version__,
        output=output,
        duration=time.monotonic() - start_time,
        pretty=not no_pretty,
    )


__name__ == "__main__" and sys.exit(cli())
