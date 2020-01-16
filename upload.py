#!/usr/bin/env python

import os
import re
import sys
import shelve
import getpass
import subprocess

from datetime   import datetime, timedelta
from subprocess import Popen, CalledProcessError


def count(top, weeks_included):
  count = 0
  for dirpath, _, filenames in filter(lambda t: modified_last_n_weeks(weeks_included, t[0]),
                                      os.walk(top)):
    print("\nInspecting directory: " + dirpath)
    for filename in filenames:
      filepath = os.path.join(dirpath, filename)
      print("Inspecting file: " + filepath)
      if filename.lower().endswith((".dicom", ".jpg", ".jpeg")):
        print("Found file: " + filepath)
        count += 1
      else:
        print("Ignoring non image file: " + filepath)
    print("Finished with directory: " + dirpath + "\n")
  print("\n\n**********\nNumber of files to transfer: " + str(count))


def do_send_image(command_array):
  with Popen(command_array, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
    for line in proc.stdout:
      print(line)
      sys.stdout.flush()

  if proc.returncode == 0:
    return True
  else:
    raise CalledProcessError(proc.returncode, proc.args)

def send_dicom_image_rest(filepath, test):
  print("curl -K curl_credentials -X POST http://localhost:8042/instances --data-binary @" + filepath)
  if test:
    return False
  else:
    return do_send_image(["curl", "-K", "curl_credentials", "-X", "POST", "http://localhost:8042/instances", "--data-binary", "@" + filepath])

def send_dicom_image_dcmtools(filepath, test):
  if test:
    print("docker exec -it dcmtools stowrs --url http://localhost:8080/dcm4chee-arc/aets/DCM4CHEE/rs/studies " + filepath)
    return False
  else:
    # start container with:
    # docker run -it --rm --network host --name dcmtools --mount type=bind,source=/run/imagerie,target=/run/imagerie dcm4che/dcm4che-tools bash
    return do_send_image(["docker", "exec", "-it", "dcmtools", "stowrs", "--url", "http://localhost:8080/dcm4chee-arc/aets/DCM4CHEE/rs/studies", filepath])

def send_dicom_image(filepath, test):
  return send_dicom_image_rest(filepath, test)

def split_jpg_path(path, prefix):
  components = (path, [])
  while not ((components[0] == prefix) or (components[0] + "/" == prefix)):
    if components[0] == "/":
      raise Exception("Root of filesystem reached.")
    c = os.path.split(components[0])
    components = (c[0], components[1] + [c[1]])
  return components[1]


def search_attributes(components):
  datestr = name = None
  for c in components:
    if not datestr:
      datestr = re.search(r"[0-9]{14}", c).group()
    if not name:
      n = re.search(r"[a-zA-Z ]{3}[a-zA-Z ]*", c.replace("jpg", ""))
      if n:
        name = n.group()
  return (datestr, name.split(" "))


def send_jpg_image(filepath, test):
  print("Sending of JPG images is not yet supported.")
  return False


def send_image(filepath, test):
  if filepath.lower().endswith(".dicom"):
    return send_dicom_image(filepath, test)
  elif filepath.lower().endswith((".jpg", ".jpeg")):
    return send_jpg_image(filepath, test)
  else:
    raise Exception("Unknown file extension: " + filepath)


def modified_last_n_weeks(weeks_included, directory):
  # 104 weeks = 2 years
  return datetime.fromtimestamp(os.path.getmtime(directory)) > (datetime.now() - timedelta(weeks = weeks_included))

def print_summary(images_found, images_sent, images_already_sent):
  print("\n****" +
        "\nImages found: " + str(images_found) +
        "\nImages sent: " + str(images_sent) + 
        "\nImages already sent: " + str(images_already_sent) +
        "\nImages that could not be sent: " + str(images_found - images_sent - images_already_sent) +
        "\n****\n")


def do_walk(top, weeks_included, s, test):
  print("Starting to walk " + top + "...")
  images_found = 0
  images_sent  = 0
  images_already_sent = 0
  for dirpath, _, filenames in filter(lambda t: modified_last_n_weeks(weeks_included, t[0]),
                                      os.walk(top)):
#                                      sorted(os.walk(top),
#                                             key = lambda t: os.path.getmtime(t[0]),
#                                             reverse = True)):
    print("\nInspecting directory: " + dirpath)
    for path in map(lambda f: os.path.join(dirpath, f), filenames):
      print("Inspecting file: " + path)
      if path.lower().endswith((".dicom", ".jpg", ".jpeg")):
        images_found += 1
        if not path in s:
          print("Sending image at: " + path)
          if send_image(path, test):
            s[path] = True
            s.sync()
            images_sent += 1
        else:
          images_already_sent += 1
          print("Ignoring already uploaded file: " + path)
      else:
        print("Ignoring unsupported filetype: " + path)
    print("Finished with directory: " + dirpath + "\n")
    print_summary(images_found, images_sent, images_already_sent)


def walk(top, weeks_included, shelve_name = "upload.dat", test = True):
  with shelve.open(shelve_name, flag = "c", writeback = True) as s:
    do_walk(top, weeks_included, s, test)


def main(args):
  if len(args) < 2 or len(args[1].strip()) == 0:
    raise Exception("Specify the directory to scan.")

  weeks_included = 52 * 30

  walk_dir = os.path.abspath(args[1])
  print('walk_dir = ' + walk_dir)
  #count(walk_dir, weeks_included)
  #walk(walk_dir, weeks_included)
  walk(walk_dir, weeks_included, shelve_name = "run/upload_prod.dat", test = False)

if __name__ == "__main__":
  # Exec the main function
  main(sys.argv)


