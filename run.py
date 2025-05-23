from app import create_app
import os
print("GOOGLE_SERVICE_KEY exists?", os.environ.get("GOOGLE_SERVICE_KEY") is not None)

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
