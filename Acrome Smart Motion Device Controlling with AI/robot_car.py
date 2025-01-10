from flask import Flask, request, jsonify  
from smd.red import Master, Red,OperationMode
import time
import math
from serial.tools.list_ports import comports
from platform import system
app = Flask(__name__)
def USB_Port():
	ports = list(comports())
	usb_names = {
		"Windows": ["USB Serial Port"],
		"Linux": ["/dev/ttyUSB"],
		"Darwin": [
			"/dev/tty.usbserial",
			"/dev/tty.usbmodem",
			"/dev/tty.SLAB_USBtoUART",
			"/dev/tty.wchusbserial",
			"/dev/cu.usbserial",
            		"/dev/cu.usbmodem",
			"/dev/cu.SLAB_USBtoUART",
			"/dev/cu.wchusbserial",
		]
	}
	
	os_name = system()
	if ports:
		for port, desc, hwid in sorted(ports):
			if any(name in port or name in desc for name in usb_names.get(os_name, [])):
				return port
		print("Current ports:")
		for port, desc, hwid in ports:
			print(f"Port: {port}, Description: {desc}, Hardware ID: {hwid}")
	else:
		print("No port found")
	return None
class RobotController:
    def __init__(self, wheel_radius, robot_width):
        self.m = None
        self.x = None
        self.y = None
        self.angle = None
        self.wheel_radius = wheel_radius
        self.robot_width = robot_width
        self.robot_initialized = False  
    def init_robot(self):
        if self.robot_initialized:
            return self.x, self.y, self.angle  
        self.m = Master(USB_Port())
        self.x = 0
        self.y = 0
        self.angle = 0
        self.m.attach(Red(0))
        self.m.attach(Red(1))
        self.m.set_operation_mode(0, OperationMode.Velocity)
        self.m.set_operation_mode(1, OperationMode.Velocity)
        self.m.set_shaft_rpm(0,100)
        self.m.set_shaft_rpm(1,100)
        self.m.set_shaft_cpr(0,6533)
        self.m.set_shaft_cpr(1,6533)
        self.m.enable_torque(0, True)
        self.m.enable_torque(1, True)
        self.m.set_control_parameters_velocity(0, 25.83, 4.27, 0)
        self.m.set_control_parameters_velocity(1, 29.48, 5.50, 0)
        self.robot_initialized = True  

        return self.x, self.y, self.angle
    def linear_movement(self, cm, speed=30):
      kp = 1
      if speed > 100:
          print("You cannot exceed speed 100.")
          speed = 30
      print(speed)
  
  
      try:
          motor1_offset = self.m.get_position(0) / 6533
          motor2_offset = self.m.get_position(1) / 6533
          err = 100
  
          while abs(err) > 2:
              try:
                  # Motor pozisyonlarını oku
                  motor1 = self.m.get_position(0) / 6533 - motor1_offset
                  motor2 = self.m.get_position(1) / 6533 - motor2_offset
                  motor_mean = (-motor1 + motor2) / 2
  
                  # Robotun ilerlediği mesafeyi hesapla
                  car_pos = motor_mean * 2 * math.pi * self.wheel_radius
                  err = cm - car_pos
                  print(cm, car_pos)
  
                  # PID tabanlı hız kontrolü
                  calc_velo = err * kp
                  if calc_velo > speed:
                      calc_velo = speed
                  elif calc_velo < -speed:
                      calc_velo = -speed
  
                  # Motor hızlarını ayarla
                  self.m.set_velocity(0, -calc_velo)
                  self.m.set_velocity(1, calc_velo)
  
              except Exception as e:
                  print("Error during motor position read or calculation:", str(e))
                  continue  
  
      except Exception as e:
          print("Error initializing motor positions:", str(e))
  
      
      self.m.set_velocity(0, 0)
      self.m.set_velocity(1, 0)
  
      # Robotun pozisyonunu güncelle
      self.x += cm
      return self.x, self.y, self.angle



    def turn_left(self, degree, rotation_speed=30):
        """Robotun saat yönünün tersine (sola) dönüşü pozisyon tabanlı kontrol ile."""
        rotation_speed = float(rotation_speed)
        degree = float(degree)

        if rotation_speed > 100:
            print("Rotation speed cannot exceed 100.")
            rotation_speed = 30
        if rotation_speed < -100:
            print("Rotation speed cannot be less than -100.")
            rotation_speed = -30

        print("Adjusted rotation speed:", rotation_speed)

        # Dönüş sırasında gereken tekerlek mesafesi
        arc_length = (degree / 360) * (math.pi * self.robot_width)  # Robotun döneceği yay uzunluğu
        wheel_rotation = arc_length / (2 * math.pi * self.wheel_radius)  # Tekerleklerin dönmesi gereken tur sayısı

        # Motorların hedef pozisyonlarını hesapla
        left_motor_target = self.m.get_position(0) - (wheel_rotation * 6533)  # Sol motor geri
        right_motor_target = self.m.get_position(1) + (wheel_rotation * 6533)  # Sağ motor ileri

        # Hareketi başlat
        while True:
            left_motor_current = self.m.get_position(0)
            right_motor_current = self.m.get_position(1)

            # Her iki motorun hedef pozisyona ne kadar yaklaştığını kontrol et
            left_error = abs(left_motor_target - left_motor_current)
            right_error = abs(right_motor_target - right_motor_current)
            print(left_error)
            print(right_error)
            if left_error < 525 or right_error < 525:  # Hata toleransı
                self.m.set_velocity(0, 0)
                self.m.set_velocity(1, 0)
                break

            # Motorlara hız gönder
            if left_motor_current > left_motor_target:
                self.m.set_velocity(0, rotation_speed)  # Sol motor geri

            if right_motor_current < right_motor_target:
                self.m.set_velocity(1, rotation_speed)  # Sağ motor ileri
            

        # Robotun açısını güncelle
        self.angle -= degree
        if self.angle < 0:
            self.angle += 360

        print(f"Updated Position: x={self.x}, y={self.y}, angle={self.angle}")
        return self.x, self.y, self.angle
    def turn_right(self, degree, rotation_speed=30):
        """Robotun saat yönünde (sağa) dönüşü pozisyon tabanlı kontrol ile."""
        if rotation_speed > 100:
            print("Rotation speed cannot exceed 100.")
            rotation_speed = 30
        if rotation_speed < -100:
            print("Rotation speed cannot be less than -100.")
            rotation_speed = -30
    
        print("Adjusted rotation speed:", rotation_speed)
    
        # Dönüş sırasında gereken tekerlek mesafesi
        arc_length = (degree / 360) * (math.pi * self.robot_width)  # Robotun döneceği yay uzunluğu
        wheel_rotation = arc_length / (2 * math.pi * self.wheel_radius)  # Tekerleklerin dönmesi gereken tur sayısı
    
        # Motorların hedef pozisyonlarını hesapla
        left_motor_target = self.m.get_position(0) + (wheel_rotation * 6533)  # Sol motor ileri
        right_motor_target = self.m.get_position(1) - (wheel_rotation * 6533)  # Sağ motor geri
    
        # Hareketi başlat
        while True:
            left_motor_current = self.m.get_position(0)
            right_motor_current = self.m.get_position(1)
    
            # Her iki motorun hedef pozisyona ne kadar yaklaştığını kontrol et
            left_error = abs(left_motor_target - left_motor_current)
            right_error = abs(right_motor_target - right_motor_current)
            print(left_error)
            print(right_error)
            if left_error < 525 or right_error < 525:  # Hata toleransı
                self.m.set_velocity(0, 0)
                self.m.set_velocity(1, 0)
                break
    
            # Motorlara hız gönder
            if left_motor_current < left_motor_target:
                self.m.set_velocity(0, -rotation_speed)  # Sol motor ileri
            
    
            if right_motor_current > right_motor_target:
                self.m.set_velocity(1, -rotation_speed)  # Sağ motor geri
    
        # Robotun açısını güncelle
        self.angle += degree
        if self.angle >= 360:
            self.angle -= 360
    
        print(f"Updated Position: x={self.x}, y={self.y}, angle={self.angle}")
        return self.x, self.y, self.angle

    def radial_movement(self, radius, degree, speed=40, steps=20):
        """
        Robotun belirtilen yarıçap (radius) ve açı (degree) boyunca bir daire üzerinde hareket etmesini sağlar.

        Args:
            radius (float): Dairenin yarıçapı (cm). Pozitif değer sağa, negatif değer sola döner.
            degree (float): Hareket edilecek toplam açı (derece).
            speed (int): Maksimum hız (% olarak, -100 ile 100 arası).
            steps (int): Hareketi kaç adıma böleceğinizi belirtir.
        """
        if speed > 100:
            speed = 100
        if speed < -100:
            speed = -100

        speed=40
        
        
        degree_per_step = degree / steps
        arc_length_per_step = (2 * math.pi * abs(radius) * abs(degree_per_step)) / 360

        for _ in range(steps):
           
            if radius > 0:  
                inner_wheel_speed = speed * (radius - (self.robot_width / 2)) / radius
                outer_wheel_speed = speed
            else:  
                inner_wheel_speed = speed
                outer_wheel_speed = speed * (radius + (self.robot_width/ 2)) / radius

            
            self.m.set_velocity(0, inner_wheel_speed)  
            self.m.set_velocity(1, outer_wheel_speed)  

            
            time_per_step = arc_length_per_step / (speed * (2 * math.pi * (abs(radius)) / 60))  
            
            # Bekle
            time.sleep(time_per_step)

        
        self.m.set_velocity(0, 0)
        self.m.set_velocity(1, 0)

        
        self.angle += degree
        self.angle %= 360  

        return self.x, self.y, self.angle
    def distance_movement(self,cm):
        self.m.set_velocity(0,-30)
        self.m.set_velocity(1,30)
        while True:
            a= self.m.get_distance(1,5)
            print(a)
            if (a<cm) and a>0.5:
                self.m.set_velocity(0,0)
                self.m.set_velocity(1,0)
                break
    def stop(self):
        self.m.set_velocity(0,0)
        self.m.set_velocity(1,0)
    

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
        rotation_speed= data.get("rotation_speed",30)
        x, y, angle = robot_controller.turn_left(degree,rotation_speed)
    elif command_id == "3":
        degree = data.get("degree", 0)
        rotation_speed= data.get("rotation_speed",30)
        x, y, angle = robot_controller.turn_right(degree,rotation_speed)
    elif command_id == "4":
        radius = data.get("radius", 0)
        degree = data.get("degree", 0)
        x, y, angle = robot_controller.radial_movement(radius, degree)
    elif command_id=="5":
        cm=data.get("cm",0)
        robot_controller.distance_movement(cm)
    elif command_id=="6":
        robot_controller.stop()
    else:
        return jsonify({"error": "Invalid command"}), 400

    return jsonify({"x": x, "y": y, "angle": angle})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)   #You should change it.  You use your raspberry Pi Ip.
