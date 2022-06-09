import csv

data = []
for row in csv.DictReader(open("data.csv")):
    last_name = row["LAST NAME"].lower()
    full_name = f"{row['FIRST NAME']} {last_name}".lower()
    alias = row["ALIAS"]
    data.append(f"{full_name}, {alias}, professor")
    data.append(f"{last_name}, {alias}, professor")

    if row.get("COURSE"):
        course_name = row["COURSE NAME"].lower()
        course = row["COURSE"]
        data.append(f"{course_name}, {course}, course")
        data.append(f"{course.lower()}, {course}, course")

data = list(set(data))
data.sort(key=lambda x: len(x.split(",")[0]), reverse=True)

with open("model.txt", "w") as f:
    f.write("\n".join(data))