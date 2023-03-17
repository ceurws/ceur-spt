"""
Created on 2023-03-17

@author: wf
"""
from argparse import ArgumentParser, Namespace
from argparse import RawDescriptionHelpFormatter
from ceurspt.version import Version
from ceurspt.webserver import WebServer
import socket
import sys
import traceback
import webbrowser
import uvicorn
from pathlib import Path


class CeurSptCmd:
    """
    command line interface for CEUR Single Point of Truth
    """

    def get_arg_parser(self, description: str, version_msg) -> ArgumentParser:
        """
        Setup command line argument parser
        
        Args:
            description(str): the description
            version_msg(str): the version message
            
        Returns:
            ArgumentParser: the argument parser
        """
        script_path=Path(__file__)
        base_path=f"{script_path.parent.parent}/ceur-ws"
        parser = ArgumentParser(description=description, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-a", "--about", help="show about info [default: %(default)s]", action="store_true")
        parser.add_argument("-b","--basepath",help="the base path to the ceur-ws volumes [default: %(default)s]",default=base_path)
        parser.add_argument("-d", "--debug", dest="debug", action="store_true",
                            help="show debug info [default: %(default)s]")
        parser.add_argument("--host", default=self.get_default_host(),
                            help="the host to serve / listen from [default: %(default)s]")
        parser.add_argument("--port", type=int, default=9990, help="the port to serve from [default: %(default)s]")
        parser.add_argument("-s", "--serve", action="store_true", help="start webserver [default: %(default)s]")
        parser.add_argument("-V", "--version", action='version', version=version_msg)
        return parser

    def get_default_host(self) -> str:
        """
        get the default host as the fully qualifying hostname
        of the computer the server runs on
        
        Returns:
            str: the hostname
        """
        host = socket.getfqdn()
        # work around https://github.com/python/cpython/issues/79345
        if host == "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa":
            host = "localhost"  # host="127.0.0.1"
        return host

    def start(self, args: Namespace):
        """
        Args:
            args(Arguments): command line arguments
        """
        ws = WebServer(base_path=args.basepath)
        uvicorn.run(ws.app, host=args.host, port=args.port)


def main(argv=None):  # IGNORE:C0111
    """main program."""

    if argv is None:
        argv = sys.argv[1:]

    program_name = "ceurspt"
    program_version = f"v{Version.version}"
    program_build_date = str(Version.date)
    program_version_message = f'{program_name} ({program_version},{program_build_date})'

    args = None
    try:
        spt_cmd = CeurSptCmd()
        parser = spt_cmd.get_arg_parser(description=Version.license, version_msg=program_version_message)
        args = parser.parse_args(argv)
        if len(argv) < 1:
            parser.print_usage()
            sys.exit(1)
        if args.about:
            print(program_version_message)
            print(f"see {Version.doc_url}")
            webbrowser.open(Version.doc_url)
        elif args.serve:
            spt_cmd.start(args)

    except KeyboardInterrupt:
        ###
        # handle keyboard interrupt
        # ###
        return 1
    except Exception as e:
        if DEBUG:
            raise e
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        if args is None:
            print("args could not be parsed")
        elif args.debug:
            print(traceback.format_exc())
        return 2


DEBUG = 1
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())
