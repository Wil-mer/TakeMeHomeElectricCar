import time

class PIDController:
    def __init__(self, P=1/4000, I=0, D=0):
        self.P = P
        self.I = I
        self.D = D
        self.current_time = time.time()
        self.last_time = self.current_time
        self.clear()

    def clear(self):
        self.SetPoint = 0.0
        self.PTerm = 0.0
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0

    def update(self, feedback_value):
        error = self.SetPoint - feedback_value
        self.current_time = time.time()
        delta_time = self.current_time - self.last_time
        delta_error = error - self.last_error

        if (delta_time >= 0.01):
            self.PTerm = self.P * error
            self.ITerm += error * delta_time

            if (delta_time > 0):
                self.DTerm = delta_error / delta_time

            self.last_time = self.current_time
            self.last_error = error

        return self.PTerm + (self.I * self.ITerm) + (self.D * self.DTerm)
