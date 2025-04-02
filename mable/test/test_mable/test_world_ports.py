"""
Tests for world_ports module.
"""

import os

import mable.extensions.world_ports as wp


def test_get_ports(tmp_path):
    os.chdir(tmp_path)
    filename = "ports.csv"
    with open(filename, 'w') as ports_file:
        ports_file.write("Port_Name,Position_Latitude,Position_Longitude\n")
        ports_file.write("Aberdeen-f8ea5ddd09c3  , 57.14151,-2.07729 \n")
        ports_file.write("Abidjan-ef95aea8399b, 5.28604,-3.97572\n")
        ports_file.flush()
    ports = wp.get_ports(filename)
    assert len(ports) == 2
    assert ports[0].name == "Aberdeen-f8ea5ddd09c3"
    assert ports[0].latitude == 57.14151
    assert ports[0].longitude == -2.07729
    assert ports[1].name == "Abidjan-ef95aea8399b"
    assert ports[1].latitude == 5.28604
    assert ports[1].longitude == -3.97572
