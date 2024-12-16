from flask import Flask, request, jsonify  
from smd.red import Master, Red 
import time
import math

app = Flask(__name__)

class RobotController:
    def __init__(self,wheel_radius, robot_width):
        self.m =None
        self.x=None
        self.y= None
        self.angle=None
        self.wheel_radius=wheel_radius
        self.robot_width=robot_width
    def init_robot(self):
        self.m = Master("COM8")
        self.x=0
        self.y=0
        self.angle=0
        self.m.attach(Red(0))
        self.m.attach(Red(1))
        self.m.set_operation_mode(0, 2)
        self.m.set_operation_mode(1, 2)
        self.m.enable_torque(0, True)
        self.m.enable_torque(1, True)
        return self.x,self.y,self.angle
    def linear_movement(self, cm,speed=30):
        if speed>100:
            print("You cannot")
            speed=30
        if speed < -100:
            print("You cannot")
            speed=-30
        print(speed)
        velocity_rpm = speed  # Desired velocity in RPM
        distance_per_rev = 23.56  # Distance covered by one revolution in cm (adjust based on robot specs)
        
        # Calculate time to move the desired distance
        time_to_move = (cm / distance_per_rev) / (velocity_rpm / 60)  # Time in seconds
        
        # Set velocity for both motors to move forward
        self.m.set_velocity(0, -velocity_rpm )  
        self.m.set_velocity(1, velocity_rpm)  
        # Sleep for the calculated time to move
        time.sleep(time_to_move)
        
        # Stop the motors after moving
        self.m.set_velocity(0, 0)  # Left motor
        self.m.set_velocity(1,0)
        
        self.x += cm  
        return self.x, self.y, self.angle


    def turn(self,degree,rotation_speed=30):
        if rotation_speed>100:
            print("You cannot")
            rotation_speed=30
        if rotation_speed<-100:
            print("You cannot")
            rotation_speed=-30
        print(rotation_speed)
        
        if degree > 0:  # Right turn (clockwise)
            self.m.set_velocity(0, -rotation_speed)  # Left motor reverse
            self.m.set_velocity(1, -rotation_speed)   # Right motor forward
        else:  
            self.m.set_velocity(0,  rotation_speed)   # Left motor forward
            self.m.set_velocity(1,  rotation_speed)  # Right motor reverse

        # Assume a simple relationship between degrees and time for turning
        # Robotunuzun çapı ve RPM (motor hızı) ile dönüş süresini hesaplayın
        # wheel_radius = 3.75  # cm cinsinden
        # rpm = 100
        # circumferential_velocity = 2 * math.pi * wheel_radius * (rpm / 60)  # cm/sn cinsinden
        # print("Çevresel Hız:", circumferential_velocity, "cm/sn")
        # # Dönüş süresini açısal hıza göre ayarlayın
        # time_to_turn = abs(degree) / 360 * circumferential_velocity/rotation_speed  
        ay=(20*11.25)/rotation_speed
        time_to_turn = abs(degree) / 360 * ay 
        time.sleep(time_to_turn)
        
        self.m.set_velocity(0, 0)
        self.m.set_velocity(1,0)
        
        # Update the robot's angle
        self.angle += degree
        if self.angle >= 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360
    
        print(self.x,self.y,self.angle)
        return self.x, self.y, self.angle
    def radial_movement(self, radius,degree,steps=20):
        
    
        degree_per_step = degree / steps  
        distance_per_step = (2 * math.pi * abs(radius)) / steps  
    
    
        for _ in range(steps):
            if radius > 0:
                self.turn(degree_per_step)  
            else:
                self.turn(-degree_per_step)  
        
        
            self.linear_movement(distance_per_step)
            time.sleep(0.25) 
    
        return self.x, self.y, self.angle

    

robot_controller = RobotController(wheel_radius=3.75,robot_width=27.5)

@app.route('/execute', methods=['POST'])
def execute_command():
    data = request.get_json()
    command_id = data.get("id")

    if command_id == "0":
        x, y, angle = robot_controller.init_robot()
    elif command_id == "1":
        cm = data.get("cm", 0)
        speed=data.get("speed",30)
        x, y, angle = robot_controller.linear_movement(cm,speed)
    elif command_id == "2":
        degree = data.get("degree", 0)
        rotation_speed= data.get("rotation_speed",20)
        x, y, angle = robot_controller.turn(degree,rotation_speed)
    elif command_id == "3":
        radius = data.get("radius", 0)
        degree = data.get("degree", 0)
        x, y, angle = robot_controller.radial_movement(radius, degree)
    else:
        return jsonify({"error": "Invalid command"}), 400

    return jsonify({"x": x, "y": y, "angle": angle})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)   #You should change it.  You use your raspberry Pi Ip.
