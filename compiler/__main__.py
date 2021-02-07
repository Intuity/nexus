import click

from .parser import Parser

@click.command()
@click.argument("input")
def main(input):
    """ Compiles Yosys JSON export into a Nexus instruction schedule

    Arguments:

        input: Path to the Yosys JSON export
    """
    # Run the parse step on the Yosys JSON input
    parser = Parser(input)
    parser.parse()
    print(parser.modules[0])

if __name__ == "__main__":
    main()
