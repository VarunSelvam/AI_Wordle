#-----------------------------------------------------------------------------------------------
# Import libraries
import random as r
import turtle
import os
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import official_wordle_function as owf # Custom function that I created in another script
from pathlib import Path
import re
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.prompts import SystemMessagePromptTemplate,HumanMessagePromptTemplate,MessagesPlaceholder,ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import json
#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------
# File Setup 

# Set Folder Path, where file will be stored.
folder_path = r"C:\Users\varun\Box Sync\Python\Python_Projects\Wordle_AI"

# List all the files in the folder
files = os.listdir(folder_path)

if 'frequent_guesses.txt' not in files: # If the file is already created, then python will skip over this statement
    with open(os.path.join(folder_path,"frequent_guesses.txt"),"w"):
        pass # We just want to create an empty file, so pass will be put here.
if 'wordle_stats.txt' not in files:
    with open(os.path.join(folder_path,"wordle_stats.txt"),"w"):
        pass

# Read in word file which contains all the 5 letter words:
with open(os.path.join(folder_path, "5_letter_words.txt"),"r") as word_file:
    words = word_file.readlines() # File handler is word_file. Read all of the file handler's content into a new variable called words.
# After the file handler is done, file will be automatically closed.

# Strip the newline character from each element in the list (with open context manager reads the contents in as a list by default)
complete_words = [] # Final list that will contain the edited version of the words. (No Whitespace and Capitalized)

for word in words:
    removed = word.rstrip() # Remove whitespace characters, \n is on the right of every word.
    capitalized = removed.upper() # Make all the letters uppercase
    complete_words.append(capitalized) # Add the new processed letter to the complete_words list.

# Words have been edited, no need to keep the original list
del words

# Convert words to a set and then convert words to tuple afterwards to prevent accidental modifcation.
# Sets also cannot be subset which is what the choice function in random does.
complete_words = tuple(set(complete_words))
#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------
# Environment Setup
# Extract API Keys
cwd = os.getcwd()
os.chdir("..")
env = os.path.join("Environment_Variables", ".env")
load_dotenv(env)
os.chdir(cwd)
#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------
# Create Turtle Screen
s = turtle.getcanvas()
root = s.master
turtle.title("Wordle")
#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------
# Create turtle clone
regular_turtle_pen = turtle.Turtle()
title_turtle_pen = regular_turtle_pen.clone() # Create separate text pen for title, so that when we reset turtle, the title does not dissapear.
#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------
# Create Functions for drawing squares, grid, messages, etc.
def square(x: float,y: float,outline: str,shape_color: str = None,pen_speed: int = None):
    regular_turtle_pen.penup()
    regular_turtle_pen.goto(x,y)
    regular_turtle_pen.pendown()
    regular_turtle_pen.pen(pencolor=outline, fillcolor=shape_color,speed=pen_speed,pensize=2)
    regular_turtle_pen.begin_fill()
    for i in range(4):
        regular_turtle_pen.forward(75)
        regular_turtle_pen.right(90)
    regular_turtle_pen.end_fill()

def write_letter(x: float,y: float,letter_color: str,letter: str,letter_font: tuple, pen_type):
    if pen_type == regular_turtle_pen:
        pen_type.penup()
        pen_type.goto(x,y)
        pen_type.color(letter_color)
        pen_type.write(letter,align="center",font=letter_font)
    elif pen_type == title_turtle_pen:
        pen_type.penup()
        pen_type.goto(x,y)
        pen_type.color(letter_color)
        pen_type.write(letter,align="center",font=letter_font)

def message_box(top_left_xcoor: float,top_left_ycoor: float,bttm_right_xcoor: 
                 float,bttm_right_ycoor: float,shape_color: str,x_letter: float,y_letter: 
                 float,text_color: str, message: str,mssg_font: tuple):
        rect = s.create_rectangle(top_left_xcoor,top_left_ycoor,bttm_right_xcoor,
                                  bttm_right_ycoor,fill=shape_color)
        mssg = s.create_text(x_letter,y_letter,fill=text_color,text=message,font=mssg_font)
        # Schedule deletion after 1500 milliseconds (1.5 seconds)
        s.after(1500, lambda: (s.delete(rect), s.delete(mssg))) # s.after() freezes Tkinter Canvas, so use this after function which will call the function after a specified time, enables us to draw and then undo the same drawing.
#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------
# Create functions to track the stats and graph the stats as well.
def stats_tracker(file_mode: str,file_name: str,status: str = None): # Create a function consolidate the code for reading and writing to a file
    if file_mode == "a+": # use append if a file needs to be updated
        with open(os.path.join(folder_path,file_name),file_mode) as stats:
            stats.write(f'{status},')
    elif file_mode == "r": # use append if we only want to read in a file.
        with open(os.path.join(folder_path,file_name),file_mode) as stats:
            word_stats = stats.readlines()
        return word_stats
    
def plot_wordle_summary( # Function to plot both visualizations at the same time. Old code only would plot guess distribution, while new code plots both visualizations.
    wins, loss, tries,
    attempt_num, attempt_freq,
    freq_guesses
):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))

    # -------------------------
    # Plot 1: Attempt Distribution
    # -------------------------
    bars = ax1.barh(attempt_num, attempt_freq, color="grey")

    if tries < 7:
        loc = attempt_num.index(str(tries))
        bars[loc].set_color("#619F5B")

    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax1.set_title(
        f'Total Games: {wins + loss} | Wins: {wins} | Losses: {loss}\n'
        f'Win Rate: {round((wins/(wins+loss))*100,2)}% | '
        f'Loss Rate: {round((loss/(wins+loss))*100,2)}%',
        fontsize=14,
        weight="bold"
    )

    # -------------------------
    # Plot 2: Frequent Guesses
    # -------------------------
    if freq_guesses != []:
        freq_guesses = freq_guesses[0].split(",")
        freq_guesses.remove("")

        freq_counts = Counter(freq_guesses).most_common(10)
        words, counts = zip(*freq_counts)

        ax2.barh(words[::-1], counts[::-1])
        ax2.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax2.set_title("Top 10 Frequently Guessed Words", fontsize=16, weight="bold")
    else:
        ax2.text(
            0.5, 0.5,
            "Frequently Guessed Words Unavailable",
            ha="center", va="center",
            fontsize=14,
            transform=ax2.transAxes
        )

    fig.suptitle("Wordle Statistics Summary", fontsize=22, weight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show(block=False)
#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------
# Title Block
write_letter(-20,325,"black","WORDLE PYTHON",("Arial",80,"bold"),title_turtle_pen)
#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------
# Grid Code
# tl = top left, br = bottom right
tl_x_coor = -200 
tl_x_coor_og = -200 # Original Starting Position, used to reset xgrid_coor back to original x-coor. This is required, since loop goes row by row.
tl_y_coor = 200
br_x_coor = -125
br_x_coor_og = -125 # Original Starting Position, used to reset xgrid_coor back to original x-coor. This is required, since loop goes row by row.
br_y_coor = 125
xgrid_coor_increment = 80 # How much to increment each square in a row (controls spacing of square, length of square is 75, so +5 is needed for a space between the squares)
ygrid_coor_increment = 80 # Controls moving up a row to draw the next row of squares
switch = True

for i in range(11): # The square is drawn on every other i, so we need twice the i's. Range starts from zero, so double of 6 is eleven, if we count from zero.
    if switch == True:
        for sq in range(0,5): # Draws one row of 5 squares
            s.create_rectangle(tl_x_coor,tl_y_coor,br_x_coor,br_y_coor,outline="#dcdee1")
            tl_x_coor += xgrid_coor_increment 
            br_x_coor += xgrid_coor_increment
            switch = False # When Switch if false reset values before drawing the next row of squares
    elif switch == False:
        tl_x_coor = tl_x_coor_og
        br_x_coor = br_x_coor_og
        tl_y_coor -= ygrid_coor_increment # Coordinates are opposite, lower values are drawn higher in canvas, so decrease y to draw a square higher, grid starts from bottom row.
        br_y_coor -= ygrid_coor_increment # Coordinates are opposite, lower values are drawn higher in canvas, so decrease y to draw a square higher, grid starts from bottom row.
        switch = True
#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------
# Keyboard
key_locations = {}
letter_locations = {}

first_row = ("Q","W","E","R","T","Y","U","I","O","P") # Make as tuples to prevent modifications, row values should be locked in.
second_row = ("A","S","D","F","G","H","J","K","L")
third_row = ("Z","X","C","V","B","N","M")

x_coor_incrementor = 50 # Length is 45 plus 5 for spacing to the next rectangle
x_letter_coor_incrementor = 50 # Each letter should be 50 pixels away from each other

r1_switch = True # Controls which keyboard row we are drawing for, r1 = row 1, etc. True means we draw, False means we don't.
r2_switch = False
r3_switch = False

while True:
    if r1_switch == True and r2_switch == False and r3_switch == False: # Row 1
        tl_x_coor = -255 # Coordinates for first rectangle/key in Row 1
        tl_y_coor = 215
        br_x_coor = -210
        br_y_coor = 275
        for i in first_row:
            key_locations[i] = (tl_x_coor,tl_y_coor,br_x_coor,br_y_coor)
            tl_x_coor += x_coor_incrementor # Length is 45 plus 5 for spacing to the next rectangle
            br_x_coor += x_coor_incrementor # Length is 45 plus 5 for spacing to the next rectangle
        x_letter_loc = -233 # Coordinates for first letter in row 1
        y_letter_loc = 244 # Coordinates for first letter
        for i in first_row:
            letter_locations[i] = (x_letter_loc,y_letter_loc)
            x_letter_loc += x_letter_coor_incrementor
        r1_switch = False # Turn off row 1, 
        r2_switch = True  # Turn on row 2
    elif r2_switch == True and r1_switch == False and r3_switch == False: # Row 2
        tl_x_coor = -230 # Coordinates for first rectangle/key in Row 2
        tl_y_coor = 280
        br_x_coor = -185
        br_y_coor = 340
        for i in second_row:
            key_locations[i] = (tl_x_coor,tl_y_coor,br_x_coor,br_y_coor)
            tl_x_coor += x_coor_incrementor 
            br_x_coor += x_coor_incrementor
        x_letter_loc = -207.5 # Coordinates for first letter in row 2
        y_letter_loc = 310
        for i in second_row:
            letter_locations[i] = (x_letter_loc,y_letter_loc)
            x_letter_loc += x_letter_coor_incrementor
        r2_switch = False
        r3_switch = True
    elif r3_switch == True and r1_switch == False and r2_switch == False: # Row 3
        tl_x_coor = -180
        tl_y_coor = 345
        br_x_coor = -135
        br_y_coor = 405
        for i in third_row:
            key_locations[i] = (tl_x_coor,tl_y_coor,br_x_coor,br_y_coor)
            tl_x_coor += x_coor_incrementor
            br_x_coor += x_coor_incrementor
        x_letter_loc = -157.5 
        y_letter_loc = 375
        for i in third_row:
            letter_locations[i] = (x_letter_loc,y_letter_loc)
            x_letter_loc += x_letter_coor_incrementor
        break

# Draw the keyboard from the two dictionaries
for i in key_locations: 
    loc = key_locations[i] # Retrieve the location values associated with each key.
    s.create_rectangle(*loc,outline="#DBEAFE",fill="#DBEAFE") # *loc unpacks the tuple

for i in letter_locations:
    letter_loc = letter_locations[i] # Retrieve the location values associated with each letter.
    s.create_text(*letter_loc,font=("Arial",29,"bold"),fill="black",text=i,justify="center")

# Kept here, since it's apart of the keyboard as opposed to the function section.
def keyboard_color(color,range_on = True): # Function for determining keyboard color, so that we don't have to repeat the same code
    if range_on == True: # To access list_letter and the letters specifically, we need to do slicing which requires integers, range function will be used to assist with that.
        keyboard_letter = list_letter[gu][0]
        keyboard_loc = key_locations[keyboard_letter]
        keyletter_loc = letter_locations[keyboard_letter]
        rect = s.create_rectangle(*keyboard_loc,outline="#DBEAFE",fill=color)
        text = s.create_text(*keyletter_loc,font=("Arial",29,"bold"),fill="white",text=list_letter[gu][0],justify="center")
        return rect,text # These values need to be returned, so that we can delete the colors and text in the keyboard.
    else: # This code is if the llm wins
        keyboard_loc = key_locations[win] # win is the iterator used for when the llm wins
        keyletter_loc = letter_locations[win]
        rect = s.create_rectangle(*keyboard_loc,outline="#DBEAFE",fill=color)
        text = s.create_text(*keyletter_loc,font=("Arial",29,"bold"),fill="white",text=win,justify="center")
        return rect,text
#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------
# LLM Setup

class WordleAgentManager:
    """
    Manages the selection, configuration, and history of the Wordle AI Agent.
    """
    def __init__(self, instructions_path: str):
        self.instructions_path = Path(instructions_path)
        self.chat_map = {}
        
        # 1. Select and Initialize the AI Model
        self.ai_model = self._setup_model()
        
        # 2. Load and Prepare Instructions
        self.wordle_instructions = self._load_prompt(self.instructions_path)
        
        # 3. Build the LangChain Pipeline
        self.pipeline = self._build_pipeline()
        
        # 4. Initialize the Runnable with Message History
        self.wordle_history_pipeline = RunnableWithMessageHistory(
            self.pipeline,
            get_session_history=self.get_chat_history,
            input_messages_key="query",
            history_messages_key="history"
        )

        #5. Setup model names
        self.choice = self.model_selector.lower().strip()

    def _setup_model(self):
        """Prompts user for model choice and handles typos."""
        self.model_selector = turtle.textinput("Select AI Model", "ChatGPT\nClaude\nGemini")
        if not self.model_selector:
            # Default to Gemini if user cancels
            return ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-09-2025")
            
        self.choice = self.model_selector.lower().strip()

        # Mapping variations to standard names
        model_map = {
            "gemini": ["gemeni", "jemini", "gimini", "gemmini", "gemineye"],
            "chatgpt": ["chatgtp", "chaptgpt", "chapt gpt", "chat-gpt", "chat gpt", "chaatgpt"],
            "claude": ["claud", "cloud", "claudia", "claudie", "claudel", "claudi", "claudu", "cluade"]
        }

        if self.choice == "gemini" or any(self.choice == typo for typo in model_map["gemini"]):
            return ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-09-2025")
        elif self.choice == "chatgpt" or any(self.choice == typo for typo in model_map["chatgpt"]):
            return ChatOpenAI(model="gpt-4o-mini")
        elif self.choice == "claude" or any(self.choice == typo for typo in model_map["claude"]):
            return ChatAnthropic(model="claude-3-haiku-20240307")
        else:
            # Fallback if unknown input
            return ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-09-2025")

    def _load_prompt(self, path: Path, escape_json_braces: bool = True) -> str:
        """Loads and escapes JSON braces for LangChain templates."""
        if not path.exists():
            raise FileNotFoundError(f"Instructions file not found at {path}")
            
        text = path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff").rstrip()

        if not escape_json_braces:
            return text

        def _escape_block(m: re.Match) -> str:
            inner = m.group(1)
            # Escape single braces to {{ }} so LangChain doesn't try to fill them
            inner = re.sub(r'(?<!{){(?!{)', '{{', inner)
            inner = re.sub(r'(?<!})}(?!})', '}}', inner)
            return f"```json\n{inner}\n```"

        return re.sub(r"```json\s*\r?\n(.*?)\r?\n```", _escape_block, text, flags=re.S | re.I)

    def _build_pipeline(self):
        """Creates the LangChain prompt template and joins it with the model."""
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.wordle_instructions),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{query}"),
        ])
        return prompt_template | self.ai_model

    def get_chat_history(self, chat_session_id: str) -> InMemoryChatMessageHistory:
        """Accesses or creates the message history for a specific session."""
        if chat_session_id not in self.chat_map:
            self.chat_map[chat_session_id] = InMemoryChatMessageHistory()
        return self.chat_map[chat_session_id]

    def reset_session(self, chat_session_id: str):
        """Clears the history for a specific session (useful for starting a new game)."""
        if chat_session_id in self.chat_map:
            del self.chat_map[chat_session_id]


# Path to instructions
instructions_path = os.path.join(folder_path,"instructions.md")
# Game ID
chat_id = "id_123"
# Obtain pipeline from WordleAgentManager class.
llm_pipeline_memory = WordleAgentManager(instructions_path)

def json_backtick_cleaner(llm_response):
    """
    Get rid of the backticks in the JSON when the LLM responds.
    """
    try:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", llm_response.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()
        parsed_response = json.loads(cleaned)
        return parsed_response
    except:
        print(llm_response)
        return (llm_response)


def llm_converter(owf_output):
    """
    This converts the output from the official wordle function into a predictable format that the LLM can understand.
    """
    ai_list_letter = []
    for j in enumerate(owf_output): # enumerate returns tuples (first index is location, second index is letter)
        char_loc = j[0] # First Tuple Element
        char = j[1] # Second Tuple Element
        if len(char) == 1:
            character = f'{char_loc}:{char}:C'
        elif len(char) == 2:
            character = f'{char_loc}:{char[0]}:P'
        elif len(char) == 3:
            character = f'{char_loc}:{char[0]}:A'

        ai_list_letter.append(character)

    ai_list_letter = ", ".join(ai_list_letter)
    return ai_list_letter

def ai_guess(attempt: int, attempt_1: bool, previous_guess_info = None, win = None):
    """
    Function consolidates both adding to the chain ("LLM's Memory") and parsing the LLM's response.  
    """
    if attempt != 7 and win != True: 
        if attempt_1 == True: # Meant to display custom message to LLM on first try only, for every new game played.
            response = llm_pipeline_memory.wordle_history_pipeline.invoke(
            {"query": f"Welcome to Wordle, this is guess {attempt}. Please enter a guess to guess the secret word:"},
            config={"session_id": chat_id})
        elif attempt_1 == False:
            response = llm_pipeline_memory.wordle_history_pipeline.invoke(
            {"query": f"This is guess {attempt}. Here is the information from your previous attempt {previous_guess_info}"},
            config={"session_id": chat_id})   
    
    if win == True:
        win_messages = ["Genius","Magnificent","Impressive","Splendid","Great","Phew"]
        if attempt == 1:
            response = llm_pipeline_memory.wordle_history_pipeline.invoke(
                {"query": f'{win_messages[0]}! You won in {attempt} tries!'},
                config={"session_id": chat_id})
        elif attempt == 2:
            response = llm_pipeline_memory.wordle_history_pipeline.invoke(
                {"query": f'{win_messages[1]}! You won in {attempt} tries!!'}, config={"session_id": chat_id})
        elif attempt == 3:
            response = llm_pipeline_memory.wordle_history_pipeline.invoke(
                {"query": f'{win_messages[2]}! You won in {attempt} tries!!'}, config={"session_id": chat_id})
        elif attempt == 4:
            response = llm_pipeline_memory.wordle_history_pipeline.invoke(
                {"query": f'{win_messages[3]}! You won in {attempt} tries!!'}, config={"session_id": chat_id})
        elif attempt == 5:
            response = llm_pipeline_memory.wordle_history_pipeline.invoke(
                {"query": f'{win_messages[4]}! You won in {attempt} tries!!'}, config={"session_id": chat_id})
        elif attempt == 6:
            response = llm_pipeline_memory.wordle_history_pipeline.invoke(
                {"query": f'{win_messages[5]}! You won in {attempt} tries!!'}, config={"session_id": chat_id})
    
    elif win == False:
        response = llm_pipeline_memory.wordle_history_pipeline.invoke(
            {"query": f"Sorry, you are out of tries. The correct word was {answer}. Better luck next time!"},
            config={"session_id": "id_123"}) 


    llm_string = response.content
    try:
        parsed_response = json_backtick_cleaner(llm_string)
    # if "guess" in parsed_response:
        guess = parsed_response['guess']
        return guess
    # elif "reply" in parsed_response:
    # reply = parsed_response['reply']
    # return reply
    except:
        print(llm_string)
        return llm_string

def invalid_guess(scn1 = False,scn2 = False,scn3 = False,scn4 = False, scn5 = False): # scn = scenario
    if scn1 == True:
        faulty_response = llm_pipeline_memory.wordle_history_pipeline.invoke(
                    {"query": "Not enough letters in provided guess, Generate a valid guess. (Valid Guesses are valid 5 letter English Words that exist in the English Language.)"},
                    config={"session_id": chat_id})
    elif scn2 == True:
        faulty_response = llm_pipeline_memory.wordle_history_pipeline.invoke(
                    {"query": "Guess contains numbers, Generate a valid guess. (Valid Guesses are valid 5 letter English Words. The guess should NOT contain Alphanumeric characters.)"},
                    config={"session_id": chat_id})
    elif scn3 == True:
        faulty_response = llm_pipeline_memory.wordle_history_pipeline.invoke(
                    {"query": "The guess was not found in the word list. Generate another valid guess. (Valid Guesses are valid 5 letter English Words that exist in the English Language.)"},
                    config={"session_id": chat_id})
    elif scn4 == True:
        faulty_response = llm_pipeline_memory.wordle_history_pipeline.invoke(
                    {"query": "repeat guess entered. Generate another valid guess. (Valid Guesses are valid 5 letter English Words. Additionally the guess should be a word that you previously guessed.)"},
                    config={"session_id": chat_id})
    elif scn5 == True:
        faulty_response = llm_pipeline_memory.wordle_history_pipeline.invoke(
                    {"query": "The word is longer than 5 letters. Generate another valid guess. (Valid Guesses are valid 5 letter English Words.)"},
                    config={"session_id": chat_id})
    
    llm_new_response = faulty_response.content
    response_parsed = json_backtick_cleaner(llm_new_response)
    new_response = response_parsed['guess']
    return new_response


#-----------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------
# Main Wordle Loop
game_1_completed = None
play_again = "YES"
keyboard_positions = [] # Create empy list to store the id's of the rectangle colors and text in the keyboard when playing wordle. Needed for first ieration.
while play_again == "YES" or play_again == "Y":
    xgrid_coor = -200
    ygrid_coor = 275
    xletter_coor = -162
    yletter_coor = 212
    switch = True
    tries = 1
    if keyboard_positions != []: # Needed to prevent list which has the id's to be deleted from being cleared.
        for pos in range(len(keyboard_positions)):
            shape = keyboard_positions[pos][0] # function returns tuple with shape being first element and letter being second element.
            letter = keyboard_positions[pos][1]
            s.delete(shape)
            s.delete(letter)
        keyboard_positions.clear() # Clear the list, so that we can store the new rectangle id's and text and delete them.
    correct_pos = [] # In the word, correct position
    incorrect_pos = [] # In the word, wrong position
    invalid_pos = [] # Not in the word at all
    previous_words = [] # Store word entries, so that the program can prevent repeat entries
    regular_turtle_pen.clear() # Clear all the squares and text in squares for next game
    answer = r.choice(complete_words) # Randomly select a word from this list
    if game_1_completed == True:
        same_model = turtle.textinput(f"Do you want to continue with {llm_pipeline_memory.choice.upper()}?","Yes(Y)/No(N)")
        same_model = same_model.upper()
        if same_model == "Y" or same_model == "YES":
            llm_pipeline_memory.reset_session(chat_id) # Resets the pipeline and clears previous game from context window before doing API Call.
        elif same_model == "N" or same_model == "NO":
            llm_pipeline_memory = WordleAgentManager(instructions_path) # This will show them the models, keeping this in case user accidentally wanted to continue with the same model. This allows them to continue, since it'll delete everything and the user can select the previous ai model.
    g = ai_guess(attempt = tries, attempt_1= True)
    g = g.upper()
    # If the LLM accidentally enters invalid entries sequentially, they'll be stuck in this loop until they enter a valid entry which will cause the loop to close.
    while True:
        while (len(g) < len(answer) and (g.isalpha() == True)) or ((g.isalpha() == False)) or ((len(g) == len(answer)) and g not in complete_words) or (g in previous_words):
        # Words less than 5 letters with valid alphanumeric characters are not allowed
            if len(g) < len(answer) and (g.isalpha() == True): 
                message_box(-101,-301,94.5,-250,"black",-3,-277,"white","not enough letters",("Arial",16,"normal"))
                g = invalid_guess(scn1=True)
                g = g.upper()
            elif (g.isalpha() == False): # isalpha checks if any letters are in word. If special characters or nothing (len = 0) is there, it returns false.
                message_box(-101,-301,94.5,-250,"black",-3,-277,"white","guess contains numbers",("Arial",16,"normal"))
                g = invalid_guess(scn2=True)
                g = g.upper()
            elif (len(g) == len(answer)) and g not in complete_words: # Basically these while loops will force a llm to remain in the loop until they enter a word that does not meet the condition of the while loop. The while loops have been built this way to prevent llms from entering invalid entries or trying to cheat by only entering one letter a or certain word combinations like only vowels: aeiou.
                message_box(-101,-301,94.5,-250,"black",-3,-277,"white","word not in word list",("Arial",16,"normal"))
                g = invalid_guess(scn3=True)
                g = g.upper()
            elif g in previous_words: # Prevent the llm from entering repeat words
                message_box(-101,-301,94.5,-250,"black",-3,-277,"white","repeat guess entered",("Arial",16,"normal"))
                g = invalid_guess(scn4=True)
                g = g.upper()
        
        if g != answer:
            try:
                previous_words.append(g)
                list_letter = owf.wordle(answer,g)
                previous_guesses = llm_converter(list_letter)
                stats_tracker(file_mode="a+",file_name="frequent_guesses.txt",status=g)
                for letter in list_letter:
                    if len(letter) == 1:
                        square(xgrid_coor,ygrid_coor,outline = "#dcdee1",shape_color = "#6ca965",pen_speed=10)
                        xgrid_coor += 80
                        correct_pos.append(letter)
                    elif len(letter) == 2:
                        square(xgrid_coor,ygrid_coor,outline = "#dcdee1",shape_color = "#c8b653",pen_speed=10)
                        xgrid_coor += 80
                        l = letter.strip("*")
                        incorrect_pos.append(l)
                    elif len(letter) == 3:
                        square(xgrid_coor,ygrid_coor,outline = "#dcdee1",shape_color = "#787c7f",pen_speed=10)
                        xgrid_coor += 80
                        le = letter.strip("**")
                        invalid_pos.append(le)
                for guess_letter in g:
                    gl = guess_letter
                    write_letter(xletter_coor,yletter_coor,"White",gl,letter_font=("Arial",32,"bold"),pen_type=regular_turtle_pen)
                    xletter_coor += 80
                    switch = False
                for gu in range(len(list_letter)):
                    if list_letter[gu][0] in correct_pos:
                        green = keyboard_color("#6ca965") # store as variable so that we can add to keyboard_positions_list. (The rectangle will still be drawn on the screen due to hte s.create_rectangle method in the function.)
                        keyboard_positions.append(green) # list will store the id's so that we can delete them later, if the player choses to play a new game.
                    elif list_letter[gu][0] in incorrect_pos and (list_letter[gu][0] not in correct_pos):
                        yellow = keyboard_color("#c8b653")
                        keyboard_positions.append(yellow)
                    elif list_letter[gu][0] in invalid_pos and (list_letter[gu][0] not in correct_pos or list_letter[gu][0] not in incorrect_pos):
                        grey = keyboard_color("#787c7f")
                        keyboard_positions.append(grey)
                tries += 1
                if tries == 7: # On the 7th try break from loop, don't this for 6th try otherwise llm can't enter sixth guess.
                    message_box(-50,-295,45,-265,"black",-3,-280,"white",answer,("Arial",18,"normal"))
                    stats_tracker(status ="L",file_mode="a+",file_name="wordle_stats.txt")
                    ai_guess(attempt=tries,attempt_1=False,win = False)
                    game_1_completed = True
                    break
                if switch == False:
                    xgrid_coor = -200
                    ygrid_coor -= 80
                    xletter_coor = -162
                    yletter_coor -= 79
                    switch = True
                g = ai_guess(attempt=tries,attempt_1=False, previous_guess_info=f'{g}\n{previous_guesses}')
                g = g.upper()
            except IndexError: # Words that are longer than 5 letters in length
                while len(g) > len(answer):
                    g = invalid_guess(scn5=True)
                    g = g.upper()
        elif g == answer:
            stats_tracker(status = "W",file_mode = "a+",file_name="wordle_stats.txt")
            for sq in range(0,5): # Draws one row of 5 squares
                square(xgrid_coor,ygrid_coor,outline = "#dcdee1",shape_color = "#6ca965",pen_speed=10)
                xgrid_coor += 80
            for letter in answer:
                l = letter
                write_letter(xletter_coor,yletter_coor,"White",l,letter_font=("Arial",32,"bold"),pen_type=regular_turtle_pen)
                xletter_coor += 80
            for win in g:
                winning = keyboard_color("#6ca965",range_on=False) # range_on = False, tells Python to execute the other half of the function for when a player wins. range_on executes the first half of the function which is when a guess does not match the answer.
                keyboard_positions.append(winning)
            if tries == 1:
                message_box(-44,-295,39,-265,"black",-3,-280,"white","Genius",("Arial",18,"normal"))
            elif tries == 2:
                message_box(-70,-295,63,-261,"black",-4,-279,"white","Magnificent",("Arial",18,"normal"))
            elif tries == 3:
                message_box(-70,-295,63,-261,"black",-4,-279,"white","Impressive",("Arial",18,"normal"))
            elif tries == 4:
                message_box(-70,-295,63,-261,"black",-4,-279,"white","Splendid",("Arial",18,"normal"))
            elif tries == 5:
                message_box(-41,-295,35,-265,"black",-3,-280,"white","Great",("Arial",18,"normal"))
            elif tries == 6:
                message_box(-41,-295,35,-265,"black",-3,-280,"white","Phew",("Arial",18,"normal"))
            ai_guess(attempt=tries,attempt_1=False,win = True)
            stats_tracker(status =str(tries),file_mode="a+",file_name="wordle_stats.txt")
            game_1_completed = True
            break
    
    # Create Graph and Aggregate Player Stats per Game
    agg_stats = stats_tracker(file_mode="r",file_name="wordle_stats.txt") # create variable to store info from wordle_stats.txt
    agg_stats = agg_stats[0] # Variable is a list, so slice into first spot to get all the information
    agg_stats = agg_stats.split(",") # Info however is stored as a large string, so split on commas, since all the info was written into the files with commas to separate the words.

    wins = agg_stats.count("W") # Count the number of wins and loss in the file.
    loss = agg_stats.count("L")

    attempt_freq = [] # Empty list to store the guess distribution for each attempt. i.e across all the games it took the player 4 tries to guess the correct word for 5 separate games.
    for i in range(1,7): # Do the distribution values in order, i.e 5 games took 1 attempt, 2 games took 3, attempts, easier to make it easy to pair with the actual attempt number.
        string_value = str(i) # Convert to string because the information in the file was read in as a string
        attempt = agg_stats.count(string_value) # Count how many games there for each attempt. i.e there are 5 separate games which took 4 tries to solve.
        num_value = int(attempt) # Finally reconvert the attempts back into an integer for plotting purposes.
        attempt_freq.append(num_value) # Add to list to store all the attempt values

    attempt_freq.reverse() # Matplot lib plots from the end of the list, so we want the list reversed with smaller numbers at the end. Ensures matplot lib graphs in ascending order.

    attempt_num = list(range(1,7)) # Just create the actual attempt_numbers, i.e it took 4 attempts to solve a game, etc. This will be the x-axis.
    attempt_num.reverse() # Reverse as well, so that the attempt numbrers match up with their respective attempt_frequencies.
    attempt_num = [str(i) for i in attempt_num] # Convert to string, otherwise matplotlib will sort these values if they are numerical.
    # Create the plot 
    freq_guesses = stats_tracker(file_mode="r", file_name="frequent_guesses.txt")

    # If llm never had frequent guesses (won on first try only)
    if freq_guesses == [] or freq_guesses == [""]:
        message_box(
            -300, -301, 300, -250,
            "black",
            -3, -277,
            "white",
            "Frequently Guessed Words Unavailable",
            ("Arial", 16, "normal")
    )

    plot_wordle_summary( # Enables both visualizations to be plotted at the same time
        wins=wins,
        loss=loss,
        tries=tries,
        attempt_num=attempt_num,
        attempt_freq=attempt_freq,
        freq_guesses=freq_guesses
    )

    # Prompt the player to play again
    play_again = turtle.textinput("Play Again?","Yes or No")
    play_again = play_again.upper()
#-----------------------------------------------------------------------------------------------  
turtle.done()
#-----------------------------------------------------------------------------------------------

