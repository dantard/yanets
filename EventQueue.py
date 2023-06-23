import bisect

class EventQueue(list):

    def size(self):
        return len(self)

    def push(self, event):
        self.append(event)
        self.sort(key=lambda x: x.ts, reverse=True)

