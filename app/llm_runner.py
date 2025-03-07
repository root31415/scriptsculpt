from ollama import Client, chat
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time

class OllamaChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Model Chat")
        self.client = Client()
        self.downloading = False
        self.chat_active = False
        self.update_queue = queue.Queue()
        self.chat_buffer = ""

        # Configure styles
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 10))
        self.style.configure("TButton", font=("Helvetica", 10), padding=5)
        self.style.configure("TEntry", font=("Helvetica", 10), padding=5)
        self.style.configure("TText", font=("Helvetica", 10))

        # Main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Model Entry
        self.model_label = ttk.Label(self.main_frame, text="Enter the Ollama model name:")
        self.model_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.model_entry = ttk.Entry(self.main_frame, width=50)
        self.model_entry.grid(row=1, column=0, sticky=tk.W, pady=(0, 10))

        # Download Button
        self.download_button = ttk.Button(self.main_frame, text="Download Model", command=self.start_download)
        self.download_button.grid(row=2, column=0, sticky=tk.W, pady=(0, 10))

        # Status Label
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=3, column=0, sticky=tk.W, pady=(0, 10))

        # Chat Output Frame
        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.grid(row=4, column=0, sticky=tk.NSEW, pady=(0, 10))

        # Chat Output Text Widget
        self.chat_output = tk.Text(self.chat_frame, width=60, height=20, wrap=tk.WORD, state=tk.DISABLED, font=("Helvetica", 10))
        self.chat_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for Chat Output
        self.scrollbar = ttk.Scrollbar(self.chat_frame, command=self.chat_output.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_output.config(yscrollcommand=self.scrollbar.set)

        # User Input
        self.user_input = tk.Text(self.main_frame, width=60, height=3, font=("Helvetica", 10))
        self.user_input.grid(row=5, column=0, sticky=tk.W, pady=(0, 10))

        # Chat Button
        self.chat_button = ttk.Button(self.main_frame, text="Send", command=self.start_chat, state=tk.DISABLED)
        self.chat_button.grid(row=6, column=0, sticky=tk.W, pady=(0, 10))

        # Configure grid weights
        self.main_frame.grid_rowconfigure(4, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Start the UI update loop
        self.root.after(100, self.process_updates)

    def start_download(self):
        model_name = self.model_entry.get()
        if not model_name:
            messagebox.showerror("Error", "Please enter a model name.")
            return

        self.downloading = True
        self.download_button.config(state=tk.DISABLED)
        self.status_label.config(text=f"Downloading model '{model_name}'...")

        # Run the download in a separate thread
        threading.Thread(target=self.download_model, args=(model_name,), daemon=True).start()

    def download_model(self, model_name):
        try:
            response = self.client.pull(model=model_name, stream=True)
            for chunk in response:
                status = chunk.get('status')
                if status == 'pulling manifest':
                    self.update_status(f"Downloading model '{model_name}'...")
                elif 'progress' in chunk:
                    self.update_status(f"{chunk['status']}: {chunk['progress']}")
                elif status == 'download complete':
                    self.update_status(f"Download complete for layer: {chunk.get('id', '')}")
                elif status == 'pull complete':
                    self.update_status("Pull complete.")
                    self.downloading = False
                    self.update_queue.put(lambda: self.enable_chat())

        except Exception as e:
            self.update_status("Could not find or download the specified model.")
            self.update_queue.put(lambda: messagebox.showerror("Error", "Check the model name and your internet connection."))
            self.downloading = False
            self.update_queue.put(lambda: self.enable_download_button())

    def start_chat(self):
        if self.chat_active:
            return

        self.chat_active = True
        self.chat_button.config(state=tk.DISABLED)
        self.user_input.config(state=tk.DISABLED)

        user_message = self.user_input.get("1.0", tk.END).strip()
        if user_message.lower() == 'exit':
            self.root.quit()
            return

        self.update_chat_output(f"You: {user_message}\n")

        # Run the chat in a separate thread
        threading.Thread(target=self.run_chat, args=(user_message,), daemon=True).start()

    def run_chat(self, user_message):
        model_name = self.model_entry.get()
        try:
            stream = chat(
                model=model_name,
                messages=[{'role': 'user', 'content': user_message}],
                stream=True,
            )
            response = ""
            for chunk in stream:
                response += chunk['message']['content']
                self.update_chat_output(chunk['message']['content'])

            self.update_chat_output("\n")
            self.chat_active = False
            self.update_queue.put(lambda: self.enable_chat_ui())

        except Exception as chat_error:
            self.update_status(f"Error during chat session: {chat_error}")
            self.update_queue.put(lambda: messagebox.showerror("Error", "Check your Ollama server status."))
            self.chat_active = False
            self.update_queue.put(lambda: self.enable_chat_ui())

    def update_status(self, message):
        self.update_queue.put(lambda: self.status_label.config(text=message))

    def update_chat_output(self, message):
        self.chat_buffer += message
        if len(self.chat_buffer) >= 100:  # Update UI in chunks of 100 characters
            self.update_queue.put(lambda: self.append_to_chat_output(self.chat_buffer))
            self.chat_buffer = ""

    def append_to_chat_output(self, message):
        self.chat_output.config(state=tk.NORMAL)
        self.chat_output.insert(tk.END, message)
        self.chat_output.config(state=tk.DISABLED)
        self.chat_output.see(tk.END)

    def enable_chat(self):
        self.chat_button.config(state=tk.NORMAL)
        self.download_button.config(state=tk.DISABLED)

    def enable_download_button(self):
        self.download_button.config(state=tk.NORMAL)

    def enable_chat_ui(self):
        self.chat_button.config(state=tk.NORMAL)
        self.user_input.config(state=tk.NORMAL)
        self.user_input.delete("1.0", tk.END)

    def process_updates(self):
        try:
            while True:
                task = self.update_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        self.root.after(100, self.process_updates)

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaChatApp(root)
    root.mainloop()