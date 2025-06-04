import os
import requests


SUPABASE_URL = "https://fezhvhzorzdwzbrexwgu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZlemh2aHpvcnpkd3picmV4d2d1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg2Mzg4MTEsImV4cCI6MjA2NDIxNDgxMX0.sGyjrLa2Ey-s46muPFEvVzUnGF1fHnFFOBoi6YhZ1Lg"


supabase = None
current_user = None
gemini_api_key = None


def init_supabase():
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
    try:
        requests.head(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False
    except requests.Timeout:
        return False


checkInternet = check_internet_connection()
print(f"Internet connected: {checkInternet}")


init_supabase() 