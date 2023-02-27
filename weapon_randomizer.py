from bcml import util
import oead
import json
import random
import os
import botw_flag_util.generator as flag_util
from bcml.install import install_mod, link_master_mod
import shutil
from pathlib import Path

class Generator:
    def __init__(self, be: bool):
        self.big_endian = be

    actor: bool = False
    revival: list = [1, 1]
    directory: str = "Weapon Randomizer"
    bigendian: bool = True
    verbose: bool = False

RULES = str('[Definition]\n' + 
'titleIds = 00050000101C9300,00050000101C9400,00050000101C9500\n' +
'name = Weapon Randomizer\n' + 
'path = The Legend of Zelda: Breath of the Wild/Mods/Weapon Randomizer\n' +
'description = Randomizes standalone weapons, chest weapons and enemy weapons (except for Wizzrobes) at choice everywhere in the game.\n' +
'version = 7')

MOD_META = {
    "name": "Weapon Randomizer",
    "image": "",
    "url": "",
    "desc": "",
    "version": "1.0",
    "options": {},
    "depends": [],
    "showCompare": False,
    "showConvert": False,
    "platform": "wiiu" if util.get_settings("wiiu") == True else "switch",
    "id": ""
}

#Importing all configuration files

with open('config.json') as config:
    CONFIG = json.loads(config.read())

with open('file_list.json') as file_list:
    FILE_LIST = json.loads(file_list.read())

with open('weapons.json') as weapons:
    WEAPONS = json.loads(weapons.read())

#Creating the weapon tables

ARROWS = WEAPONS['Arrow']
BOWS = ['Weapon_Bow_' + WEAPONS['Bow'][i] for i in range(len(WEAPONS['Bow']))]
LSWORDS = ['Weapon_Lsword_' + WEAPONS['Lsword'][i] for i in range(len(WEAPONS['Lsword']))]
SHIELDS = ['Weapon_Shield_' + WEAPONS['Shield'][i] for i in range(len(WEAPONS['Shield']))]
SPEARS = ['Weapon_Spear_' + WEAPONS['Spear'][i] for i in range(len(WEAPONS['Spear']))]
SWORDS = ['Weapon_Sword_' + WEAPONS['Sword'][i] for i in range(len(WEAPONS['Sword']))]

WELCOME = str(
    + "Your settings are as follows: \n"
    + "\n"
    + "Randomize enemy weapons: " + str(CONFIG['enemies'])
    + "\nRandomize chest weapons: " + str(CONFIG['chests'])
    + "\nRandomize standalone weapons: " + str(CONFIG['standalone'])
    + "\nAuto Install with BCML: " + str(CONFIG['autoinstall'])
    + "\n\nIf you want to modify them, feel free to modify config.json .\n\n"
    + "Are you okay with these settings ? y/n : "
)

#Utility function

def to_oead(obj):
    obj_type = type(obj)

    if obj_type not in [int, float, list, dict]:
        return obj

    if obj_type is int:
        try:
            return oead.S32(obj)
        except:
            return oead.U32(obj)

    elif obj_type is float:
        return oead.F32(obj)

    elif obj_type is list:
        _list = list()
        for item in list(obj):
            _list.append(to_oead(item))
        return oead.byml.Array(_list)

    elif obj_type is dict:
        _dict = dict()
        for key, value in dict(obj).items():
            _dict[to_oead(key)] = to_oead(value)
        return _dict
    
#Function to fully and randomly change the weapons from an object data

def change_actor(config_data):

    actor_name = config_data['UnitConfigName']
    if 'Enemy_' in actor_name and CONFIG['enemies'] and not 'Wizzrobe' in actor_name:

        if '!Parameters' in config_data:
            for parameter in config_data['!Parameters']:
                if 'EquipItem' in parameter:
                    if 'Weapon_Spear' in config_data['!Parameters'][parameter]:
                        config_data['!Parameters'][parameter] = random.choice(SPEARS)
                    elif 'Weapon_Sword' in config_data['!Parameters'][parameter]:
                        config_data['!Parameters'][parameter] = random.choice(SWORDS)
                    elif 'Weapon_Lsword' in config_data['!Parameters'][parameter]:
                        config_data['!Parameters'][parameter] = random.choice(LSWORDS)
                    elif 'Weapon_Shield' in config_data['!Parameters'][parameter]:
                        config_data['!Parameters'][parameter] = random.choice(SHIELDS)
                    elif 'Weapon_Bow' in config_data['!Parameters'][parameter]:
                        config_data['!Parameters'][parameter] = random.choice(BOWS)
                if 'ArrowName' in parameter:
                    config_data['!Parameters'][parameter] = random.choice(ARROWS)

    elif 'TBox' in actor_name and CONFIG['chests']:

        if '!Parameters' in config_data:
            if 'DropActor' in config_data['!Parameters']:
                parameter = 'DropActor'
                if 'Weapon_Spear' in config_data['!Parameters'][parameter]:
                    config_data['!Parameters'][parameter] = random.choice(SPEARS)
                elif 'Weapon_Sword' in config_data['!Parameters'][parameter]:
                    config_data['!Parameters'][parameter] = random.choice(SWORDS)
                elif 'Weapon_Lsword' in config_data['!Parameters'][parameter]:
                    config_data['!Parameters'][parameter] = random.choice(LSWORDS)
                elif 'Weapon_Shield' in config_data['!Parameters'][parameter]:
                    config_data['!Parameters'][parameter] = random.choice(SHIELDS)
                elif 'Weapon_Bow' in config_data['!Parameters'][parameter]:
                    config_data['!Parameters'][parameter] = random.choice(BOWS)

    elif 'Weapon_' in actor_name and CONFIG['standalone']:
        if 'Weapon_Spear' in actor_name:
            config_data['UnitConfigName'] = random.choice(SPEARS)
        elif 'Weapon_Sword' in actor_name:
            config_data['UnitConfigName'] = random.choice(SWORDS)
        elif 'Weapon_Lsword' in actor_name:
            config_data['UnitConfigName'] = random.choice(LSWORDS)
        elif 'Weapon_Shield' in actor_name:
            config_data['UnitConfigName'] = random.choice(SHIELDS)
        elif 'Weapon_Bow' in actor_name:
            config_data['UnitConfigName'] = random.choice(BOWS)

    return config_data

#Functions to modify map and pack files

def change_map(data, map_unit):
    
    file_map_decr = oead.byml.from_binary(oead.yaz0.decompress(data))
    
    for unit_config in file_map_decr["Objs"]:

        unit_config = change_actor(unit_config)

    if map_unit is not None:
        print(f'Randomized {map_unit}')

    return oead.yaz0.compress(oead.byml.to_binary(to_oead(file_map_decr), True))

def change_pack(data, pack_name):

    sarc = oead.Sarc(data)
    sarc_writer = oead.SarcWriter(endian=oead.Endianness.Big)

    for file in sarc.get_files():
        if file.name.endswith(".smubin") and not file.name.endswith("_NoGrudgeMerge.smubin"):
            sarc_writer.files[file.name] = change_map(file.data, None)
        else:
            sarc_writer.files[file.name] = oead.Bytes(file.data)

    print(f"Randomized '{pack_name}'")

    _, sarc_bytes = sarc_writer.write()
    return sarc_bytes

#Functions to operate the changes

def change_all_mainfield():
    for file in FILE_LIST['MainField files']:
        
        file_data = util.get_game_file(file, aoc = False).read_bytes()
        file_data = change_map(file_data, file)

        folder = os.path.join('Weapon Randomizer\\content\\Map\\MainField\\' + file[18:21])
        os.makedirs(folder, exist_ok = True)

        with open('Weapon Randomizer\\content\\' + file,'wb') as f:
            f.write(file_data)

def change_all_non_dlc_shrines():
    for file in FILE_LIST['Base Packs']:

        file_data = util.get_game_file(file, aoc = False).read_bytes()
        file_data = change_pack(file_data, file)

        folder = os.path.join('Weapon Randomizer\\content\\Pack')
        os.makedirs(folder, exist_ok = True)

        with open('Weapon Randomizer\\content\\' + file, 'wb') as f:
            f.write(file_data)

def change_all_dlc_shrines():
    for file in FILE_LIST['DLC shrine packs']:

        file_data = util.get_game_file(file, aoc = True).read_bytes()
        file_data = change_pack(file_data, file)

        folder = os.path.join('Weapon Randomizer\\aoc\\0010\\Pack')
        os.makedirs(folder, exist_ok = True)

        with open('Weapon Randomizer\\aoc\\0010\\' + file, 'wb') as f:
            f.write(file_data)

def change_divine_beasts():
    for file in FILE_LIST['Divine Beast packs']:

        file_data = util.get_game_file(file, aoc = True).read_bytes()
        file_data = change_pack(file_data, file)

        folder = os.path.join('Weapon Randomizer\\aoc\\0010\\Pack')
        os.makedirs(folder, exist_ok = True)

        with open('Weapon Randomizer\\aoc\\0010\\' + file, 'wb') as f:
            f.write(file_data)

def change_trials():
    for file in FILE_LIST['Trials files']:

        file_data = util.get_game_file(file, aoc = True).read_bytes()
        file_data = change_pack(file_data, file)

        folder = os.path.join('Weapon Randomizer\\aoc\\0010\\Map\\AocField' + file[17:20])
        os.makedirs(folder, exist_ok = True)

        with open('Weapon Randomizer\\aoc\\0010\\' + file, 'wb') as f:
            f.write(file_data)

def create_rules():
    with open('Weapon Randomizer\\rules.txt', 'w') as f:
        f.write(RULES)

def create_meta():
    with open('Weapon Randomizer\\info.json', 'w') as f:
        f.write(json.dumps(MOD_META, indent = 2))

def main():

    if input(WELCOME) != 'y':
        print('Cancelled randomization')

    else:
        change_all_mainfield()
        change_all_non_dlc_shrines()
        change_all_dlc_shrines()
        change_divine_beasts()
        change_trials()
        create_rules()
        create_meta()
        bootup_path = Path("Weapon Randomizer\\content\\Pack\\Bootup.pack")
        bootup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(util.get_game_file("Pack/Bootup.pack"), bootup_path)
        flag_util.generate(Generator(util.get_settings("wiiu")))
        if CONFIG['autoinstall']:
            mod_path = Path('Weapon Randomizer\\info.json')
            mod_meta = MOD_META
            mod_path.write_text(json.dumps(mod_meta))
            install_mod(mod=mod_path, merge_now=True)
            link_master_mod()

if __name__ == '__main__':
    main()