from ollama import Client, chat
import sys
import time

def run_ollama_model():
    """
    Asks for Ollama model, downloads (with progress), and runs a chat session.
    Handles errors gracefully and provides clear output.
    """

    client = Client()

    while True:
        print("-" * 30)  # Separator line
        model_name = input("Enter the Ollama model name you want to use (e.g., 'mistralai/Mistral-7B-Instruct-v0.1', or 'codellama:7b-code'): ")
        if not model_name:
            print("Please enter a model name.")
            continue

        try:
            # --- Model Pulling (Download) ---
            try:
                response = client.pull(model=model_name, stream=True)
                downloading = False

                for chunk in response:
                    status = chunk.get('status')
                    if status == 'pulling manifest':
                        downloading = True
                        print(f"Downloading model '{model_name}'...", end="", flush=True)
                    elif 'progress' in chunk:
                        downloading = True
                        print(f"\r{chunk['status']}: {chunk['progress']}", end="", flush=True)
                    elif status == 'download complete':
                        print(f"\nDownload complete for layer: {chunk.get('id', '')}", flush=True)
                    elif status == 'pull complete':
                        downloading = True
                        print("\nPull complete.", flush=True)

                if not downloading:
                    print(f"Model '{model_name}' is already available locally.")

            except Exception as e:
                # Simplified error message, as requested
                print("\nCould not find or download the specified model.")
                print("Check the model name and your internet connection.")
                continue  # Go back to model selection

            # --- Chat Session ---
            if downloading:
                while True:
                    user_message = input("\nEnter your message (or type 'exit' to quit): ")
                    if user_message.lower() == 'exit':
                        break

                    try:
                        stream = chat(
                            model=model_name,
                            messages=[{'role': 'user', 'content': user_message}],
                            stream=True,
                        )
                        for chunk in stream:
                            print(chunk['message']['content'], end='', flush=True)
                        print()

                    except Exception as chat_error:
                        print(f"\nError during chat session: {chat_error}")
                        print("Check your Ollama server status.")
                        break

        except Exception as general_error:
            print(f"An unexpected error occurred: {general_error}")

        finally:
            pass

if __name__ == "__main__":
    run_ollama_model()