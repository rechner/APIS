from collections import Counter
from django.core.management.base import BaseCommand, CommandError


from registration.models import *

flatten = lambda l: [item for sublist in l for item in sublist]

shirt_sizes = { size.id : size.name for size in ShirtSizes.objects.filter() }

def select_event():
    selection = 0
    events = Event.objects.filter()
    print("Select an Event:")
    for e in events:
        print("{0}. {1}".format(selection, e.name))
        selection += 1

    selection = raw_input(" > ")
    if selection == "":
        exit()
    try:
        selection = int(selection)
        return events[selection]
    except ValueError, KeyError:
        print("Invalid selection.")
        return select_event()

def main():
    event = select_event()
    print("Calculating...\n\n")
    counts = { size.id : 0 for size in ShirtSizes.objects.filter() }
    staffs = Staff.objects.filter(event=event)
    for staff in staffs:
        if staff.shirtsize:
            counts[staff.shirtsize.id] += 1

    for size in counts.keys():
        print("{0},{1}".format(shirt_sizes[size], counts[size]))


class Command(BaseCommand):
    def handle(self, **options):
        main()
        
        
if __name__ == "__main__":
    main()
