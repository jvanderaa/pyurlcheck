"""Example cli using click."""
import click

from pyurlcheck.check import CheckUrl
from pyurlcheck.find import FindUrls
from pyurlcheck.validate import ValidateUrl


@click.command()
@click.argument(
    "input_data",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    required=True
    )
def main(input_data):
    """Entry point into the pyurlcheck command line tool.

    Args:
        input_data (str) - Either filename or directory to search for URLs.
    """
    files_urls = FindUrls(input_data).find_urls()
    for file_name, url_list in files_urls.items():
        for line_num, urls in url_list.items():
            for url in urls:
                is_private = CheckUrl(url).is_private()
                # print(f"URL is {url}")
                # print(f"Is RFC1918: {is_private}")
                is_valid = ValidateUrl(url).validate()
                # print(f"Is Valid: {is_valid}")
                if not is_valid:
                    print(f"{file_name}:{line_num}\tURL Issue: {url}")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
