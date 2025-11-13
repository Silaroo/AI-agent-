import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import json
import os
from datetime import datetime
from openai import OpenAI  # NEW: Import OpenAI client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# The client automatically reads OPENAI_API_KEY from the environment
client = OpenAI()  # NEW: Initialize the client

CHAT_FILE = "chat_history.json"

# Load chat history
if os.path.exists(CHAT_FILE):
    try:
        with open(CHAT_FILE, "r") as f:
            chat_history = json.load(f)
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Could not load chat history. Starting fresh.")
        chat_history = []
else:
    chat_history = []

# Track the currently selected chat
current_chat_idx = 0 if chat_history else None

def save_chats():
    """Saves the current chat history to a JSON file."""
    with open(CHAT_FILE, "w") as f:
        json.dump(chat_history, f, indent=2)

# --- Core Functions ---

def send_message(event=None):
    """Handles sending a user message, calling the API, and displaying the response."""
    global current_chat_idx
    
    message = entry.get().strip()
    if not message:
        return

    if current_chat_idx is None:
        # If no chat exists, create a new one, using the first message as a title placeholder
        title = message[:30] + "..." if len(message) > 30 else message
        chat_history.append({"title": title, "messages": []})
        current_chat_idx = len(chat_history) - 1
        update_sidebar()
        load_chat(current_chat_idx)

    chat = chat_history[current_chat_idx]

    timestamp = datetime.now().strftime("%H:%M")
    chat["messages"].append({"role": "user", "text": message, "time": timestamp})
    
    # Update the chat title with the first message if it was a default "New Chat" title
    if chat["title"] == "New Chat" and len(chat["messages"]) == 1:
        new_title = message[:30] + "..." if len(message) > 30 else message
        chat_history[current_chat_idx]["title"] = new_title
        update_sidebar()

    entry.delete(0, tk.END)
    load_chat(current_chat_idx) # Display user message immediately
    chat_area.yview(tk.END)
    root.update_idletasks() # Force UI refresh

    # Prepare messages for API (role/content only)
    api_messages = [{"role": m["role"], "content": m["text"]} for m in chat["messages"]]

    # OpenAI API call
    try:
        response = client.chat.completions.create(  # NEW API CALL
            model="gpt-3.5-turbo",
            messages=api_messages
        )
        bot_reply = response.choices[0].message.content.strip()  # NEW RESPONSE ACCESS
    except Exception as e:
        bot_reply = f"Error: Failed to connect to OpenAI. Check your API key and network. ({e})"
        print(bot_reply)

    chat["messages"].append({
        "role": "assistant", # Correct role for bot reply
        "text": bot_reply,
        "time": datetime.now().strftime("%H:%M")
    })
    save_chats()
    load_chat(current_chat_idx) # Reload to display bot response
    chat_area.yview(tk.END)


def update_sidebar():
    """Refreshes the list of chats in the sidebar."""
    sidebar.delete(0, tk.END)
    for i, chat in enumerate(chat_history):
        sidebar.insert(tk.END, chat["title"])
    
    if current_chat_idx is not None and chat_history:
        sidebar.selection_set(current_chat_idx)
        sidebar.activate(current_chat_idx)

def load_chat(idx):
    """Loads the messages for the specified chat index into the main area."""
    global current_chat_idx
    current_chat_idx = idx
    
    chat_area.config(state=tk.NORMAL)
    chat_area.delete(1.0, tk.END)

    if idx is not None and idx < len(chat_history):
        chat = chat_history[idx]
        if "messages" in chat:
            for msg in chat["messages"]:
                tag = "user" if msg["role"] == "user" else "bot"
                insert_message(msg["text"], msg["time"], tag)
        
        # Update sidebar selection
        sidebar.selection_clear(0, tk.END)
        sidebar.selection_set(idx)
        sidebar.activate(idx)
    
    chat_area.config(state=tk.DISABLED)
    chat_area.yview(tk.END)

def insert_message(text, timestamp, tag):
    """Inserts a formatted message bubble into the chat area."""
    chat_area.insert(tk.END, "\n")
    
    # Format: Message (Time)
    bubble_text = f"{text}\n({timestamp})"
    chat_area.insert(tk.END, bubble_text, tag)
    
    chat_area.insert(tk.END, "\n\n")

def on_sidebar_select(event):
    """Event handler for selecting a chat in the sidebar."""
    selection = sidebar.curselection()
    if selection:
        idx = selection[0]
        if idx != current_chat_idx:
            load_chat(idx)

def new_chat():
    """Prompts for a title and creates a new, empty chat."""
    global current_chat_idx
    title = simpledialog.askstring("New Chat", "Enter chat title:")
    if not title:
        title = "New Chat" # Default title if user cancels or leaves empty
        
    chat = {"title": title, "messages": []}
    chat_history.append(chat)
    current_chat_idx = len(chat_history) - 1
    save_chats()
    update_sidebar()
    load_chat(current_chat_idx)

def delete_chat():
    """Deletes the currently selected chat from history."""
    global current_chat_idx
    selection = sidebar.curselection()
    
    if not selection and current_chat_idx is not None:
        selection = (current_chat_idx,) # Use the active chat if nothing is explicitly selected
    elif not selection:
        messagebox.showwarning("Delete Error", "No chat selected to delete.")
        return

    idx = selection[0]
    if idx >= len(chat_history): return 

    confirm = messagebox.askyesno("Delete Chat", f"Are you sure you want to delete '{chat_history[idx]['title']}'?")
    if confirm:
        chat_history.pop(idx)
        save_chats()
        
        if not chat_history:
            current_chat_idx = None
            load_chat(None) # Clear the chat area
        else:
            # Select the previous chat or the first one
            current_chat_idx = max(0, idx - 1)
            load_chat(current_chat_idx)
            
        update_sidebar()

# --- GUI ---

root = tk.Tk()
root.title("Modern Chat App")
root.geometry("900x600")

# Sidebar
sidebar_frame = tk.Frame(root, width=220, bg="#f0f0f0", relief=tk.RIDGE, bd=1)
sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
sidebar_frame.pack_propagate(False)

sidebar_buttons = tk.Frame(sidebar_frame, bg="#f0f0f0")
sidebar_buttons.pack(fill=tk.X, pady=5, padx=5)

btn_new = tk.Button(sidebar_buttons, text="New Chat", command=new_chat, relief=tk.FLAT, bg="#e0e0e0")
btn_new.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

btn_delete = tk.Button(sidebar_buttons, text="Delete", command=delete_chat, relief=tk.FLAT, bg="#e0e0e0")
btn_delete.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

sidebar = tk.Listbox(sidebar_frame, width=30, bg="#f9f9f9", bd=0, highlightthickness=0, selectbackground="#d0d0d0", selectforeground="black", activestyle="none", font=("Arial", 11))
sidebar.pack(fill=tk.BOTH, expand=True, pady=(5,0))
sidebar.bind("<<ListboxSelect>>", on_sidebar_select)

# Main chat area
chat_frame = tk.Frame(root, bg="#e5ddd5") # WhatsApp-style background
chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

chat_area = scrolledtext.ScrolledText(chat_frame, bg="#e5ddd5", state=tk.DISABLED, bd=0, padx=10, pady=10, font=("Arial", 11), wrap=tk.WORD)
chat_area.pack(fill=tk.BOTH, expand=True)

# Bubble style tags (mimicking the image)
chat_area.tag_config("user", 
                     background="#DCF8C6", 
                     foreground="#000000", 
                     lmargin1=10, lmargin2=10, 
                     rmargin=100, # Large right margin
                     spacing3=5, 
                     justify="left",
                     relief="flat", bd=0, lmarginr=10) # Minimal border/relief

chat_area.tag_config("bot", 
                     background="#FFFFFF", 
                     foreground="#000000", 
                     lmargin1=100, # Large left margin
                     lmargin2=10, 
                     rmargin=10, 
                     spacing3=5, 
                     justify="left",
                     relief="flat", bd=0, lmarginr=10)


# Entry and send button
entry_frame = tk.Frame(chat_frame, bg="#f0f0f0", height=50) 
entry_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
entry_frame.pack_propagate(False)

entry = tk.Entry(entry_frame, font=("Arial", 11), bd=1, relief=tk.FLAT)
entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
entry.bind("<Return>", send_message)

send_btn = tk.Button(entry_frame, text="Send", command=send_message, bg="#0088cc", fg="white", font=("Arial", 10, "bold"), relief=tk.FLAT)
send_btn.pack(side=tk.RIGHT, padx=5, pady=5)

# Initialize
update_sidebar()
load_chat(current_chat_idx)

root.mainloop()