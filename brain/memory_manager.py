import json
import os

class MemoryManager:
    def __init__(self):
        self.memory_file = "brain/memory.json"
        self.memory = {}
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                self.memory = json.load(f)

    def remember(self, key, value):
        self.memory[key] = value
        self.save()

    def recall(self, key):
        return self.memory.get(key)

    def save(self):
        with open(self.memory_file, "w") as f:
            json.dump(self.memory, f)