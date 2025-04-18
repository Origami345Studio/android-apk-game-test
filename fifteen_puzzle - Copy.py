import random
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window

class SlidePuzzle(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.padding = 10
        self.spacing = 10

        # Initialize alpha parameters
        self.alpha = 0
        self.alpha_increment = 1
        self.fib_cost = 1

        # --- Top: Time display ---
        self.top_time_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.time_label = Label(text='Time: 0.00s', font_size=16, size_hint_x=0.5)
        self.best_time_label = Label(text='Best: --', font_size=16, size_hint_x=0.5)
        self.top_time_layout.add_widget(self.time_label)
        self.top_time_layout.add_widget(self.best_time_label)
        self.add_widget(self.top_time_layout)

        # --- Middle: Puzzle square container ---
        self.main_section = BoxLayout(orientation='vertical', size_hint=(1, 0.6))
        self.add_widget(self.main_section)

        # Create centered puzzle container
        self.puzzle_container = BoxLayout(size_hint=(0.9, None))  # Reduced from 1 to 0.9 for padding
        self.puzzle_container.bind(width=self.update_puzzle_height)
        
        # Add centering BoxLayout
        center_layout = BoxLayout(orientation='horizontal')
        center_layout.add_widget(BoxLayout(size_hint_x=0.05))  # Left padding
        center_layout.add_widget(self.puzzle_container)
        center_layout.add_widget(BoxLayout(size_hint_x=0.05))  # Right padding
        
        self.main_section.add_widget(center_layout)

        # Puzzle grid inside container
        self.puzzle_grid = GridLayout(cols=3, size_hint=(1, 1))
        self.puzzle_container.add_widget(self.puzzle_grid)

        # Win message
        self.message_label = Label(text='', size_hint=(1, None), height=30, font_size=16)
        self.main_section.add_widget(self.message_label)

        # Reset button (centered and wider)
        self.reset_container = BoxLayout(size_hint_y=None, height=50)
        center_box = BoxLayout(orientation='horizontal', size_hint_x=0.8)  # Container for centered button
        self.reset_button = Button(
            text='Reset',
            size_hint=(1, 0.8),  # Make button take 80% of container width
            pos_hint={'center_x': 0.5, 'center_y': 0.5}  # Center the button
        )
        self.reset_button.bind(on_press=self.reset_puzzle)
        center_box.add_widget(self.reset_button)
        self.reset_container.add_widget(BoxLayout(size_hint_x=0.1))  # Left padding
        self.reset_container.add_widget(center_box)
        self.reset_container.add_widget(BoxLayout(size_hint_x=0.1))  # Right padding
        self.main_section.add_widget(self.reset_container)

        # --- Alpha controls at bottom ---
        self.alpha_layout = BoxLayout(orientation='vertical', size_hint_y=0.3)
        self.add_widget(self.alpha_layout)

        # Alpha label
        self.alpha_label = Label(
            text=f"Alpha (α): {self.alpha}",
            font_size=16,
            size_hint_y=None,
            height=30
        )
        self.alpha_layout.add_widget(self.alpha_label)

        # Scrollable buttons container
        self.alpha_scroll = ScrollView(size_hint=(1, 1))
        self.alpha_buttons_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=5
        )
        self.alpha_buttons_container.bind(minimum_height=self.alpha_buttons_container.setter('height'))
        self.alpha_scroll.add_widget(self.alpha_buttons_container)

        # Upgrade button
        self.upgrade_trigger_button = Button(
            text=f"Upgrade Alpha (cost: {self.fib_cost})",
            size_hint_y=None,
            height=40
        )
        self.upgrade_trigger_button.bind(on_press=self.upgrade_alpha)
        self.alpha_buttons_container.add_widget(self.upgrade_trigger_button)

        # Additional buttons
        for i in range(9):
            btn = Button(
                text=f"Alpha Button {i+2}",
                size_hint_y=None,
                height=40
            )
            self.alpha_buttons_container.add_widget(btn)

        # Add scroll to layout
        self.alpha_layout.add_widget(self.alpha_scroll)

        # Initialize game state
        self.tiles = []
        self.empty_pos = (2, 2)
        self.start_time = None
        self.elapsed_time = 0
        self.clock_event = None
        self.first_move_made = False
        self.best_time = None

        self.create_tiles()
        self.shuffle_tiles()
        self.start_timer()

    def update_puzzle_height(self, instance, value):
        # Keep the puzzle square shape
        self.puzzle_container.height = self.puzzle_container.width

    def create_tiles(self):
        self.puzzle_grid.clear_widgets()
        self.tiles = []
        numbers = list(range(1, 9))
        for i in range(3):
            row = []
            for j in range(3):
                if (i, j) == self.empty_pos:
                    btn = Button(text='', font_size=40)
                else:
                    num = numbers.pop(0)
                    btn = Button(text=str(num), font_size=40)
                btn.bind(on_press=self.on_tile_press)
                self.puzzle_grid.add_widget(btn)
                row.append(btn)
            self.tiles.append(row)

    def shuffle_tiles(self):
        tile_numbers = list(range(1, 9)) + [0]
        while True:
            random.shuffle(tile_numbers)
            if self.is_solvable(tile_numbers):
                break
        index = 0
        for i in range(3):
            for j in range(3):
                num = tile_numbers[index]
                btn = self.tiles[i][j]
                if num == 0:
                    btn.text = ''
                    self.empty_pos = (i, j)
                else:
                    btn.text = str(num)
                index += 1
        self.message_label.text = ''
        self.reset_timer()
        self.first_move_made = False
        self.start_timer()

    def on_tile_press(self, button):
        if self.message_label.text != '':
            return
        # Find pressed tile position
        tile_pos = None
        for i in range(3):
            for j in range(3):
                if self.tiles[i][j] == button:
                    tile_pos = (i, j)
                    break
            if tile_pos:
                break
        if self.is_adjacent(tile_pos, self.empty_pos):
            if not self.first_move_made:
                self.start_time = time.time()
                self.first_move_made = True
                self.cancel_clock()
                self.clock_event = Clock.schedule_interval(self.update_time, 0.01)
            self.move_tile(tile_pos)
            if self.check_win():
                self.on_win()

    def is_adjacent(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

    def move_tile(self, tile_pos):
        i, j = tile_pos
        ei, ej = self.empty_pos
        tile_btn = self.tiles[i][j]
        empty_btn = self.tiles[ei][ej]
        empty_btn.text, tile_btn.text = tile_btn.text, empty_btn.text
        self.empty_pos = (i, j)

    def check_win(self):
        expected = [str(n) for n in range(1, 9)] + ['']
        current = []
        for i in range(3):
            for j in range(3):
                current.append(self.tiles[i][j].text)
        return current == expected

    def on_win(self):
        self.message_label.text = 'Congratulations! You solved it!'
        self.cancel_clock()
        total_time = self.elapsed_time
        if self.best_time is None or total_time < self.best_time:
            self.best_time = total_time
            self.best_time_label.text = f'Best: {self.best_time:.2f}s'
        self.alpha += self.alpha_increment
        self.alpha_label.text = f"Alpha (α): {self.alpha}"
        self.update_timer(self.elapsed_time)

    def is_solvable(self, tile_numbers):
        inv_count = 0
        nums = [num for num in tile_numbers if num != 0]
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] > nums[j]:
                    inv_count += 1
        return inv_count % 2 == 0

    def reset_puzzle(self, *args):
        self.create_tiles()
        self.shuffle_tiles()

    def reset_timer(self):
        self.elapsed_time = 0
        self.update_timer(0)
        self.cancel_clock()
        self.start_time = None
        self.first_move_made = False

    def start_timer(self):
        if self.first_move_made:
            return
        self.start_time = None
        self.cancel_clock()

    def cancel_clock(self):
        if self.clock_event:
            self.clock_event.cancel()
            self.clock_event = None

    def update_time(self, dt):
        if self.start_time is None:
            return
        self.elapsed_time = time.time() - self.start_time
        self.update_timer(self.elapsed_time)

    def update_timer(self, elapsed):
        self.time_label.text = f'Time: {elapsed:.2f}s'

    def upgrade_alpha(self, instance=None):
        # Triggered by the first button in scroll view
        if self.alpha >= self.fib_cost:
            self.alpha -= self.fib_cost
            self.alpha_increment += 1
            self.update_fib_cost()
            self.alpha_label.text = f"Alpha (α): {self.alpha}"
            self.upgrade_trigger_button.text = f"Upgrade Alpha (cost: {self.fib_cost})"

    def update_fib_cost(self):
        a, b = 1, 1
        for _ in range(self.alpha_increment):
            a, b = b, a + b
        self.fib_cost = a

class SlidePuzzleApp(App):
    def build(self):
        # Set window size for mobile aspect ratio (16:9)
        Window.size = (360, 640)
        return SlidePuzzle()

if __name__ == '__main__':
    SlidePuzzleApp().run()