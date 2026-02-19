import psutil

def get_ram_usage_mb():
    mem = psutil.virtual_memory()
    return round(mem.used / 1024 / 1024, 2)

def get_storage_usage_mb():
    disk = psutil.disk_usage('/')
    return round(disk.used / 1024 / 1024, 2)
