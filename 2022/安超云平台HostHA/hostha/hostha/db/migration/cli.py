# Copyright (c) 2021 Archeros Inc.
# hostha is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the
# Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import os

from alembic import command as alembic_cmd
from alembic import config as alembic_cfg
from alembic import util as alembic_u

from oslo_config import cfg
from oslo_db import options


# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2013 Mirantis Inc.

CONF = cfg.CONF
options.set_defaults(CONF)


def do_alembic_command(config, cmd, *args, **kwargs):
    try:
        getattr(alembic_cmd, cmd)(config, *args, **kwargs)
    except alembic_u.CommandError as e:
        alembic_u.err(str(e))


def do_check_migration(config, _cmd):
    do_alembic_command(config, 'branches')


def do_upgrade_downgrade(config, cmd):
    if not CONF.command.revision and not CONF.command.delta:
        raise SystemExit('You must provide a revision or relative delta')

    revision = CONF.command.revision

    if CONF.command.delta:
        sign = '+' if CONF.command.name == 'upgrade' else '-'
        revision = sign + str(CONF.command.delta)

    do_alembic_command(config, cmd, revision, sql=CONF.command.sql)


def do_stamp(config, cmd):
    do_alembic_command(config, cmd,
                       CONF.command.revision,
                       sql=CONF.command.sql)


def do_revision(config, cmd):
    do_alembic_command(config, cmd,
                       message=CONF.command.message,
                       autogenerate=CONF.command.autogenerate,
                       sql=CONF.command.sql)


def add_command_parsers(subparsers):
    for name in ['current', 'history', 'branches']:
        parser = subparsers.add_parser(name)
        parser.set_defaults(func=do_alembic_command)

    parser = subparsers.add_parser('check_migration')
    parser.set_defaults(func=do_check_migration)

    for name in ['upgrade']:
        parser = subparsers.add_parser(name)
        parser.add_argument('--delta', type=int)
        parser.add_argument('--sql', action='store_true')
        parser.add_argument('revision', nargs='?')
        parser.set_defaults(func=do_upgrade_downgrade)

    parser = subparsers.add_parser('stamp')
    parser.add_argument('--sql', action='store_true')
    parser.add_argument('revision')
    parser.set_defaults(func=do_stamp)

    parser = subparsers.add_parser('revision')
    parser.add_argument('-m', '--message')
    parser.add_argument('--autogenerate', action='store_true')
    parser.add_argument('--sql', action='store_true')
    parser.set_defaults(func=do_revision)


command_opt = cfg.SubCommandOpt('command',
                                title='Command',
                                help='Available commands',
                                handler=add_command_parsers)

CONF.register_cli_opt(command_opt)


def main():
    config = alembic_cfg.Config(
        os.path.join(os.path.dirname(__file__), 'alembic.ini')
    )
    config.set_main_option('script_location',
                           'hostha.db.migration:alembic_migrations')
    # attach the OpenStack CloudUltra conf to the Alembic conf
    config.cloudultra_config = CONF

    CONF(project='hostha')
    CONF.command.func(config, CONF.command.name)
