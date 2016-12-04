# Copyright 2014 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#
from __future__ import absolute_import

import glob
import os

from vdsm import utils
from vdsm.network.netinfo import misc


NET_CONF_DIR = '/etc/sysconfig/network-scripts/'
NET_CONF_PREF = NET_CONF_DIR + 'ifcfg-'


class IfcfgAcquire(object):
    @staticmethod
    def acquire_device(device):
        """
        Attempts to detect a device ifcfg file and rename it to a vdsm
        supported format.
        In case of multiple ifcfg files that treat the same device, all except
        the first are deleted.
        """
        device_files = IfcfgAcquire._collect_device_files(device)
        IfcfgAcquire._normalize_device_filenames(device, device_files)

    @staticmethod
    def acquire_vlan_device(device):
        """
        VLAN devices may be represented in an ifcfg configuration syntax that
        is different from the common case. Specifically when being created
        using Network Manager.
        """
        device_files = IfcfgAcquire._collect_vlan_device_files(device)
        IfcfgAcquire._normalize_device_filenames(device, device_files)

    @staticmethod
    def _collect_device_files(device):
        device_files = []
        paths = glob.iglob(NET_CONF_PREF + '*')
        for ifcfg_file in paths:
            conf = misc.ifcfg_config(ifcfg_file)
            if conf.get('DEVICE') == device:
                device_files.append(ifcfg_file)
        return device_files

    @staticmethod
    def _collect_vlan_device_files(device):
        device_files = []
        paths = glob.iglob(NET_CONF_PREF + '*')
        for ifcfg_file in paths:
            conf = misc.ifcfg_config(ifcfg_file)
            is_vlan_device = conf.get('TYPE', '').upper() == 'VLAN'
            config_device = '{}.{}'.format(conf.get('PHYSDEV'),
                                           conf.get('VLAN_ID'))
            if is_vlan_device and config_device == device:
                device_files.append(ifcfg_file)
        return device_files

    @staticmethod
    def _config_entry(line):
        key, value = line.rstrip().split('=', 1)
        if value and value[0] == '\"' and value[-1] == '\"':
            value = value[1:-1]
        return key.upper(), value

    @staticmethod
    def _normalize_device_filenames(device, device_files):
        if device_files:
            os.rename(device_files[0], NET_CONF_PREF + device)
            for filepath in device_files[1:]:
                utils.rmFile(filepath)
