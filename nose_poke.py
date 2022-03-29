import pyfirmata
import numpy as np
import pandas as pd
import xlsxwriter
import datetime

###############################################
### Parameters to change between recordings ###
###############################################
recordings_number = 4
# folder to store the recordings. It needs a double \ to separate folders
folder = 'E:\\Irenie\\test\\'

# time in minutes to run the experiment
time_min = 0.5 # in minutes
# delay before allowing another stimulation
thres_betw_interv = 1 # in seconds

# Arduino pins to write to or read from
pin = 1 # analog pin to receive the obstacle info
pin2 = 2 # analog pin to receive the second obstacle info
pin_out = 12 # digital pin to send the trigger info
pin_outduplicated = 10 # to light the led #1
pin2_out = 8 # digital pin to send the trigger info
pin2_outduplicated = 6 # to light the led #2
pin_start = 7 # led that will light at the beginning of each recording
pin_buzz = 3 # feeding the speaker that will buzz at the beginning of each recording

total_time = time_min*60 # in seconds
time_exp_start = 1 # the speaker and led from pin3 will work for 1 second

# Parameters to follow the protocol in Carlezon & Chartoff (2007)
stim_len = 0.44  # it should be 0.5s but the TTL hardware that receives the arduino signal 
                 # produces a 0.5s pulse when receives an slightly shorter pulse
sampling_freq = 20 #141 # Hz
sampling_time = 1/sampling_freq # in seconds
half_sampling = sampling_time/2

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
  stim_times = np.zeros(int(total_time/sampling_time))
  stim_times2 = np.zeros(int(total_time/sampling_time))
  poke_times = np.zeros(int(total_time/sampling_time))
  poke_times2 = np.zeros(int(total_time/sampling_time))
  time = np.arange(0, total_time, sampling_time)

  c = 0

  
  for i in np.arange(0, total_time, sampling_time):

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
        if (board.analog[pin].read() > 0.75):

          poke_times[c] = 1
          
          if counter < stim_len and took_nose_out and count_betw_interv > thres_betw_interv:
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
          count_betw_interv = count_betw_interv + sampling_time
          if counter < stim_len and keep_stimulus:
            board.digital[pin_out].write(1)
            board.digital[pin_outduplicated].write(1)
            counter = counter + sampling_time
          else:
            took_nose_out = True
            counter = 0
            board.digital[pin_out].write(0)
            board.digital[pin_outduplicated].write(0)
            keep_stimulus = False
        
        stim_times[c] = int(keep_stimulus)

      else:
        print("Pin with no value")

      # Analysis for the detector that does not give reinforcement
      if board.analog[pin2].read() is not None:
        #print("Pin %i : %s" % (pin2, board.analog[pin2].read()))
        if (board.analog[pin2].read() > 0.75):
          poke_times2[c] = 1
          
          if counter2 < stim_len and took_nose_out2 and count_betw_interv2 > thres_betw_interv:
            board.digital[pin2_out].write(1)
            board.digital[pin2_outduplicated].write(1)
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
          count_betw_interv2 = count_betw_interv2 + sampling_time
          if counter2 < stim_len and keep_stimulus2:
            board.digital[pin2_out].write(1)
            board.digital[pin2_outduplicated].write(1)
            counter2 = counter2 + sampling_time
          else:
            took_nose_out2 = True
            counter2 = 0
            board.digital[pin2_out].write(0)
            board.digital[pin2_outduplicated].write(0)
            keep_stimulus2 = False
      else:
        print("Pin 2 with no value")
      
      stim_times2[c] = int(keep_stimulus2)

      board.pass_time(sampling_time)

      c = c + 1

  # Setting the outputs to 0 so the animal does not receive anything once the experiment is finished
  board.digital[pin_out].write(0)
  board.digital[pin_outduplicated].write(0)
  board.digital[pin2_out].write(0)
  board.digital[pin2_outduplicated].write(0)

  total_number_stims1 = sum(stim_times)/9
  print('Total number of rewards hole 1:', total_number_stims1)

  df_stim = pd.DataFrame({'Time': time, 'Poke in 1': poke_times, 'Stim from 1': stim_times, 'Poke in 2': poke_times2, 'Stim from 2': stim_times2, 'Total_number_stim': total_number_stims1})
  
  filename = datetime.datetime.now().strftime("%d%m%Y-%H%M%S")
  df_stim.to_excel(folder + 'record_' + str(rec+1) + '_' + filename + '.xlsx')
  print('Recording number ' + str(rec + 1) + ' finished')
  print('')
  
board.exit()