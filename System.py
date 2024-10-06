import sys, os

class Clear():
    def __init__(self) -> None:
        pass

    def clear_previous_line(self): # https://stackoverflow.com/a/72874759/20924888
        # cursor up one line
        sys.stdout.write('\x1b[1A')
        # delete last line
        sys.stdout.write('\x1b[2K')

    def clear_full_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def move_mouse_to_top(self):
        sys.stdout.write("\033[H")

class Terminal():
    def get_terminal_width(self):
        return os.get_terminal_size().columns
    
    def get_terminal_height(self):
        return os.get_terminal_size().lines
    
    def get_terminal_size(self):
        return os.get_terminal_size()
    
    def set_terminal_size(self, rows, columns=30):
        """Only sometimes works :("""
        sys.stdout.write("\x1b[8;{rows};{cols}t".format(rows=rows, cols=columns))
        sys.stdout.flush()