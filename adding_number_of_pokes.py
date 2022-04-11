import pandas as pd
import numpy as np
import glob, os

folder = "/media/jorge/otherprojects/Data/Irenie/"

def search_sequence_numpy(arr,seq):
    """ Find sequence in an array using NumPy only.

    Parameters
    ----------    
    arr    : input 1D array
    seq    : input 1D array

    Output
    ------    
    Output : 1D Array of indices in the input array that satisfy the 
    matching of input sequence in the input array.
    In case of no match, an empty list is returned.
    """

    # Store sizes of input array and sequence
    Na, Nseq = arr.size, seq.size

    # Range of sequence
    r_seq = np.arange(Nseq)

    # Create a 2D array of sliding indices across the entire length of input array.
    # Match up with the input sequence & get the matching starting indices.
    M = (arr[np.arange(Na-Nseq+1)[:,None] + r_seq] == seq).all(1)

    # Get the range of those indices as final output
    if M.any() >0:
        return np.where(np.convolve(M,np.ones((Nseq),dtype=int))>0)[0]
    else:
        return []         # No match found


sequence = np.array([0, 1]) #looking for the times where no poke was detected and the next sample it was

os.chdir(folder)
for file in glob.glob("*.xlsx"):
    df = pd.read_excel(file)
    pokes_one = df['Poke in 1'].to_numpy()
    pokes_two = df['Poke in 2'].to_numpy()
    l_pokes_one = search_sequence_numpy(pokes_one, sequence)
    l_pokes_two = search_sequence_numpy(pokes_two, sequence)
    df['number_of_pokes_1'] = len(l_pokes_one)
    df['number_of_pokes_2'] = len(l_pokes_two)
    # exporting the dataframe to a excel file
    index = file.rfind(".")
    filename = file[:index]
    df.to_csv(filename + '_with_number_pokes.csv')
