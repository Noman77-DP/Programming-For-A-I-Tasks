

student = {
    "name": "Noman",
    "age": 20,
    "course": "AI",
    "university": "Dawood University",
    "semester": 4,
    "city": "Panoakil",
    "email": "nomandp77@gmail.com",
    "phone": "0301-3888324"
}

print("Hey, this is the student's name:", student["name"])
print("Age:", student["age"])
print("Course:", student.get("course"))
print("University:", student["university"])
print("Semester:", student["semester"])
print("City:", student["city"])
print("Email:", student["email"])
print("Phone:", student["phone"])


if "address" in student:
    print("Address exists")
else:
    print("Address key is not found, let's add it!")


student["address"] = "Foujhi Colony Panoakil"
print("Updated info:", student)
