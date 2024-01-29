from waitress import serve

from application_routes import get_app


app = get_app()
print("starting waitress...")
serve(app, listen="*:8000")
