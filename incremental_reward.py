import pyfirmata
import numpy as np
import pandas as pd
import xlsxwriter
import datetime
from time import sleep

###############################################
### Parameters to change between recordings ###
###############################################
recordings_number = 1
# folder to store the recordings. It needs a double \ to separate folders
folder = 'E:\\Irenie\\test\\'
# time in minutes to run the experiment
time_limit = 60 # in minutes
# delay before allowing another stimulation
thres_betw_interv = 1 # in seconds

# necessary pokes to receive the reward in each level
number_of_levels = 3

constant_levels = 3*np.ones(number_of_levels) # [3, 3, .... , 3]
linear_progression = np.arange(1, number_of_levels + 1) # [1, 2, ..., 10]
exp_progression = np.exp(linear_progression) # [e^1, ... , e^10]
geom_progression = np.geomspace(1, number_of_levels, 5) # 
log_progression = np.logspace(1, number_of_levels, num=number_of_levels, base=2) # [2^1, ... , 2^10]

# if repetition is required
repeated_progression = np.repeat(linear_progression, 3)

pokes_per_level = linear_progression.astype(int)

print("testing the reward progression")
level = 0
for pokes in pokes_per_level:
    print("level", level, ". Necessary pokes: ", pokes)
    level = level +1

good_progression = input("Should it proceed with this progression? y/n \n")
if good_progression != "y":
  print("Please, change the parameter to obtain the correct progression")
  exit()

####################################################################
### Parameters to change if the Arduino configuration is changed ###
####################################################################
# Arduino pins to write to or read from
pin = 1 # analog pin to receive the obstacle info
pin2 = 2 # analog pin to receive the second obstacle info
pin_out = 8 # digital pin to send the trigger info
pin_outduplicated = 10 # to light the led #1
pin2_out = 12 # digital pin to send the trigger info
pin2_outduplicated = 6 # to light the led #2
pin_start = 7 # led that will light at the beginning of each recording
pin_buzz = 3 # feeding the speaker that will buzz at the beginning of each recording

total_time = time_limit*60 # in seconds
time_exp_start = 1 # the speaker and led from pin3 will work for 1 second

# Parameters to follow the protocol in Carlezon & Chartoff (2007)
stim_len = 0.44  # it should be 0.5s but the TTL hardware that receives the arduino signal 
                 # produces a 0.5s pulse when receives an slightly shorter pulse
sampling_freq = 20 #141 # Hz
sampling_time = 1/sampling_freq # in seconds
half_sampling = sampling_time/2

# multiplying by 100 because the experiment time can be expanded if the rat does not 
# poke 5 times before the time limit passes
time = np.arange(0, total_time, sampling_time) 
time_array_lenght = int(total_time/sampling_time)

# recording time in samples
rec_time = (total_time/sampling_time)

# samples to light the led and make the speaker buzz
samples_exp_start = time_exp_start*sampling_freq

# Creates a new board 
board = pyfirmata.Arduino('COM4') # Windows
#board = pyfirmata.Arduino('/dev/ttyACM0') # Linux
print("Setting up the connection to the board ...")
it = pyfirmata.util.Iterator(board)
it.start()
 
# Start reporting for define pin
board.analog[pin].enable_reporting()
board.analog[pin2].enable_reporting()

# loop over all the recordings/stimulation levels
for rec in np.arange(recordings_number):
    
  # Run until the total time is reached
  counter = 0
  counter2 = 0
  count_betw_interv = 5
  count_betw_interv2 = 5

  delay_stimulus = False
  keep_stimulus = False
  took_nose_out = True
  delay_stimulus2 = False
  keep_stimulus2 = False
  took_nose_out2 = True
  prev_stimulus = False
  prev_stimulus2 = False

  stim_times = np.zeros(time_array_lenght)
  stim_times2 = np.zeros(time_array_lenght)
  poke_times = np.zeros(time_array_lenght)
  poke_times2 = np.zeros(time_array_lenght)

  c = 0

  time_in_each_level = []
  
  # per each recording, it goes trough the different number of pokes necessary to receive the reward
  for min_pokes in pokes_per_level:

    print("New level reached.")
    print("Necesary pokes: ", min_pokes)
    
    # The recording time limit is reached
    if (c == rec_time):
      break
    
    # Initialization every time the level changes through the progression
    number_of_pokes = 1
    level_time = 0
    total_number_pokes = 0
    total_number_stims = 0
    total_number_correct_pokes = 0

    while True:

        # the number of pokes in the current level is met
        if (number_of_pokes > min_pokes) or (c == rec_time):
          time_in_each_level.append(level_time)
          total_number_stims = total_number_stims + 1
          if c < rec_time:
            total_number_correct_pokes = total_number_correct_pokes + min_pokes
          else: 
            total_number_correct_pokes = total_number_correct_pokes + number_of_pokes - 1
          break

        # the buzzer and the light will be on for sampes_exp_start samples after a new level is reached
        if c < samples_exp_start:
          board.digital[pin_start].write(1)
          board.digital[pin_buzz].write(1) # https://github.com/Python-programming-Arduino/ppfa-code/blob/master/Chapter%2004/buzzerPattern.py
        else:
          board.digital[pin_start].write(0)
          board.digital[pin_buzz].write(0)
        
        #print("\n Checking state at second %f" % i)
        #print("Pin %i : %s" % (pin, board.analog[pin].read()))
        if board.analog[pin].read() is not None:
          #print("Pin %i : %s" % (pin, board.analog[pin].read()))
          # the rat is poking
          prev_stimulus = keep_stimulus
          if (board.analog[pin].read() > 0.75):

            # correct pokes or not, we count them all
            if poke_times[c-1] == 0:
              total_number_pokes = total_number_pokes + 1 
            #poke_times.append(1)
            poke_times[c] = 1
            #print("poking")
            
            if counter < stim_len and took_nose_out and count_betw_interv > thres_betw_interv:              
              # The stimulus is only given for the last poke of every level (min_pokes)
              if (number_of_pokes == min_pokes):
                board.digital[pin_out].write(1)
                board.digital[pin_outduplicated].write(1)
              keep_stimulus = True    
              count_betw_interv = 0
            elif counter > stim_len:
              took_nose_out = False
              board.digital[pin_out].write(0)
              board.digital[pin_outduplicated].write(0)
              count_betw_interv = count_betw_interv + sampling_time
              counter = 0
              keep_stimulus = False
            elif count_betw_interv <= thres_betw_interv:
              took_nose_out = False
              count_betw_interv = count_betw_interv + sampling_time

              
            counter = counter + sampling_time

          else:
            # the rat is not poking  
            #poke_times.append(0)
            
            count_betw_interv = count_betw_interv + sampling_time
            # the stimulus is maintained
            if counter < stim_len and keep_stimulus:
              if (number_of_pokes == min_pokes):
                board.digital[pin_out].write(1)
                board.digital[pin_outduplicated].write(1)
              counter = counter + sampling_time
            
            else:
              took_nose_out = True
              counter = 0
              board.digital[pin_out].write(0)
              board.digital[pin_outduplicated].write(0)
              keep_stimulus = False
          
          #stim_times.append(int(keep_stimulus))
          if (number_of_pokes == min_pokes):
            stim_times[c] = int(keep_stimulus)

          # A whole stimulus has finished
          if prev_stimulus and not keep_stimulus:
              number_of_pokes = number_of_pokes + 1
              #print("stimulus increased hole 1")

        else:
          print("Pin with no value")

        # Analysis for the detector that does not give reinforcement
        if board.analog[pin2].read() is not None:
          #print("Pin %i : %s" % (pin2, board.analog[pin2].read()))
          if (board.analog[pin2].read() > 0.75):
            #poke_times2.append(1)
            poke_times2[c] = 1
            
            if counter2 < stim_len and took_nose_out2 and count_betw_interv2 > thres_betw_interv:
              if (number_of_pokes == min_pokes):
                board.digital[pin2_out].write(0) # it does not give stimulus
                board.digital[pin2_outduplicated].write(1) # it makes the led light
              keep_stimulus2 = True    
              count_betw_interv2 = 0
            elif counter2 > stim_len:
              took_nose_out2 = False
              board.digital[pin2_out].write(0)
              board.digital[pin2_outduplicated].write(0)
              count_betw_interv2 = count_betw_interv2 + sampling_time
              counter2 = 0
              keep_stimulus2 = False
            elif count_betw_interv2 <= thres_betw_interv:
              took_nose_out2 = False
              count_betw_interv2 = count_betw_interv2 + sampling_time

              
            counter2 = counter2 + sampling_time

          else:
            #poke_times2.append(0)
            count_betw_interv2 = count_betw_interv2 + sampling_time
            if counter2 < stim_len and keep_stimulus2:
              if (number_of_pokes == min_pokes):
                board.digital[pin2_out].write(0) # it does not give stimulus
                board.digital[pin2_outduplicated].write(1) # it makes the led light
              counter2 = counter2 + sampling_time
            else:
              took_nose_out2 = True
              counter2 = 0
              board.digital[pin2_out].write(0)
              board.digital[pin2_outduplicated].write(0)
              keep_stimulus2 = False

          #stim_times2.append(int(keep_stimulus2))
          stim_times2[c] = int(keep_stimulus2)
          
          #if prev_stimulus2 and not keep_stimulus2:
              #number_of_pokes = number_of_pokes + 1 # the second hole is not counted
              #print("stimulus increased hole 2")
          
          level_time = level_time + 1

        else:
          print("Pin 2 with no value")     
        

        board.pass_time(sampling_time)      

        c = c + 1
    
  
  # Setting the outputs to 0 so the animal does not receive anything once the experiment is finished
  board.digital[pin_out].write(0)
  board.digital[pin_outduplicated].write(0)
  board.digital[pin2_out].write(0)
  board.digital[pin2_outduplicated].write(0)

  level_times = np.asarray(time_in_each_level)*sampling_time

  total_time_poking = sum(poke_times)*sampling_time
  print('Total time poking hole 1 (s):', total_time_poking)
  print('Total number of rewards hole 1:', total_number_stims)

  # creating the dataframe with the data
  df_stim = pd.DataFrame({'Time': time[:c], 'Poke in 1': poke_times[:c], 'Stim from 1': stim_times[:c], 'Poke in 2': poke_times2[:c], 'Stim from 2': stim_times2[:c], 'Total_time_poking(s)': total_time_poking, 'Correct_pokes': total_number_correct_pokes, 'Total_pokes': total_number_pokes, 'Total_number_stim': total_number_stims})
  df_time_per_level = pd.DataFrame({'Time_per_level (s)': level_times})

  # exporting the dataframe to a excel file
  filename = datetime.datetime.now().strftime("%d%m%Y-%H%M%S")
  df_stim.to_excel(folder + 'record_' + str(rec+1) + '_' + filename + '.xlsx')
  df_time_per_level.to_excel(folder + 'record_' + str(rec+1) + '_' + filename + 'times_per_level.xlsx')
  print('Recording number ' + str(rec + 1) + ' finished')
  print('')
  
board.exit()