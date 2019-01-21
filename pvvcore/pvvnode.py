from PM import PM


class ControlPlane:
    def __init__(self):
        self.rules = []
        self.pm = PM()

    def add_rule(self, rule):
        self.rules.append(rule)

    def update_pm(self, property, Space):
        return


class Pvvnode:
    def __init__(self):
        self.cps = {
            "sdn": ControlPlane(),
            "ospf": ControlPlane()
        }

    def update(self, cp, property, space):
        self.cps[cp].update_pm(property, space)