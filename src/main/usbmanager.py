import subprocess
import pyudev
import psutil

class USBManager:
    def __init__(self):
        self.context = pyudev.Context()
        self.ports = ("1-1.1", "1-1.3")

	##### INTERNALS #####
    # get port path
    def _get_port(self, device):
        parent = device.find_parent('usb', 'usb_device')
        if parent:
            for part in parent.device_path.split('/'):
                if part.startswith("1-1."):
                    return part
        return None

    # get label
    def _get_label(self, devNode):
        try:
            result = subprocess.check_output(["blkid", devNode]).decode()
            for part in result.split():
                if "LABEL=" in part:
                    return part.split("=")[1].strip('"')
        except:
            print(f"Could not retrieve drive label on devnode : {devNode}")
        return "unknown"

    def _mount_if_needed(self, devNode):
        mountPoint = f"/mnt/{devNode.split('/')[-1]}"
        
        try:
            subprocess.run(["mkdir", "-p", mountPoint], check=True)
            subprocess.run(["mount", devNode, mountPoint], check=True)
            return mountPoint
        except: return None

    # get mount + size
    def _get_mount_info(self, devNode):
        for part in psutil.disk_partitions():
            if part.device == devNode:
                usage = psutil.disk_usage(part.mountpoint)
                return {
                    "mount" : part.mountpoint,
                    "size" : usage.total,
                    "free" : usage.free
                }

        # not mounted → mount it
        mountPoint = self._mount_if_needed(devNode)
        if mountPoint:
            usage = psutil.disk_usage(mountPoint)
            return {
                "mount" : mountPoint,
                "size" : usage.total,
                "free" : usage.free
            }

        return None
	
	##### PUBLIC #####
    # get all drives on selected ports
    def get_drives(self):
        drives = {}

        for device in self.context.list_devices(subsystem='block', DEVTYPE='partition'):
            devNode = device.device_node
            port = self._get_port(device)

            if port in self.ports:
                info = self._get_mount_info(devNode)

                drives[port] = {
                    "device" : devNode,
                    "label" : self._get_label(devNode),
                    "mount" : info["mount"] if info else None,
                    "size" : round(info["size"] / (1024 ** 3), 2) if info else 0,
                    "free" : round(info["free"] / (1024 ** 3), 2) if info else 0
                }

        return drives

    def get_ready_drives(self):
        drives = {
            self.ports[0] : False,
            self.ports[1] : False,
        }
        
        for device in self.context.list_devices(subsystem='block', DEVTYPE='partition'):
            devNode = device.device_node
            port = self._get_port(device)

            if port in self.ports:
                drives[port] = True
        
        return list(drives.values())

    # get single port
    def get_drive(self, port):
        return self.get_drives().get(self.ports[port], None)
