import pyfirmata
import numpy as np
import pandas as pd
import xlsxwriter
import datetime

###############################################
### Parameters to change between recordings ###
###############################################
recordings_number = 3
# folder to store the recordings. It needs a double \ to separate folders
folder = 'E:\\Irenie\\'
# time in minutes to run the experiment
time_min = 0.2 # in minutes
# delay before allowing another stimulation
thres_betw_interv = 1 # in seconds
min_pokes = 5 # minimum number of pokes that the rat has to make before next stimulation level


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

total_time = time_min*60 # in seconds
time_exp_start = 1 # the speaker and led from pin3 will work for 1 second

# Parameters to follow the protocol in Carlezon & Chartoff (2007)
stim_len = 0.44  # it should be 0.5s but the TTL hardware that receives the arduino signal 
                 # produces a 0.5s pulse when receives an slightly shorter pulse
sampling_freq = 20 #141 # Hz
sampling_time = 1/sampling_freq # in seconds
half_sampling = sampling_time/2

# multiplying by 100 because the experiment time can be expanded if the rat does not 
# poke 5 times before the time limit passes
time = np.arange(0, 100*total_time, sampling_time) 
time_array_lenght = int(100*total_time/sampling_time)

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

  #stim_times = [] #np.zeros(int(100*c/sampling_time))
  #stim_times2 = [] #np.zeros(int(100*c/sampling_time))
  #poke_times = [] #np.zeros(int(100*c/sampling_time))
  #poke_times2 = [] #np.zeros(int(100*c/sampling_time))

  stim_times = np.zeros(time_array_lenght)
  stim_times2 = np.zeros(time_array_lenght)
  poke_times = np.zeros(time_array_lenght)
  poke_times2 = np.zeros(time_array_lenght)  

  c = 0
  number_of_pokes = 0
  

  while True:
  #for i in np.arange(0, total_time, sampling_time):
      rec_time = (total_time/sampling_time)  
      if (number_of_pokes >= min_pokes) and (c > rec_time):
          break

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

          #poke_times.append(1)
          poke_times[c] = 1
          #print("poking")
          
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
          # the rat is not poking  
          #poke_times.append(0)
          
          count_betw_interv = count_betw_interv + sampling_time
          # the stimulus is maintained
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
        
        #stim_times.append(int(keep_stimulus))
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
          #poke_times2.append(0)
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

        #stim_times2.append(int(keep_stimulus2))
        stim_times2[c] = int(keep_stimulus2)
        
        if prev_stimulus2 and not keep_stimulus2:
            number_of_pokes = number_of_pokes + 1
            #print("stimulus increased hole 2")
      else:
        print("Pin 2 with no value")     
      

      board.pass_time(sampling_time)      

      c = c + 1
  
  
  # Setting the outputs to 0 so the animal does not receive anything once the experiment is finished
  board.digital[pin_out].write(0)
  board.digital[pin_outduplicated].write(0)
  board.digital[pin2_out].write(0)
  board.digital[pin2_outduplicated].write(0)

  total_number_stims1 = sum(stim_times)/9
  print('Total number of rewards hole 1:', total_number_stims1)


  #p_times = np.asarray(poke_times)
  #s_times = np.asarray(stim_times)
  #p_times2 = np.asarray(poke_times2)
  #s_times2 = np.asarray(stim_times2)
  #time = np.arange(0, len(poke_times)*sampling_time, sampling_time)
  df_stim = pd.DataFrame({'Time': time[:c], 'Poke in 1': poke_times[:c], 'Stim from 1': stim_times[:c], 'Poke in 2': poke_times2[:c], 'Stim from 2': stim_times2[:c], 'Total_number_stim': total_number_stims1})

  #df_stim = pd.DataFrame({'Time': time, 'Poke in 1': p_times, 'Stim from 1': s_times, 'Poke in 2': p_times2, 'Stim from 2': s_times2, 'Total_number_stim': total_number_stims1})
  
  filename = datetime.datetime.now().strftime("%d%m%Y-%H%M%S")
  df_stim.to_excel(folder + 'record_' + str(rec+1) + '_' + filename + '.xlsx')
  print('Recording number ' + str(rec + 1) + ' finished')
  print('')
  
board.exit()