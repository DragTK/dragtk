# DragTK — Visual Python GUI Builder

DragTK is a free, open-source drag-and-drop GUI builder for Python. It gives students and beginners a visual canvas to build Tkinter applications — generating working Python code as they design.

Built with schools in mind, DragTK aims to fill the gap left by Visual Basic: a simple, accessible way to create graphical applications without starting from a blank terminal.

---

## Download

**Windows** — download the latest `.exe` from [Releases](../../releases/latest). Copy it to any machine and run — no installation required.

**All platforms** — clone this repository and run `DragTK.py` directly. Requires Python 3.8+.

```bash
git clone https://github.com/yourusername/dragtk.git
cd dragtk
python DragTK.py
```

---

## Requirements

- Python 3.8 or later
- Tkinter (included with standard Python installations on Windows and macOS)

On some Linux distributions Tkinter must be installed separately:

```bash
sudo apt-get install python3-tk
```

---

## Why DragTK?

Python is now the dominant language taught in UK schools, but it lacks the kind of visual development environment that once made Visual Basic so effective in the classroom. Students are asked to learn an abstract, text-based craft with very little visual feedback.

DragTK addresses this by letting students drag buttons, labels, inputs, and other widgets onto a canvas and immediately see the Python code that represents them. This approach is grounded in the **Concrete–Representational–Abstract (CRA)** model — students begin with something tangible and familiar before moving toward abstraction.

Every student already knows what an app looks like. DragTK turns that prior knowledge into a starting point rather than an obstacle.

**Practical classroom considerations:**

- Runs from a single `.exe` — no admin rights or installation needed
- Raw `.py` source available for schools where `.exe` files are restricted
- MIT licensed — no fees, no sign-ups, no per-seat costs
- Step-by-step lessons and example projects at [dragtk.com/learn](https://dragtk.com/learn)

---

## Features

- Drag-and-drop canvas for placing and positioning widgets
- Supported widgets: Label, Button, Entry, Treeview, Checkbutton, Radiobutton, Text Area, Listbox, Combobox, Image
- Live Python code generation as you design
- Widget properties panel for adjusting text, font, colour, and size
- Export project as a standalone `.py` file
- Run projects directly from within DragTK

---

## Known limitations

- Limited undo / redo support. Current implementation basic and inefficient. Performance issues with current undo/redo implementation on larger projects
- Performance may degrade the more widgets are added and for larger projects
- Users must place their code between the marked start and end areas or could be at risk of losing work. The app does its best to prevent this

---

## Getting Started

1. Download the `.exe` from [Releases](../../releases/latest) or clone the repository
2. Run `DragTK.exe` or `python DragTK.py`
3. Add widgets from the panel on the left onto the canvas
4. Adjust properties in the panel on the right
5. Switch to the **Code** tab to view and edit the generated Python
6. Click **Run** to launch your application

Full widget guides and example projects are available at **[dragtk.com/learn](https://dragtk.com/learn)**.

---

## Contributing

Contributions are welcome. If you find a bug or have a feature suggestion:

- **Bug reports** — open an [Issue](../../issues) with as much detail as possible: what you were doing, what you expected, what happened, and your Python version
- **Pull requests** — fork the repository, make your changes on a new branch, and open a PR with a clear description of what you've changed and why
- **General feedback** — [support@dragtk.com](mailto:support@dragtk.com)

There are no strict contribution guidelines at this stage — the project is small and informal. Clear, readable code and a brief explanation of the change is all that's needed.

---

## Licence

MIT — see [LICENSE](LICENSE) for the full text.

Free to use, modify, and redistribute. No attribution required, though it's always appreciated.

---

## Links

- Website: [dragtk.com](https://dragtk.com)
- Lessons & tutorials: [dragtk.com/learn](https://dragtk.com/learn)
- Bug reports & support: [support@dragtk.com](mailto:support@dragtk.com)
