class StateManager:
    def __init__(self):
        self.state = {"listening": False, "speaking": False, "expression": "neutral"}

    def set_state(self, key, value):
        self.state[key] = value

    def get_state(self, key):
        return self.state.get(key)