#!/usr/bin/env python3
from collections import OrderedDict
import datetime
import os
import re
import shutil
import sys

from peewee import *
from print_utils import inputw, printw, wraptext


db = SqliteDatabase('timesheets.db')

DATEFORMAT = "%m/%d/%Y"


class Entry(Model):
    date = DateField(default=datetime.date.today)
    employee_name = CharField(max_length=100)
    task_name = CharField(max_length=100)
    minutes_spent = IntegerField()
    notes = TextField()

    class Meta:
        database = db

    def __str__(self):
        try:
            terminal_width = min(
                shutil.get_terminal_size((80, 20)).columns - 10, 120)
        except OSError:
            terminal_width = 70
        out = ""
        if self.date:
            out += "Date: {}\n".format(self.date.strftime(DATEFORMAT))
        if self.employee_name:
            out += "Employee: {}\n".format(self.employee_name)
        if self.task_name:
            out += "Task Name: {}\n".format(self.task_name)
        if self.minutes_spent:
            out += "Minutes Spent: {}\n".format(self.minutes_spent)
        if self.notes:
            out += '\n'
            out += "NOTES".center(terminal_width)
            out += '\n\n'
            wrapped_notes = wraptext(self.notes)
            out += '{}'.format(wrapped_notes)
        return out


def initialize():
    db.connect()
    db.create_tables([Entry], safe=True)


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def menu_loop():
    """Show the main menu"""
    action = None

    while action != 'q':
        clear()
        for key, value in menu.items():
            print('{}) {}'.format(key, value.__doc__))
        print('q) Exit program')
        action = input('Action: ').lower().strip()

        if action in menu:
            try:
                menu[action]()
            except EOFError:
                inputw("Error occurred entering notes. Try running the application "
                       "in a different terminal program.")


def get_employee_name(default=""):
    name = input("Employee Name: ") or default
    if not name:
        print("Employee name cannot be blank.")
        return get_employee_name()
    return name


def get_task_name(default=""):
    task_name = input("Task Name: ") or default
    if not task_name:
        print("Task name cannot be blank.")
        return get_task_name()
    return task_name


def get_minutes(default=""):
    minutes_spent = input("Minutes Spent: ") or default
    if not minutes_spent:
        print("Minutes spent cannot be blank.")
        return get_minutes()
    try:
        minutes_spent = int(minutes_spent)
    except ValueError:
        print("Minutes spent must be entered as a whole number.")
        return get_minutes()
    else:
        if minutes_spent >= 0:
            return minutes_spent
        else:
            print("Minutes spent on a task must be a positive integer.")
            return get_minutes()


def get_notes():
    eof_character = 'CTRL+Z and then Enter' if os.name == 'nt' else 'CTRL+D'
    message = "Enter any additional notes. Press {} when finished.\n"
    print(message.format(eof_character))
    notes = sys.stdin.read().rstrip()
    return notes


def add_entry():
    """Add a new entry"""
    try:
        terminal_width = min(
            shutil.get_terminal_size((80, 20)).columns - 10, 120)
    except OSError:
        terminal_width = 70
    employee_name = get_employee_name()
    task_name = get_task_name()
    minutes_spent = get_minutes()
    has_notes = input("Would you like to enter notes? [Yn] ").lower()
    if has_notes != 'n':
        notes = get_notes()
    else:
        notes = ""
    if input("Would you like to save this entry? [Yn]: ").lower() != 'n':
        Entry.create(employee_name=employee_name,
                     task_name=task_name,
                     minutes_spent=minutes_spent,
                     notes=notes)
    else:
        clear()
        print("\n" + "ENTRY ABORTED =(".center(terminal_width) + "\n")
        msg1 = ("Entry aborted. Please enter the time you wasted entering a "
                "timesheet entry that you weren't even going to bother to save "
                "into a new timesheet entry. People like you are the reason "
                "this company is dying. But don't worry about it. I don't "
                "want to stress you out. You've got more important things to "
                "think about than the time and resources you waste while you're "
                "at work.")
        msg2 = ("Press Enter to acknowledge your ingratitude for all of " 
                "the opportunities we have so painstakingly given to you and "
                "return to the main menu...")
        printw(msg1)
        print()
        inputw(msg2)


def view_entries(entries=None):
    """View previous entries"""
    if not entries:
        entries = Entry.select()
    i = 0
    while i < len(entries):
        clear()
        print(entries[i])
        print()
        print('='*50)
        print('n) Next entry')
        print('p) Previous entry')
        print('e) Edit entry')
        print('d) Delete entry')
        print('q) Return to main menu')

        next_action = input("Action: ").lower()
        if next_action == 'q':
            break
        elif next_action == 'n':
            i += 1
        elif next_action == 'p':
            i -=1
            if i < 0:
                input("\nThere are no previous entries. Press Enter...")
                i += 1
        elif next_action == 'e':
            edit_entry(entries[i])
        elif next_action == 'd':
            delete_entry(entries[i])
            # Clone to force removal of deleted item.
            entries = entries.clone()
    else:
        if len(entries) == 0:
            input("\nNo entries found. Press Enter to return to menu...")
        else:
            input("\nFinal entry. Press Enter to return to menu...")


def get_date(input_msg, ignore=False):
    pattern = r'\d{2}/\d{2}/\d{4}'
    date_string = input(input_msg)
    if re.match(pattern, date_string):
        return datetime.datetime.strptime(date_string, DATEFORMAT).date()
    else:
        if ignore:
            return ""
        else:
            print("Date must be in MM/DD/YYYY format.")
            return get_date(input_msg)

def find_entry():
    """Find a previous entry"""
    if not Entry.select():
        input("No entries currently exist. Press Enter to return to menu...")
        return

    def list_of_employees(query=None):
        clear()
        if query:
            entries = Entry.select().where(Entry.employee_name.contains(query))
        else:
            entries = Entry.select(Entry.employee_name)
        employees = sorted(set(entry.employee_name for entry in entries))
        employee_list = list(enumerate(employees, 1))
        for key, employee in employee_list:
            print("{}) {}".format(key, employee))
        print("\n(Enter a partial name to refine search.)")
        choice = input("Selection: ")
        if not choice:
            clear()
            input("Selection cannot be blank. To see entries for all employees, "
                  "press v on the main menu. Press Enter to continue...")
            return list_of_employees()

        try:
            choice = int(choice) - 1
        except ValueError:
            # Assume non-numeric value was passed to enter name directly.
            entries = Entry.select().where(Entry.employee_name.contains(choice))
            employees = sorted(set(entry.employee_name for entry in entries))
            if entries:
                if len(employees) > 1:
                    return list_of_employees(choice)
                else:
                    return entries
            else:
                input("{} not found. Press Enter to continue.".format(choice))
                return list_of_employees()
        else:
            try:
                employee = employees[choice]
            except IndexError:
                input("Valid entries are between 1 and {}. "
                      "Press Enter to continue.".format(len(employees)))
                return list_of_employees()
            else:
                entries = Entry.select().where(Entry.employee_name==employee)
                return entries

    def employee_name():
        clear()
        printw("Enter a partial or full name to view matching employees with timesheet entries.")
        query = input("Query: ")
        entries = Entry.select().where(
            Entry.employee_name.contains(query)).order_by(Entry.employee_name)
        if not entries:
            clear()
            msg = ("We're sorry. No employees with that name exist. Perhaps "
                   "this person you're looking for never existed at all. Have "
                   "you had a psych evaluation recently? We provide excellent "
                   "psychological care on the first floor.")
            printw(msg)
            input("\nIn any case, please press Enter to continue...")
            return
        else:
            employees = sorted(set(entry.employee_name for entry in entries))
            if len(employees) > 1:
                return list_of_employees(query)
            else:
                return Entry.select().where(Entry.employee_name==employees[0])

    def show_dates():
        clear()
        print("Dates with entries:\n")
        entries = Entry.select(Entry.date).order_by(Entry.date)
        dates = sorted(set(entry.date.strftime(DATEFORMAT) for entry in entries))
        for entry_date in dates:
            print(entry_date)

    def date():
        show_dates()
        entry_date = get_date("\nEnter a date to view records: ")
        entries = Entry.select().where(Entry.date==entry_date)
        if entries:
            return entries
        else:
            input("No entries found for that date. Press Enter to return...")

    def range_of_dates():
        show_dates()
        start_date = get_date("\nEnter a start date: ")
        end_date = get_date("Enter an end date: ")
        if start_date > end_date:
            print("End date must be after start date. Press Enter...")
            return range_of_dates()
        entries = Entry.select().where(Entry.date.between(start_date, end_date))
        if entries:
            return entries
        else:
            input("No entries found for that date range. Press Enter...")

    def minutes_spent():
        clear()
        try:
            time_spent = int(input("Minutes Spent: "))
        except ValueError:
            print("Minutes must be entered as a whole number.")
            return minutes_spent()
        else:
            entries = Entry.select().where(Entry.minutes_spent==time_spent)
            if entries:
                return entries
            else:
                input("No entries found with those criteria. Press Enter...")

    def search_term():
        clear()
        query = input("Search term: ")
        entries = Entry.select().where((Entry.notes.contains(query))|
                                       (Entry.task_name.contains(query)))
        if entries:
            return entries
        else:
            input("No entries containing that search term were found. Press Enter...")

    options = OrderedDict([
        ('1', list_of_employees),
        ('2', employee_name),
        ('3', date),
        ('4', range_of_dates),
        ('5', minutes_spent),
        ('6', search_term)
    ])

    clear()
    print("Find by:\n")
    for key, value in options.items():
        print('  {}) {}'.format(key, value.__name__.capitalize().replace('_', ' ')))
    print('  q) Return to main menu')

    option = input("\nOption: ")
    if option.lower() == 'q':
        return
    if option in options:
        entries = options[option]()
        if entries:
            view_entries(entries)


def delete_entry(entry):
    """Delete an entry"""
    if input("\nAre you sure you want to delete this? [Yn] ").lower() != 'n':
        entry.delete_instance()
        input("\nEntry deleted. Press Enter to continue...")


def edit_entry(entry):
    """Edit entry"""
    print("\nPress enter after making changes. Leave fields you do not wish to change blank.")
    date = get_date("Date: ", True)
    employee_name = get_employee_name(entry.employee_name)
    task_name = get_task_name(entry.task_name)
    minutes_spent = get_minutes(entry.minutes_spent)
    notes = ""
    if input("Would you like to update your notes? [Yn] ").lower() != 'n':
        notes = get_notes()

    if input("Would you like to save changes? [Yn] ").lower() != 'n':
        entry.date = date or entry.date
        entry.employee_name = employee_name or entry.employee_name
        entry.task_name = task_name or entry.task_name
        entry.minutes_spent = minutes_spent or entry.minutes_spent
        entry.notes = notes or entry.notes
        entry.save()
    else:
        input("Changes not saved. Press Enter to continue...")


menu = OrderedDict([
    ('a', add_entry),
    ('v', view_entries),
    ('f', find_entry)
])


if __name__ == '__main__':
    testing = True
    initialize()
    if testing and not Entry.select():
        from testdata import data
        for entry in data:
            date = datetime.datetime.strptime(entry['date'], DATEFORMAT).date()
            notes = entry['notes']
            try:
                Entry.create(date=date,
                             employee_name=entry['employee_name'],
                             task_name=entry['task_name'],
                             minutes_spent=entry['minutes_spent'],
                             notes=entry['notes'])
            except Exception:
                printw("Something seems to have gone wrong. What did you do? "
                       "I'm going to let you take some time to really think "
                       "about what you've done, because it obviously couldn't "
                       "possibly have been my fault.")
    try:
        menu_loop()
    except EOFError:
        print('EOF Error. Try running the application in a different terminal program.')
