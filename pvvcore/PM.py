from space import Space

# PM for one protocol
class PM:
    def __init__(self):
        self.entries = {}  # a map, key: property, value: {nexthop: space}]

    def add_space(self, property, space, related_rule):
        if property not in self.entries:
            self.entries[property] = {'space': Space(), 'rule': related_rule}

        return self.entries[property]['space'].plus(space)

    def union_space(self, property):
        areas = []
        for v in self.entries[property].values():
            for a in v.areas:
                areas.append(a)

        return areas

    def show(self):
        for property in self.entries:
            print property + ':'
            for nexthop in self.entries[property]:
                print nexthop + ':'
                print self.entries[property][nexthop].areas

