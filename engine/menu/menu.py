from hardware import Lcd
from shared import Worker
from time import sleep
from plotter import plot

class MenuItem(Worker):
    """ Base class for MenuItems. """
    def __init__(self, parent, header, select=None, activated=None):
        super(MenuItem, self).__init__()
        self._items = []
        self._parent = parent
        self.header = header
        self._select = select
        self._activated = activated

    @property
    def menu(self):
        """ Return top-level menu. """
        item = self
        while item.parent != None:
            item = item.parent
        return item

    @property
    def parent(self):
        """ Return parent item; None for top-level menu. """
        return self._parent

    @property
    def items(self):
        """ Return child items in this menu. """
        return self._items

    @property
    def header(self):
        """ Return text to display. """
        return self._header

    @header.setter
    def header(self, value):
        """ Set text to display. Notify top-level menu of changed text. """
        self._header = value
        if self != self.menu:
            if self.menu.current_item == self:
                self.menu.item_header_changed()

    @property
    def select(self):
        """ Return method called when user selects this MenuItem. """
        return self._select
 
    @property
    def next(self):
        """ Return next MenuItem in this menu level. """
        index = self.parent.items.index(self)
        if index < (len(self.parent.items) - 1):
            return self.parent.items[index+1]
        else:
            return None
    @property
    def previous(self):
        """ Return previous MenuItem in this menu level.  """
        index = self.parent.items.index(self)
        if index > 0:
            return self.parent.items[index-1]
        else:
            return None

    def add_item(self, header, select=None, activated=None):
        """
        Add a MenuItem to this Menu with 
        specified header and callback method.
        """
        item = MenuItem(self, header, select, activated)
        self.items.append(item)
        return item

    @property
    def activated(self):
        """
        Invoked when this item becomes
        the active item in top-level menu.
        """
        return self._activated

class Menu(MenuItem):
    """ Base class for top-level menu. """
    def __init__(self):
        super(Menu, self).__init__(None, None)
        self._current = None

    @property
    def current_item(self):
        """ Return the currently active MenuItem. """
        return self._current

    @current_item.setter
    def current_item(self, value):
        """
        Set the currently active MenuItem.
        Notify inheriting class of changing value.
        """
        self.current_changing(value)
        self._current = value
        if value != None and value.activated != None:
            value.activated()
        self.current_changed()

    def current_changing(self, new_item):
        """
        Notify inherited class that the active 
        menu item is about to be changed.
        """
        pass

    def current_changed(self):
        """
        Notify inherited class that the active
        menu item has been changed.
        """
        pass

    def item_header_changed(self):
        """ 
        Notification about changed item
        sent by the active MenuItem.
        """
        pass

    def _run(self):
        """ Do nothing by default """
        pass
   
class LcdMenu(Menu):
    """ Menu implementation using Adafruit LCD Display. """
    def __init__(self):
        super(LcdMenu, self).__init__()
        self._lcd = Lcd()

    @property
    def lcd(self):
        """ Return the LCD display instance. """
        return self._lcd

    @property
    def message(self):
        """ Return the message on the display. """
        return self._message

    @message.setter
    def message(self, value):
        """
        Set the message on the display.
        Include markers showing possible actions
        which can be performed using buttons.
        """
        self.lcd.clear()
        if self.current_item != None:
            if self.current_item.previous != None:
                # User can move upwards in the menu
                self.lcd.message('o')
            if self.current_item.next != None:
                # User can move downwards in the menu
                self.lcd.setCursor(0,1)
                self.lcd.message('o')
            if self.current_item.parent != self:
                # User can move to upper menu level
                self.lcd.setCursor(13,0)
                self.lcd.message('<')
            if self.current_item.select != None:
                # User can press the Select button to perform action
                self.lcd.setCursor(14,0)
                self.lcd.message('*')
            if len(self.current_item.items) > 0:
                # User can move to sub-menu
                self.lcd.setCursor(15,0)
                self.lcd.message('>')
        if len(value) > 0:
            # split the menu to lines and output text into correct position
            lines = value.split('\n')
            for i, line in enumerate(lines):
                self.lcd.setCursor(2,i)
                self.lcd.message(line)
        
    def item_header_changed(self):
        # Notification from the current item
        self.message = self.current_item.header
    
    def _run(self):
        """ 
        Poll for buttons and move in the menu 
        or invoke command as defined in the MenuItem.select callback.
        """
        lcd = self.lcd
        lcd.begin(16, 2)
        lcd.clear()
        lcd.message(self.header)
        if len(self.items) > 0: 
            self.current_item = self.items[0]

        # Method to call on button press
        callbacks = {lcd.SELECT: self.select,
                   lcd.UP: self.up,
                   lcd.DOWN: self.down,
                   lcd.LEFT: self.left,
                   lcd.RIGHT: self.right}

        # Status of each button to sense raising edge
        states = {lcd.SELECT: False,
                   lcd.UP: False,
                   lcd.DOWN: False,
                   lcd.LEFT: False,
                   lcd.RIGHT: False}

        prev = -1
        while self._should_stop == False:
            for b in states.keys():
                if lcd.buttonPressed(b):
                    # Detect raising edge
                    if states[b] == False:
                        callbacks[b]()
                    states[b] = True
                else:
                    states[b] = False

            sleep(0.25)
        lcd.clear()
        lcd.stop()

    def current_changing(self, value):
        """
        Current item is about to change.
        Stop current MenuItem.
        """
        if self.current_item != None:
            if self.current_item.is_running:
                self.current_item.stop()
    
    def current_changed(self):
        """
        Current item has been changed.
        Update header and start current item.
        """
        self.message = self.current_item.header            
        self.current_item.start()

    def select(self):
        """
        Select button has been pressed.
        Invoke the menu callback, if defined.
        """
        if self.current_item == None:
            return
        else:
            if self.current_item.select == None:
                return
            else:
                self.current_item.select()

    def up(self):
        """
        Up button has been pressed.
        Move upwards in the menu.
        """
        if self.current_item == None:
            return
        else:
            if self.current_item.previous == None:
                return                
            else:
                self.current_item = self.current_item.previous

    def down(self):
        """
        Down button has been pressed.
        Move downwards in the menu.
        """
        if self.current_item == None:
            return
        else:
            if self.current_item.next == None:
                return
            else:
                self.current_item = self.current_item.next

    def left(self):
        """
        Left button has been pressed.
        Move inwards in the menu.
        """
        if self.current_item == None:
            return
        else:
            if self.current_item.parent == self:
                return
            else:
                self.current_item = self.current_item.parent

    def right(self):
        """
        Right button has been pressed.
        Move outwards in the menu.
        """
        if self.current_item == None:
            return
        else:
            if len(self.current_item.items) == 0:
                return
            else:
                self.current_item = self.current_item.items[0]

