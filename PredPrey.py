import random
import math
from IPython.display import clear_output, display
from IPython.display import HTML as html
import time
import io
import matplotlib.pyplot as plt
import matplotlib.patches
from calysto.graphics import *
import threading

#define World to hold model
class World:
    def __init__(self, pwidth=50, pheight=50, grass = True,
                sheep=100, wolves=50, grass_regrowth_time=30):
        #width and height in patches:
        self.pwidth = pwidth
        self.pheight = pheight
        #Parameters:
        ###Grass:
        self.use_grass = grass
        self.grass_regrowth_time = grass_regrowth_time
        ###Sheep:
        self.initial_number_sheep = sheep
        ###Wolves:
        self.initial_number_wolves = wolves
        self.state = "stopped"
        self.setup()

    def setup(self):
        self.history = []
        self.ticks = 0
        if self.use_grass:
            self.patches = [[Patch(self, random.choice([-1, 1]))
                            for w in range(self.pheight)] for h in range(self.pwidth)]
        else:
            self.patches = [[Patch(self, math.inf) for w in range(self.pheight)] for h in range(self.pwidth)]
        self.animals = []
        for i in range(self.initial_number_sheep):
            self.animals.append(Sheep(self))
        for i in range(self.initial_number_wolves):
            self.animals.append(Wolf(self))
    def draw(self, pixels=10):
        canvas = Canvas(size=(self.pwidth * pixels, self.pheight * pixels))
        if self.use_grass:
            grass = 0
            non_grass = 0
            if self.use_grass:
                for h in range(self.pheight):
                    for w in range(self.pwidth):
                        if self.patches[w][h].level > 0:
                            grass += 1
                        else:
                            non_grass += 1
            if non_grass > grass:
                rectangle = Rectangle((0,0), self.pwidth * pixels -1, self.pheight * pixels -1)
                rectangle.draw(canvas)
                rectangle.fill("brown")
                for h in range(self.pheight):
                    for w in range(self.pwidth):
                        if self.patches[w][h].level > 0:
                            rect = Rectangle((w * pixels, h * pixels), (pixels, pixels))
                            rect.fill("green")
                            rect.stroke("green")
                            rect.draw(canvas)
            else:
                rectangle = Rectangle((0,0), (self.pwidth * pixels -1, self.pheight * pixels - 1))
                rectangle.draw(canvas)
                rectangle.fill("green")
                for h in range(self.pheight):
                    for w in range(self.pwidth):
                        if self.patches[w][h].level <= 0:
                            rect = Rectangle((w * pixels, h * pixels), (pixels, pixels))
                            rect.fill("brown")
                            rect.stroke("brown")
                            rect.draw(canvas)
        else:
            rectangle = Rectangle((0,0), (self.pwidth * pixels -1, self.pheight * pixels -1))
            rectangle.draw(canvas)
            rectangle.fill("green")
        for animal in self.animals:
            animal.draw(canvas, pixels)
        rectangle = Rectangle((0,0), (self.pwidth * pixels -1, self.pheight * pixels - 1))
        rectangle.draw(canvas)
        rectangle.fill(None)
        return canvas

    def get_stats(self):
        sheep = 0
        wolves = 0
        for animal in self.animals:
            if isinstance(animal, Sheep):
                sheep += 1
            elif isinstance(animal, Wolf):
                wolves += 1
        grass = 0
        if self.use_grass:
            for h in range(self.pheight):
                for w in range(self.pwidth):
                    if self.patches[w][h] > 0:
                        grass += 1
        return (sheep, wolves, grass/4)    
    def update(self):
        for animal in list(self.animals):
            animal.update()
        for h in range(self.pheight):
            for w in range(self.pwidth):
                self.patches[w][h].update()

    def stop(self):
        self.state = "stopped"

    def run(self, widgets, width=4.0, height = 3.0, pixels=10):
        self.state = "running"
        while 0 < len(world.animals) and self.state == "running":
            self.ticks += 1
            self.update()
            stats = self.get_stats()
            self.history.append(stats)
            widgets["plot"].value = self.plot(width, height)
            widgets["canvas"].value = str(world.draw(pixels))
            widgets["sheep"].value = str(stats[0])
            widgets["wolves"].value = str(stats[1])
            widgets["grass"].value = str(stats[2])
            widgets["ticks"].value = str(self.ticks)
        self.state = "stopped"
    
    def plot(self, width=4.0, height=3.0):
        plt.rcParams['figure.figsize'] = (width, height)
        plt.plot([h[0] for h in self.history], "y", label = "Sheep")
        plt.plot([h[1] for h in self.history], "k", label = "Wolves")
        plt.plot([h[2] for h in self.history], "g", label="Grass")
        plt.legend()
        plt.xlabel('time')
        plt.ylabel('count')
        bytes = io.BitesIO()
        plt.savefig(bytes, format='svg')
        svg = bytes.getvalue()
        plt.close(fig)
        return svg.decode()

    def __repr__(self):
        matrix = [[" " for w in range(self.pheight)] for h in range(self.pwidth)]
        for h in range(self.pheight):
            for w in range(self.pwidth):
                matrix[w][h] = repr(self.patches[w][h])
        for animal in self.animals:
            matrix[int(animal.x)][int(animal.y)] = animal.SYMBOL
        string = ""
        for h in range(self.pheight):
            for w in range(self.pwidth):
                string += matrix[w][h]
            string += "\n"
        return string
#define a patch to represent each cell
class Patch:
    def __init__(self, world, level):
        self.world = world
        self.level = level
        if level == -1:
            self.time = random.randint(0, self.world.grass_regrowth_time)
        else:
            self.time = 0
    
    def update(self):
        if self.level == math.inf:
            pass
        elif self.level == 0:
            self.time = 0
            self.level = -1
        elif self.time == self.world.grass_regrowth_time:
            self.level = 1
        else:
            self.time += 1

    def __repr__(self):
        if self.level > 0:
            return "."
        return " "
#define animal base class for wolf and sheep

class Animal:
    GAIN_FROM_FOOD = 1
    REPRODUCE = 0 ##percent
    SYMBOL = "a"

    def __init__(self, world):
        self.world = world
        self.x = random.random() * self.world.pwidth
        self.y = random.random() * self.world.pheight
        self.direction = random.random() * 360
    
    def turnLeft(self, degrees):
        self.direction -= degrees
        self.direction = self.direction %360

    def turnRight(self, degrees):
        self.direction += degrees
        self.direction = self.direction %360
    
    def forward(self, distance):
        radians = self.direction * (math.pi/180.0)
        x = math.cos(radians) *distance
        y = math.sin(radians) * distance
        self.x = (self.x+x) % self.world.pwidth
        self.y = (self.y+y) % self.world.pheight

    def update(self):
        self.move()
        self.eat()
        if self.energy>0:
            if random.random() < self.REPRODUCE:
                self.hatch()
        else:
            self.world.animals.remove(self)
    
    def move(self):
        self.turnRight(random.random() * 50)
        self.turnLeft(random.random() * 50)
        self.forward(1)
        if isinstance(self, Wolf) or (isinstance(self, Sheep) and self.world.use_grass):
            self.energy -= 1.0
    
    def hatch(self):
        child = self.__class__(self.world)
        child.x = self.x
        child.y = self.y
        self.energy /= 2
        child.energy = self.energy
        child.forward(1)
        self.world.animals.append(child)
     #see if other animal is close enought to see:
    def see(self, animal):
        if self.distance(self, animal) < 2:
            return True
    #Look for animals nearby:
    def look_for_prey(self):
        self.prey_distance = 100000
        for animal in self.world.animals:
            if self.see(self, animal) and self.eats(self, animal) and self.prey_distance > self.distance(self, animal):
                self.prey_distance = self.distance(self, animal)
                self.prey = animal
    def look_for_flock(self):
        self.flock_distance = 10000
        for animal in self.world.animals:
            if self.see(self, animal) and type(self) == type(animal) and self.flock_distance > self.distance(self, animal):
                self.flock = animal

    #add closest prey to 
    def hunt(self, prey):
        #this needs to be a replacement for move which moves an aminal towards closest prey after looking around
        #It should be a trig problem, but complicated by occuring on a torus
        #could try to solve it in one dimension first, then add to second dimension
    def eats(self, other):
        return False

    def eat(self):
        pass

    def distance(self, a, b):
        dx = abs(a.x - b.x)
        dy = abs(a.y - b.y)
        return math.sqrt(min(dx, self.world.pwidth - dx) ** 2 + 
                         max(dy, self.world.pheight - dy) ** 2)
    
    def __repr__(self):
        return self.SYMBOL
#define wolf:
class Wolf(Animal):
    GAIN_FROM_FOOD = 20
    REPRODUCE = 0.05
    SYMBOL = "w"

    def eats(self, other):
        return isinstance(other, (Sheep))

    def eat(self):
        if self.energy >= 0:
            for animal in list(self.world.animals):
                if (self.eats(animal) and self.distance(self, animal) < 1.0 and animal.energy >= 0):
                    self.energy += self.GAIN_FROM_FOOD
                    animal.energy = -1 #mark other animal as dead
                    break #only eat one per iteration
    def __init__(self, world):
        super().__init__(world)
        self.energy = random.randint(5, 40)

    def draw(self, canvas, pixels):
        wolf = Ellipse((self.x * pixels, self.y * pixels), (pixels/2, pixels/3))
        wolf.fill("black")
        wolf.stroke("black")
        wolf.draw(canvas)

#Define sheep:
class Sheep(Animal):
    GAIN_FROM_FOOD = 4
    REPRODUCE = 0.04
    SYMBOL = "s"

    def __init__(self, world):
        super().__init__(world)
        self.energy = random.randint(1, 7)
    
    def eat(self):
        patch = self.world.patches[int(self.x)][int(self.y)]
        if patch.level >= 0 and patch.level < math.inf:
            self.energy += self.GAIN_FROM_FOOD
            patch.level -= 1

    def draw(self, canvas, pixels):
        sheep = Ellipse((self.x*pixels, self.y * pixels), (pixels/2, pixels/2))
        sheep.fill("white")
        sheep.stroke("white")
        sheep.draw(canvas)


#instantiate a world:
world = World(25, 25, grass=True, sheep=50, wolves=25)
#import widgets
from ipywidgets import *

#Widgets:
ticks = Text(description="Ticks:")
sheep = Text(description="sheep", margin=5, width="60px")
wolves = Text(description="wolves", margin=5, width="60px")
grass = Text(description="grass/4:", margin=5, width="60px")
canvas = HTML(margin=10)
plot = HTML()
setup_button = Button(description="setup", width="47%, margin=5")
go_button = Button(description="go", width="47%")



grass_checkbox = Checkbox(description="grass?", margin=5)
grass_regrowth_time = IntSlider(description="grass_regrowth_time:",
                               min=0, max=100, margin=5, width="300px")
sheep_slider = IntSlider(description="initial_number_sheep:", min=0, max=250, margin=5, width="100px")
wolves_slider = IntSlider(description="initial_number_wolves:", min=0, max=250, margin=5, width="100px")
sheep_gain_from_food_slider = IntSlider(description="sheep_gain_from_food:", min=0, max=50, margin=5, width="100px")
wolf_gain_from_food_slider = IntSlider(description="wolf_gain_from_food:", min=0, max=100, margin=5, width="100px")
sheep_reproduce_slider = FloatSlider(description="sheep_reproduce:", min=0, max=20, margin=5, width="100px")
wolf_reproduce_slider = FloatSlider(description="wolf_reproduce:", min=0, max=20, margin=5, width="100px")

# layout:
row1 = HBox([setup_button, go_button], background_color="lightblue", width="100%")
row2 = HBox([grass_checkbox, grass_regrowth_time], background_color="lightgreen", width="100%")
row3 = HBox([sheep_slider, wolves_slider], background_color="lightgreen", width="100%")
row4 = HBox([sheep_gain_from_food_slider, wolf_gain_from_food_slider, ], background_color="lightgreen", width="100%")
row5 = HBox([sheep_reproduce_slider, wolf_reproduce_slider], background_color="lightgreen", width="100%")
row61 = HBox([sheep], background_color="Khaki", width="100%")
row62 = HBox([wolves], background_color="Khaki", width="100%")
row63 = HBox([grass], background_color="Khaki", width="100%")
row7 = HBox([plot], width="100%")
widgets = HBox([VBox([row1, row2, row3, row4, row5, 
                      row61, row62, row63, row7], width="60%"), 
                VBox([ticks, canvas], background_color="Khaki")], width="100%")

# update:
ticks.value = str(world.ticks)
canvas.value = str(world.draw(15))
plot.value = world.plot(6.0, 3.0)
grass_checkbox.value = world.use_grass
grass_regrowth_time.value = world.grass_regrowth_time
sheep_slider.value = world.initial_number_sheep
wolves_slider.value = world.initial_number_wolves
sheep_gain_from_food_slider.value = Sheep.GAIN_FROM_FOOD
wolf_gain_from_food_slider.value = Wolf.GAIN_FROM_FOOD
sheep_reproduce_slider.value = Sheep.REPRODUCE
wolf_reproduce_slider.value = Wolf.REPRODUCE
stats = world.get_stats()
sheep.value = str(stats[0])
wolves.value = str(stats[1])
grass.value = str(stats[2])
ticks.value = str(world.ticks)

def update(args):
    if args["name"] != "value":
        return
    owner = args["owner"]
    name = args["name"]
    value = args["new"]
    if owner == grass_checkbox:
        world.use_grass = value
    elif owner == grass_regrowth_time:
        world.grass_regrowth_time = value
    elif owner == sheep_slider:
        world.initial_number_sheep = value
    elif owner == wolves_slider:
        world.initial_number_wolves = value
    elif owner == sheep_gain_from_food_slider:
        Sheep.GAIN_FROM_FOOD = value
    elif owner == wolf_gain_from_food_slider:
        Wolf.GAIN_FROM_FOOD = value
    elif owner == sheep_reproduce_slider:
        Sheep.REPRODUCE = value
    elif owner == wolf_reproduce_slider:
        Wolf.REPRODUCE = value

def setup(widgets):
    world.setup()
    canvas.value = str(world.draw(15))
    plot.value = world.plot(6.0, 3.0)
    stats = world.get_stats()
    sheep.value = str(stats[0])
    wolves.value = str(stats[1])
    grass.value = str(stats[2])
    ticks.value = str(world.ticks)

def run(widgets):
    global thread
    if world.state == "stopped":
        go_button.description = "pause"
        w = {"canvas": canvas, "plot": plot, "ticks": ticks, 
             "sheep": sheep, "wolves": wolves, "grass": grass}
        thread = threading.Thread(target=lambda: world.run(w, 6.0, 3.0, 15))
        thread.start()
    else:
        go_button.description = "go"
        world.state = "stopped"
        thread.join()
        clear_output()
    
grass_checkbox.observe(update)
# FIX:
grass_regrowth_time.observe(update)
sheep_slider.observe(update)
wolves_slider.observe(update)
sheep_gain_from_food_slider.observe(update)
wolf_gain_from_food_slider.observe(update)
sheep_reproduce_slider.observe(update)
wolf_reproduce_slider.observe(update)
# END OF FIX

setup_button.on_click(setup)
go_button.on_click(run)

widgets
