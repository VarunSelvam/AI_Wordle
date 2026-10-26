# Scrap Code

import tkinter as tk
import turtle
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import SystemMessagePromptTemplate,HumanMessagePromptTemplate,MessagesPlaceholder,ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import os
from pathlib import Path
import tkinter as tk
import os
from pathlib import Path
import re

# Make sure these are imported from your LangChain setup
# Helper function for loading prompts
def load_prompt(path: Path, escape_json_braces: bool = True) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff").rstrip()
    if not escape_json_braces:
        return text

    def _escape_block(m: re.Match) -> str:
        inner = m.group(1)
        inner = re.sub(r'(?<!{){(?!{)', '{{', inner)
        inner = re.sub(r'(?<!})}(?!})', '}}', inner)
        return f"```json\n{inner}\n```"

    return re.sub(
        r"```json\s*\r?\n(.*?)\r?\n```",
        _escape_block,
        text,
        flags=re.S | re.I
    )

# Main DropDown class
class DropDown:
    def __init__(self, root, folder_path):
        self.folder_path = folder_path
        self.opt = tk.StringVar(value="ChatGPT")
        model_list = ["ChatGPT", "Claude", "Gemini"]
        self.model = None
        self.wordle_history_pipeline = None

        # Label
        self.label = tk.Label(root, text="Choose AI Model:", font=("Arial", 18))
        self.label.place(x=860, y=300)

        # OptionMenu
        self.menu = tk.OptionMenu(root, self.opt, *model_list)
        self.menu.config(font=("Arial", 16))          # Font for visible button
        self.menu["menu"].config(font=("Arial", 14))  # Font for dropdown items
        self.menu.place(x=890, y=340)

        # Confirm Button
        self.button = tk.Button(
            root,
            text="Click to Confirm Choice",
            font=("Arial", 18),
            command=self.initialize_ai_model
        )
        self.button.place(x=820, y=385)

    def initialize_ai_model(self):
        selection = self.opt.get().lower()
        ai_model = None

        if selection == "gemini":
            ai_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        elif selection == "chatgpt":
            ai_model = ChatOpenAI(model="gpt-4o-mini")
        elif selection == "claude":
            ai_model = ChatAnthropic(model="claude-3-haiku-20240307")

        if ai_model is None:
            print(f"Warning: Model '{selection}' not recognized.")

        self.model = ai_model

        # Destroy widgets after selection
        self.label.destroy()
        self.menu.destroy()
        self.button.destroy()

        # Setup Wordle pipeline
        self.setup_wordle_pipeline()

    def setup_wordle_pipeline(self):
        wordle_instructions_path = os.path.join(self.folder_path, "instructions.md")
        wordle_instructions = load_prompt(Path(wordle_instructions_path))

        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(wordle_instructions),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{query}"),
        ])

        pipeline = prompt_template | self.model

        chat_map = {}
        def get_chat_history(session_id: str) -> InMemoryChatMessageHistory:
            if session_id not in chat_map:
                chat_map[session_id] = InMemoryChatMessageHistory()
            return chat_map[session_id]

        # Store pipeline for external access
        self.wordle_history_pipeline = RunnableWithMessageHistory(
            pipeline,
            get_session_history=get_chat_history,
            input_messages_key="query",
            history_messages_key="history"
        )

        print("Wordle pipeline is ready and stored in self.wordle_history_pipeline")































# class DropDown:
#     def __init__(self, root):
#         # store opt as an instance variable
#         self.opt = tk.StringVar(value="ChatGPT")
#         model_list = ["ChatGPT", "Claude", "Gemini"]
#         self.model = None  # store result here
        
#         # Button Label
#         self.label = tk.Label(root, text = "Choose AI Model:",font=("Arial", 18))
#         self.label.place(x=860, y=300)  # <-- add placement
        
#         # Option Menu
#         self.menu = tk.OptionMenu(root, self.opt, *model_list)
#         # Change font of the visible button
#         self.menu.config(font=("Arial", 16))
#         # Change font of the dropdown items
#         self.menu["menu"].config(font=("Arial", 14))
#         self.menu.place(x=890, y=340)

#         # Confirm Button
#         self.button = tk.Button(root, text="Click to Confirm Choice",font=("Arial", 18), command=self.initialize_ai_model)
#         self.button.place(x=820, y=385)
    
#     def initialize_ai_model(self):
#         # get the current selection from the dropdown
#         selection = self.opt.get().lower()  # <-- get() returns the string

#         ai_model = None  # default to None

#         if selection == "gemini":
#             ai_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
#         elif selection == "chatgpt":
#             ai_model = ChatOpenAI(model="gpt-4o-mini")
#         elif selection == "claude":
#             ai_model = ChatAnthropic(model="claude-3-haiku-20240307")

#         if ai_model is None:
#             print(f"Warning: Model '{selection}' not recognized.")
        
#         self.model = ai_model  # store for later reference

#         # Destroy widgets after selection
#         self.label.destroy()
#         self.menu.destroy()
#         self.button.destroy()

#         # Set up the Wordle pipeline
#         self.setup_wordle_pipeline()
    
#     def setup_wordle_pipeline(self):
#         wordle_instructions_path = os.path.join(folder_path, "instructions.md")
#         wordle_instructions = load_prompt(Path(wordle_instructions_path))

#         prompt_template = ChatPromptTemplate.from_messages([
#             SystemMessagePromptTemplate.from_template(wordle_instructions),
#             MessagesPlaceholder(variable_name="history"),
#             HumanMessagePromptTemplate.from_template("{query}"),
#         ])

#         pipeline = prompt_template | self.model

#         chat_map = {}
#         def get_chat_history(session_id: str) -> InMemoryChatMessageHistory:
#             if session_id not in chat_map:
#                 chat_map[session_id] = InMemoryChatMessageHistory()
#             return chat_map[session_id]

#         # Store the pipeline as an instance variable
#         self.wordle_history_pipeline = RunnableWithMessageHistory(
#             pipeline,
#             get_session_history=get_chat_history,
#             input_messages_key="query",
#             history_messages_key="history"
#         )

#         print("Wordle pipeline is ready and stored in self.wordle_history_pipeline")

# Any functions, events, etc. that need to take place right after a button click should be placed in a function.
# This function should then be given as reference to the command parameter in tk.button(). This reference is then used when it's time to execute the function.
# This also means that when we are running a drop down menu outside of a class, we should define the function first.