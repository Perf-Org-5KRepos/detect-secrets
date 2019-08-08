from __future__ import absolute_import

import argparse
from collections import namedtuple

from detect_secrets import VERSION
from detect_secrets.plugins.common.util import import_plugins


def add_exclude_lines_argument(parser):
    parser.add_argument(
        '--exclude-lines',
        type=str,
        help='Pass in regex to specify lines to ignore during scan.',
    )


def add_word_list_argument(parser):
    parser.add_argument(
        '--word-list',
        type=str,
        help=(
            'Text file with a list of words, '
            'if a secret contains a word in the list we ignore it.'
        ),
        dest='word_list_file',
    )


def add_use_all_plugins_argument(parser):
    parser.add_argument(
        '--use-all-plugins',
        action='store_true',
        help='Use all available plugins to scan files.',
    )


def add_verify_flag(parser):
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Enables additional verification of secrets via network call.',
    )


class ParserBuilder(object):

    def __init__(self):
        self.parser = argparse.ArgumentParser()

        self.add_default_arguments()

    def add_default_arguments(self):
        self._add_verbosity_argument()\
            ._add_version_argument()

    def add_pre_commit_arguments(self):
        self._add_filenames_argument()\
            ._add_set_baseline_argument()\
            ._add_exclude_lines_argument()\
            ._add_word_list_argument()\
            ._add_use_all_plugins_argument()\
            ._add_verify_flag()

        PluginOptions(self.parser).add_arguments()

        return self

    def add_console_use_arguments(self):
        subparser = self.parser.add_subparsers(
            dest='action',
        )

        for action_parser in (ScanOptions, AuditOptions):
            action_parser(subparser).add_arguments()

        return self

    def parse_args(self, argv):
        output = self.parser.parse_args(argv)
        PluginOptions.consolidate_args(output)

        return output

    def _add_version_argument(self):
        self.parser.add_argument(
            '--version',
            action='version',
            version=VERSION,
            help='Display version information.',
        )
        return self

    def _add_verbosity_argument(self):
        self.parser.add_argument(
            '-v',
            '--verbose',
            action='count',
            help='Verbose mode.',
        )
        return self

    def _add_filenames_argument(self):
        self.parser.add_argument(
            'filenames',
            nargs='*',
            help='Filenames to check.',
        )
        return self

    def _add_set_baseline_argument(self):
        self.parser.add_argument(
            '--baseline',
            nargs=1,
            default=[''],
            help='Sets a baseline for explicitly ignored secrets, generated by `--scan`.',
        )
        return self

    def _add_exclude_lines_argument(self):
        add_exclude_lines_argument(self.parser)
        return self

    def _add_word_list_argument(self):
        add_word_list_argument(self.parser)
        return self

    def _add_use_all_plugins_argument(self):
        add_use_all_plugins_argument(self.parser)
        return self

    def _add_verify_flag(self):
        add_verify_flag(self.parser)
        return self


class ScanOptions(object):

    def __init__(self, subparser):
        self.parser = subparser.add_parser(
            'scan',
        )

    def add_arguments(self):
        self._add_initialize_baseline_argument()\
            ._add_adhoc_scanning_argument()\
            ._add_output_raw_argument()

        PluginOptions(self.parser).add_arguments()

        return self

    def _add_initialize_baseline_argument(self):
        self.parser.add_argument(
            'path',
            nargs='*',
            default='.',
            help=(
                'Scans the entire codebase and outputs a snapshot of '
                'currently identified secrets.'
            ),
        )

        # Pairing `--exclude-lines` and `--word-list` to
        # both pre-commit and `--scan` because it can be used for both.
        add_exclude_lines_argument(self.parser)
        add_word_list_argument(self.parser)

        # Pairing `--exclude-files` with `--scan` because it's only used for the initialization.
        # The pre-commit hook framework already has an `exclude` option that can
        # be used instead.
        self.parser.add_argument(
            '--exclude-files',
            type=str,
            help='Pass in regex to specify ignored paths during initialization scan.',
        )

        # Pairing `--update` with `--scan` because it's only used for
        # initialization.
        self.parser.add_argument(
            '--update',
            nargs=1,
            metavar='OLD_BASELINE_FILE',
            help='Update existing baseline by importing settings from it.',
            dest='import_filename',
        )

        # Pairing `--update` with `--use-all-plugins` to overwrite plugins list
        # from baseline
        add_use_all_plugins_argument(self.parser)

        self.parser.add_argument(
            '--all-files',
            action='store_true',
            help='Scan all files recursively (as compared to only scanning git tracked files).',
        )

        add_verify_flag(self.parser)

        return self

    def _add_adhoc_scanning_argument(self):
        self.parser.add_argument(
            '--string',
            nargs='?',
            const=True,
            help=(
                'Scans an individual string, and displays configured '
                'plugins\' verdict.'
            ),
        )
        return self

    def _add_output_raw_argument(self):
        self.parser.add_argument(
            '--output-raw',
            action='store_true',
            help=(
                'Outputs the raw secret in the baseline file.'
                'For development/extension purposes.'
                'Do not use this option in a repo monitoring context.'
            ),
        )
        return self


class AuditOptions(object):

    def __init__(self, subparser):
        self.parser = subparser.add_parser(
            'audit',
        )

    def add_arguments(self):
        self.parser.add_argument(
            'filename',
            nargs='+',
            help=(
                'Audit a given baseline file to distinguish the difference '
                'between false and true positives.'
            ),
        )

        action_parser = self.parser.add_mutually_exclusive_group()

        action_parser.add_argument(
            '--diff',
            action='store_true',
            help=(
                'Allows the comparison of two baseline files, in order to '
                'effectively distinguish the difference between various '
                'plugin configurations.'
            ),
        )

        action_parser.add_argument(
            '--display-results',
            action='store_true',
            help=(
                'Displays the results of an interactive auditing session '
                'which have been saved to a baseline file.'
            ),
        )

        return self


<<<<<<< HEAD
class PluginDescriptor(
    namedtuple(
        'PluginDescriptor',
        [
            # Classname of plugin; used for initialization
            'classname',

            # Flag to disable plugin. e.g. `--no-hex-string-scan`
            'disable_flag_text',

            # Description for disable flag.
            'disable_help_text',

            # type: list
            # Allows the bundling of all related command line provided
            # arguments together, under one plugin name.
            # Assumes there is no shared related arg.
            #
            # Furthermore, each related arg can have its own default
            # value (paired together, with a tuple). This allows us to
            # distinguish the difference between a default value, and
            # whether a user has entered the same value as a default value.
            # Therefore, only populate the default value upon consolidation
            # (rather than relying on argparse default).
            'related_args',
        ],
    ),
):
=======
class PluginDescriptor(namedtuple(
    'PluginDescriptor',
    [
        # Classname of plugin; used for initialization
        'classname',

        # Flag to disable plugin. e.g. `--no-hex-string-scan`
        'disable_flag_text',

        # Description for disable flag.
        'disable_help_text',

        # type: list
        # Allows the bundling of all related command line provided
        # arguments together, under one plugin name.
        # Assumes there is no shared related arg.
        #
        # Furthermore, each related arg can have its own default
        # value (paired together, with a tuple). This allows us to
        # distinguish the difference between a default value, and
        # whether a user has entered the same value as a default value.
        # Therefore, only populate the default value upon consolidation
        # (rather than relying on argparse default).
        'related_args',

        # If this plugin is enabled by default
        'is_default',
    ],
)):

>>>>>>> Define default plugin list
    def __new__(cls, related_args=None, **kwargs):
        if not related_args:
            related_args = []

        return super(PluginDescriptor, cls).__new__(
            cls,
            related_args=related_args,
            **kwargs
        )

    @classmethod
    def from_plugin_class(cls, plugin, name):
        """
        :type plugin: Type[TypeVar('Plugin', bound=BasePlugin)]
        :type name: str
        """
        related_args = None
        if plugin.default_options:
            related_args = []
            for arg_name, value in plugin.default_options.items():
                related_args.append((
                    '--{}'.format(arg_name.replace('_', '-')),
                    value,
                ))

        return cls(
            classname=name,
            disable_flag_text='--{}'.format(plugin.disable_flag_text),
            disable_help_text=cls.get_disabled_help_text(plugin),
            related_args=related_args,
        )

    @staticmethod
    def get_disabled_help_text(plugin):
        for line in plugin.__doc__.splitlines():
            line = line.strip().lstrip()
            if line:
                break
        else:
            raise NotImplementedError('Plugins must declare a docstring.')

        line = line[0].lower() + line[1:]
        return 'Disables {}'.format(line)


class PluginOptions(object):

    all_plugins = [
<<<<<<< HEAD
        PluginDescriptor.from_plugin_class(plugin, name)
        for name, plugin in import_plugins().items()
=======
        PluginDescriptor(
            classname='HexHighEntropyString',
            disable_flag_text='--no-hex-string-scan',
            disable_help_text='Disables scanning for hex high entropy strings.'
            + ' (Disabled by default)',
            related_args=[
                ('--hex-limit', 3,),
            ],
            is_default=False,
        ),
        PluginDescriptor(
            classname='Base64HighEntropyString',
            disable_flag_text='--no-base64-string-scan',
            disable_help_text='Disables scanning for base64 high entropy strings.'
            + ' (Disabled by default)',
            related_args=[
                ('--base64-limit', 4.5,),
            ],
            is_default=False,
        ),
        PluginDescriptor(
            classname='PrivateKeyDetector',
            disable_flag_text='--no-private-key-scan',
            disable_help_text='Disables scanning for private keys.',
            is_default=True,
        ),
        PluginDescriptor(
            classname='BasicAuthDetector',
            disable_flag_text='--no-basic-auth-scan',
            disable_help_text='Disables scanning for Basic Auth formatted URIs.',
            is_default=True,
        ),
        PluginDescriptor(
            classname='KeywordDetector',
            disable_flag_text='--no-keyword-scan',
            disable_help_text='Disables scanning for secret keywords. (Disabled by default)',
            is_default=False,
        ),
        PluginDescriptor(
            classname='AWSKeyDetector',
            disable_flag_text='--no-aws-key-scan',
            disable_help_text='Disables scanning for AWS keys.',
            is_default=True,
        ),
        PluginDescriptor(
            classname='SlackDetector',
            disable_flag_text='--no-slack-scan',
            disable_help_text='Disables scanning for Slack tokens.',
            is_default=True,
        ),
        PluginDescriptor(
            classname='ArtifactoryDetector',
            disable_flag_text='--no-artifactory-scan',
            disable_help_text='Disable scanning for Artifactory credentials',
            is_default=True,
        ),
        PluginDescriptor(
            classname='StripeDetector',
            disable_flag_text='--no-stripe-scan',
            disable_help_text='Disable scanning for Stripe keys',
            is_default=True,
        ),
        PluginDescriptor(
            classname='GHDetector',
            disable_flag_text='--no-gh-scan',
            disable_help_text='Disable scanning for GH credentials',
            is_default=False,
        ),
    ]

    default_plugins_list = [
        plugin.classname for plugin in all_plugins if plugin.is_default
>>>>>>> Define default plugin list
    ]

    def __init__(self, parser):
        default_plugins_name_list = ', '.join(self.default_plugins_list)
        self.parser = parser.add_argument_group(
            title='plugins',
            description=(
                'Configure settings for each secret scanning '
                'ruleset. By default, only selected plugins are enabled. '
                'Some high false positive ratio plugins such as keyword '
                'and entropy based scans are disabled. You can explicitly '
                'enable them to use more scans. '
                'The default plugins are %s.' % default_plugins_name_list
            ),
        )

    def add_arguments(self):
        self._add_custom_limits()
        self._add_opt_out_options()
        self._add_keyword_exclude()

        return self

    @staticmethod
    def get_disabled_plugins(args):
        return [
            plugin.classname
            for plugin in PluginOptions.all_plugins
            if plugin.classname not in args.plugins
        ]

    @staticmethod
    def consolidate_args(args):
        """There are many argument fields related to configuring plugins.
        This function consolidates all of them, and saves the consolidated
        information in args.plugins.

        Note that we're deferring initialization of those plugins, because
        plugins may have various initialization values, referenced in
        different places.

        :param args: output of `argparse.ArgumentParser.parse_args`
        """
        # Using `--hex-limit` as a canary to identify whether this
        # consolidation is appropriate.
        if not hasattr(args, 'hex_limit'):
            return

        active_plugins = {}
        is_using_default_value = {}

        for plugin in PluginOptions.all_plugins:
            arg_name = PluginOptions._convert_flag_text_to_argument_name(
                plugin.disable_flag_text,
            )

            # Remove disabled plugins
            is_disabled = getattr(args, arg_name, False)
            delattr(args, arg_name)
            if is_disabled:
                continue

            # Consolidate related args
            related_args = {}
            for related_arg_tuple in plugin.related_args:
                flag_name, default_value = related_arg_tuple

                arg_name = PluginOptions._convert_flag_text_to_argument_name(
                    flag_name,
                )

                related_args[arg_name] = getattr(args, arg_name)
                delattr(args, arg_name)

                if default_value and related_args[arg_name] is None:
                    related_args[arg_name] = default_value
                    is_using_default_value[arg_name] = True

            active_plugins.update({
                plugin.classname: related_args,
            })

        args.plugins = active_plugins
        args.is_using_default_value = is_using_default_value

    def _add_custom_limits(self):
        high_entropy_help_text = (
            'Sets the entropy limit for high entropy strings. '
            'Value must be between 0.0 and 8.0, '
        )

        self.parser.add_argument(
            '--base64-limit',
            type=self._argparse_minmax_type,
            nargs='?',
            help=high_entropy_help_text + 'defaults to 4.5.',
        )
        self.parser.add_argument(
            '--hex-limit',
            type=self._argparse_minmax_type,
            nargs='?',
            help=high_entropy_help_text + 'defaults to 3.0.',
        )

    def _add_opt_out_options(self):
        for plugin in self.all_plugins:
            self.parser.add_argument(
                plugin.disable_flag_text,
                action='store_true',
                help=plugin.disable_help_text,
                default=False,
            )

    def _argparse_minmax_type(self, string):
        """Custom type for argparse to enforce value limits"""
        value = float(string)
        if value < 0 or value > 8:
            raise argparse.ArgumentTypeError(
                '%s must be between 0.0 and 8.0' % string,
            )

        return value

    @staticmethod
    def _convert_flag_text_to_argument_name(flag_text):
        """This just emulates argparse's underlying logic.

        :type flag_text: str
        :param flag_text: e.g. `--no-hex-string-scan`
        :return: `no_hex_string_scan`
        """
        return flag_text[2:].replace('-', '_')

    def _add_keyword_exclude(self):
        self.parser.add_argument(
            '--keyword-exclude',
            type=str,
            help='Pass in regex to exclude false positives found by keyword detector.',
        )
