import gradio as gr
from ollama import Client, chat
import threading
import queue
import os

class OllamaChatGradio:
    def __init__(self):
        ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
        self.client = Client(host=f'http://{ollama_host}:11434')
        self.downloading = False
        self.chat_active = False
        self.update_queue = queue.Queue()
        self.chat_history = []
        self.model_name = ""
        self.download_progress = ""

    def download_model(self, model_name, progress=gr.Progress()):
        self.model_name = model_name
        self.downloading = True
        self.download_progress = ""

        try:
            response = self.client.pull(model=model_name, stream=True)
            for chunk in response:
                status = chunk.get('status')
                if status == 'pulling manifest':
                    self.download_progress = f"Downloading model '{model_name}'..."
                    progress(0, desc=self.download_progress)
                elif 'progress' in chunk:
                    self.download_progress = f"{chunk['status']}: {chunk['progress']}"
                    progress(chunk['progress'], desc=self.download_progress)
                elif status == 'download complete':
                    self.download_progress = f"Download complete for layer: {chunk.get('id', '')}"
                    progress(1, desc=self.download_progress)
                elif status == 'pull complete':
                    self.download_progress = "Pull complete."
                    progress(1, desc=self.download_progress)
                    self.downloading = False
                    return self.download_progress
            return self.download_progress

        except Exception as e:
            self.download_progress = "Could not find or download the specified model."
            self.downloading = False
            return self.download_progress

    def chat_function(self, user_message, chat_history, progress=gr.Progress()):
        if self.downloading:
            yield chat_history, "Model downloading. Please wait."
            return

        if not self.model_name:
            yield chat_history, "Please download a model first."
            return

        self.chat_active = True
        chat_history.append([user_message, ""])
        yield chat_history, ""

        try:
            stream = chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': user_message}],
                stream=True,
            )
            response = ""
            for chunk in stream:
                response += chunk['message']['content']
                chat_history[-1][1] = response
                yield chat_history, ""

            self.chat_active = False
            return chat_history, ""

        except Exception as chat_error:
            self.chat_active = False
            yield chat_history, f"Error during chat: {chat_error}"
            return chat_history, ""

    def create_ui(self):
        with gr.Blocks() as demo:
            gr.Markdown("# Ollama Model Chat")
            model_name_input = gr.Textbox(label="Model Name", placeholder="Enter model name")
            download_button = gr.Button("Download Model")
            download_output = gr.Textbox(label="Download Status", interactive=False)
            chatbot = gr.Chatbot()
            msg = gr.Textbox()
            clear = gr.ClearButton([msg, chatbot])

            download_button.click(
                fn=self.download_model,
                inputs=[model_name_input],
                outputs=[download_output],
            )
            msg.submit(
                fn=self.chat_function,
                inputs=[msg, chatbot],
                outputs=[chatbot, msg],
            )
        return demo

if __name__ == "__main__":
    app = OllamaChatGradio()
    demo = app.create_ui()
    demo.launch(server_name="0.0.0.0")