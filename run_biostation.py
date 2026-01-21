"""
BioStation AI - Main Application Entry Point

A local AI chatbot for bioscience students to help with statistical analysis in R.
Provides test selection, code generation, debugging, and educational content.
"""

from app import create_app
import sys
import os9

# Create Flask application
app = create_app(config_name=os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    print("=" * 60)
    print(" BioStation AI - Statistical Analysis Assistant")
    print("=" * 60)
    print(f" Version: {app.config['APP_VERSION']}")
    print(f" Model: {app.config['LLM_MODEL']}")
    print(f" Running on: http://{app.config['HOST']}:{app.config['PORT']}")
    print("=" * 60)
    print("\n[*] Pre-warming LLM model...")

    
    # === MODEL PRE-WARMING ===
    # Send a dummy query to load the model into memory
    # This makes the first real user query much faster
    try:
        import threading
        from app.llm import OllamaClient
        
        def prewarm_model():
            try:
                client = OllamaClient(
                    model=app.config['LLM_MODEL'],
                    base_url=app.config['OLLAMA_BASE_URL']
                )
                # Dummy prompt to warm up the model
                client.generate(
                    prompt="Hello",
                    system_prompt="You are a helpful assistant.",
                    temperature=0.1,
                    max_tokens=10
                )
                print("[OK] Model pre-warmed and ready!\n")
            except Exception as e:
                print(f"[!] Pre-warming failed (non-critical): {e}\n")
        
        # Run in background thread so server starts immediately
        warmup_thread = threading.Thread(target=prewarm_model, daemon=True)
        warmup_thread.start()
        
    except Exception as e:
        print(f"[!] Could not pre-warm model: {e}\n")
    
    print("Press Ctrl+C to stop the server\n")
    
    try:
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG']
        )
    except KeyboardInterrupt:
        print("\n\nShutting down BioStation AI...")
        sys.exit(0)

