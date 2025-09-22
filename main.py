import os
import sys
import shlex
import subprocess
import psutil  
import re
import nltk
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

BUILT_IN_COMMANDS = ['cd', 'pwd', 'ls', 'mkdir', 'rm', 'exit', 'show_cpu', 'show_mem', 'show_processes', 'mv']

history_file = Path('terminal_history.txt')
try:
    if not history_file.exists():
        history_file.touch()
    print(f"Command history saved to: {history_file.resolve()}")
except PermissionError:
    print("Error: Cannot create/access history file due to permissions.")
    history_file = None

completer = WordCompleter(BUILT_IN_COMMANDS, ignore_case=True)
history = FileHistory(str(history_file)) if history_file else None
session = PromptSession(
    message=lambda: f"{os.getcwd()} $ ",
    completer=completer,
    history=history,
    complete_while_typing=False,
    enable_history_search=True
)

def parse_natural_language(command):
    tokens = nltk.word_tokenize(command.lower())
    tagged = nltk.pos_tag(tokens)
    
    patterns = [
        (r"(create|make|move)\s+(folder|directory|document|new folder)\s+(\w+)", lambda m: f"mkdir {m.group(3)}"),
        (r"(create|make|move)\s+file\s+(\w+\.\w+)", lambda m: f"touch {m.group(2)}"),
        (r"list\s+(files|directories|folder)", lambda m: "ls"),
        (r"move\s+(\w+\.\w+)\s+(to\s+)?(\w+)", lambda m: f"mv {m.group(1)} {m.group(3)}"),
        (r"delete\s+(file|folder|directory)\s+(\w+\.?\w*)", lambda m: f"rm {m.group(2)}"),
        (r"change\s+(to\s+)?directory\s+(\w+)", lambda m: f"cd {m.group(2)}"),
        (r"show\s+current\s+(directory|folder)", lambda m: "pwd"),
        (r"show\s+cpu", lambda m: "show_cpu"),
        (r"show\s+memory", lambda m: "show_mem"),
        (r"show\s+processes", lambda m: "show_processes")
    ]
    
    for pattern, action in patterns:
        match = re.match(pattern, command.lower())
        if match:
            return action(match)
    
    return command  

def handle_command(command):
    if not command:
        return

    command = parse_natural_language(command)
    args = shlex.split(command)
    cmd = args[0]

    if cmd == 'exit':
        sys.exit(0)

    elif cmd == 'cd':
        target = args[1] if len(args) > 1 else os.path.expanduser('~')
        try:
            os.chdir(target)
        except Exception as e:
            print(f"cd: {e}")

    elif cmd == 'pwd':
        print(os.getcwd())

    elif cmd == 'ls':
        dir_path = args[1] if len(args) > 1 else os.getcwd()
        try:
            files = os.listdir(dir_path)
            print(' '.join(files))
        except Exception as e:
            print(f"ls: {e}")

    elif cmd == 'mkdir':
        if len(args) < 2:
            print("mkdir: missing operand")
            return
        try:
            os.mkdir(args[1])
        except Exception as e:
            print(f"mkdir: {e}")

    elif cmd == 'rm':
        if len(args) < 2:
            print("rm: missing operand")
            return
        try:
            if os.path.isdir(args[1]):
                import shutil
                shutil.rmtree(args[1])
            else:
                os.remove(args[1])
        except Exception as e:
            print(f"rm: {e}")

    elif cmd == 'mv':
        if len(args) != 2:  
            print("mv: missing source or destination")
            return
        try:
            os.rename(args[0], args[1])
            print(f"Moved {args[0]} to {args[1]}")
        except FileNotFoundError:
            print(f"mv: {args[0]}: No such file or directory")
        except PermissionError:
            print(f"mv: permission denied to move {args[0]}")
        except Exception as e:
            print(f"mv: {e}")

    elif cmd == 'move':
        if len(args) < 3:
            print("move: missing source or destination")
            return
        try:
            os.rename(args[1], args[2])
        except Exception as e:
            print(f"move: {e}")

    elif cmd == 'touch':
        if len(args) < 2:
            print("touch: missing file name")
            return
        try:
            file_path = args[1]
            content = args[2] if len(args) > 2 else ""
            with open(file_path, 'a') as f:
                if content:
                    f.write(content + '\n')
            os.utime(file_path, None)  # Update timestamp
        except Exception as e:
            print(f"touch: {e}")

    elif cmd == 'show_cpu':
        print(f"CPU Usage: {psutil.cpu_percent(interval=1)}%")

    elif cmd == 'show_mem':
        mem = psutil.virtual_memory()
        print(f"Memory Usage: Total={mem.total / (1024**3):.2f}GB, Used={mem.used / (1024**3):.2f}GB, Free={mem.available / (1024**3):.2f}GB ({mem.percent}%)")

    elif cmd == 'show_processes':
        print("PID\tName\tCPU%\tMemory%")
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                print(f"{info['pid']}\t{info['name']}\t{info['cpu_percent']}\t{info['memory_percent']:.2f}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    else:
        try:
            result = subprocess.run(args, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())
        except FileNotFoundError:
            print(f"{cmd}: command not found")
        except Exception as e:
            print(f"Error executing {cmd}: {e}")

def main():
    print("Welcome to Python-Based Command Terminal. Type 'exit' to quit.")
    print("Use up/down arrows for history, Tab for auto-completion.")
    print("Try natural language, e.g., 'create folder test' or 'move file1.txt to test'.")
    while True:
        try:
            command = session.prompt()
            handle_command(command)
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit.")
        except EOFError:
            sys.exit(0)

if __name__ == "__main__":
    main()
