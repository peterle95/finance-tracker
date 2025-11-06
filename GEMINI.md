# GEMINI.md

## Project Overview

This project is a personal finance tracker with a graphical user interface (GUI) built using Python's `tkinter` library. It allows users to manage their finances by tracking income and expenses, categorizing transactions, setting budgets, and generating reports. The application uses `matplotlib` and `numpy` to create visualizations of financial data. All data is stored locally in a `finance_data.json` file.

## Building and Running

### Dependencies

The project requires the following Python libraries:

*   `tkinter` (usually included with Python)
*   `matplotlib`
*   `numpy`
*   `python-dateutil`

You can install the dependencies using pip:

```bash
pip install matplotlib numpy python-dateutil
```

### Running the Application

To run the finance tracker, execute the following command in your terminal:

```bash
python finance-tracker.py
```

## Development Conventions

*   **Code Style:** The code follows standard Python conventions (PEP 8).
*   **Data:** The application state is saved in `finance_data.json`.
*   **GUI:** The user interface is built with `tkinter`.
*   **Charting:** Reports and visualizations are generated using `matplotlib`.
*   **Modularity:** The application is structured within a single `FinanceTracker` class.
