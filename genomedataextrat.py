import pdftotext                     # converting PDF files to plain text files
from tabula.io import read_pdf       # wrapper of tabula, table extraction from pdf

# import numpy                             # working with arrays
import pandas as pd                      # for data analysis 
import csv                               # working with csv files

import os                             # interacting with operating system
import glob                           # returning all file paths that match a specific pattern


from optparse import OptionParser     # optparse make it easy to handle the command-line argument

# Creating an OptionParser object
parser = OptionParser()
parser.add_option("-i", "--input_file", dest="input_file_name",
                  help="write input FILE")

parser.add_option("-o","--output_file",dest="output_file_name",
                  help="write output FILE")

# object returned by parse_args()
(options, args) = parser.parse_args()

path = options.input_file_name
output_path = options.output_file_name

print("input path: ",path)
print("output path: ", output_path)


# making user defined functions to extract data as a dictionary based on the page format

def get_data_pg3(page_3_text):
    __dict = {}               # empty dictionary 
    for line in page_3_text:
        if ')' in line:             # page contains ')' in dst_table 
            key, value = line.split(')')          # separating into key and value pairs based on ')'
            __dict[key.strip()] = value.strip()    # adding key and value to empty dictionary
        elif 'Clinical Recommendations' in line:   # ending loop when the line reads the string
            break
    return __dict

def get_data_pg2(page_2_text):
            __dict = {}

            for line in page_2_text:         
                if ':'  in line:                        # page contains ':'
                    # print(line) 
                    line = line.replace(":","-",1) if line.count(":") > 1 else line   # if ":" is more than 1 replacing ":" with "-"
                    key, value = line.split(':')                # separating into key-value pairs based on ":"
                    __dict[key.strip()] = value.strip()                
            return __dict


def get_data_pg1(page_1_text):
    __dict = {}

    for line in page_1_text:
        if ':' in line:
            key, value = line.split(':')
            __dict[key.strip()] = value.strip()
        elif 'Report summary for Sample' in line:
            break
    return __dict


# path="/home/aman/Desktop/HaystackAnalytics/Task1/genomeanalysisfinalreport/INPUT_PDF/" 
# output_path = '/home/aman/Desktop/HaystackAnalytics/Task1/genomeanalysisfinalreport/OUTPUT/'

# using glob to return all pdf files
list_filenames = glob.glob(path+"*.pdf")     # list of all the pdf file names
# print("file names: ",list_filenames)


# creating a function that will extract data into a structured format 
def dataextract(path_file, output_path):

    outputfile_name = path_file.split("/")[-1]    # getting the pdf file name from the path  
    output_folder_name = outputfile_name.split(".")[0]+"/"     # getting the folder name based on pdf file name
    
    output_data = output_path+output_folder_name+outputfile_name
    # print(output_data)

    # using os to make directories 
    if os.path.exists(output_path+output_folder_name):
        print("continue")
    else:
        os.makedirs(output_path+output_folder_name)    # makes different folders based on the pdf file name

    with open(path_file, "rb") as f:
        pdf = pdftotext.PDF(f)

        # using pdftotext library to extact text from a pdf page
        # Extracting metadata
        #print(pdf[0])
        page_1_text= pdf[0]      # getting page 1 data
        page_1_text= page_1_text.split('\n')        # splitting based on new line ("\n")
        #print(page_1_text)

        page_data = get_data_pg1(page_1_text)     # using get_data_pg1 function

        # print(page_data)
        df = pd.DataFrame(page_data, index=[0])    # changing into dataframe
        #print(df)
        df.to_csv(output_data.replace('.pdf', '_metadata.csv'), index=None)     # converting df into csv file



        # Extractiong sample summary
        page_2_text = pdf[1]              # getting page 2 data
        page_2_text = page_2_text.split('\n')

        
        page_data = get_data_pg2(page_2_text)     # using get_data_pf2 function
        df = pd.DataFrame(page_data,index=[0])    # changing into dataframe
        del df['Disclaimer']                      # deleting the column containg "Disclaimer"
        df.to_csv(output_data.replace('.pdf', '_sample_summary.csv'),index=None)    # changing dataframe to csv

        # extracting dst_table

        page_3_text = pdf[2]                # extacting page 3 containing dst_table
        page_3_text = page_3_text.split('\n')


        # extracting dst_table

        page_data = get_data_pg3(page_3_text)    # calling get_data_pg3 function to extract data into dictionary
        df = pd.DataFrame(page_data,index=[0])   # dictionary to dataframe
        df = df.add_suffix(")")                  # split() removes ")", so adding ')' after every column with add_suffix() 
        df.to_csv(output_data.replace('.pdf', '_dst_table.csv'),index=None)    # converting dataframe into csv


        # extracting clinical summary
        clinical_summary = open(path_file.replace('.pdf','.txt'),'wb')    # creating a txt file to extract clinical summary from page 3
        text = pdf[2].encode("utf8")     # encoding text
        clinical_summary.write(text)     # writing into text file 
        clinical_summary.write(bytes((12,)))  # write page delimiter (form feed 0x0C)   # decimal to hexadecimal
        clinical_summary.close()         # closing text file

        
        text = open(path_file.replace('pdf','txt'), "r+")   # reading the txt file to delete unwanted lines
        readtext =text.readlines()
        
        del readtext[0]
        del readtext[3::]


        new_file = open(path_file.replace('.pdf','.txt'),"w+")   # updating the txt file with only the required part, i.e.. clinical summary data

        for line in readtext:
            line = line.replace("\n",",").strip()    # replacing new line ("\n") with "," and strip() removes all the spaces
            line = line.replace("    ",",").strip()   
            new_file.write(line)                     # writing everything into the same text file
                    
        new_file.close()

        dataframe = pd.read_csv(path_file.replace('.pdf','.txt'))    # reading text file as a dataframe

        dataframe = dataframe.loc[:,~dataframe.columns.str.match("Unnamed")]    # removing Unnamed columns
        dataframe.T.to_csv(output_data.replace('.pdf','_clinical_summary.csv'),header=False)   # transposing the csv file into a single column

        dataframe = pd.read_csv(output_data.replace('.pdf','_clinical_summary.csv'))    # reading the transposed csv file
        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",dataframe.columns)
        dataframe.rename(columns = {'Mycobacterium tuberculosis detected:':'Mycobacterium tuberculosis detected'}, inplace = True)    # renaming the column name
        
        if len(list(dataframe.T)) == 8:     # csv files containg one extra row
            # print("it has 8 element")         
           
            dataframe['Mycobacterium tuberculosis detected'][4] =dataframe['Mycobacterium tuberculosis detected'][4] + dataframe['Mycobacterium tuberculosis detected'][7]   # concatinating the extra row into another row which should contain the data
            data=dataframe['Mycobacterium tuberculosis detected'].drop([7])       # dropping the extra row     
            data.to_csv(output_data.replace('.pdf','_clinical_summary.csv'),header=True,index=None)    
        else:                               # csv file without the extra row
            data = dataframe['Mycobacterium tuberculosis detected']
            data.to_csv(output_data.replace('.pdf','_clinical_summary.csv'),header=True,index=None)

        dataframe = pd.read_csv(output_data.replace('.pdf','_clinical_summary.csv'))        # reading all the csv files containing clinical summary

        x=dataframe.columns     # x containg all the columns
        a=(str(dataframe.columns).replace("Index(['", "")).replace("'], dtype='object')", "")   # replacing with empty lines

        col=a       
        row=dataframe[a][0]

        # adding alternative rows from the csv file to col and row variable based on odd and even indexing
        for i in range(int(len(dataframe)/2)):
            col=col+','+dataframe[a][2*i+1]
            row=row+','+dataframe[a][2*i+2]

        new_csv=open(output_data.replace('.pdf','_clinical_summary.csv'),'w')   # updating the csv file
        new_csv.write(col+'\n'+row)                 # adding new col and row to the csv file
        new_csv.close()


        # Extracting mutation table

        df = read_pdf(path_file, pages=5, stream=True)    # using read_pdf from tabula.io to extract tables
        if df == []:                                      # pdf with no tables contain empty dataframe
            sample_data = open(output_data.replace('.pdf','_mutation_table.csv'),'w')
            sample_data.write("No Mutations were Detected")     # writing in the csv file showing no tables
            sample_data.close()
            #print("No Mutations were Detected!")
        else:                                             # if pdf contains tables
            df[0].to_csv(output_data.replace('.pdf','_mutation_table.csv'),index=None)  # converting dataframe into csv    

    return(output_data)

# running the dataextract function in loop for all pdf files present
for path_file in list_filenames:
    output_data = dataextract(path_file, output_path)
    output_data = output_data.replace(output_data.split("/")[-1],"")
    


