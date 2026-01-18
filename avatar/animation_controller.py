from pythonosc import udp_client

class AnimationController:
    def __init__(self, ip="127.0.0.1", port=9000):
        self.client = udp_client.SimpleUDPClient(ip, port)

    def trigger_animation(self, animation_name):
        # Send OSC message to trigger animation
        # Assume VTube Studio has a parameter for each animation
        self.client.send_message(f"/avatar/parameters/{animation_name}", 1.0)
        # Note: In VTube Studio, set up parameters to trigger animations

    def set_expression(self, expression):
        # Set expression parameter
        self.client.send_message("/avatar/parameters/expression", expression)

    def set_talking(self, talking):
        # Indicate talking for lip sync
        value = 1.0 if talking else 0.0
        self.client.send_message("/avatar/parameters/talking", value)