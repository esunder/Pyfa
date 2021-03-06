# ===============================================================================
# Copyright (C) 2014 Ryan Holmes
#
# This file is part of eos.
#
# eos is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# eos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with eos.  If not, see <http://www.gnu.org/licenses/>.
# ===============================================================================

import math
import re
from collections import OrderedDict

from logbook import Logger
from sqlalchemy.orm import reconstructor

import eos.db


pyfalog = Logger(__name__)


BUILTINS = OrderedDict([
    # 0 is taken by ideal target profile, composed manually in one of TargetProfile methods
    (-1, ('Uniform (25%)', 0.25, 0.25, 0.25, 0.25)),
    (-2, ('Uniform (50%)', 0.50, 0.50, 0.50, 0.50)),
    (-3, ('Uniform (75%)', 0.75, 0.75, 0.75, 0.75)),
    (-4, ('Uniform (90%)', 0.90, 0.90, 0.90, 0.90)),
    (-5, ('[T1 Resist]Shield', 0.0, 0.20, 0.40, 0.50)),
    (-6, ('[T1 Resist]Armor', 0.50, 0.45, 0.25, 0.10)),
    (-7, ('[T1 Resist]Hull', 0.33, 0.33, 0.33, 0.33)),
    (-8, ('[T1 Resist]Shield (+T2 DCU)', 0.125, 0.30, 0.475, 0.562)),
    (-9, ('[T1 Resist]Armor (+T2 DCU)', 0.575, 0.532, 0.363, 0.235)),
    (-10, ('[T1 Resist]Hull (+T2 DCU)', 0.598, 0.598, 0.598, 0.598)),
    (-11, ('[T2 Resist]Amarr (Shield)', 0.0, 0.20, 0.70, 0.875)),
    (-12, ('[T2 Resist]Amarr (Armor)', 0.50, 0.35, 0.625, 0.80)),
    (-13, ('[T2 Resist]Caldari (Shield)', 0.20, 0.84, 0.76, 0.60)),
    (-14, ('[T2 Resist]Caldari (Armor)', 0.50, 0.8625, 0.625, 0.10)),
    (-15, ('[T2 Resist]Gallente (Shield)', 0.0, 0.60, 0.85, 0.50)),
    (-16, ('[T2 Resist]Gallente (Armor)', 0.50, 0.675, 0.8375, 0.10)),
    (-17, ('[T2 Resist]Minmatar (Shield)', 0.75, 0.60, 0.40, 0.50)),
    (-18, ('[T2 Resist]Minmatar (Armor)', 0.90, 0.675, 0.25, 0.10)),
    (-19, ('[NPC][Asteroid]Angel Cartel', 0.54, 0.42, 0.37, 0.32)),
    (-20, ('[NPC][Asteroid]Blood Raiders', 0.34, 0.39, 0.45, 0.52)),
    (-21, ('[NPC][Asteroid]Guristas', 0.55, 0.35, 0.3, 0.48)),
    (-22, ('[NPC][Asteroid]Rogue Drones', 0.35, 0.38, 0.44, 0.49)),
    (-23, ('[NPC][Asteroid]Sanshas Nation', 0.35, 0.4, 0.47, 0.53)),
    (-24, ('[NPC][Asteroid]Serpentis', 0.49, 0.38, 0.29, 0.51)),
    (-25, ('[NPC][Deadspace]Angel Cartel', 0.59, 0.48, 0.4, 0.32)),
    (-26, ('[NPC][Deadspace]Blood Raiders', 0.31, 0.39, 0.47, 0.56)),
    (-27, ('[NPC][Deadspace]Guristas', 0.57, 0.39, 0.31, 0.5)),
    (-28, ('[NPC][Deadspace]Rogue Drones', 0.42, 0.42, 0.47, 0.49)),
    (-29, ('[NPC][Deadspace]Sanshas Nation', 0.31, 0.39, 0.47, 0.56)),
    (-30, ('[NPC][Deadspace]Serpentis', 0.49, 0.38, 0.29, 0.56)),
    (-31, ('[NPC][Mission]Amarr Empire', 0.34, 0.38, 0.42, 0.46)),
    (-32, ('[NPC][Mission]Caldari State', 0.51, 0.38, 0.3, 0.51)),
    (-33, ('[NPC][Mission]CONCORD', 0.47, 0.46, 0.47, 0.47)),
    (-34, ('[NPC][Mission]Gallente Federation', 0.51, 0.38, 0.31, 0.52)),
    (-35, ('[NPC][Mission]Khanid', 0.51, 0.42, 0.36, 0.4)),
    (-36, ('[NPC][Mission]Minmatar Republic', 0.51, 0.46, 0.41, 0.35)),
    (-37, ('[NPC][Mission]Mordus Legion', 0.32, 0.48, 0.4, 0.62)),
    (-38, ('[NPC][Other]Sleeper', 0.61, 0.61, 0.61, 0.61)),
    (-39, ('[NPC][Other]Sansha Incursion', 0.65, 0.63, 0.64, 0.65)),
    (-40, ('[NPC][Burner]Cruor (Blood Raiders)', 0.8, 0.73, 0.69, 0.67)),
    (-41, ('[NPC][Burner]Dramiel (Angel)', 0.35, 0.48, 0.61, 0.68)),
    (-42, ('[NPC][Burner]Daredevil (Serpentis)', 0.69, 0.59, 0.59, 0.43)),
    (-43, ('[NPC][Burner]Succubus (Sanshas Nation)', 0.35, 0.48, 0.61, 0.68)),
    (-44, ('[NPC][Burner]Worm (Guristas)', 0.48, 0.58, 0.69, 0.74)),
    (-45, ('[NPC][Burner]Enyo', 0.58, 0.72, 0.86, 0.24)),
    (-46, ('[NPC][Burner]Hawk', 0.3, 0.86, 0.79, 0.65)),
    (-47, ('[NPC][Burner]Jaguar', 0.78, 0.65, 0.48, 0.56)),
    (-48, ('[NPC][Burner]Vengeance', 0.66, 0.56, 0.75, 0.86)),
    (-49, ('[NPC][Burner]Ashimmu (Blood Raiders)', 0.8, 0.76, 0.68, 0.7)),
    (-50, ('[NPC][Burner]Talos', 0.68, 0.59, 0.59, 0.43)),
    (-51, ('[NPC][Burner]Sentinel', 0.58, 0.45, 0.52, 0.66)),
    # Source: ticket #2067
    (-52, ('[NPC][Invasion]Invading Precursor Entities', 0.422, 0.367, 0.453, 0.411)),
    (-53, ('[NPC][Invasion]Retaliating Amarr Entities', 0.360, 0.310, 0.441, 0.602)),
    (-54, ('[NPC][Invasion]Retaliating Caldari Entities', 0.303, 0.610, 0.487, 0.401)),
    (-55, ('[NPC][Invasion]Retaliating Gallente Entities', 0.383, 0.414, 0.578, 0.513)),
    (-56, ('[NPC][Invasion]Retaliating Minmatar Entities', 0.620, 0.422, 0.355, 0.399)),
    (-57, ('[NPC][Abyssal][Dark Matter All Tiers]Drones', 0.439, 0.522, 0.529, 0.435)),
    (-58, ('[NPC][Abyssal][Dark Matter All Tiers]Overmind', 0.643, 0.593, 0.624, 0.639)),
    (-59, ('[NPC][Abyssal][Dark Matter All Tiers]Seeker', 0.082, 0.082, 0.082, 0.082)),
    (-60, ('[NPC][Abyssal][Dark Matter All Tiers]Triglavian', 0.494, 0.41, 0.464, 0.376)),
    (-61, ('[NPC][Abyssal][Dark Matter All Tiers]Drifter', 0.415, 0.415, 0.415, 0.415)),
    (-62, ('[NPC][Abyssal][Dark Matter All Tiers]Sleeper', 0.435, 0.435, 0.435, 0.435)),
    (-63, ('[NPC][Abyssal][Dark Matter All Tiers]All', 0.508, 0.474, 0.495, 0.488)),
    (-64, ('[NPC][Abyssal][Electrical T0/T1/T2]Drones', 0.323, 0.522, 0.529, 0.435)),
    (-65, ('[NPC][Abyssal][Electrical T0/T1/T2]Overmind', 0.542, 0.593, 0.624, 0.639)),
    (-66, ('[NPC][Abyssal][Electrical T0/T1/T2]Seeker', 0, 0.082, 0.082, 0.082)),
    (-67, ('[NPC][Abyssal][Electrical T0/T1/T2]Triglavian', 0.356, 0.41, 0.464, 0.376)),
    (-68, ('[NPC][Abyssal][Electrical T0/T1/T2]Drifter', 0.277, 0.415, 0.415, 0.415)),
    (-69, ('[NPC][Abyssal][Electrical T0/T1/T2]Sleeper', 0.329, 0.435, 0.435, 0.435)),
    (-70, ('[NPC][Abyssal][Electrical T0/T1/T2]All', 0.381, 0.474, 0.495, 0.488)),
    (-71, ('[NPC][Abyssal][Electrical T3 (Some T5 Rooms)]Drones', 0.255, 0.522, 0.529, 0.435)),
    (-72, ('[NPC][Abyssal][Electrical T3 (Some T5 Rooms)]Overmind', 0.48, 0.593, 0.624, 0.639)),
    (-73, ('[NPC][Abyssal][Electrical T3 (Some T5 Rooms)]Seeker', 0, 0.082, 0.082, 0.082)),
    (-74, ('[NPC][Abyssal][Electrical T3 (Some T5 Rooms)]Triglavian', 0.268, 0.41, 0.464, 0.376)),
    (-75, ('[NPC][Abyssal][Electrical T3 (Some T5 Rooms)]Drifter', 0.191, 0.415, 0.415, 0.415)),
    (-76, ('[NPC][Abyssal][Electrical T3 (Some T5 Rooms)]Sleeper', 0.268, 0.435, 0.435, 0.435)),
    (-77, ('[NPC][Abyssal][Electrical T3 (Some T5 Rooms)]All', 0.308, 0.474, 0.495, 0.488)),
    (-78, ('[NPC][Abyssal][Electrical T4/T5/T6]Drones', 0.193, 0.522, 0.529, 0.435)),
    (-79, ('[NPC][Abyssal][Electrical T4/T5/T6]Overmind', 0.423, 0.593, 0.624, 0.639)),
    (-80, ('[NPC][Abyssal][Electrical T4/T5/T6]Seeker', 0, 0.082, 0.082, 0.082)),
    (-81, ('[NPC][Abyssal][Electrical T4/T5/T6]Triglavian', 0.206, 0.41, 0.464, 0.376)),
    (-82, ('[NPC][Abyssal][Electrical T4/T5/T6]Drifter', 0.111, 0.415, 0.415, 0.415)),
    (-83, ('[NPC][Abyssal][Electrical T4/T5/T6]Sleeper', 0.215, 0.435, 0.435, 0.435)),
    (-84, ('[NPC][Abyssal][Electrical T4/T5/T6]All', 0.247, 0.474, 0.495, 0.488)),
    (-85, ('[NPC][Abyssal][Firestorm T0/T1/T2]Drones', 0.461, 0.425, 0.541, 0.443)),
    (-86, ('[NPC][Abyssal][Firestorm T0/T1/T2]Overmind', 0.666, 0.489, 0.634, 0.646)),
    (-87, ('[NPC][Abyssal][Firestorm T0/T1/T2]Seeker', 0.084, 0, 0.084, 0.084)),
    (-88, ('[NPC][Abyssal][Firestorm T0/T1/T2]Triglavian', 0.537, 0.269, 0.489, 0.371)),
    (-89, ('[NPC][Abyssal][Firestorm T0/T1/T2]Drifter', 0.43, 0.289, 0.43, 0.43)),
    (-90, ('[NPC][Abyssal][Firestorm T0/T1/T2]Sleeper', 0.512, 0.402, 0.512, 0.512)),
    (-91, ('[NPC][Abyssal][Firestorm T0/T1/T2]All', 0.537, 0.352, 0.512, 0.495)),
    (-92, ('[NPC][Abyssal][Firestorm T3 (Some T5 Rooms)]Drones', 0.461, 0.36, 0.541, 0.443)),
    (-93, ('[NPC][Abyssal][Firestorm T3 (Some T5 Rooms)]Overmind', 0.666, 0.413, 0.634, 0.646)),
    (-94, ('[NPC][Abyssal][Firestorm T3 (Some T5 Rooms)]Seeker', 0.084, 0, 0.084, 0.084)),
    (-95, ('[NPC][Abyssal][Firestorm T3 (Some T5 Rooms)]Triglavian', 0.537, 0.166, 0.489, 0.371)),
    (-96, ('[NPC][Abyssal][Firestorm T3 (Some T5 Rooms)]Drifter', 0.43, 0.201, 0.43, 0.43)),
    (-97, ('[NPC][Abyssal][Firestorm T3 (Some T5 Rooms)]Sleeper', 0.512, 0.337, 0.512, 0.512)),
    (-98, ('[NPC][Abyssal][Firestorm T3 (Some T5 Rooms)]All', 0.537, 0.269, 0.512, 0.495)),
    (-99, ('[NPC][Abyssal][Firestorm T4/T5/T6]Drones', 0.461, 0.305, 0.541, 0.443)),
    (-100, ('[NPC][Abyssal][Firestorm T4/T5/T6]Overmind', 0.666, 0.345, 0.634, 0.646)),
    (-101, ('[NPC][Abyssal][Firestorm T4/T5/T6]Seeker', 0.084, 0, 0.084, 0.084)),
    (-102, ('[NPC][Abyssal][Firestorm T4/T5/T6]Triglavian', 0.537, 0.085, 0.489, 0.371)),
    (-103, ('[NPC][Abyssal][Firestorm T4/T5/T6]Drifter', 0.43, 0.117, 0.43, 0.43)),
    (-104, ('[NPC][Abyssal][Firestorm T4/T5/T6]Sleeper', 0.512, 0.276, 0.512, 0.512)),
    (-105, ('[NPC][Abyssal][Firestorm T4/T5/T6]All', 0.537, 0.201, 0.512, 0.495)),
    (-106, ('[NPC][Abyssal][Exotic T0/T1/T2]Drones', 0.439, 0.522, 0.417, 0.435)),
    (-107, ('[NPC][Abyssal][Exotic T0/T1/T2]Overmind', 0.643, 0.593, 0.511, 0.639)),
    (-108, ('[NPC][Abyssal][Exotic T0/T1/T2]Seeker', 0.082, 0.082, 0, 0.082)),
    (-109, ('[NPC][Abyssal][Exotic T0/T1/T2]Triglavian', 0.494, 0.41, 0.304, 0.376)),
    (-110, ('[NPC][Abyssal][Exotic T0/T1/T2]Drifter', 0.415, 0.415, 0.277, 0.415)),
    (-111, ('[NPC][Abyssal][Exotic T0/T1/T2]Sleeper', 0.435, 0.435, 0.329, 0.435)),
    (-112, ('[NPC][Abyssal][Exotic T0/T1/T2]All', 0.508, 0.474, 0.359, 0.488)),
    (-113, ('[NPC][Abyssal][Exotic T3 (Some T5 Rooms)]Drones', 0.439, 0.522, 0.351, 0.435)),
    (-114, ('[NPC][Abyssal][Exotic T3 (Some T5 Rooms)]Overmind', 0.643, 0.593, 0.435, 0.639)),
    (-115, ('[NPC][Abyssal][Exotic T3 (Some T5 Rooms)]Seeker', 0.082, 0.082, 0, 0.082)),
    (-116, ('[NPC][Abyssal][Exotic T3 (Some T5 Rooms)]Triglavian', 0.494, 0.41, 0.198, 0.376)),
    (-117, ('[NPC][Abyssal][Exotic T3 (Some T5 Rooms)]Drifter', 0.415, 0.415, 0.191, 0.415)),
    (-118, ('[NPC][Abyssal][Exotic T3 (Some T5 Rooms)]Sleeper', 0.435, 0.435, 0.268, 0.435)),
    (-119, ('[NPC][Abyssal][Exotic T3 (Some T5 Rooms)]All', 0.508, 0.474, 0.276, 0.488)),
    (-120, ('[NPC][Abyssal][Exotic T4/T5/T6]Drones', 0.439, 0.522, 0.293, 0.435)),
    (-121, ('[NPC][Abyssal][Exotic T4/T5/T6]Overmind', 0.643, 0.593, 0.362, 0.639)),
    (-122, ('[NPC][Abyssal][Exotic T4/T5/T6]Seeker', 0.082, 0.082, 0, 0.082)),
    (-123, ('[NPC][Abyssal][Exotic T4/T5/T6]Triglavian', 0.494, 0.41, 0.122, 0.376)),
    (-124, ('[NPC][Abyssal][Exotic T4/T5/T6]Drifter', 0.415, 0.415, 0.111, 0.415)),
    (-125, ('[NPC][Abyssal][Exotic T4/T5/T6]Sleeper', 0.435, 0.435, 0.215, 0.435)),
    (-126, ('[NPC][Abyssal][Exotic T4/T5/T6]All', 0.508, 0.474, 0.208, 0.488)),
    (-127, ('[NPC][Abyssal][Gamma T0/T1/T2]Drones', 0.449, 0.54, 0.549, 0.336)),
    (-128, ('[NPC][Abyssal][Gamma T0/T1/T2]Overmind', 0.619, 0.574, 0.612, 0.522)),
    (-129, ('[NPC][Abyssal][Gamma T0/T1/T2]Seeker', 0.085, 0.085, 0.085, 0)),
    (-130, ('[NPC][Abyssal][Gamma T0/T1/T2]Triglavian', 0.477, 0.4, 0.461, 0.202)),
    (-131, ('[NPC][Abyssal][Gamma T0/T1/T2]Drifter', 0.437, 0.437, 0.437, 0.295)),
    (-132, ('[NPC][Abyssal][Gamma T0/T1/T2]Sleeper', 0.435, 0.435, 0.435, 0.329)),
    (-133, ('[NPC][Abyssal][Gamma T0/T1/T2]All', 0.493, 0.468, 0.492, 0.35)),
    (-134, ('[NPC][Abyssal][Gamma T3 (Some T5 Rooms)]Drones', 0.449, 0.54, 0.549, 0.264)),
    (-135, ('[NPC][Abyssal][Gamma T3 (Some T5 Rooms)]Overmind', 0.619, 0.574, 0.612, 0.449)),
    (-136, ('[NPC][Abyssal][Gamma T3 (Some T5 Rooms)]Seeker', 0.085, 0.085, 0.085, 0)),
    (-137, ('[NPC][Abyssal][Gamma T3 (Some T5 Rooms)]Triglavian', 0.477, 0.4, 0.461, 0.081)),
    (-138, ('[NPC][Abyssal][Gamma T3 (Some T5 Rooms)]Drifter', 0.437, 0.437, 0.437, 0.206)),
    (-139, ('[NPC][Abyssal][Gamma T3 (Some T5 Rooms)]Sleeper', 0.435, 0.435, 0.435, 0.268)),
    (-140, ('[NPC][Abyssal][Gamma T3 (Some T5 Rooms)]All', 0.493, 0.468, 0.492, 0.264)),
    (-141, ('[NPC][Abyssal][Gamma T4/T5/T6]Drones', 0.449, 0.54, 0.549, 0.197)),
    (-142, ('[NPC][Abyssal][Gamma T4/T5/T6]Overmind', 0.619, 0.574, 0.612, 0.379)),
    (-143, ('[NPC][Abyssal][Gamma T4/T5/T6]Seeker', 0.085, 0.085, 0.085, 0)),
    (-144, ('[NPC][Abyssal][Gamma T4/T5/T6]Triglavian', 0.477, 0.4, 0.461, 0.034)),
    (-145, ('[NPC][Abyssal][Gamma T4/T5/T6]Drifter', 0.437, 0.437, 0.437, 0.121)),
    (-146, ('[NPC][Abyssal][Gamma T4/T5/T6]Sleeper', 0.435, 0.435, 0.435, 0.215)),
    (-147, ('[NPC][Abyssal][Gamma T4/T5/T6]All', 0.493, 0.468, 0.492, 0.196)),
    # Source: ticket #2265
    (-148, ('[NPC][Abyssal][Dark Matter All Tiers]Concord', 0.324, 0.318, 0.369, 0.372)),
    (-149, ('[NPC][Abyssal][Dark Matter All Tiers]Sansha', 0.137, 0.331, 0.332, 0.322)),
    (-150, ('[NPC][Abyssal][Dark Matter All Tiers]Angel', 0.582, 0.508, 0.457, 0.416)),
    (-151, ('[NPC][Abyssal][Electrical T0/T1/T2]Concord', 0.121, 0.318, 0.369, 0.372)),
    (-152, ('[NPC][Abyssal][Electrical T0/T1/T2]Sansha', 0.034, 0.331, 0.332, 0.322)),
    (-153, ('[NPC][Abyssal][Electrical T0/T1/T2]Angel', 0.456, 0.508, 0.457, 0.416)),
    (-154, ('[NPC][Abyssal][Electrical T3 (Some T5 Rooms)]Concord', 0.025, 0.318, 0.369, 0.372)),
    (-155, ('[NPC][Abyssal][Electrical T3 (Some T5 Rooms)]Sansha', 0.018, 0.331, 0.332, 0.322)),
    (-156, ('[NPC][Abyssal][Electrical T3 (Some T5 Rooms)]Angel', 0.373, 0.508, 0.457, 0.416)),
    (-157, ('[NPC][Abyssal][Electrical T4/T5/T6]Concord', 0.008, 0.318, 0.369, 0.372)),
    (-158, ('[NPC][Abyssal][Electrical T4/T5/T6]Sansha', 0.009, 0.331, 0.332, 0.322)),
    (-159, ('[NPC][Abyssal][Electrical T4/T5/T6]Angel', 0.3, 0.508, 0.457, 0.416)),
    (-160, ('[NPC][Abyssal][Firestorm T0/T1/T2]Concord', 0.324, 0.107, 0.369, 0.372)),
    (-161, ('[NPC][Abyssal][Firestorm T0/T1/T2]Sansha', 0.148, 0.181, 0.329, 0.328)),
    (-162, ('[NPC][Abyssal][Firestorm T0/T1/T2]Angel', 0.587, 0.342, 0.439, 0.39)),
    (-163, ('[NPC][Abyssal][Firestorm T3 (Some T5 Rooms)]Concord', 0.324, 0.016, 0.369, 0.372)),
    (-164, ('[NPC][Abyssal][Firestorm T3 (Some T5 Rooms)]Sansha', 0.148, 0.14, 0.329, 0.328)),
    (-165, ('[NPC][Abyssal][Firestorm T3 (Some T5 Rooms)]Angel', 0.587, 0.241, 0.439, 0.39)),
    (-166, ('[NPC][Abyssal][Firestorm T4/T5/T6]Concord', 0.324, 0.004, 0.369, 0.372)),
    (-167, ('[NPC][Abyssal][Firestorm T4/T5/T6]Sansha', 0.148, 0.106, 0.329, 0.328)),
    (-168, ('[NPC][Abyssal][Firestorm T4/T5/T6]Angel', 0.587, 0.172, 0.439, 0.39)),
    (-169, ('[NPC][Abyssal][Exotic T0/T1/T2]Concord', 0.324, 0.318, 0.18, 0.372)),
    (-170, ('[NPC][Abyssal][Exotic T0/T1/T2]Sansha', 0.137, 0.331, 0.166, 0.322)),
    (-171, ('[NPC][Abyssal][Exotic T0/T1/T2]Angel', 0.582, 0.508, 0.295, 0.416)),
    (-172, ('[NPC][Abyssal][Exotic T3 (Some T5 Rooms)]Concord', 0.324, 0.318, 0.089, 0.372)),
    (-173, ('[NPC][Abyssal][Exotic T3 (Some T5 Rooms)]Sansha', 0.137, 0.331, 0.108, 0.322)),
    (-174, ('[NPC][Abyssal][Exotic T3 (Some T5 Rooms)]Angel', 0.582, 0.508, 0.203, 0.416)),
    (-175, ('[NPC][Abyssal][Exotic T4/T5/T6]Concord', 0.324, 0.318, 0.068, 0.372)),
    (-176, ('[NPC][Abyssal][Exotic T4/T5/T6]Sansha', 0.137, 0.331, 0.073, 0.322)),
    (-177, ('[NPC][Abyssal][Exotic T4/T5/T6]Angel', 0.582, 0.508, 0.14, 0.416)),
    (-178, ('[NPC][Abyssal][Gamma T0/T1/T2]Concord', 0.324, 0.318, 0.369, 0.203)),
    (-179, ('[NPC][Abyssal][Gamma T0/T1/T2]Sansha', 0.137, 0.355, 0.352, 0.16)),
    (-180, ('[NPC][Abyssal][Gamma T0/T1/T2]Angel', 0.59, 0.528, 0.477, 0.286)),
    (-181, ('[NPC][Abyssal][Gamma T3 (Some T5 Rooms)]Concord', 0.324, 0.318, 0.369, 0.112)),
    (-182, ('[NPC][Abyssal][Gamma T3 (Some T5 Rooms)]Sansha', 0.137, 0.355, 0.352, 0.05)),
    (-183, ('[NPC][Abyssal][Gamma T3 (Some T5 Rooms)]Angel', 0.59, 0.528, 0.477, 0.197)),
    (-184, ('[NPC][Abyssal][Gamma T4/T5/T6]Concord', 0.324, 0.318, 0.369, 0.086)),
    (-185, ('[NPC][Abyssal][Gamma T4/T5/T6]Sansha', 0.137, 0.355, 0.352, 0)),
    (-186, ('[NPC][Abyssal][Gamma T4/T5/T6]Angel', 0.59, 0.528, 0.477, 0.126))])


class TargetProfile:

    # also determined import/export order - VERY IMPORTANT
    DAMAGE_TYPES = ('em', 'thermal', 'kinetic', 'explosive')
    _idealTarget = None
    _builtins = None

    def __init__(self, *args, **kwargs):
        self.builtin = False
        self.update(*args, **kwargs)

    @reconstructor
    def init(self):
        self.builtin = False

    def update(self, emAmount=0, thermalAmount=0, kineticAmount=0, explosiveAmount=0, maxVelocity=None, signatureRadius=None, radius=None):
        self.emAmount = emAmount
        self.thermalAmount = thermalAmount
        self.kineticAmount = kineticAmount
        self.explosiveAmount = explosiveAmount
        self._maxVelocity = maxVelocity
        self._signatureRadius = signatureRadius
        self._radius = radius

    @classmethod
    def getBuiltinList(cls):
        if cls._builtins is None:
            cls.__generateBuiltins()
        return list(cls._builtins.values())

    @classmethod
    def getBuiltinById(cls, id):
        if cls._builtins is None:
            cls.__generateBuiltins()
        return cls._builtins.get(id)

    @classmethod
    def __generateBuiltins(cls):
        cls._builtins = OrderedDict()
        for id, data in BUILTINS.items():
            rawName = data[0]
            data = data[1:]
            profile = TargetProfile(*data)
            profile.ID = id
            profile.rawName = rawName
            profile.builtin = True
            cls._builtins[id] = profile

    @classmethod
    def getIdeal(cls):
        if cls._idealTarget is None:
            cls._idealTarget = cls(
                emAmount=0,
                thermalAmount=0,
                kineticAmount=0,
                explosiveAmount=0,
                maxVelocity=0,
                signatureRadius=None,
                radius=0)
            cls._idealTarget.rawName = 'Ideal Target'
            cls._idealTarget.ID = 0
            cls._idealTarget.builtin = True
        return cls._idealTarget

    @property
    def maxVelocity(self):
        return self._maxVelocity or 0

    @maxVelocity.setter
    def maxVelocity(self, val):
        self._maxVelocity = val

    @property
    def signatureRadius(self):
        if self._signatureRadius is None or self._signatureRadius == -1:
            return math.inf
        return self._signatureRadius

    @signatureRadius.setter
    def signatureRadius(self, val):
        if val is not None and math.isinf(val):
            val = None
        self._signatureRadius = val

    @property
    def radius(self):
        return self._radius or 0

    @radius.setter
    def radius(self, val):
        self._radius = val

    @classmethod
    def importPatterns(cls, text):
        lines = re.split('[\n\r]+', text)
        patterns = []
        numPatterns = 0

        # When we import damage profiles, we create new ones and update old ones. To do this, get a list of current
        # patterns to allow lookup
        lookup = {}
        current = eos.db.getTargetProfileList()
        for pattern in current:
            lookup[pattern.rawName] = pattern

        for line in lines:
            try:
                if line.strip()[0] == "#":  # comments
                    continue
                line = line.split('#', 1)[0]  # allows for comments
                type, data = line.rsplit('=', 1)
                type, data = type.strip(), [d.strip() for d in data.split(',')]
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                pyfalog.warning("Data isn't in correct format, continue to next line.")
                continue

            if type not in ("TargetProfile", "TargetResists"):
                continue

            numPatterns += 1
            name, dataRes, dataMisc = data[0], data[1:5], data[5:8]
            fields = {}

            for index, val in enumerate(dataRes):
                val = float(val) if val else 0
                if math.isinf(val):
                    val = 0
                try:
                    assert 0 <= val <= 100
                    fields["%sAmount" % cls.DAMAGE_TYPES[index]] = val / 100
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    pyfalog.warning("Caught unhandled exception in import patterns.")
                    continue

            if len(dataMisc) == 3:
                for index, val in enumerate(dataMisc):
                    try:
                        fieldName = ("maxVelocity", "signatureRadius", "radius")[index]
                    except IndexError:
                        break
                    val = float(val) if val else 0
                    if fieldName != "signatureRadius" and math.isinf(val):
                        val = 0
                    fields[fieldName] = val

            if len(fields) in (4, 7):  # Avoid possible blank lines
                if name.strip() in lookup:
                    pattern = lookup[name.strip()]
                    pattern.update(**fields)
                    eos.db.save(pattern)
                else:
                    pattern = TargetProfile(**fields)
                    pattern.rawName = name.strip()
                    eos.db.save(pattern)
                patterns.append(pattern)

        eos.db.commit()

        return patterns, numPatterns

    EXPORT_FORMAT = "TargetProfile = %s,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f\n"

    @classmethod
    def exportPatterns(cls, *patterns):
        out = "# Exported from pyfa\n#\n"
        out += "# Values are in following format:\n"
        out += "# TargetProfile = [name],[EM %],[Thermal %],[Kinetic %],[Explosive %],[Max velocity m/s],[Signature radius m],[Radius m]\n\n"
        for dp in patterns:
            out += cls.EXPORT_FORMAT % (
                dp.rawName,
                dp.emAmount * 100,
                dp.thermalAmount * 100,
                dp.kineticAmount * 100,
                dp.explosiveAmount * 100,
                dp.maxVelocity,
                dp.signatureRadius,
                dp.radius
            )

        return out.strip()

    @property
    def name(self):
        return self.rawName

    @property
    def fullName(self):
        categories, tail = self.__parseRawName()
        return '{}{}'.format(''.join('[{}]'.format(c) for c in categories), tail)

    @property
    def shortName(self):
        return self.__parseRawName()[1]

    @property
    def hierarchy(self):
        return self.__parseRawName()[0]

    def __parseRawName(self):
        hierarchy = []
        remainingName = self.rawName.strip() if self.rawName else ''
        while True:
            start, end = remainingName.find('['), remainingName.find(']')
            if start == -1 or end == -1:
                return hierarchy, remainingName
            splitter = remainingName.find('|')
            if splitter != -1 and splitter == start - 1:
                return hierarchy, remainingName[1:]
            hierarchy.append(remainingName[start + 1:end])
            remainingName = remainingName[end + 1:].strip()

    def __deepcopy__(self, memo):
        p = TargetProfile(
            self.emAmount, self.thermalAmount, self.kineticAmount, self.explosiveAmount,
            self._maxVelocity, self._signatureRadius, self._radius)
        p.rawName = "%s copy" % self.rawName
        return p
