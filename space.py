


def intersect(space1, space2):
    if space1 is None or space2 is None:  # if space is empty
        return None
    result_space = ''
    for i in range(0, len(space1)):
        if space1[i] == space2[i]:
            result_space += space1[i]
        elif ord(space1[i]) + ord(space2[i]) == 97:  # 1 0 or 0 1
            return None
        elif space1[i] == '*':
            result_space += space2[i]
        else:
            result_space += space1[i]

    return result_space


class Space:
    def __init__(self, areas=[]):
        self.areas = areas

    # returns boolean: space changed or not
    def plus(self, space):
        if len(space.areas) == 0:
            return False

        changed = False

        for sa in space.areas:
            exist = False
            for a in self.areas:
                if a == sa:
                    exist = True
                    break
            if exist == False:
                self.areas.append(sa)
                changed = True

        return changed

    def minus(self, space):
        for sa in space.areas:
            if sa in self.areas:
                self.areas.remove(sa)
            else:
                # TODO: remove area using algebra
                return

    def multiply(self, space):
        result = []
        for sa in space.areas:
            for a in self.areas:
                result.append(intersect(sa, a))


        self.areas = [x for x in result if x is not None]

    # TODO: unordered areas compare
    def equal(self, space):
        if len(space.areas) != len(self.areas):
            return False

        for i in range(len(self.areas)):
            if space.areas[i] != self.areas[i]:
                return False

        return True
