import time, sys, board, subprocess, json
import adafruit_dht
import RPi.GPIO as GPIO
import ccs811LIBRARY
from datetime import datetime

dhtDevice = adafruit_dht.DHT11(board.D23)
GPIO.setmode(GPIO.BCM)
   
# Hier werden die Ausgangs-Pin deklariert, an dem die LEDs angeschlossen sind.
LED_ROT = 25
LED_GRUEN = 24
LED_BLAU = 26
 
GPIO.setup(LED_ROT, GPIO.OUT, initial= GPIO.LOW)
GPIO.setup(LED_GRUEN, GPIO.OUT, initial= GPIO.LOW)
GPIO.setup(LED_BLAU, GPIO.OUT, initial= GPIO.LOW)

#Deklarierung des Luftqualitätsensors
sensor = ccs811LIBRARY.CCS811()
def setup(mode=1):
    print('Starting CCS811 Read')
    sensor.configure_ccs811()
    sensor.set_drive_mode(mode)

    if sensor.check_for_error():
        sensor.print_error()
        raise ValueError('Error at setDriveMode.')

    result = sensor.get_base_line()
    sys.stdout.write("baseline for this sensor: 0x")
    if result < 0x100:
        sys.stdout.write('0')
    if result < 0x10:
        sys.stdout.write('0')
    sys.stdout.write(str(result) + "\n")

################################################################################
def temphum():
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity
        print("Temp: {:.1f} C    Humidity: {}% ".format(temperature_c, humidity))

def airqual(border = 1800):
        if sensor.data_available():
                sensor.read_logorithm_results()
                print("eCO2[%d] TVOC[%d]" % (sensor.CO2, sensor.tVOC))
        elif sensor.check_for_error():
                sensor.print_error()

        if sensor.CO2 < border:
                GPIO.output(LED_ROT,GPIO.LOW) 
                GPIO.output(LED_GRUEN,GPIO.HIGH) 
                GPIO.output(LED_BLAU,GPIO.LOW) 
        else:
                GPIO.output(LED_ROT,GPIO.HIGH) 
                GPIO.output(LED_GRUEN,GPIO.LOW) 
                GPIO.output(LED_BLAU,GPIO.LOW) 
             
#save data in JSON file (add an entry every 5 seconds)
#store in same folder as python file
def save_data(eCO2, TVOC, temperature_c, humidity):
        #sampling time
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        
        #data to be saved
        data = {
                'time': current_time,
                'eCO2': eCO2,
                'TVOC': TVOC,
                'temperature': temperature_c,
                'humidity': humidity
        }
        #serializing JSON
        json_object = json.dumps(data, indent = 4)       
        
        #writing to JSON file
        with open('data.json', 'w') as outfile:
                outfile.write(json_object)
        

setup(1)

# Starten von Prozess pigpiod, um die PWM-Funktion nutzen zu können (mit Sudorechten)
subprocess.Popen(['sudo', 'pigpiod'])


while True:
        try:
                temphum()
                airqual(2000)
                time.sleep(5)
                airqual(2000)
                time.sleep(5)
                
                #save data in JSON file
                save_data(sensor.CO2, sensor.tVOC, dhtDevice.temperature, dhtDevice.humidity)
                

        

        except RuntimeError as error:
                print(error.args[0])
                time.sleep(2.0)
        except Exception as error:
                dhtDevice.exit()
                raise error
        # Aufraeumarbeiten nachdem das Programm beendet wurde
        except KeyboardInterrupt:
                GPIO.cleanup()
                break
