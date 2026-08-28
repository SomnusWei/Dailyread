import os

d = '/opt/dailyread-server'
b = chr(92)  # backslash
removed = 0
for root, dirs, files in os.walk(d):
    if b + 'node_modules' in root:
        continue
    for n in list(dirs) + list(files):
        if b in n:
            p = os.path.join(root, n)
            print('remove:', p)
            if os.path.isdir(p):
                import shutil
                shutil.rmtree(p, ignore_errors=True)
            else:
                try:
                    os.remove(p)
                except OSError:
                    pass
            removed += 1
print('removed count:', removed)
