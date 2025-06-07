import matplotlib
matplotlib.use('TkAgg')  # 确保放在最前面

import matplotlib.pyplot as plt

class DraggablePoint:
    def __init__(self, ax):
        self.x = [1, 2, 3]
        self.y = [1, 4, 9]
        self.ax = ax
        self.point, = ax.plot(self.x, self.y, 'o', picker=5)
        self._ind = None
        self.cid_press = self.point.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = self.point.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = self.point.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def get_ind_under_point(self, event):
        if event.xdata is None or event.ydata is None:
            return None
        for i, (x, y) in enumerate(zip(self.x, self.y)):
            if abs(x - event.xdata) < 0.5 and abs(y - event.ydata) < 0.5:
                return i
        return None

    def on_press(self, event):
        self._ind = self.get_ind_under_point(event)

    def on_release(self, event):
        self._ind = None

    def on_motion(self, event):
        if self._ind is None:
            return
        self.x[self._ind] = event.xdata
        self.y[self._ind] = event.ydata
        self.point.set_data(self.x, self.y)
        self.ax.figure.canvas.draw()

fig, ax = plt.subplots()
ax.set_xlim(0, 5)
ax.set_ylim(0, 10)
ax.grid(True)

draggable = DraggablePoint(ax)

plt.show()
