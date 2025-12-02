"""Configuration module for the DocuSmart application.

This module handles the loading of environment variables, initialization of global
variables, and setup of external services like Supabase. It also provides utility
functions for checking prerequisites, such as internet connectivity.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Supabase project URL and anon key loaded from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Global variables to hold the Supabase client, current user session, and API keys
supabase = None
current_user = None
gemini_api_key = None


def init_supabase():
    """Initializes the global Supabase client.

    Uses the SUPABASE_URL and SUPABASE_KEY environment variables to create a Supabase client instance.
    If the client is created successfully, a confirmation message is printed.
    If the variables are not set or an error occurs, an appropriate message is printed.
    """
    global supabase
    try:
        from supabase import create_client, Client
        if SUPABASE_URL and SUPABASE_KEY:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Supabase has connected.")
        else:
            print("Supabase URL or Key not configured.")
    except Exception as e:
        print(f"Erro ao inicializar Supabase: {e}")


def check_internet_connection(url='http://www.google.com/', timeout=5):
    """Checks for an active internet connection.

    Sends a HEAD request to a reliable URL to determine if an internet connection is available.

    Args:
        url (str, optional): The URL to check against. Defaults to 'http://www.google.com/'.
        timeout (int, optional): The timeout for the request in seconds. Defaults to 5.

    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    try:
        requests.head(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False
    except requests.Timeout:
        return False


# Check for internet connection on startup
checkInternet = check_internet_connection()
print(f"Internet connected: {checkInternet}")

# Initialize the Supabase client on startup
init_supabase() 