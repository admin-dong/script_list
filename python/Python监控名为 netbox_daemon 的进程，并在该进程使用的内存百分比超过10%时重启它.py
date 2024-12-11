#!/usr/bin/python3.6
# coding: utf-8

import psutil
import subprocess


def run_command(cmd, branch=True):
    status, output = subprocess.getstatusoutput(cmd)
    result = output.strip().strip('\n')
    if branch:
        return status, [x for x in result.split('\n') if not x == '']
    else:
        return status, result


def main():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.name() == 'netbox_daemon':
            if proc.memory_percent() > 10.0:
                # proc.terminate()
                run_command('systemctl restart netbox_daemon')


if __name__ == '__main__':
    main()