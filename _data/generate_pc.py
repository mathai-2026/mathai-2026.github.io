

lines = open("reviewers.txt").readlines()
# print(pcs)

names = []
for line in lines[1:]:
    names.append(line.strip())

names = sorted(names, key=lambda name : name.split()[0], reverse=False)

for name in names:
    print(f'"{name}",')

