import tkinter as tk
from tkinter import ttk
root = tk.Tk()
frame = ttk.Frame(root)
frame.pack(fill='x', expand=True)

spacer = ttk.Frame(frame, style='TFrame')
spacer.pack(side='left', expand=True, fill='x')

def cb1(): print('Btn 1 clicked')
def cb2(): print('Btn 2 clicked')

btn1 = ttk.Button(frame, text='Btn 1', command=cb1)
btn1.pack(side='left')

btn2 = ttk.Button(frame, text='Btn 2', command=cb2)
btn2.pack(side='left')

root.update()
print('Btn1 geometry:', btn1.winfo_geometry())
print('Btn2 geometry:', btn2.winfo_geometry())
print('Spacer geometry:', spacer.winfo_geometry())
