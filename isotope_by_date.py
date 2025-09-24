import msgpack

dates = [
    '2020.5.26',
    '2020.5.27',
    '2023.9.6',
    '2024.3.14',
    '2024.3.15',
    '2024.3.19',
    '2024.3.20',
    '2024.2.9',
    '2024.2.13',
    '2024.2.20',
    '2024.2.21',
    '2024.2.22',
    '2024.3.1'
]

db = None
with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\index.msgpk', 'rb') as file:
    db = msgpack.unpackb(file.read(), strict_map_key=False)

for shotn in db:
    shot = db[shotn]
    if 'date' in shot and shot['date'].split(' ')[0] in dates:
        print(shot['date'].split(' ')[0], shot['shotn'], shot['plasma isotope'])

print('OK')