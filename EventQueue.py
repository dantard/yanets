import bisect


class EventQueue(list):

    def size(self):
        return len(self)

    def push(self, event):
        # print("pushing event {} at ts:{}".format(type(event), event.get_ts()))
        self.append(event)
        self.sort(key=lambda x: x.ts, reverse=True)
        # print("event queue: {}".format([ts.ts for ts in self]))
