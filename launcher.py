import blessed
import subprocess
import os
import sys
import time
from contextlib import contextmanager

term = blessed.Terminal()

MENU_ITEMS = [
    ("Ollama", "ol1.py", "Launch Ollama-based chat application"),
    ("Perplexity", "p1.py", "Launch Perplexity-based chat application"),
    ("Groq", "g1.py", "Launch Groq-based chat application"),
    ("Edit .env", "edit_env", "Edit environment variables"),
    ("Exit", None, "Exit the launcher")
]

@contextmanager
def fullscreen():
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        yield

def draw_3d_box(y, x, height, width, color):
    shadow_color = term.color_rgb(50, 50, 50)
    
    # Draw shadow
    print(term.move(y+1, x+2) + shadow_color + '█' * (width-1) + term.normal)
    for i in range(height-1):
        print(term.move(y+2+i, x+width) + shadow_color + '█' + term.normal)

    # Draw main box
    print(term.move(y, x) + color + '╔' + '═' * (width - 2) + '╗' + term.normal)
    for i in range(height - 2):
        print(term.move(y + i + 1, x) + color + '║' + ' ' * (width - 2) + '║' + term.normal)
    print(term.move(y + height - 1, x) + color + '╚' + '═' * (width - 2) + '╝' + term.normal)

def draw_menu(current_option):
    menu_width = 50
    menu_height = len(MENU_ITEMS) * 3 + 5
    start_y = (term.height - menu_height) // 2
    start_x = (term.width - menu_width) // 2

    main_color = term.cornflower_blue
    draw_3d_box(start_y, start_x, menu_height, menu_width, main_color)

    title = '🚀 Launcher Menu 🚀'
    print(term.move(start_y + 1, start_x + (menu_width - len(title)) // 2) + term.bold + term.yellow(title))

    for i, (option, _, _) in enumerate(MENU_ITEMS):
        y = start_y + i * 3 + 4
        if i == current_option:
            item_color = term.black_on_yellow
            draw_3d_box(y-1, start_x+3, 3, menu_width-6, item_color)
            print(term.move(y, start_x + 5) + item_color + term.bold(f" {option:<{menu_width - 10}} ") + term.normal)
        else:
            item_color = term.white_on_blue
            draw_3d_box(y-1, start_x+3, 3, menu_width-6, item_color)
            print(term.move(y, start_x + 5) + item_color + term.bold(f" {option:<{menu_width - 10}} ") + term.normal)

    description = MENU_ITEMS[current_option][2]
    print(term.move(start_y + menu_height, start_x) + term.center(term.italic(description), menu_width))

def run_script(script):
    with fullscreen():
        print(term.clear + term.move_y(term.height // 2) + term.bold_green(term.center(f"Running {script}...")))
        time.sleep(1)

    process = subprocess.Popen(["streamlit", "run", script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    with term.cbreak():
        print(term.clear)
        try:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                if term.inkey(timeout=0.1) == 'q':
                    process.terminate()
                    print(term.bold_red("\nScript terminated. Press any key to return to the launcher..."))
                    term.inkey()
                    return
        except KeyboardInterrupt:
            process.terminate()
            print(term.bold_red("\nScript terminated. Press any key to return to the launcher..."))
            term.inkey()
            return

    print(term.bold_green("\nScript finished. Press any key to return to the launcher..."))
    term.inkey()

def edit_env():
    os.system('clear')
    os.system("nano .env")

def main_menu():
    current_option = 0

    while True:
        with fullscreen():
            print(term.clear)
            draw_menu(current_option)

            key = term.inkey()

            if key.name == 'KEY_UP' and current_option > 0:
                current_option -= 1
            elif key.name == 'KEY_DOWN' and current_option < len(MENU_ITEMS) - 1:
                current_option += 1
            elif key.name == 'KEY_ENTER':
                selected_option = MENU_ITEMS[current_option][1]
                if selected_option is None:
                    return
                elif selected_option == "edit_env":
                    edit_env()
                else:
                    run_script(selected_option)
            elif key == 'q':
                return

if __name__ == "__main__":
    main_menu()