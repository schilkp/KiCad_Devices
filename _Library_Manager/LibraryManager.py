import json
import os
from os.path import join, isfile, isdir


class DeviceParseWarning(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class DeviceParseError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


def link_path_clean(path):
    if path.startswith("./"):
        path = path.replace("./", "", 1)
    if path.startswith("../"):
        path = path.replace("../", "", 1)
    return path


def nbsp_pad(count):
    result = ""
    for i in range(count):
        result += "&nbsp;"
    return result


class Device:
    def __init__(self, path, settings):

        self.settings = settings

        # Attempt to open Device properties file
        try:
            with open(join(path, 'Device.json')) as device_file:
                self.properties = json.load(device_file)
        except FileNotFoundError:
            raise DeviceParseWarning("Warning: " + path + " does not contain a Device.json file! Continuing..")
        except json.decoder.JSONDecodeError:
            raise DeviceParseError("Error: Device.json for " + path + " did not parse!")

        # Make sure all needed settings are specified:
        needed_properties = ['Device_Name']

        for device_property in needed_properties:
            if device_property not in self.properties:
                raise DeviceParseError("Error: Device.json for " + path + " does not specify " + device_property)

        # Track down all pictures

        self.imgs_symbol = []
        self.imgs_footprint = []

        img_dir = join(path, settings['Image_Directory'])
        images = [f for f in os.listdir(img_dir) if isfile(join(img_dir, f))]

        for image in images:
            if image.startswith(settings['SymbolImage_Name']):
                self.imgs_symbol.append(join(img_dir, image))
            elif image.startswith(settings['FootprintImage_Name']):
                self.imgs_footprint.append(join(img_dir, image))
            else:
                print("Warning: Found " + join(img_dir, image) + " but unsure what to do!")

    def table_entry(self):
        # Name and Description
        entry = "| "
        entry += "**" + self.properties['Device_Name'] + "**"

        if 'Device_Description' in self.properties:
            entry += " <br/> " + self.properties['Device_Description']

        # Symbol notes and images
        entry += " | "

        if 'Symbol_Note' in self.properties:
            entry += self.properties['Symbol_Note']

        for image in self.imgs_symbol:
            entry += " <br/> ![" + self.properties['Device_Name'] + " Symbol ]("

            entry += link_path_clean(image)

            entry += ")"

        # Footprint notes and images
        entry += " | "

        if 'Footprint_Note' in self.properties:
            entry += self.properties['Footprint_Note']

        for image in self.imgs_footprint:
            entry += " <br/> ![" + self.properties['Device_Name'] + " Footprint ]("

            entry += link_path_clean(image)

            entry += ") "

        # Finish Table
        entry += " |"

        return entry


working_dir = ""
settings_dir = ""
global_settings = None

# Find and read Settings File
# If it is in LibraryManager/, search for the library in this directory
# If it is in the current directory, search for the library in the enclosing directory
if isfile('Settings.json'):
    working_dir = ".."
    settings_dir = "."
elif isfile('_Library_Manager/Settings.json'):
    working_dir = "."
    settings_dir = "_Library_Manager"
else:
    print('Error: Settings.json not found!')
    exit()

try:
    with open(join(settings_dir, 'Settings.json')) as settings_file:
        global_settings = json.load(settings_file)
except json.decoder.JSONDecodeError:
    print('Error parsing Settings.json!')
    exit()
except FileNotFoundError:
    print('Error: Settings.json not found!')
    exit()

# Make sure all needed settings are specified:
needed_settings = ['ImageResize_Width_Default', 'Image_Directory', 'SymbolImage_Name', 'FootprintImage_Name',
                   'ResizedImage_Directory', 'Table_nbsp_Pad_Device', 'Table_nbsp_Pad_Symbol',
                   'Table_nbsp_Pad_Footprint', 'Ignore_Directories']

for setting in needed_settings:
    if setting not in global_settings:
        print('Error: Setting.json does not specify \'' + setting + '\'')
        exit()

# Make sure the padding counts are int:
if not isinstance(global_settings['Table_nbsp_Pad_Device'], int) \
        or not isinstance(global_settings['Table_nbsp_Pad_Symbol'], int) \
        or not isinstance(global_settings['Table_nbsp_Pad_Footprint'], int):
    print('Error: nbsp padding count needs to be an int!')
    exit()

# ==== Parse Library ====
lib = []

directories = [f for f in os.listdir(working_dir) if isdir(join(working_dir, f))]

for directory in directories:
    if directory not in global_settings['Ignore_Directories']:
        try:
            if ' ' in directory:
                raise DeviceParseError("Error: Folder name contains space: " + directory)
            lib.append(Device(join(working_dir, directory), global_settings))
        except DeviceParseError as e:
            print(e)
            exit()
        except DeviceParseWarning as e:
            did_warn = True
            print(e)

# ==== Cleanup previously generated files ====

readme_path = join(working_dir, 'README.md')
if isfile(readme_path):
    os.remove(readme_path)

# ==== Generate Images (later/TODO) ====

# ==== Generate README ====
readme = ""

# Add Readme prefix from file
with open(settings_dir + '/README_PREFIX.md') as prefix_file:
    for line in prefix_file:
        readme += line

# Generate Table header

pad_dev = global_settings['Table_nbsp_Pad_Device']
pad_sym = global_settings['Table_nbsp_Pad_Symbol']
pad_foot = global_settings['Table_nbsp_Pad_Footprint']

readme += "|" + nbsp_pad(pad_dev) + "**Device**" + nbsp_pad(pad_dev) + \
          "|" + nbsp_pad(pad_sym) + "**Symbol**" + nbsp_pad(pad_sym) + \
          "|" + nbsp_pad(pad_foot) + "**Footprint**" + nbsp_pad(pad_foot) + \
          "|\n"

readme += "|---|---|---|\n"

# Generate Table
for device in lib:
    readme += device.table_entry() + "\n"

# Add Readme postfix from file
with open(settings_dir + '/README_POSTFIX.md') as postfix_file:
    for line in postfix_file:
        readme += line

with open(readme_path, 'w') as readme_file:
    readme_file.write(readme)
