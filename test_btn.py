import tkinter as tk
from tkinter import ttk
root = tk.Tk()
def cb(): print('Clicked!')
btn = ttk.Button(root, text='Base Monthly Income:', command=cb)
btn.pack()
root.update()
print('State:', btn.state())
