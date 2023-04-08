from __future__ import annotations
import getopt

from cowrie.shell.command import HoneyPotCommand
from cowrie.shell.honeypot import StdOutStdErrEmulationProtocol

#Support of the 'command' command, essentially reimplementing which + sudo

commands = {}

COMMAND_HELP = """command: command [-pVv] command [arg ...]
    Execute a simple command or display information about commands.
    
    Runs COMMAND with ARGS suppressing  shell function lookup, or display
    information about the specified COMMANDs.  Can be used to invoke commands
    on disk when a function with the same name exists.
    
    Options:
      -p    use a default value for PATH that is guaranteed to find all of
            the standard utilities
      -v    print a description of COMMAND similar to the `type' builtin
      -V    print a more verbose description of each COMMAND
    
    Exit Status:
    Returns exit status of COMMAND, or failure if COMMAND is not found.
"""

class Command_command(HoneyPotCommand):
    def call(self) -> None:
        """
        Look up all the arguments on PATH and print each (first) result
        """

        # No arguments, just exit
        if not len(self.args) or "PATH" not in self.environ:
            return

        try:
            opts, args = getopt.gnu_getopt(self.args, "pVv:", ["help"])
        except getopt.GetoptError as err:
            self.errorWrite(
                f"command: -'{err.opt}': invalid option\n"
                 "command: usage: command [-pVv] command [arg ...]"
            )
            return
        for vars in opts:
            if vars[0] == '--help':
                self.write(COMMAND_HELP)
                return
            if vars[0] == '-p':
                cmd = args[0]
                cmdclass = self.protocol.getCommand(cmd, self.environ["PATH"].split(":"))
                if cmdclass:
                    command = StdOutStdErrEmulationProtocol(
                        self.protocol, cmdclass, args[1:], None, None
                    )
                    self.protocol.pp.insert_command(command)
                    # this needs to go here so it doesn't write it out....
                    if self.input_data:
                        self.writeBytes(self.input_data)
                    self.exit()
            #'Faking' verbose output for now
            if vars[0] == '-v' or vars[0] == '-V':
                # Look up each file
                for f in self.args:
                    for path in self.environ["PATH"].split(":"):
                        resolved = self.fs.resolve_path(f, path)

                        if self.fs.exists(resolved):
                            self.write(f"{path}/{f}\n")


commands["command"] = Command_command