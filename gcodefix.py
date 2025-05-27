import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent

class DraggableScatter:
    def __init__(self, ax, coords):
        self.ax = ax
        self.coords = coords
        self.scatter = ax.scatter(*zip(*coords), color='blue', s=80, picker=5)
        self.dragging_idx = None

        self.cid_press = self.scatter.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = self.scatter.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = self.scatter.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event: MouseEvent):
        if event.inaxes != self.ax:
            return
        contains, attr = self.scatter.contains(event)
        if contains:
            self.dragging_idx = attr['ind'][0]

    def on_motion(self, event: MouseEvent):
        if self.dragging_idx is None or event.inaxes != self.ax:
            return
        # Update data
        self.coords[self.dragging_idx] = [event.xdata, event.ydata]
        self.scatter.set_offsets(self.coords)
        self.ax.figure.canvas.draw_idle()

    def on_release(self, event: MouseEvent):
        self.dragging_idx = None

# ---------- Main ----------
coords = [[1, 1], [2, 3], [3, 2], [4, 4]]
fig, ax = plt.subplots()
ax.set_title("Drag points with your mouse")
ax.set_xlim(0, 5)
ax.set_ylim(0, 5)

draggable = DraggableScatter(ax, coords)
plt.show()
