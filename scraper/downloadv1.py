"""
A downloading library, must be run in the cwd of the library
"""

"""
 A useful fragment that I found
# display link counts
for url in links:
    if ('data:image/' not in url[0:20]) and ('https://encrypted' not in url[0:20]):
        count += 1
        

"""


import urllib.request
import urllib3
import pathlib
import socket
import imghdr
import os
import sys
import time
from subprocess import Popen, PIPE
from tensorflow import io
from tensorflow import image
import os
import multiprocessing
from multiprocessing import Process
from multiprocessing import Semaphore
import time
import sys

socket.setdefaulttimeout(5)


#DELETES CORRUPTED IMAGES ---------------------------------------------------------------------------

WHITELIST_FORMATS = ["jpeg", "jpg", "bmp", "png", "gif"]
def checkImage(fn):
    proc = Popen(['magick', 'identify', '-verbose', fn], stdout=PIPE, stderr=PIPE)
    out, _ = Popen(['magick', 'identify', '-format', "%m:%f", fn], stdout=PIPE, stderr=PIPE).communicate()
    _, err = proc.communicate()
    exitcode = proc.returncode
    return exitcode, out, err

#doesnt delete any images that might have the wrong file format... but also dont want it deleting text files or directories
def checkFiles(folder, WHITELIST_FORMATS = ["jpeg", "jpg", "bmp", "png", "gif"], VERIFIED_FILES = ["args_txt.txt", "error_logs.txt", "error_links.txt", "all_links.txt", ".py"], start = 0):

    #a method to try and load in the image to see that it will indeed decode just fine
    def checkDecodingTF_Image_Decode(filename):
        can_load = True
        try:
            im = io.read_file(filename)
            im = image.decode_image(im, channels=3, expand_animations=False).numpy()
        except Exception as e:
            can_load = False
        return can_load

    count = 0
    for directory, subdirectories, files, in os.walk(folder):
        for file in files:
            #checks to make sure that we arent going to overwrite any .py files or any config or error .txt files that we generate
            if True not in [VERIFIED_FILES[i] in file for i in range(len(VERIFIED_FILES))] and count >= start:
                filePath = os.path.join(directory, file)
                code, output, error = checkImage(filePath)

                #gets us the file's suffix and the type of the file, lowecased to compare
                outputs = str(output)[1:].replace("'", "").split(":")
                if len(outputs) > 1:
                    outputs[0] = outputs[0].lower()
                    outputs[1] = outputs[1].split(".")[1].lower()
                    if outputs[0] != outputs[1] and outputs[0] in WHITELIST_FORMATS:
                        os.rename(str(filePath), str(filePath).replace(outputs[1], outputs[0]))

                    #boolean that tells us if the image is corrupted or if the image can't be decoded
                    cant_load = (str(code) !="0" or str(error, "utf-8") != "" or outputs[0] not in WHITELIST_FORMATS) or not checkDecodingTF_Image_Decode(filePath)

                    #removes the image if it is corrupted and returns can_load
                    if cant_load:
                        print("ERROR " + filePath)
                        print(str(error))
                        os.remove(str(filePath))
                else:
                    print("ERROR " + filePath)
                    print("Couldnt open the image or anything")
                    os.remove(str(filePath))

            if count % 500 == 0:
                print("Verified " + str(count) + " files         " + str(folder))
            count += 1


    if count == 0:
        print("No files found in folder: " + str(folder))

def task(semaphore, dir):
    semaphore.acquire()
    checkFiles(dir)
    semaphore.release()


def parallel_checker(folders, maxProcesses):

    print("Max Threads: " + str(maxProcesses))
    assert maxProcesses <= multiprocessing.cpu_count()

    proc = []
    sema = Semaphore(maxProcesses)

    for dir in folders:
        p = Process(target = task, args = [sema, dir])
        p.start()
        proc.append(p)
        time.sleep(1)

    for p in proc:
        p.join()



#-------------------------------------------------------------------------------------------------------




def download(links, folder):
    curr_fp = pathlib.Path(__file__).parent.absolute()
    #fp is the folder we will be downloading into
    pathlib.Path("downloads").mkdir(exist_ok = True)
    fp = pathlib.Path("downloads/" + folder[:254])

    subfolder = pathlib.Path("downloads/" + folder[:254] + "/fullsize")
    subfolder.mkdir(exist_ok = True)
    subfolder = pathlib.Path("downloads/" + folder[:254] + "/previews")
    subfolder.mkdir(exist_ok = True)

    error_links = open(str(fp) + "/error_links.txt", "a+")
    error_logs = open(str(fp) + '/' + "error_logs.txt", "a+")

    errors = 0
    print(str(len(links)) + " links found")
    for i in range(len(links)):
        subfolder = ""
        if ('data:image/' not in links[i][0:20]) and ('https://encrypted' not in links[i][0:20]):
            subfolder = "/fullsize/"
        else:
            subfolder = "/previews/"
        if i % 500 == 0:
            print("Downloaded " + str(i) + "...     " + folder)
        try:
            ending = "jpeg"
            for format in WHITELIST_FORMATS:
                if format in links[i].lower():
                    ending = format
                    if format == "jpg":
                        ending = "jpeg"
                    break

            #download line
            urllib.request.urlretrieve(links[i], "downloads/" + folder[:254] + subfolder + str(i) + "." + ending)

            #----------------Checking proper file format for image
            file_type = imghdr.what("downloads/" + folder[:254] + subfolder + str(i) + "." + ending)
            if file_type == ending:
                pass
            elif not (file_type in WHITELIST_FORMATS):
                os.remove("downloads/" + folder[:254] + subfolder + str(i) + "." + ending)
                raise Exception("Improper format: " + str(file_type))
            elif (file_type in WHITELIST_FORMATS) and (file_type != ending):
                os.rename("downloads/" + folder[:254] + subfolder + str(i) + "." + ending,
                    "downloads/" + folder[:254] + subfolder + str(i) + "." + file_type)
            else:
                raise Exception("URL Error")
            #---------------------------------

        except Exception as err:
            #os.remove("downloads/" + folder[:254] + subfolder + str(i - errors) + "." + ending)
            errors += 1
            error_links.write(links[i] + "\n")
            error_logs.write(links[i] + "\n")
            error_logs.write(str(err) + "\n" + "\n")

    print("Checking files' validity")
    checkFiles("downloads/" + folder[:254])

    print("Pictures succesfully downloaded      " + folder)


def scan_for_mislabeled(folder):
    WHITELIST_FORMATS = ["jpeg", "bmp", "png", "gif", "args_txt.txt", "error_logs.txt", "error_links.txt", "all_links.txt"]
    count = 0
    for directory, subdirectories, files, in os.walk(folder):
        for file in files:
            if True not in [WHITELIST_FORMATS[i] in file for i in range(len(WHITELIST_FORMATS))]:
                print(str(file))



#---------------------------------------

if __name__ == "__main__":
    if len(sys.argv) == 1:
        searchterm = open("download_from_folder_config.txt", 'r').read().split("; ")
        for folder in searchterm:
            curr_fp = pathlib.Path(__file__).parent.absolute()
            #fp is the folder we will be downloading into
            pathlib.Path("downloads").mkdir(exist_ok = True)
            fp = pathlib.Path("downloads/" + folder[:254])

            links = open(str(fp) + "/all_links.txt", 'r').read().split("\n")

            download(links, folder)

    #for when we call this script from another function with args on the command line
    else:
        folder = sys.argv[1]

        curr_fp = pathlib.Path(__file__).parent.absolute()
        #fp is the folder we will be downloading into
        pathlib.Path("downloads").mkdir(exist_ok = True)
        fp = pathlib.Path("downloads/" + folder[:254])

        links = open(str(fp) + "/all_links.txt", 'r').read().split("\n")

        download(links, folder)
