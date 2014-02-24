from menu import LcdMenu
from menu import MenuItem
from time import sleep

done = False

# Menu callbacks
def foo():
    print "Foo!"

def bar():
    print "Bar!"

def baz():
    print "Baz!"

def exit():
    global done
    done = True

# Custom worker-like menuitem
class MyItem(MenuItem):
    def __init__(self, parent):
        super(MyItem, self).__init__(parent, "Wohoo!")

    def _run(self):
        i = 0
        while self._should_stop == False:
            self.header = "{0}".format(i)
            i+=1
            sleep(1)

    def select(self):
        print "MyItem selected!"


# Top-level menu
menu = LcdMenu()
# MenuItem with text, no action
item = menu.add_item("Foo")
# Child item with 2 lines of text + callback
item.add_item("Bar\nBaz", bar)
# Child item with 2 lines of text + callback
item.add_item("Fubar\nrabuF", baz)
# Custom worker-like MenuItem
menu.items.append(MyItem(menu))
# Top-level menuitem with callback
item = menu.add_item("Exit", exit)

try:
    menu.start()
    while done == False:
        sleep(1)
except KeyboardInterrupt:
    pass
menu.stop()

