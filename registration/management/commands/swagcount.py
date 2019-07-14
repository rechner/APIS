from collections import Counter
from django.core.management.base import BaseCommand, CommandError


from registration.models import *

flatten = lambda l: [item for sublist in l for item in sublist]

shirt_sizes = { str(size.id) : size.name for size in ShirtSizes.objects.filter() }

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
    badges = [ b for b in Badge.objects.filter(event=event) if b.paidTotal > 0 ]
    items = [ b.getOrderItems() for b in badges ]
    all_options = flatten([ b.getOptions() for b in flatten(items) ])
    counted = Counter([ (o.option.optionName, o.option.optionExtraType, o.optionValue) for o in all_options ])

    print("item,extra,count")
    for k in counted:
        value = k[2]
        if k[1] == 'ShirtSizes':
            value = shirt_sizes[k[2]]
        print("{0},{1},{2}".format(k[0], value, counted[k]))

class Command(BaseCommand):
    def handle(self, **options):
        main()
        
        
if __name__ == "__main__":
    main()
