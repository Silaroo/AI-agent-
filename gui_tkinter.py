import customtkinter as ctk
import tkinter as tk # Kept for simpledialog, messagebox
from tkinter import simpledialog, messagebox
import json
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# --- Configuration and Initialization ---

# Set CustomTkinter appearance
ctk.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue") # Themes: "blue", "green", "dark-blue"

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"OpenAI Client Initialization Error: {e}")
    client = None

CHAT_FILE = "chat_history.json"
SIDEBAR_WIDTH = 220

# Load chat history
if os.path.exists(CHAT_FILE):
    try:
        with open(CHAT_FILE, "r") as f:
            chat_history = json.load(f)
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Could not load chat history. Starting a new session.")
        chat_history = []
else:
    chat_history = []

# Track the currently selected chat
current_chat_idx = 0 if chat_history else None

# --- Core Data Functions ---

def save_chats():
    """Saves the current chat history to a JSON file."""
    with open(CHAT_FILE, "w") as f:
        json.dump(chat_history, f, indent=2)

# --- GUI Logic Functions ---

def send_message(event=None):
    """Handles sending a user message, calling the API, and updating the view."""
    global current_chat_idx
    
    message = entry.get().strip()
    if not message:
        return

    # 1. Handle Chat Creation if None Exists
    if current_chat_idx is None:
        title = message[:30] + "..." if len(message) > 30 else message
        chat_history.append({"title": title, "messages": []})
        current_chat_idx = len(chat_history) - 1
        update_sidebar()
        
    chat = chat_history[current_chat_idx]
    timestamp = datetime.now().strftime("%H:%M")

    # 2. Append User Message
    chat["messages"].append({"role": "user", "text": message, "time": timestamp})

    # Update title if it's the first message
    if chat["title"] == "New Chat" and len(chat["messages"]) == 1:
        new_title = message[:30] + "..." if len(message) > 30 else message
        chat["title"] = new_title
        update_sidebar()

    entry.delete(0, tk.END)
    load_chat(current_chat_idx) # Display user message immediately
    root.update_idletasks() # Force UI refresh

    # 3. Call OpenAI API
    bot_reply = "API Unavailable."
    if client:
        try:
            api_messages = [{"role": m["role"], "content": m["text"]} for m in chat["messages"]]

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=api_messages
            )
            bot_reply = response.choices[0].message.content.strip()
        except Exception as e:
            bot_reply = f"Error: {e}"

    # 4. Append Bot Message
    chat["messages"].append({
        "role": "assistant",
        "text": bot_reply,
        "time": datetime.now().strftime("%H:%M")
    })
    
    # 5. Save and Reload
    save_chats() 
    load_chat(current_chat_idx)

def update_sidebar(select_idx=None):
    """Refreshes the sidebar buttons and highlights the current chat."""
    global current_chat_idx
    
    # Clear existing buttons (A common pattern for dynamic CTk sidebars)
    for widget in sidebar_scrollable_frame.winfo_children():
        widget.destroy()

    if not chat_history:
        current_chat_idx = None
        load_chat(None)
        return

    # Determine which index to highlight
    if select_idx is not None:
        current_chat_idx = select_idx
    elif current_chat_idx is None:
        current_chat_idx = 0

    # Create a button for each chat thread
    for i, chat in enumerate(chat_history):
        # Determine color based on selection status
        if i == current_chat_idx:
            # Use the selected color from the segmented button theme
            fg_color = ctk.ThemeManager.theme['CTkSegmentedButton']['selected_color']
            text_color = ctk.ThemeManager.theme['CTkSegmentedButton']['selected_color'][1] # Get light/dark text color
        else:
            # Use the unselected color from the segmented button theme
            fg_color = ctk.ThemeManager.theme['CTkSegmentedButton']['unselected_color']
            text_color = ctk.ThemeManager.theme['CTkButton']['text_color'] # Default CTkButton text color
            
        btn = ctk.CTkButton(
            sidebar_scrollable_frame,
            text=chat["title"],
            fg_color=fg_color,
            text_color=text_color,
            text_color_disabled=("gray70", "gray30"),
            anchor="w",
            # FIXED: Use a simple tuple for hover_color to avoid KeyError
            hover_color=("#dbdbdb", "#4d4d4d"), 
            command=lambda idx=i: load_chat(idx)
        )
        btn.pack(fill="x", pady=2, padx=5)
        
def load_chat(idx):
    """Loads the messages for the specified chat index using CTkFrames for bubbles."""
    global current_chat_idx
    
    if idx is None or idx >= len(chat_history) or idx < 0:
        current_chat_idx = None
        # Clear main chat area
        for widget in chat_scrollable_frame.winfo_children():
            widget.destroy()
        return
        
    current_chat_idx = idx
    chat = chat_history[idx]
    
    # Clear existing messages in the scrollable frame
    for widget in chat_scrollable_frame.winfo_children():
        widget.destroy()

    # Create a message frame (bubble) for each message
    if "messages" in chat:
        for msg in chat["messages"]:
            role = msg["role"]
            text = msg["text"]
            time = msg["time"]
            
            # --- Bubble Styling ---
            if role == "user":
                # User bubble (right-aligned, green)
                bg_color = "#DCF8C6"  # WhatsApp Green
                text_color = "black"
                
                # Create a container frame to push the bubble to the right
                container = ctk.CTkFrame(chat_scrollable_frame, fg_color="transparent")
                container.pack(fill="x", pady=5)
                
                bubble = ctk.CTkFrame(
                    container,
                    fg_color=bg_color,
                    corner_radius=10,
                    border_width=0
                )
                # Pack to the right side of its container frame
                bubble.pack(side="right", padx=(SIDEBAR_WIDTH, 10), pady=2, anchor="e")

            else:
                # Bot bubble (left-aligned, white/light gray)
                bg_color = "#FFFFFF" # Light background
                text_color = "black"
                
                # Simple packing for left alignment in the main scrollable frame
                bubble = ctk.CTkFrame(
                    chat_scrollable_frame,
                    fg_color=bg_color,
                    corner_radius=10,
                    border_width=0
                )
                # Pack to the left side of the main scrollable frame
                bubble.pack(side="top", fill="x", padx=(10, SIDEBAR_WIDTH), pady=5, anchor="w")
                
            # Add text label inside the bubble frame
            text_label = ctk.CTkLabel(
                bubble,
                text=f"{text}",
                font=("Arial", 12),
                text_color=text_color,
                justify="left",
                wraplength=root.winfo_width() - 350 # Wrap text based on window width
            )
            text_label.pack(padx=10, pady=(5, 0), anchor="w")
            
            # Add timestamp label (smaller)
            time_label = ctk.CTkLabel(
                bubble,
                text=time,
                font=("Arial", 8),
                text_color="gray50",
                justify="right"
            )
            time_label.pack(padx=10, pady=(0, 5), anchor="e")

    update_sidebar(idx) # Update sidebar highlight
    chat_scrollable_frame._scrollbar.set(1.0, 1.0) # Scroll to bottom

def new_chat():
    """Creates a new, empty chat."""
    title = simpledialog.askstring("New Chat", "Enter chat title:", parent=root)
    
    title = title if title else "New Chat"
    chat = {"title": title, "messages": []}
        
    chat_history.append(chat)
    save_chats()
    load_chat(len(chat_history) - 1)
    update_sidebar()

def delete_chat():
    """Deletes the currently selected chat from history."""
    global current_chat_idx
    
    if current_chat_idx is None:
        messagebox.showwarning("Delete Error", "No chat selected to delete.", parent=root)
        return

    idx = current_chat_idx

    confirm = messagebox.askyesno("Delete Chat", f"Are you sure you want to delete '{chat_history[idx]['title']}'?", parent=root)
    if confirm:
        chat_history.pop(idx)
        save_chats()
        
        if not chat_history:
            current_chat_idx = None
            load_chat(None)
        else:
            current_chat_idx = max(0, idx - 1)
            load_chat(current_chat_idx)
            
        update_sidebar()

# --- GUI Setup ---

root = ctk.CTk()
root.title("CTk Modern Chat App")
root.geometry("900x600")

# --- 1. Grid Configuration ---
root.grid_columnconfigure(0, weight=0) # Sidebar column
root.grid_columnconfigure(1, weight=1) # Main chat column
root.grid_rowconfigure(0, weight=1)    # Chat area row
root.grid_rowconfigure(1, weight=0)    # Entry bar row


# --- 2. Sidebar Frame ---
sidebar_frame = ctk.CTkFrame(root, width=SIDEBAR_WIDTH, corner_radius=0)
sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
sidebar_frame.grid_columnconfigure(0, weight=1)
sidebar_frame.grid_rowconfigure(0, weight=0) # Buttons row
sidebar_frame.grid_rowconfigure(1, weight=1) # Scrollable area row

# Sidebar Buttons
sidebar_buttons_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
sidebar_buttons_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
sidebar_buttons_frame.grid_columnconfigure((0, 1), weight=1)

btn_new = ctk.CTkButton(sidebar_buttons_frame, text="New Chat", command=new_chat)
btn_new.grid(row=0, column=0, padx=(0, 2), sticky="ew")

btn_delete = ctk.CTkButton(sidebar_buttons_frame, text="Delete", command=delete_chat, fg_color="red", hover_color="#880000")
btn_delete.grid(row=0, column=1, padx=(2, 0), sticky="ew")

# Sidebar Chat List (Scrollable Frame acting as a list)
sidebar_scrollable_frame = ctk.CTkScrollableFrame(sidebar_frame, label_text="Conversations", corner_radius=0)
sidebar_scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 0))
sidebar_scrollable_frame.grid_columnconfigure(0, weight=1)


# --- 3. Main Chat Area ---

# Chat Display Frame (Scrollable)
chat_scrollable_frame = ctk.CTkScrollableFrame(root, fg_color="#e5ddd5", corner_radius=0) # WhatsApp Background
chat_scrollable_frame.grid(row=0, column=1, sticky="nsew")
chat_scrollable_frame.grid_columnconfigure(0, weight=1)


# --- 4. Entry Frame (Bottom) ---
entry_frame = ctk.CTkFrame(root, fg_color="#f0f0f0", corner_radius=0)
entry_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=10)
entry_frame.grid_columnconfigure(0, weight=1)

entry = ctk.CTkEntry(entry_frame, placeholder_text="Type a message...", font=("Arial", 12))
entry.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)
entry.bind("<Return>", send_message)

send_btn = ctk.CTkButton(entry_frame, text="Send", command=send_message, fg_color="#0088cc", hover_color="#0070a8")
send_btn.grid(row=0, column=1, padx=(5, 0), pady=5)

# --- Initialization ---
update_sidebar()
load_chat(current_chat_idx)

root.mainloop()

# Save upon exit
save_chats()