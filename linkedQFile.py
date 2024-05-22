# Node class to represent one node in the linked list
class Section:
    def __init__(self, distance, slope, radius, speedLimit):
        self.distance = distance
        self.slope = slope
        self.radius = radius
        self.speedLimit = speedLimit
        self.next = None

# Class to implement the queue using linked list
class LinkedQ:
    def __init__(self):
        self.front = None # Pointer to front of queue (Head)
        self.rear = None # Pointer to last element of queue
        self.len = 0

    # Method to append elements to the queue
    def enqueue(self, distance, slope, radius, speedLimit):
        new_section = Section(distance, slope, radius, speedLimit) # Create node with value to be queued
        if self.is_empty(): # If queue is empty - set both first and last to new element
            self.front = self.rear = new_section
            self.len+=1
            return
        # Else - put new node/element last in queue
        self.rear.next = new_section
        self.rear = new_section
        self.len+=1
        

    # Method to remove and return first element in queue
    def dequeue(self):
        # Error handle if dequeuing empty queue
        if self.is_empty():
            raise IndexError("Queue is empty")
        removedElement = self.front
        self.front = self.front.next # Set new front to prior second
        if self.front is None: # If front now is empty, queue must be empty
            self.rear = None # Rear pointer has to be cleared too
        self.len-=1
        return removedElement
        

    # Method to check if queue is empty
    def is_empty(self): 
        return self.front is None
    
    # Method to return current queue length
    def length(self):
        return self.len
    
    def peek(self):
        if self.front is not None:
            return self.front
    # Method to print the current queue, debugging tool
    def print(self):
        current = self.front
        while current:
            print(current.distance, current.slope, current.radius, current.speedLimit)
            current = current.next
