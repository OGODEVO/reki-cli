
import os
import argparse
import requests
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# --- Constants ---
BASE_URL = "https://api.polygon.io/fed/v1/inflation"

# --- Main Functions ---

def fetch_inflation_data(api_key, params):
    """
    Fetches inflation data from the Polygon.io API.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Clean up params: remove None values and format for URL
    request_params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = requests.get(BASE_URL, headers=headers, params=request_params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
    except requests.exceptions.RequestException as req_err:
        print(f"A request error occurred: {req_err}")
    except Exception as err:
        print(f"An unexpected error occurred: {err}")
    return None

def display_data(data, console):
    """
    Displays the inflation data in a formatted table.
    """
    if not data or not data.get("results"):
        console.print("[bold red]No data found for the given parameters.[/bold red]")
        return

    table = Table(
        title="U.S. Inflation Indicators",
        header_style="bold magenta",
        show_header=True,
        box=None
    )
    table.add_column("Date", style="dim", width=12)
    table.add_column("CPI", justify="right")
    table.add_column("Core CPI", justify="right")
    table.add_column("CPI YoY (%)", justify="right")
    table.add_column("PCE", justify="right")
    table.add_column("Core PCE", justify="right")
    table.add_column("PCE Spending (B)", justify="right")

    for item in data["results"]:
        table.add_row(
            item.get("date", "N/A"),
            f"{item.get('cpi', 0):.2f}",
            f"{item.get('cpi_core', 0):.2f}",
            f"{item.get('cpi_year_over_year', 0):.2f}%",
            f"{item.get('pce', 0):.2f}",
            f"{item.get('pce_core', 0):.2f}",
            f"{item.get('pce_spending', 0):.1f}B"
        )

    console.print(table)
    
    # Display request ID and next_url if available
    if "request_id" in data:
        console.print(f"[dim]Request ID: {data['request_id']}[/dim]")
    if "next_url" in data:
        console.print(f"[dim]Next URL: {data['next_url']}[/dim]")


def main():
    """
    Main function to parse arguments and run the tool.
    """
    load_dotenv()
    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        print("Error: POLYGON_API_KEY environment variable not set.")
        return

    parser = argparse.ArgumentParser(description="Fetch U.S. inflation data from Polygon.io.")
    
    # Add arguments based on the API documentation
    parser.add_argument("--date", help="Calendar date of the observation (YYYY-MM-DD).")
    parser.add_argument("--date-any-of", dest="date.any_of", help="Filter for dates equal to any in a comma-separated list.")
    parser.add_argument("--date-gt", dest="date.gt", help="Filter for dates greater than the value.")
    parser.add_argument("--date-gte", dest="date.gte", help="Filter for dates greater than or equal to the value.")
    parser.add_argument("--date-lt", dest="date.lt", help="Filter for dates less than the value.")
    parser.add_argument("--date-lte", dest="date.lte", help="Filter for dates less than or equal to the value.")
    parser.add_argument("--limit", type=int, help="Limit the maximum number of results. Max 50000.")
    parser.add_argument("--sort", help="A comma-separated list of sort columns (e.g., 'date.desc').")

    args = parser.parse_args()
    
    # Convert argparse namespace to a dictionary for the request
    params = vars(args)

    console = Console()
    with console.status("[bold green]Fetching data...[/bold green]"):
        data = fetch_inflation_data(api_key, params)
    
    if data:
        display_data(data, console)

if __name__ == "__main__":
    main()
